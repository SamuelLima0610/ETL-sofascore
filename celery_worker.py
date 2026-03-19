from celery import Celery
from etl.extractor import Extractor
from etl.transform import Transform
from etl.load import Load
from utils.database import Database
from dotenv import load_dotenv
import os
from typing import List, Optional, Union
from utils import process
from etl.features import compute_season_features, generate_match_features, season_features_to_dataframe
from models.train_model import (
    prepare_training_data,
    split_and_scale_data,
    train_logistic_regression,
    prepare_prediction_data
)
from datetime import datetime


load_dotenv()

# Configuração do Celery com Redis como broker
REDIS_URL = os.getenv('REDIS_URL', os.getenv('REDIS_URL'))

celery_app = Celery(
    'etl_statistics',
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Configurações do Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Sao_Paulo',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hora
    task_soft_time_limit=3300,  # 55 minutos
)

@celery_app.task(bind=True, name='extract_games_by_season')
def extract_games_by_season_task(self, season_id: int, tournament_id: int, collection: str = "games", tournament_name: str="Unknow"):
    try:
        # Atualiza progresso
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': 0, 'status': 'Iniciando extração...', 'tournament_name': tournament_name, 'seasons_id': season_id})
        
        # Inicializa extractor
        extractor = Extractor()
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': 0, 'status': 'Extractor inicializado', 'tournament_name': tournament_name, 'seasons_id': season_id})
        
        # Extrai jogos
        games = extractor.get_games_by_season(tournament_id, season_id)
        self.update_state(state='PROGRESS', meta={'current': len(games), 'total': len(games), 'status': f'{len(games)} jogos extraídos', 'tournament_name': tournament_name, 'seasons_id': season_id})
        
        # Aplica transformações se necessário
        if games:
            transformer = Transform(games, tournament_id)
            games = transformer.transform()
            # Salva no MongoDB
            database = Database()
            loader = Load(database)
            games_saved = database.read_data(collection, {'season': season_id, 'tournament_id': tournament_id})
            if len(games_saved) == len(games):
                self.update_state(state='PROGRESS', meta={'current': len(games), 'total': len(games), 'status': 'Dados já existem no MongoDB', 'tournament_name': tournament_name, 'seasons_id': season_id})
            else:
                loader.insert_data(games, collection)
                self.update_state(state='PROGRESS', meta={'current': len(games), 'total': len(games), 'status': 'Dados salvos no MongoDB', 'tournament_name': tournament_name, 'seasons_id': season_id})
            database.disconnect()
            
            # Limpa ObjectIds do MongoDB para que os dados sejam JSON serializáveis
            games = process.clean_mongodb_ids(games)
        
        return {
            'status': 'completed',
            'seasons_id': season_id,
            'total_games': len(games),
            'tournament_name': tournament_name
        }
    except Exception as e:
        raise


@celery_app.task(bind=True, name='extract_all_games')
def extract_all_games_task(
    self,
    slug_tournament: str,
    tournament_id: int,
    country: str = "brazil",
    collection: str = "games",
    seasons_ids: Optional[Union[int, List[int]]] = None,
    tournament_name: str = "Unknow"
):
    try:
        # Atualiza progresso
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': 0, 'status': 'Iniciando extração...', 'tournament_name': tournament_name})
        
        # Inicializa extractor
        extractor = Extractor()
        database = Database()
        loader = Load(database)
        competition_url = f"https://www.sofascore.com/pt/football/tournament/{country}/{slug_tournament}/{tournament_id}"
        seasons = extractor.get_seasons(competition_url)
        total_seasons = len(seasons)
        
        self.update_state(
            state='PROGRESS', 
            meta={
                'current': 0, 
                'total': total_seasons, 
                'status': f'Encontradas {total_seasons} temporadas. Iniciando extração...',
                'tournament_name': tournament_name
            }
        )
        if seasons_ids is not None:
            if isinstance(seasons_ids, list):
                allowed_ids = set(seasons_ids)
                seasons = [season for season in seasons if season['id'] in allowed_ids]
                total_seasons = len(seasons)
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': 0,
                        'total': total_seasons,
                        'status': f'Filtrando para {total_seasons} temporadas específicas...',
                        'tournament_name': tournament_name
                    }
                )
            else:
                seasons = seasons[:seasons_ids]
                total_seasons = len(seasons)
                self.update_state(
                    state='PROGRESS', 
                    meta={
                        'current': 0, 
                        'total': total_seasons, 
                        'status': f'Limitando a {total_seasons} temporadas para pesquisar...',
                        'tournament_name': tournament_name
                    }
                )
        games = []
        for i, season in enumerate(seasons):
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': i + 1,
                    'total': total_seasons,
                    'status': f'Processando temporada {i + 1} de {total_seasons} ({season.get("year", season.get("id"))})...',
                    'tournament_name': tournament_name,
                    'seasons_id': ';'.join(map(str, seasons_ids)) if seasons_ids else None
                }
            )
            extracted_games = extractor.get_games_by_season(tournament_id, season['id'])
            games_saved = database.read_data(collection, {'season': season['id'], 'tournament_id': tournament_id})
            if len(games_saved) != len(extracted_games):
                games.extend(extracted_games)
        
        self.update_state(
            state='PROGRESS', 
            meta={
                'current': len(games), 
                'total': len(games), 
                'status': f'{len(games)} jogos extraídos de {total_seasons} temporadas',
                'tournament_name': tournament_name,
                'seasons_id': ';'.join(map(str, seasons_ids)) if seasons_ids else None
            }
        )
        
        # Aplica transformações se necessário
        if games:
            transformer = Transform(games, tournament_id)
            games = transformer.transform()
            loader.insert_data(games, collection)
            database.disconnect()
            self.update_state(state='PROGRESS', meta={'current': len(games), 'total': len(games), 'status': 'Dados salvos no MongoDB', 'tournament_name': tournament_name, 'seasons_id': ';'.join(map(str, seasons_ids)) if seasons_ids else None})
            
            # Limpa ObjectIds do MongoDB para que os dados sejam JSON serializáveis
            games = process.clean_mongodb_ids(games)
        
        return {
            'status': 'completed',
            'total_seasons': total_seasons,
            'total_games': len(games),
            'tournament_name': tournament_name
        }
    except Exception as e:
        raise


@celery_app.task(bind=True, name='get_seasons')
def get_seasons_task(self, slug_tournament: str, id_tournament: int, country: str):
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Buscando temporadas...'})
        extractor = Extractor()
        competition_url = f"https://www.sofascore.com/pt/football/tournament/{country}/{slug_tournament}/{id_tournament}"
        seasons = extractor.get_seasons(competition_url)
        return {
            'status': 'completed',
            'seasons': seasons
        }
    except Exception as e:
        raise


@celery_app.task(bind=True, name='predict_match')
def predict_match_task(self, collection, game_id: int, home_team: str, away_team: str, tournament_id: int, season_id: int):
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Realizando predição...'})
        database = Database()

        # 1. Buscar dados da temporada e gerar features
        games_processed, teams_elo_raiting = compute_season_features(database, collection=collection, season_id=season_id, tournament_id=tournament_id)
        df = season_features_to_dataframe(games_processed)

        # 2. Preparar dados de treino
        X, y = prepare_training_data(df)

        # 3. Separar em treino/teste e normalizar
        X_train_scaled, _, y_train, _, scaler = split_and_scale_data(X, y)

        # 4. Treinar modelo
        model = train_logistic_regression(X_train_scaled, y_train)

        # 5. Preparar dados de predição
        to_predict = generate_match_features(
            database, 
            collection=collection, 
            home_team=home_team, 
            away_team=away_team, 
            home_elo_raiting=teams_elo_raiting.get(home_team, 1500.0),
            away_elo_raiting=teams_elo_raiting.get(away_team, 1500.0),
            tournament_id=tournament_id, 
            season_id=season_id
        )
        df_predict = season_features_to_dataframe([to_predict])

        # 6. Preparar e normalizar dados de predição
        df_predict_scaled = prepare_prediction_data(df_predict, X.columns, scaler)

        # 7. Fazer a predição
        y_prob = model.predict_proba(df_predict_scaled)[0]
        prediction = {
            "home_team": home_team,
            "away_team": away_team,
            "game_id": game_id,
            "database_size": len(games_processed),
            "home_team_win_probability": float(y_prob[1]),
            "away_team_win_probability": float(y_prob[0]),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        database.insert_data([prediction], "predictions")
        database.disconnect()
    except Exception as e:
        print(e)
        database.disconnect()
        raise