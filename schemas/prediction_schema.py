from pydantic import BaseModel


class PredictionRequest(BaseModel):
    tournament_id: int
    season_id: int
    game_id: int
    home_team: str
    away_team: str