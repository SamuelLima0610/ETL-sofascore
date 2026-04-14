from celery import Celery
from etl.extractor import Extractor
from etl.transform import Transform
from etl.load import Load
from utils.database import Database
from dotenv import load_dotenv
import os
from typing import List, Optional, Union
from utils import process
from utils.tournaments import has_draws
from etl.features import compute_season_features, generate_match_features, season_features_to_dataframe
from models.train_model import (
    prepare_training_data,
    split_and_scale_data,
    train_logistic_regression,
    train_random_forest,
    train_xgboost,
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
        database = Database()
        loader = Load(database)
        
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
            
            # Carrega os times
            teams = transformer.transform_teams()
            self.update_state(state='PROGRESS', meta={'current': 0, 'total': len(teams), 'status': f'{len(teams)} equipes encontradas', 'tournament_name': tournament_name, 'seasons_id': season_id})
            loader.insert_data(teams, 'teams')
            self.update_state(state='PROGRESS', meta={'current': len(teams), 'total': len(teams), 'status': 'Equipes salvas no MongoDB', 'tournament_name': tournament_name, 'seasons_id': season_id})
            
            #Carrega os jogadores
            player_stats = database.read_data(collection='players_stats', query={'game_id': games[0]['id']})
            if player_stats and len(player_stats) > 0:
                print('Informação dos jogadores da partida já existem no MongoDB. Pulando etapa de extração e carga dos jogadores')   
                self.update_state(state='PROGRESS', meta={'current': 0, 'total': 0, 'status': 'Informação dos jogadores da partida já existem no MongoDB. Pulando etapa de extração e carga dos jogadores', 'tournament_name': tournament_name, 'seasons_id': season_id})
            else: 
                players_stats = transformer.transform_players_stats()
                self.update_state(state='PROGRESS', meta={'current': 0, 'total': len(players_stats), 'status': f'{len(players_stats)} jogadores encontrados', 'tournament_name': tournament_name, 'seasons_id': season_id})
                database.insert_player_stats(players_stats)
                self.update_state(state='PROGRESS', meta={'current': len(players_stats), 'total': len(players_stats), 'status': 'Jogadores salvos no MongoDB', 'tournament_name': tournament_name, 'seasons_id': season_id})
                
            games = transformer.transform_games()
            # Salva no MongoDB
            loader.insert_data(games, collection)
            self.update_state(state='PROGRESS', meta={'current': len(games), 'total': len(games), 'status': 'Dados salvos no MongoDB', 'tournament_name': tournament_name, 'seasons_id': season_id})
            
            # Limpa ObjectIds do MongoDB para que os dados sejam JSON serializáveis
            games = process.clean_mongodb_ids(games)

        database.disconnect()

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
            games = transformer.transform_games()
            loader.insert_data(games, collection)
            self.update_state(state='PROGRESS', meta={'current': len(games), 'total': len(games), 'status': 'Dados salvos no MongoDB', 'tournament_name': tournament_name, 'seasons_id': ';'.join(map(str, seasons_ids)) if seasons_ids else None})
            # Limpa ObjectIds do MongoDB para que os dados sejam JSON serializáveis
            games = process.clean_mongodb_ids(games)
            
            # Carrega os times
            teams = transformer.transform_teams()
            self.update_state(state='PROGRESS', meta={'current': 0, 'total': len(teams), 'status': f'{len(teams)} equipes encontradas', 'tournament_name': tournament_name, 'seasons_id': season['id']})
            loader.insert_data(teams, 'teams')
            self.update_state(state='PROGRESS', meta={'current': len(teams), 'total': len(teams), 'status': 'Equipes salvas no MongoDB', 'tournament_name': tournament_name, 'seasons_id': season['id']})
            
            #Carrega os jogadores
            player_stats = database.read_data(collection='players_stats', query={'game_id': games[0]['id']})
            if player_stats and len(player_stats) > 0:
                self.update_state(state='PROGRESS', meta={'current': 0, 'total': 0, 'status': 'Informação dos jogadores da partida já existem no MongoDB. Pulando etapa de extração e carga dos jogadores', 'tournament_name': tournament_name, 'seasons_id': season['id']})
            else: 
                players_stats = transformer.transform_players_stats()
                self.update_state(state='PROGRESS', meta={'current': 0, 'total': len(players_stats), 'status': f'{len(players_stats)} jogadores encontrados', 'tournament_name': tournament_name, 'seasons_id': season['id']})
                database.insert_player_stats(players_stats)
                self.update_state(state='PROGRESS', meta={'current': len(players_stats), 'total': len(players_stats), 'status': 'Jogadores salvos no MongoDB', 'tournament_name': tournament_name, 'seasons_id': season['id']})
            
        database.disconnect()
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
def predict_match_task(self, category: str, game_id: int, home_team: str, away_team: str, tournament_id: int, season_id: int):
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Realizando predição...'})
        database = Database()

        # 1. Buscar dados da temporada e gerar features
        games_processed, teams_elo_raiting = compute_season_features(database, collection=category, season_id=season_id, tournament_id=tournament_id)
        
        # Validar se há dados suficientes para treino
        if not games_processed or len(games_processed) == 0:
            database.disconnect()
            raise ValueError(f"Nenhum jogo encontrado para treino na temporada {season_id} {category}. Verifique os dados no MongoDB.")
        
        df = season_features_to_dataframe(games_processed)
        
        # Validar se o DataFrame tem a coluna 'result'
        if df.empty or 'result' not in df.columns:
            database.disconnect()
            raise ValueError(f"DataFrame não contém coluna 'result' na temporada {season_id} {category}. Verifique os dados no MongoDB.")

        # 2. Preparar dados de treino
        X, y = prepare_training_data(df)
        
        # Validar se y foi obtido corretamente
        if y is None:
            database.disconnect()
            raise ValueError("Falha ao extrair coluna 'result' dos dados de treino")

        # 3. Separar em treino/teste e normalizar
        X_train_scaled, _, y_train, _, scaler = split_and_scale_data(X, y)

        # 4. Treinar modelos (Logistic Regression, Random Forest, XGBoost)
        model_lr = train_logistic_regression(X_train_scaled, y_train)
        model_rf = train_random_forest(X_train_scaled, y_train)
        model_xgb = train_xgboost(X_train_scaled, y_train)

        # 5. Preparar dados de predição
        to_predict = generate_match_features(
            database, 
            collection=category, 
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

        # 7. Fazer predições com todos os modelos e calcular média
        predictions = []
        for model in [model_lr, model_rf, model_xgb]:
            y_prob = model.predict_proba(df_predict_scaled)[0]
            prob_by_class = dict(zip(model.classes_, y_prob))
            predictions.append({
                'home': float(prob_by_class.get(1, 0.0)),
                'draw': float(prob_by_class.get(0, 0.0)),
                'away': float(prob_by_class.get(-1, 0.0))
            })
        
        # Calcular média das probabilidades
        home_prob = sum(p['home'] for p in predictions) / len(predictions)
        draw_prob = sum(p['draw'] for p in predictions) / len(predictions)
        away_prob = sum(p['away'] for p in predictions) / len(predictions)
        
        # 8. Ajustar probabilidades conforme categoria de esporte
        
        # Se o esporte não permite empate, ajustar probabilidades
        if not has_draws(category):
            # Se houver probabilidade de empate, redistribuir entre home e away proporcionalmente
            if draw_prob > 0:
                total_non_draw = home_prob + away_prob
                if total_non_draw > 0:
                    # Redistribuir o draw_prob mantendo a proporção entre home e away
                    home_prob = home_prob + (draw_prob * home_prob / total_non_draw)
                    away_prob = away_prob + (draw_prob * away_prob / total_non_draw)
                else:
                    # Se ambos têm probabilidade zero, dividir o draw_prob igualmente
                    home_prob = draw_prob / 2
                    away_prob = draw_prob / 2
            draw_prob = 0.0
        
        # Normalizar para garantir que soma = 1.0
        total_prob = home_prob + draw_prob + away_prob
        if total_prob > 0:
            home_prob = home_prob / total_prob
            draw_prob = draw_prob / total_prob
            away_prob = away_prob / total_prob
        
        prediction = {
            "home_team": home_team,
            "away_team": away_team,
            "game_id": game_id,
            "database_size": len(games_processed),
            "home_team_win_probability": home_prob,
            "draw_probability": draw_prob,
            "away_team_win_probability": away_prob,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        database.insert_prediction(prediction)
        database.disconnect()
    except Exception as e:
        print(e)
        database.disconnect()
        raise