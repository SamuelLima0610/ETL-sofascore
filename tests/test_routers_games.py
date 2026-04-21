"""Tests para o router games.py"""

import pytest
from unittest.mock import Mock
from fastapi.testclient import TestClient
import app_dependencies as deps


class TestGamesRouter:
    """Testes para os endpoints do router games."""

    def test_get_games_success(self, client, setup_dependencies):
        """Testa busca de jogos com sucesso."""
        deps.database.read_data = Mock(return_value=[
            {
                '_id': '507f1f77bcf86cd799439011',
                'id': 1,
                'home_team': 'Flamengo',
                'away_team': 'São Paulo',
                'home_score': 2,
                'away_score': 1,
                'round': 1,
                'status': 'finished'
            }
        ])

        response = client.get("/games/football")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert data["count"] == 1
        assert "games" in data
        assert len(data["games"]) == 1
        assert data["games"][0]["home_team"] == "Flamengo"
        # _id deve ser convertida para string
        assert isinstance(data["games"][0]["_id"], str)

    def test_get_games_with_filters(self, client, setup_dependencies):
        """Testa busca de jogos com filtros."""
        deps.database.read_data = Mock(return_value=[
            {
                '_id': '507f1f77bcf86cd799439011',
                'id': 1,
                'home_score': 75,
                'away_score': 60
            }
        ])

        response = client.get("/games/football?home_score_gte=70&home_score_lte=80")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["filters"]["home_score"] == {"$gte": 70, "$lte": 80}

    def test_get_games_no_results(self, client, setup_dependencies):
        """Testa busca de jogos sem resultados."""
        deps.database.read_data = Mock(return_value=[])

        response = client.get("/games/football")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["games"] == []

    def test_get_games_load_not_ready(self, client, setup_dependencies):
        """Testa busca de jogos quando Load não está ready."""
        deps.load = None

        response = client.get("/games/football")
        assert response.status_code == 503
        data = response.json()
        assert "detail" in data

    def test_get_games_with_multiple_filters(self, client, setup_dependencies):
        """Testa busca de jogos com múltiplos filtros."""
        deps.database.read_data = Mock(return_value=[])

        response = client.get(
            "/games/football?team=Flamengo&round_gte=5&round_lte=10&status=finished"
        )
        assert response.status_code == 200
        data = response.json()
        
        filters = data["filters"]
        assert filters["team"] == "Flamengo"
        assert filters["round"] == {"$gte": 5, "$lte": 10}
        assert filters["status"] == "finished"

    def test_get_games_different_category(self, client, setup_dependencies):
        """Testa busca de jogos em categoria diferente."""
        deps.database.read_data = Mock(return_value=[
            {
                '_id': '507f1f77bcf86cd799439012',
                'id': 1,
                'home_team': 'Lakers',
                'away_team': 'Celtics',
                'home_score': 115,
                'away_score': 110
            }
        ])

        response = client.get("/games/basketball")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["games"][0]["home_team"] == "Lakers"

    def test_filter_operators(self, client, setup_dependencies):
        """Testa diferentes operadores de filtro."""
        deps.database.read_data = Mock(return_value=[])

        # Testando operador ne (not equal)
        response = client.get("/games/football?status_ne=cancelled")
        assert response.status_code == 200
        data = response.json()
        assert data["filters"]["status"] == {"$ne": "cancelled"}

    def test_parse_float_filter_value(self, client, setup_dependencies):
        """Testa parsing de valores float em filtros."""
        deps.database.read_data = Mock(return_value=[])

        response = client.get("/games/football?rating_gte=4.5")
        assert response.status_code == 200
        data = response.json()
        assert data["filters"]["rating"]["$gte"] == 4.5

    def test_parse_integer_filter_value(self, client, setup_dependencies):
        """Testa parsing de valores inteiros em filtros."""
        deps.database.read_data = Mock(return_value=[])

        response = client.get("/games/football?round_eq=5")
        assert response.status_code == 200
        data = response.json()
        assert data["filters"]["round"] == {"$eq": 5}
