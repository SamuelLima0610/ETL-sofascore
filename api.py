from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from extractor import Extractor

from celery_worker import (
    celery_app,
    extract_games_by_season_task,
    extract_all_games_task,
    get_seasons_task
)
from celery.result import AsyncResult

# URL padrão do Brasileirão Série A
DEFAULT_COMPETITION_URL = "https://www.sofascore.com/pt/football/tournament/brazil/brasileirao-serie-a/325#id:87678"

# Instância global do extractor (inicializada no lifespan)
extractor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa recursos na startup e limpa no shutdown."""
    global extractor
    print("Inicializando Extractor...")
    extractor = Extractor(DEFAULT_COMPETITION_URL)
    print("Extractor inicializado com sucesso!")
    yield
    print("Encerrando aplicação...")

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
            "sync": ["/seasons", "/health"],
            "async": ["/async/seasons", "/async/games/{season_id}", "/async/games"],
            "status": ["/tasks/{task_id}"]
        }
    }


# ============================================
# ENDPOINTS SÍNCRONOS (resposta imediata)
# ============================================

@app.get("/seasons")
async def get_seasons():
    if extractor is None:
        raise HTTPException(status_code=503, detail="Extractor não inicializado")
    return {"seasons": extractor.get_seasons()}


@app.get("/health")
async def health_check():
    """Endpoint para verificar se a API está funcionando."""
    return {
        "status": "healthy",
        "extractor_ready": extractor is not None,
        "celery_ready": celery_app.control.inspect().ping() is not None
    }


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
async def get_all_games_async(transform_data: bool = False):
    task = extract_all_games_task.delay(transform_data)
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
