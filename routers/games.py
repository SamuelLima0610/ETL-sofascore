"""Endpoints responsáveis por consultas e estatísticas de jogos."""
from fastapi import APIRouter, HTTPException, Request

import app_dependencies as deps
import utils.process as process

router = APIRouter()

@router.get("/games/{category}")
async def get_games(category: str, request: Request):
    """Busca jogos de uma categoria usando filtros dinâmicos via query params."""
    if deps.load is None:
        raise HTTPException(status_code=503, detail="Load não inicializado")

    filters = {}
    query_params = dict(request.query_params)
    for key, value in query_params.items():
        if value.isdigit():
            filters[key] = int(value)
        elif value.replace('.', '', 1).isdigit():
            filters[key] = float(value)
        else:
            filters[key] = value

    try:
        games = deps.database.read_data(category, query=filters)
        for game in games:
            if '_id' in game:
                game['_id'] = str(game['_id'])
        return {
            "count": len(games),
            "filters": filters,
            "games": games
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar jogos: {str(exc)}") from exc

@router.get("/versus/{collection}")
async def get_versus_stats(collection: str, team_one: str, team_two: str):
    """Compara desempenho histórico entre duas equipes."""
    if deps.extractor is None:
        raise HTTPException(status_code=503, detail="Extractor não inicializado")
    if deps.database is None:
        raise HTTPException(status_code=503, detail="Database não inicializado")

    at_house = deps.database.read_data(collection, query={"home_team": team_one, "away_team": team_two})
    at_away = deps.database.read_data(collection, query={"home_team": team_two, "away_team": team_one})
    return process.get_versus_stats(at_house, at_away)

@router.get("/games/{collection}/{id}")
async def get_game(collection: str, id: int):
    """Busca um jogo específico pelo ID (síncrono) de uma determinada configuração."""
    if deps.database is None:
        raise HTTPException(status_code=503, detail="Database não inicializado")
    try:
        game = deps.database.read_data(collection, query={"id": id})
        game = process.clean_mongodb_ids(game)
        if not game:
            raise HTTPException(status_code=404, detail="Jogo não encontrado")
        return game[0]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar jogo: {str(exc)}") from exc
