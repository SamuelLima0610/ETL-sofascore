from celery import Celery
from etl.extractor import Extractor
from etl.transform import Transform
from etl.load import Load
from dotenv import load_dotenv
import os
from typing import List, Optional, Union

load_dotenv()

def clean_mongodb_ids(data):
    if isinstance(data, list):
        for item in data:
            if '_id' in item:
                del item['_id']
        return data
    elif isinstance(data, dict):
        if '_id' in data:
            del data['_id']
        return data
    return data

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
def extract_games_by_season_task(self, season_id: int, tournament_id: int, collection: str = "games"):
    try:
        # Atualiza progresso
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': 38, 'status': 'Iniciando extração...'})
        
        # Inicializa extractor
        extractor = Extractor()
        self.update_state(state='PROGRESS', meta={'current': 1, 'total': 38, 'status': 'Extractor inicializado'})
        
        # Extrai jogos
        games = extractor.get_games_by_season(tournament_id, season_id)
        self.update_state(state='PROGRESS', meta={'current': 35, 'total': 38, 'status': f'{len(games)} jogos extraídos'})
        
        # Aplica transformações se necessário
        if games:
            transformer = Transform(games, tournament_id)
            games = transformer.transform()
            self.update_state(state='PROGRESS', meta={'current': 36, 'total': 38, 'status': 'Dados transformados'})
            
            # Salva no MongoDB
            loader = Load()
            games_saved = loader.read_data(collection, {'season': season_id, 'tournament_id': tournament_id})
            if len(games_saved) == len(games):
                self.update_state(state='PROGRESS', meta={'current': 37, 'total': 38, 'status': 'Dados já existem no MongoDB'})
            else:
                loader.insert_data(games, collection)
                self.update_state(state='PROGRESS', meta={'current': 37, 'total': 38, 'status': 'Dados salvos no MongoDB'})
            loader.desconnect()
            
            # Limpa ObjectIds do MongoDB para que os dados sejam JSON serializáveis
            games = clean_mongodb_ids(games)
        
        return {
            'status': 'completed',
            'season_id': season_id,
            'total_games': len(games),
            'games': games
        }
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise


@celery_app.task(bind=True, name='extract_all_games')
def extract_all_games_task(
    self,
    slug_tournament: str,
    tournament_id: int,
    country: str = "brazil",
    collection: str = "games",
    length_tournaments: Optional[Union[int, List[int]]] = None
):
    try:
        # Atualiza progresso
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': 100, 'status': 'Iniciando extração...'})
        
        # Inicializa extractor
        extractor = Extractor()
        loader = Load()
        
        competition_url = f"https://www.sofascore.com/pt/football/tournament/{country}/{slug_tournament}/{tournament_id}"
        seasons = extractor.get_seasons(competition_url)
        total_seasons = len(seasons)
        
        self.update_state(
            state='PROGRESS', 
            meta={
                'current': 5, 
                'total': 100, 
                'status': f'Encontradas {total_seasons} temporadas. Iniciando extração...'
            }
        )
        if length_tournaments is not None:
            if isinstance(length_tournaments, list):
                allowed_ids = set(length_tournaments)
                seasons = [season for season in seasons if season['id'] in allowed_ids]
                total_seasons = len(seasons)
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': 5,
                        'total': 100,
                        'status': f'Filtrando para {total_seasons} temporadas específicas...'
                    }
                )
            else:
                seasons = seasons[:length_tournaments]
                total_seasons = len(seasons)
                self.update_state(
                    state='PROGRESS', 
                    meta={
                        'current': 5, 
                        'total': 100, 
                        'status': f'Limitando a {total_seasons} temporadas para pesquisar...'
                    }
                )
        games = []
        for season in seasons:
            extracted_games = extractor.get_games_by_season(tournament_id, season['id'])
            games_saved = loader.read_data(collection, {'season': season['id'], 'tournament_id': tournament_id})
            if len(games_saved) != len(extracted_games):
                games.extend(extracted_games)
        
        self.update_state(
            state='PROGRESS', 
            meta={
                'current': 90, 
                'total': 100, 
                'status': f'{len(games)} jogos extraídos de {total_seasons} temporadas'
            }
        )
        
        # Aplica transformações se necessário
        if games:
            transformer = Transform(games, tournament_id)
            games = transformer.transform()
            self.update_state(state='PROGRESS', meta={'current': 92, 'total': 100, 'status': 'Dados transformados'})
            
            loader.insert_data(games, collection)
            loader.desconnect()
            self.update_state(state='PROGRESS', meta={'current': 95, 'total': 100, 'status': 'Dados salvos no MongoDB'})
            
            # Limpa ObjectIds do MongoDB para que os dados sejam JSON serializáveis
            games = clean_mongodb_ids(games)
        
        return {
            'status': 'completed',
            'total_seasons': total_seasons,
            'total_games': len(games),
            'games': games
        }
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
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
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise
