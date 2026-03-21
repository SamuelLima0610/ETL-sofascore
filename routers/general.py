"""General purpose FastAPI endpoints (health, docs, tournaments)."""
from fastapi import APIRouter, HTTPException
from celery_worker import celery_app
import utils.process as process
import app_dependencies as deps
from utils.tournaments import get_tournaments_info

router = APIRouter()

@router.get("/")
async def root():
    """Apresenta informações iniciais da API e links úteis."""
    return {
        "message": "ETL Statistics API v2.0 - Com processamento em background via Celery",
        "docs": "/docs",
        "endpoints": {
            "sync": ["/seasons", "/health", "/games"],
            "async": ["/async/seasons", "/async/games/season", "/async/games"],
            "status": ["/tasks/{task_id}"]
        }
    }

@router.get("/health")
async def health_check():
    """Verifica se a API e dependências principais (Extractor e Celery) estão saudáveis."""
    inspector = celery_app.control.inspect()
    return {
        "status": "healthy",
        "extractor_ready": deps.extractor is not None,
        "celery_ready": inspector.ping() is not None if inspector else False
    }

@router.get("/tournaments")
async def get_tournaments():
    """Lista torneios disponíveis para cada categoria esportiva suportada."""
    return {"tournaments": get_tournaments_info()}

@router.get("/seasons")
async def get_seasons(slug_tournament: str, tournament_id: int, country: str):
    """Retorna as temporadas de um torneio especificado nos parâmetros."""
    if deps.extractor is None:
        raise HTTPException(status_code=503, detail="Extractor não inicializado")

    competition_url = (
        f"https://www.sofascore.com/pt/football/tournament/{country}/"
        f"{slug_tournament}/{tournament_id}"
    )
    return {"seasons": deps.extractor.get_seasons(competition_url)}


@router.get("/prediction/{id}")
async def get_game(id: int):
    """Busca um jogo específico pelo ID (síncrono) de uma determinada configuração."""
    if deps.database is None:
        raise HTTPException(status_code=503, detail="Database não inicializado")
    try:
        prediction = deps.database.read_data('predictions', query={"game_id": id})
        prediction = process.clean_mongodb_ids(prediction)
        if not prediction:
            raise HTTPException(status_code=404, detail="Jogo não encontrado")
        return prediction[0]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar jogo: {str(exc)}") from exc
