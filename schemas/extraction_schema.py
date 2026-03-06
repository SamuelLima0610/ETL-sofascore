from typing import List, Optional

from pydantic import BaseModel


class SeasonExtractionRequest(BaseModel):
    tournament_id: int
    season_id: int


class AllSeasonsExtractionRequest(BaseModel):
    slug_tournament: str
    tournament_id: int
    country: str
    length_tournaments: Optional[List[int]] = None