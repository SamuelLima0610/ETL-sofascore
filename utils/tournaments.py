"""Utility helpers for tournament discovery and categorization."""
from fastapi import HTTPException
import app_dependencies as deps
import requests

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
                return category_name, tournament.get("name")
    return 'stats', None

def has_draws(category: str) -> bool:
    """Check if a sport category allows draws in regular matches.
    
    Args:
        category: The sport category (e.g., 'football', 'basketball')
        
    Returns:
        bool: True if draws are possible, False otherwise
    """
    sports_with_draws = {'football'}  # Only football allows draws by default in these sports
    return category.lower() in sports_with_draws

def get_team_image(team: dict):
    """Fetch team image data from the database if available."""
    if team:
        team_id = team.get("id")
        if team_id:
            response = requests.get(f"https://img.sofascore.com/api/v1/team/{team_id}/image/small")
            if response.status_code == 200:
                return response.content
    return None
