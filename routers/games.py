"""Endpoints responsáveis por consultas e estatísticas de jogos."""
from fastapi import APIRouter, HTTPException, Request

import app_dependencies as deps
import utils.process as process

router = APIRouter()

def _parse_filter_value(value: str):
    """Converte valor do parâmetro para tipo apropriado."""
    if value.isdigit():
        return int(value)
    elif value.replace('.', '', 1).isdigit():
        return float(value)
    else:
        return value


def _build_mongo_query(query_params: dict) -> dict:
    """Constrói query MongoDB a partir de parâmetros com operadores."""
    filters = {}
    operators = {
        'gte': '$gte',
        'lte': '$lte',
        'gt': '$gt',
        'lt': '$lt',
        'eq': '$eq',
        'ne': '$ne',
        'in': '$in',
        'nin': '$nin',
    }
    
    for key, value in query_params.items():
        # Verifica se a chave termina com um operador
        operator_found = None
        field_name = key
        
        for op_suffix, mongo_op in operators.items():
            if key.endswith(f'_{op_suffix}'):
                operator_found = mongo_op
                field_name = key[:-len(op_suffix)-1]  # Remove _operador
                break
        
        parsed_value = _parse_filter_value(value)
        
        # Se encontrou um operador, usa a sintaxe MongoDB
        if operator_found:
            if field_name not in filters:
                filters[field_name] = {}
            filters[field_name][operator_found] = parsed_value
        else:
            # Sem operador, usa igualdade simples
            filters[key] = parsed_value
    
    return filters


@router.get("/games/{category}")
async def get_games(category: str, request: Request):
    """Busca jogos de uma categoria usando filtros dinâmicos via query params.
    
    Suporta operadores de comparação: gte, lte, gt, lt, eq, ne, in, nin
    Exemplos:
        /games/football?score_gte=50&score_lte=100
        /games/football?date_gt=2020-01-01&team=Barcelona
    """
    if deps.load is None:
        raise HTTPException(status_code=503, detail="Load não inicializado")

    query_params = dict(request.query_params)
    filters = _build_mongo_query(query_params)

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

@router.get("/games/{collection}/{id}/players")
async def get_players_of_game(collection: str, id: int):
    """Busca os jogadores de um jogo específico pelo ID (síncrono) de uma determinada configuração."""
    if deps.database is None:
        raise HTTPException(status_code=503, detail="Database não inicializado")
    try:
        game = deps.database.read_data(collection, query={"id": id})
        if not game:
            raise HTTPException(status_code=404, detail="Jogo não encontrado")
        players = deps.database.read_data("players_stats", query={"game_id": id})
        players = process.clean_mongodb_ids(players)
        return players
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar jogadores do jogo: {str(exc)}") from exc
