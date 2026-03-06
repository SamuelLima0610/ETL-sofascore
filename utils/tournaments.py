"""Utility helpers for tournament discovery and categorization."""
from fastapi import HTTPException
import app_dependencies as deps


CATEGORIES = [
    "football",
    "basketball",
    "volleyball",
    "tennis",
    "american-football",
]

def get_tournaments_info():
    """Return tournaments available per category using the shared extractor."""
    if deps.extractor is None:
        raise HTTPException(status_code=503, detail="Extractor não inicializado")

    tournaments = {}
    for category in CATEGORIES:
        try:
            tournaments_list = deps.extractor.get_tournaments(category)
            if tournaments_list:
                tournaments[category] = tournaments_list
        except Exception as exc:  # pragma: no cover - logging side-effect
            print(f"Erro ao buscar torneios para categoria '{category}': {str(exc)}")
    return tournaments

def get_category_by_tournament_id(tournament_id: int):
    """Discover the category for a given tournament id using cached tournament info."""
    tournaments = get_tournaments_info()
    for category_name, tournaments_list in tournaments.items():
        for tournament in tournaments_list:
            if tournament.get("id") == tournament_id:
                return category_name
    return None
