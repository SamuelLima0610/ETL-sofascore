from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from etl.extractor import Extractor
from etl.load import Load
import process

from celery_worker import (
    celery_app,
    extract_games_by_season_task,
    extract_all_games_task,
    get_seasons_task
)
from celery.result import AsyncResult

# Instâncias globais (inicializadas no lifespan)
extractor = None
load = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa recursos na startup e limpa no shutdown."""
    global extractor, load
    print("Inicializando Extractor...")
    extractor = Extractor()
    print("Extractor inicializado com sucesso!")
    print("Inicializando Load...")
    load = Load()
    print("Load inicializado com sucesso!")
    yield
    print("Encerrando aplicação...")
    if load:
        load.desconnect()

app = FastAPI(
    title="ETL Statistics API",
    description="API para extração de estatísticas de futebol do SofaScore com processamento em background via Celery",
    version="2.0.0",
    lifespan=lifespan
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Apresenta informações iniciais da API e links úteis."""
    return {
        "message": "ETL Statistics API v2.0 - Com processamento em background via Celery",
        "docs": "/docs",
        "endpoints": {
            "sync": ["/seasons", "/health", "/games"],
            "async": ["/async/seasons", "/async/games/{season_id}", "/async/games"],
            "status": ["/tasks/{task_id}"]
        }
    }


# ============================================
# ENDPOINTS SÍNCRONOS (resposta imediata)
# ============================================
@app.get("/health")
async def health_check():
    """Verifica se a API e dependências principais (Extractor e Celery) estão saudáveis."""
    return {
        "status": "healthy",
        "extractor_ready": extractor is not None,
        "celery_ready": celery_app.control.inspect().ping() is not None
    }

def get_tournaments_info():
    categories = ["football", "basketball", "volleyball", "tennis", "american-football"]  # Podemos expandir para outros esportes no futuro
    if extractor is None:
        raise HTTPException(status_code=503, detail="Extractor não inicializado")
    # Construir a URL da competição com base nos parâmetros
    tournaments = {}
    for category in categories:
        try:
            tournaments_list = extractor.get_tournaments(category)
            if tournaments_list:
                tournaments[category] = tournaments_list
        except Exception as e:
            print(f"Erro ao buscar torneios para categoria '{category}': {str(e)}")
    return tournaments

def get_category_by_tournament_id(tournament_id):
    tournaments = get_tournaments_info()
    for category_name, tournaments_list in tournaments.items():
        for tournament in tournaments_list:
            if tournament.get('id') == tournament_id:
                return category_name
    return None

@app.get("/tournaments")
async def get_tournaments():
    """Lista torneios disponíveis para cada categoria esportiva suportada."""
    if extractor is None:
        raise HTTPException(status_code=503, detail="Extractor não inicializado")
    # Construir a URL da competição com base nos parâmetros
    return {"tournaments": get_tournaments_info()}


@app.get("/seasons")
async def get_seasons(slug_tournament: str, tournament_id: int, country: str):
    """Retorna as temporadas de um torneio.

    Parâmetros:
    - slug_tournament: slug do torneio no SofaScore.
    - tournament_id: identificador numérico do torneio.
    - country: país presente na URL do torneio.
    """
    if extractor is None:
        raise HTTPException(status_code=503, detail="Extractor não inicializado")
    # Construir a URL da competição com base nos parâmetros
    competition_url = f"https://www.sofascore.com/pt/football/tournament/{country}/{slug_tournament}/{tournament_id}"
    
    return {"seasons": extractor.get_seasons(competition_url)}

@app.get("/games/{category}")
async def get_games(category: str, request: Request):
    """Busca jogos de uma categoria usando filtros dinâmicos via query params.

    Parâmetros de rota:
    - category: coleção ou esporte em que os dados estão salvos.

    Principais query params aceitos (todos opcionais e combináveis):
    - season: id da temporada.
    - round: número da rodada.
    - home_team / away_team: nomes das equipes.
    - Outros campos numéricos ou texto são aceitos e usados como filtro direto.

    Exemplos:
    - /games/football?season=87678
    - /games/stats?home_team=Flamengo&away_team=Palmeiras
    - /games/football (retorna todos os jogos da categoria)
    """
    if load is None:
        raise HTTPException(status_code=503, detail="Load não inicializado")
    
    # Captura todos os query params e cria o filtro dinamicamente
    filters = {}
    query_params = dict(request.query_params)
    
    for key, value in query_params.items():
        # Tenta converter valores numéricos
        if value.isdigit():
            filters[key] = int(value)
        elif value.replace('.', '', 1).isdigit():
            filters[key] = float(value)
        else:
            filters[key] = value
    
    try:
        games = load.read_data(category, query=filters)
        
        # Remove o campo _id do MongoDB para serialização JSON
        for game in games:
            if '_id' in game:
                game['_id'] = str(game['_id'])
        
        return {
            "count": len(games),
            "filters": filters,
            "games": games
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar jogos: {str(e)}")

@app.get("/versus/{category}")
async def get_versus_stats(category: str, team_one: str, team_two: str):
    """Compara desempenho histórico entre duas equipes.

    Parâmetros de rota:
    - category: coleção/esporte consultado.
    - team_one: equipe A (considerada mandante na primeira busca).
    - team_two: equipe B (considerada visitante na primeira busca).
    """
    if extractor is None:
        raise HTTPException(status_code=503, detail="Extractor não inicializado")
    
    at_house = load.read_data(category, query={"home_team": team_one, "away_team": team_two})
    at_away = load.read_data(category, query={"home_team": team_two, "away_team": team_one})

    return process.get_versus_stats(at_house, at_away)

# ============================================
# ENDPOINTS ASSÍNCRONOS (processamento em background)
# ============================================

@app.post("/async/seasons")
async def get_seasons_async():
    """Dispara task Celery para buscar temporadas de todos os torneios configurados."""
    task = get_seasons_task.delay()
    return {
        "task_id": task.id,
        "status": "processing",
        "message": "Task iniciada. Use GET /tasks/{task_id} para verificar o status"
    }


@app.post("/async/games/{tournament_id}/{season_id}")
async def get_games_by_season_async(season_id: int, tournament_id: int, transform_data: bool = False):
    """Agenda extração assíncrona dos jogos de uma temporada específica.

    Parâmetros de rota:
    - tournament_id: id do torneio no SofaScore.
    - season_id: id da temporada a ser extraída.

    Query param opcional:
    - transform_data: salva no MongoDB se verdadeiro; só retorna dados se falso.
    """
    try:
        # Busca o torneio pelo id fornecido e guarda também a categoria em que ele foi encontrado
        selected_category = get_category_by_tournament_id(tournament_id)
        if selected_category is None:
            selected_category = 'stats'
        task = extract_games_by_season_task.delay(season_id, tournament_id, transform_data, selected_category)
        return {
            "task_id": task.id,
            "season_id": season_id,
            "tournament_id": tournament_id,
            "transform_data": transform_data,
            "category": selected_category,
            "status": "processing",
            "message": f"Task iniciada. {'Dados serão salvos no MongoDB.' if transform_data else 'Dados não serão salvos.'} Use GET /tasks/{{task_id}} para verificar o status"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar extração: {str(e)}")


@app.post("/async/games")
async def get_all_games_async(slug_tournament: str, tournament_id: int, country: str,transform_data: bool = False, length_tournaments: int = None):
    """Agenda extração assíncrona de todas as temporadas de um torneio.

    Query params obrigatórios:
    - slug_tournament: slug do torneio.
    - id_tournament: id numérico do torneio.
    - country: país presente na URL do torneio.

    Query param opcional:
    - transform_data: salva no MongoDB se verdadeiro; só retorna dados se falso.
    """
    selected_category = get_category_by_tournament_id(tournament_id)
    if selected_category is None:
        selected_category = 'stats'
    task = extract_all_games_task.delay(slug_tournament, 
                                        tournament_id, 
                                        country, transform_data, 
                                        collection=selected_category,
                                        length_tournaments=length_tournaments)
    return {
        "task_id": task.id,
        "transform_data": transform_data,
        "status": "processing",
        "message": f"Task iniciada. Esta operação pode demorar. {'Dados serão salvos no MongoDB.' if transform_data else 'Dados não serão salvos.'} Use GET /tasks/{{task_id}} para verificar o status"
    }


# ============================================
# ENDPOINTS DE STATUS DE TASKS
# ============================================

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Consulta o estado atual de uma task Celery pelo id."""
    task_result = AsyncResult(task_id, app=celery_app)
    
    if task_result.state == 'PENDING':
        response = {
            "task_id": task_id,
            "state": task_result.state,
            "status": "Task aguardando processamento ou não existe"
        }
    elif task_result.state == 'PROGRESS':
        response = {
            "task_id": task_id,
            "state": task_result.state,
            "progress": task_result.info
        }
    elif task_result.state == 'SUCCESS':
        response = {
            "task_id": task_id,
            "state": task_result.state,
            "result": task_result.result
        }
    elif task_result.state == 'FAILURE':
        response = {
            "task_id": task_id,
            "state": task_result.state,
            "error": str(task_result.info)
        }
    else:
        response = {
            "task_id": task_id,
            "state": task_result.state,
            "info": task_result.info if task_result.info else None
        }
    
    return response


@app.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    """Cancela uma task em background, solicitando encerramento imediato."""
    task_result = AsyncResult(task_id, app=celery_app)
    task_result.revoke(terminate=True)
    
    return {
        "task_id": task_id,
        "message": "Task cancelada"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
