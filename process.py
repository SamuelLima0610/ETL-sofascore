from typing import Any, Dict, Tuple


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

def _extract_entry(raw: Dict) -> Tuple[str, float, float]:
    """Normaliza um item de estat para (nome, home_val, away_val)."""
    if not isinstance(raw, dict):
        return None, 0.0, 0.0

    # Formato direto: possui homeValue/awayValue na raiz
    if 'homeValue' in raw and 'awayValue' in raw:
        name = raw.get('name') or raw.get('key')
        return name, _to_float(raw.get('homeValue')), _to_float(raw.get('awayValue'))

    # Formato agrupado: {"Big chances": {"homeValue": 1, "awayValue": 2, ...}}
    if len(raw) == 1:
        inner_name, inner_data = next(iter(raw.items()))
        if isinstance(inner_data, dict) and 'homeValue' in inner_data and 'awayValue' in inner_data:
            name = inner_data.get('name') or inner_name
            return name, _to_float(inner_data.get('homeValue')), _to_float(inner_data.get('awayValue'))

    return None, 0.0, 0.0

def _compute_outcome(home_score: float, away_score: float, team_as_home: bool) -> str:
    team_goals = home_score if team_as_home else away_score
    opp_goals = away_score if team_as_home else home_score
    if team_goals > opp_goals:
        return "wins"
    if team_goals == opp_goals:
        return "draws"
    return "losses"


def _aggregate(games: list, team_as_home: bool) -> Dict:
    """Calcula média por estatística e resultados para a lista de jogos fornecida."""
    accum: Dict[str, Dict[str, Dict[str, float]]] = {}
    games_count = 0
    record = {"wins": 0, "draws": 0, "losses": 0}

    for game in games:
        stats = game.get('stats') or {}
        games_count += 1

        home_score = _to_float(game.get('home_score'))
        away_score = _to_float(game.get('away_score'))
        outcome = _compute_outcome(home_score, away_score, team_as_home)
        record[outcome] += 1
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

    averages = {}
    for category, stats_map in accum.items():
        cat_avg = {}
        for name, data in stats_map.items():
            count = data["count"] or 1
            cat_avg[name] = {
                "team_avg": data["team_sum"] / count,
                "opponent_avg": data["opp_sum"] / count,
            }
        averages[category] = cat_avg

    return {"games_count": games_count, "record": record, "stats_avg": averages}


def get_versus_stats(home_games: list, away_games: list):
    seasons = {game.get('season') for game in home_games + away_games if game.get('season') is not None}

    return {
        "seasons": sorted(seasons),
        "home_games": _aggregate(home_games, team_as_home=True),
        "away_games": _aggregate(away_games, team_as_home=False),
    }