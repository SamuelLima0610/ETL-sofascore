"""Endpoints responsáveis por tasks assíncronas e monitoramento."""
from fastapi import APIRouter, HTTPException, Query
from celery.result import AsyncResult
from typing import Optional

from celery_worker import (
    celery_app,
    extract_games_by_season_task,
    extract_all_games_task,
    get_seasons_task,
    predict_match_task
)
from schemas.extraction_schema import AllSeasonsExtractionRequest, SeasonExtractionRequest
from schemas.prediction_schema import PredictionRequest
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
        selected_category, tournament_name = get_category_by_tournament_id(tournament_id)
        task = extract_games_by_season_task.delay(season_id, tournament_id, selected_category, tournament_name)
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
    seasons_ids = payload.seasons_ids

    selected_category, tournament_name = get_category_by_tournament_id(tournament_id)
    task = extract_all_games_task.delay(
        slug_tournament,
        tournament_id,
        country,
        collection=selected_category,
        seasons_ids=seasons_ids,
        tournament_name=tournament_name
    )
    return {
        "task_id": task.id,
        "status": "processing",
        "message": "Task iniciada. Esta operação pode demorar. Dados serão salvos no MongoDB. Use GET /tasks/{task_id} para verificar o status",
    }

@router.post("/async/prediction")
async def predict_game_winner_probability_async(payload: PredictionRequest):
    """Agenda extração assíncrona dos jogos de uma temporada específica."""
    try:
        season_id = payload.season_id
        tournament_id = payload.tournament_id
        home_team = payload.home_team
        away_team = payload.away_team
        game_id = payload.game_id
        selected_category,_ = get_category_by_tournament_id(tournament_id)

        task = predict_match_task.delay(selected_category, game_id, home_team, away_team, tournament_id, season_id)
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

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Consulta o estado atual de uma task Celery pelo id."""
    task_result = AsyncResult(task_id, app=celery_app)
    try:
        state = task_result.state
        info = task_result.info
        result = task_result.result
    except Exception as exc:
        return {
            "task_id": task_id,
            "state": "UNKNOWN",
            "status": "Não foi possível decodificar o resultado da task (backend pode estar corrompido)",
            "error": str(exc),
        }

    if state == "PENDING":
        response = {
            "task_id": task_id,
            "state": state,
            "status": "Task aguardando processamento ou não existe",
        }
    elif state == "PROGRESS":
        response = {
            "task_id": task_id,
            "state": state,
            "progress": info,
        }
    elif state == "SUCCESS":
        response = {
            "task_id": task_id,
            "state": state,
            "result": result,
        }
    elif state == "FAILURE":
        response = {
            "task_id": task_id,
            "state": state,
            "error": str(info),
        }
    else:
        response = {
            "task_id": task_id,
            "state": state,
            "info": info if info else None,
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

@router.get("/tasks")
async def list_tasks(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    state: Optional[str] = Query(None, description="Filtra por estado (SUCCESS, PROGRESS, etc.)")
):
    """
    Lista tarefas registradas no Redis/Celery com suporte a paginação.
    Nota: O Celery não mantém nativamente uma lista indexada de todas as tasks 
    no backend de resultados sem configurações extras (como Flower ou DB persistente).
    Esta implementação utiliza as chaves do Redis como fallback se disponível.
    """
    # Tenta obter do Redis via broker/backend para fins didáticos/debug
    # Em produção, recomenda-se o uso do Flower API ou persistência em DB (SQL/Mongo)
    try:
        from redis import Redis
        import os
        
        # Conecta ao Redis configurado para buscar chaves de resultado
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        r = Redis.from_url(redis_url)
        
        # O prefixo padrão de resultados do Celery é 'celery-task-meta-'
        # Buscamos todas as tarefas monitoradas no backend
        pattern = "celery-task-meta-*"
        all_keys = [k.decode('utf-8') for k in r.keys(pattern)]
        
        # Inverte para ter as mais recentes primeiro (assumindo nomes de chaves cronológicos ou apenas para exibição)
        # Nota: k.split('-')[-1] extrai o task_id da chave
        task_ids = [k.split('celery-task-meta-')[-1] for k in all_keys]
        
        total = len(task_ids)
        
        # Paginação
        paginated_ids = task_ids[offset : offset + limit]
        
        tasks_details = []
        for tid in paginated_ids:
            res = AsyncResult(tid, app=celery_app)
            # Filtro opcional por estado
            if state and res.state != state:
                continue
                
            tasks_details.append({
                "task_id": tid,
                "state": res.state,
                "info": res.info.get('total_games') if isinstance(res.info, dict) else 'N/A',
            })
            
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "count": len(tasks_details),
            "tasks": tasks_details
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar tasks: {str(e)}")
