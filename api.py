from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from extractor import Extractor
from load import Load

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
@app.get("/tournaments")
async def get_tournaments():
    if extractor is None:
        raise HTTPException(status_code=503, detail="Extractor não inicializado")
    # Construir a URL da competição com base nos parâmetros
    return {"tournaments": extractor.get_football_tournaments()}


@app.get("/seasons")
async def get_seasons(slug_tournament: str, id_tournament: int, country: str):
    
    if extractor is None:
        raise HTTPException(status_code=503, detail="Extractor não inicializado")
    # Construir a URL da competição com base nos parâmetros
    competition_url = f"https://www.sofascore.com/pt/football/tournament/{country}/{slug_tournament}/{id_tournament}"
    
    return {"seasons": extractor.get_seasons(competition_url)}


@app.get("/health")
async def health_check():
    """Endpoint para verificar se a API está funcionando."""
    return {
        "status": "healthy",
        "extractor_ready": extractor is not None,
        "celery_ready": celery_app.control.inspect().ping() is not None
    }


@app.get("/games")
async def get_games(request: Request):
    """
    Endpoint para buscar jogos com filtros dinâmicos.
    Aceita qualquer combinação de parâmetros de filtro via query params.
    
    Exemplos de uso:
    - /games?season=2023
    - /games?home_team=Flamengo
    - /games?season=2023&round=10
    - /games?home_team=Flamengo&away_team=Palmeiras
    - /games (retorna todos os jogos)
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
        games = load.read_data(query=filters)
        
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


# ============================================
# ENDPOINTS ASSÍNCRONOS (processamento em background)
# ============================================

@app.post("/async/seasons")
async def get_seasons_async():
    task = get_seasons_task.delay()
    return {
        "task_id": task.id,
        "status": "processing",
        "message": "Task iniciada. Use GET /tasks/{task_id} para verificar o status"
    }


@app.post("/async/games/{season_id}")
async def get_games_by_season_async(season_id: int, transform_data: bool = False):
    task = extract_games_by_season_task.delay(season_id, transform_data)
    return {
        "task_id": task.id,
        "season_id": season_id,
        "transform_data": transform_data,
        "status": "processing",
        "message": f"Task iniciada. {'Dados serão salvos no MongoDB.' if transform_data else 'Dados não serão salvos.'} Use GET /tasks/{{task_id}} para verificar o status"
    }


@app.post("/async/games")
async def get_all_games_async(slug_tournament: str, id_tournament: int, country: str,transform_data: bool = False):
    task = extract_all_games_task.delay(slug_tournament, id_tournament, country, transform_data)
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
    """
    Cancela uma task em background.
    """
    task_result = AsyncResult(task_id, app=celery_app)
    task_result.revoke(terminate=True)
    
    return {
        "task_id": task_id,
        "message": "Task cancelada"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
