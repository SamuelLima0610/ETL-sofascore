"""Endpoints responsáveis por tasks assíncronas e monitoramento."""
from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult

from celery_worker import (
    celery_app,
    extract_games_by_season_task,
    extract_all_games_task,
    get_seasons_task,
)
from schemas.extraction_schema import AllSeasonsExtractionRequest, SeasonExtractionRequest
from utils.tournaments import get_category_by_tournament_id

router = APIRouter()

@router.post("/async/seasons")
async def get_seasons_async():
    """Dispara task Celery para buscar temporadas de todos os torneios configurados."""
    task = get_seasons_task.delay()
    return {
        "task_id": task.id,
        "status": "processing",
        "message": "Task iniciada. Use GET /tasks/{task_id} para verificar o status",
    }

@router.post("/async/games/season")
async def get_games_by_season_async(payload: SeasonExtractionRequest):
    """Agenda extração assíncrona dos jogos de uma temporada específica."""
    try:
        season_id = payload.season_id
        tournament_id = payload.tournament_id
        selected_category = get_category_by_tournament_id(tournament_id) or "stats"
        task = extract_games_by_season_task.delay(season_id, tournament_id, selected_category)
        return {
            "task_id": task.id,
            "season_id": season_id,
            "tournament_id": tournament_id,
            "category": selected_category,
            "status": "processing",
            "message": "Task iniciada. Dados serão salvos no MongoDB. Use GET /tasks/{task_id} para verificar o status",
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar extração: {str(exc)}") from exc

@router.post("/async/games")
async def get_all_games_async(payload: AllSeasonsExtractionRequest):
    """Agenda extração assíncrona de todas as temporadas de um torneio."""
    slug_tournament = payload.slug_tournament
    tournament_id = payload.tournament_id
    country = payload.country
    length_tournaments = payload.length_tournaments

    selected_category = get_category_by_tournament_id(tournament_id) or "stats"
    task = extract_all_games_task.delay(
        slug_tournament,
        tournament_id,
        country,
        collection=selected_category,
        length_tournaments=length_tournaments,
    )
    return {
        "task_id": task.id,
        "status": "processing",
        "message": "Task iniciada. Esta operação pode demorar. Dados serão salvos no MongoDB. Use GET /tasks/{task_id} para verificar o status",
    }

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Consulta o estado atual de uma task Celery pelo id."""
    task_result = AsyncResult(task_id, app=celery_app)
    if task_result.state == "PENDING":
        response = {
            "task_id": task_id,
            "state": task_result.state,
            "status": "Task aguardando processamento ou não existe",
        }
    elif task_result.state == "PROGRESS":
        response = {
            "task_id": task_id,
            "state": task_result.state,
            "progress": task_result.info,
        }
    elif task_result.state == "SUCCESS":
        response = {
            "task_id": task_id,
            "state": task_result.state,
            "result": task_result.result,
        }
    elif task_result.state == "FAILURE":
        response = {
            "task_id": task_id,
            "state": task_result.state,
            "error": str(task_result.info),
        }
    else:
        response = {
            "task_id": task_id,
            "state": task_result.state,
            "info": task_result.info if task_result.info else None,
        }
    return response

@router.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    """Cancela uma task em background, solicitando encerramento imediato."""
    task_result = AsyncResult(task_id, app=celery_app)
    task_result.revoke(terminate=True)
    return {
        "task_id": task_id,
        "message": "Task cancelada",
    }
