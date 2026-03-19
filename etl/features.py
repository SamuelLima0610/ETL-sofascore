import time

from utils.process import _aggregate, clean_mongodb_ids, _extract_entry
from typing import Any, Dict, Tuple
import pandas as pd


def _split_by_role(games: list, team_name: str):
    """Divide os jogos de um time em partidas como mandante e visitante."""
    home = [g for g in games if g.get('home_team') == team_name]
    away = [g for g in games if g.get('away_team') == team_name]
    return home, away

def _aggregate(games: list, team_as_home: bool) -> Dict:
    """Calcula média por estatística e resultados para a lista de jogos fornecida."""
    accum: Dict[str, Dict[str, Dict[str, float]]] = {}
    games_count = 0

    for game in games:
        stats = game.get('stats') or {}
        games_count += 1

        for stat in stats:
            for category, items in stat.items():
                if not isinstance(items, list):
                    continue
                for item in items:
                    name, home_val, away_val = _extract_entry(item)
                    if not name:
                        continue

                    # Seleciona o valor da equipe e do adversário dependendo se ela é mandante/visitante
                    team_val = home_val if team_as_home else away_val
                    opp_val = away_val if team_as_home else home_val

                    cat_bucket = accum.setdefault(category, {})
                    stat_bucket = cat_bucket.setdefault(name, {"team_sum": 0.0, "opp_sum": 0.0, "count": 0})
                    stat_bucket["team_sum"] += team_val
                    stat_bucket["opp_sum"] += opp_val
                    stat_bucket["count"] += 1
    avg = {}
    for category, stats_map in accum.items():
        for name, data in stats_map.items():
            count = data["count"] or 1
            avg[f'{name}'] = data["team_sum"] / count
    return {"games_count": games_count, "stats_avg": avg}



def compute_team_features(prev_games: list, team_name: str) -> dict:
    """Calcula médias de estatísticas para um time a partir de uma lista de jogos anteriores.

    Retorna as médias separadas por papel (mandante/visitante) e o total de jogos encontrados.
    """
    home_games, away_games = _split_by_role(prev_games, team_name)
    return {
        "total_games": len(prev_games),
        "as_home": _aggregate(home_games, team_as_home=True),
        "as_away": _aggregate(away_games, team_as_home=False),
    }


def generate_match_features(load, collection, tournament_id, season_id, home_team, away_team, home_elo_raiting, away_elo_raiting) -> dict:
    """Gera um dicionário de features para um jogo específico entre dois times.

    Para cada time, calcula as médias das estatísticas dos n jogos anteriores, separando por papel (mandante/visitante).
    """
    home_team_stats = compute_actual_features_of_a_team(load, collection, home_team, tournament_id, season_id, is_home=True)
    away_team_stats = compute_actual_features_of_a_team(load, collection, away_team, tournament_id, season_id, is_home=False)
    general = {
        "time": int(time.time()),
        "elo_rating_home": home_elo_raiting,
        "elo_rating_away": away_elo_raiting,
        "elo_diff": home_elo_raiting - away_elo_raiting
    }
    return general | home_team_stats | away_team_stats

def compute_actual_features_of_a_team(database, collection, team_name, tournament_id, season_id, is_home) -> list:
    prefix = "home_team" if is_home else "away_team"
    games = database.read_last_games(collection, team_name, n=15, tournament_id=tournament_id, season_id=season_id, lt_value=int(time.time()))
    return{
        f"{prefix}_features_5_games": compute_team_features(games[:5], team_name),
        f"{prefix}_features_10_games": compute_team_features(games[:10], team_name),
        f"{prefix}_features_15_games": compute_team_features(games[:15], team_name)
    }


def compute_season_features(database, collection: str, tournament_id: int, season_id: int) -> list:
    """Para cada jogo de uma temporada, calcula as médias históricas das estatísticas
    dos n jogos anteriores de cada time.

    Parâmetros:
    - database: instância de Database (conexão MongoDB)
    - collection: nome da coleção no MongoDB
    - tournament_id: ID do torneio/campeonato
    - season_id: ID da temporada

    Retorna uma lista de dicts. Cada item contém as informações básicas do jogo
    mais as features históricas do time mandante e visitante.
    """
    teams_elo_raiting = {}
    games = database.read_data(collection, query={"season": season_id, "tournament_id": tournament_id})
    games = sorted(games, key=lambda g: g.get("time") or 0)

    result = []
    for game in games:
        round_game = str(game.get("round"))
        game_time = game.get("time")
        home_team = game.get("home_team")
        away_team = game.get("away_team")

        if home_team in list(teams_elo_raiting.keys()):
            home_elo = teams_elo_raiting[home_team]
        else:            
            home_elo = 1500.0 if "Qualification" not in round_game else 500.0

        if away_team in list(teams_elo_raiting.keys()):
            away_elo = teams_elo_raiting[away_team]
        else:         
            away_elo = 1500.0 if "Qualification" not in round_game else 500.0

        home_prev = database.read_last_games(
            collection, home_team, n=15, lt_value=game_time, tournament_id=tournament_id, season_id=season_id
        )
        away_prev = database.read_last_games(
            collection, away_team, n=15, lt_value=game_time, tournament_id=tournament_id, season_id=season_id
        )

        clean_mongodb_ids(home_prev)
        clean_mongodb_ids(away_prev)

        result.append({
            "time": game_time,
            "elo_rating_home": home_elo,
            "elo_rating_away": away_elo,
            "elo_diff": home_elo - away_elo,
            "home_team_features_5_games": compute_team_features(home_prev[:5], home_team),
            "away_team_features_5_games": compute_team_features(away_prev[:5], away_team),
            "home_team_features_10_games": compute_team_features(home_prev[:10], home_team),
            "away_team_features_10_games": compute_team_features(away_prev[:10], away_team),
            "home_team_features_15_games": compute_team_features(home_prev[:15], home_team),
            "away_team_features_15_games": compute_team_features(away_prev[:15], away_team),
            "is_home_team_winner": int(game.get("home_score", 0) > game.get("away_score", 0)),
        })

        # Atualiza os ratings Elo dos times
        new_home_elo, new_away_elo = compute_elo_rating(
            game.get("home_score", 0),
            game.get("away_score", 0),
            home_elo,
            away_elo
        )
        teams_elo_raiting[home_team] = new_home_elo
        teams_elo_raiting[away_team] = new_away_elo

    return result, teams_elo_raiting


def _flatten_team_features(features: dict, prefix: str, window: int) -> dict:
    """Achata as features de um time em um dicionário plano com prefixo adequado.

    Convenção de nomes: {prefix}_{window}g_as_{role}_{stat_name}
    Exemplo: home_5g_as_home_Ball possession
    """
    flat = {}
    base = f"{prefix}_{window}g"
    flat[f"{base}_total_games"] = features.get("total_games", 0)

    for role in ("as_home", "as_away"):
        role_data = features.get(role, {})
        role_prefix = f"{base}_{role}"
        flat[f"{role_prefix}_games_count"] = role_data.get("games_count", 0)
        for stat_name, value in (role_data.get("stats_avg") or {}).items():
            flat[f"{role_prefix}_{stat_name}"] = value

    return flat

def season_features_to_dataframe(season_features: list) -> pd.DataFrame:
    """Transforma a saída de compute_season_features em um DataFrame pandas.

    Cada linha representa um jogo. As colunas são:
    - Informações básicas: time, home_team, away_team, is_home_team_winner
    - Features do time mandante e visitante para janelas de 5, 10 e 15 jogos anteriores,
      separadas por papel (as_home / as_away) e por estatística.

    Naming: {home|away}_{5|10|15}g_as_{home|away}_{stat_name}
    """
    windows = [5, 10, 15]
    rows = []

    for record in season_features:
        row = {
            "time": record.get("time"),
            "is_home_team_winner": record.get("is_home_team_winner"),
        }

        for w in windows:
            home_key = f"home_team_features_{w}_games"
            away_key = f"away_team_features_{w}_games"
            row.update(_flatten_team_features(record.get(home_key, {}), prefix="home", window=w))
            row.update(_flatten_team_features(record.get(away_key, {}), prefix="away", window=w))

        rows.append(row)

    return pd.DataFrame(rows)

def compute_elo_rating(home_score: int, away_score: int, home_elo: float, away_elo: float, k=32) -> Tuple[float, float]:
    """Calcula o novo Elo rating para os times mandante e visitante após um jogo.

    Args:
        home_score: gols do time mandante
        away_score: gols do time visitante
        home_elo: Elo rating atual do time mandante
        away_elo: Elo rating atual do time visitante
        k: fator de ajuste (default 32)

    Returns:
        Tuple[float, float]: (novo_home_elo, novo_away_elo)
    """
    # Determina o resultado do jogo
    if home_score > away_score:
        outcome = 1  # vitória do mandante
    elif home_score < away_score:
        outcome = 0  # vitória do visitante
    else:
        outcome = 0.5  # empate

    # Calcula a expectativa de vitória para o mandante
    expected_home = 1 / (1 + 10 ** ((away_elo - home_elo) / 400))
    
    # Atualiza os ratings usando a fórmula do Elo
    new_home_elo = home_elo + k * (outcome - expected_home)
    new_away_elo = away_elo + k * ((1 - outcome) - (1 - expected_home))

    return new_home_elo, new_away_elo