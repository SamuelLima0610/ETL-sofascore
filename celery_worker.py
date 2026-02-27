from celery import Celery
from extractor import Extractor
from transform import Transform
from load import Load
from dotenv import load_dotenv
import os

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

# URL padrão do Brasileirão Série A
DEFAULT_COMPETITION_URL = "https://www.sofascore.com/pt/football/tournament/brazil/brasileirao-serie-a/325#id:87678"

@celery_app.task(bind=True, name='extract_games_by_season')
def extract_games_by_season_task(self, season_id: int, transform_data: bool = False):
    try:
        # Atualiza progresso
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': 38, 'status': 'Iniciando extração...'})
        
        # Inicializa extractor
        extractor = Extractor(DEFAULT_COMPETITION_URL)
        self.update_state(state='PROGRESS', meta={'current': 1, 'total': 38, 'status': 'Extractor inicializado'})
        
        # Extrai jogos
        games = extractor.get_games_by_season(season_id)
        self.update_state(state='PROGRESS', meta={'current': 35, 'total': 38, 'status': f'{len(games)} jogos extraídos'})
        
        # Aplica transformações se necessário
        if transform_data and games:
            transformer = Transform(games)
            games = transformer.transform()
            self.update_state(state='PROGRESS', meta={'current': 36, 'total': 38, 'status': 'Dados transformados'})
            
            # Salva no MongoDB
            loader = Load()
            loader.insert_data(games)
            loader.desconnect()
            self.update_state(state='PROGRESS', meta={'current': 37, 'total': 38, 'status': 'Dados salvos no MongoDB'})
            
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
def extract_all_games_task(self, transform_data: bool = False):
    try:
        # Atualiza progresso
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': 100, 'status': 'Iniciando extração...'})
        
        # Inicializa extractor
        extractor = Extractor(DEFAULT_COMPETITION_URL)
        seasons = extractor.get_seasons()
        total_seasons = len(seasons)
        
        self.update_state(
            state='PROGRESS', 
            meta={
                'current': 5, 
                'total': 100, 
                'status': f'Encontradas {total_seasons} temporadas. Iniciando extração...'
            }
        )
        
        # Extrai jogos
        games = extractor.get_games()
        
        self.update_state(
            state='PROGRESS', 
            meta={
                'current': 90, 
                'total': 100, 
                'status': f'{len(games)} jogos extraídos de {total_seasons} temporadas'
            }
        )
        
        # Aplica transformações se necessário
        if transform_data and games:
            transformer = Transform(games)
            games = transformer.transform()
            self.update_state(state='PROGRESS', meta={'current': 92, 'total': 100, 'status': 'Dados transformados'})
            
            # Salva no MongoDB
            loader = Load()
            loader.insert_data(games)
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
def get_seasons_task(self):
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Buscando temporadas...'})
        
        extractor = Extractor(DEFAULT_COMPETITION_URL)
        seasons = extractor.get_seasons()
        
        return {
            'status': 'completed',
            'seasons': seasons
        }
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise
