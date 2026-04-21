"""Tests para os schemas do projeto"""

import pytest
from pydantic import ValidationError
from schemas.extraction_schema import SeasonExtractionRequest, AllSeasonsExtractionRequest
from schemas.prediction_schema import PredictionRequest


class TestSeasonExtractionRequest:
    """Testes para o schema SeasonExtractionRequest."""

    def test_valid_season_extraction_request(self):
        """Testa criação válida de SeasonExtractionRequest."""
        payload = {
            "tournament_id": 325,
            "season_id": 1
        }
        request = SeasonExtractionRequest(**payload)
        assert request.tournament_id == 325
        assert request.season_id == 1

    def test_missing_tournament_id(self):
        """Testa falta de tournament_id."""
        payload = {"season_id": 1}
        with pytest.raises(ValidationError):
            SeasonExtractionRequest(**payload)

    def test_missing_season_id(self):
        """Testa falta de season_id."""
        payload = {"tournament_id": 325}
        with pytest.raises(ValidationError):
            SeasonExtractionRequest(**payload)

    def test_invalid_tournament_id_type(self):
        """Testa tipo inválido para tournament_id."""
        payload = {
            "tournament_id": "invalid",
            "season_id": 1
        }
        with pytest.raises(ValidationError):
            SeasonExtractionRequest(**payload)


class TestAllSeasonsExtractionRequest:
    """Testes para o schema AllSeasonsExtractionRequest."""

    def test_valid_all_seasons_extraction_request(self):
        """Testa criação válida de AllSeasonsExtractionRequest."""
        payload = {
            "slug_tournament": "brasileirao-serie-a",
            "tournament_id": 325,
            "country": "brazil"
        }
        request = AllSeasonsExtractionRequest(**payload)
        assert request.slug_tournament == "brasileirao-serie-a"
        assert request.tournament_id == 325
        assert request.country == "brazil"
        assert request.seasons_ids is None

    def test_with_optional_seasons_ids(self):
        """Testa com seasons_ids opcionais."""
        payload = {
            "slug_tournament": "brasileirao-serie-a",
            "tournament_id": 325,
            "country": "brazil",
            "seasons_ids": [1, 2, 3]
        }
        request = AllSeasonsExtractionRequest(**payload)
        assert request.seasons_ids == [1, 2, 3]

    def test_missing_required_fields(self):
        """Testa falta de campos obrigatórios."""
        payload = {
            "slug_tournament": "brasileirao-serie-a",
            "tournament_id": 325
        }
        with pytest.raises(ValidationError):
            AllSeasonsExtractionRequest(**payload)

    def test_empty_seasons_ids(self):
        """Testa com seasons_ids vazia."""
        payload = {
            "slug_tournament": "brasileirao-serie-a",
            "tournament_id": 325,
            "country": "brazil",
            "seasons_ids": []
        }
        request = AllSeasonsExtractionRequest(**payload)
        assert request.seasons_ids == []


class TestPredictionRequest:
    """Testes para o schema PredictionRequest."""

    def test_valid_prediction_request(self):
        """Testa criação válida de PredictionRequest."""
        payload = {
            "tournament_id": 325,
            "season_id": 1,
            "game_id": 100,
            "home_team": "Flamengo",
            "away_team": "São Paulo"
        }
        request = PredictionRequest(**payload)
        assert request.tournament_id == 325
        assert request.season_id == 1
        assert request.game_id == 100
        assert request.home_team == "Flamengo"
        assert request.away_team == "São Paulo"

    def test_missing_game_id(self):
        """Testa falta de game_id."""
        payload = {
            "tournament_id": 325,
            "season_id": 1,
            "home_team": "Flamengo",
            "away_team": "São Paulo"
        }
        with pytest.raises(ValidationError):
            PredictionRequest(**payload)

    def test_invalid_game_id_type(self):
        """Testa tipo inválido para game_id."""
        payload = {
            "tournament_id": 325,
            "season_id": 1,
            "game_id": "invalid",
            "home_team": "Flamengo",
            "away_team": "São Paulo"
        }
        with pytest.raises(ValidationError):
            PredictionRequest(**payload)

    def test_empty_team_names(self):
        """Testa com nomes de times vazios."""
        payload = {
            "tournament_id": 325,
            "season_id": 1,
            "game_id": 100,
            "home_team": "",
            "away_team": ""
        }
        # Schemas permitem strings vazias, mas devem ser testados com validações customizadas
        request = PredictionRequest(**payload)
        assert request.home_team == ""
        assert request.away_team == ""
