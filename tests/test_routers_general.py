"""Tests para o router general.py"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
import app_dependencies as deps


class TestGeneralRouter:
    """Testes para os endpoints do router general."""

    def test_root_endpoint(self, client):
        """Testa se o endpoint raiz retorna informações esperadas."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data
        assert "endpoints" in data
        assert data["docs"] == "/docs"

    def test_health_check_healthy(self, client, setup_dependencies):
        """Testa se health check retorna status healthy."""
        with patch('routers.general.celery_app') as mock_celery:
            mock_inspector = MagicMock()
            mock_inspector.ping.return_value = {"worker1": "ok"}
            mock_celery.control.inspect.return_value = mock_inspector

            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "extractor_ready" in data
            assert "celery_ready" in data

    def test_health_check_extractor_not_ready(self, client, setup_dependencies):
        """Testa health check quando Extractor não está ready."""
        deps.extractor = None
        
        with patch('routers.general.celery_app') as mock_celery:
            mock_inspector = MagicMock()
            mock_inspector.ping.return_value = {"worker1": "ok"}
            mock_celery.control.inspect.return_value = mock_inspector

            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["extractor_ready"] is False

    def test_get_tournaments_success(self, client, setup_dependencies):
        """Testa busca de torneios com sucesso."""
        response = client.get("/tournaments")
        assert response.status_code == 200
        data = response.json()
        assert "tournaments" in data
        assert isinstance(data["tournaments"], dict)

    def test_get_tournaments_extractor_not_ready(self, client, setup_dependencies):
        """Testa busca de torneios quando Extractor não está ready."""
        deps.extractor = None
        
        response = client.get("/tournaments")
        assert response.status_code == 503
        data = response.json()
        assert "detail" in data

    def test_get_team_success(self, client, setup_dependencies):
        """Testa busca de time com sucesso."""
        deps.database.read_data = Mock(return_value=[
            {
                'id': 1,
                'name': 'Flamengo',
                'country': 'Brazil',
                'founded': 1895
            }
        ])

        with patch('routers.general.get_team_image', return_value=None):
            response = client.get("/teams/1")
            assert response.status_code == 200
            data = response.json()
            assert "team" in data
            assert data["team"]["id"] == 1
            assert data["team"]["name"] == "Flamengo"

    def test_get_team_not_found(self, client, setup_dependencies):
        """Testa busca de time que não existe."""
        deps.database.read_data = Mock(return_value=[])

        response = client.get("/teams/999")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_get_seasons_success(self, client, setup_dependencies):
        """Testa busca de temporadas com sucesso."""
        response = client.get(
            "/seasons",
            params={
                "slug_tournament": "brasileirao-serie-a",
                "tournament_id": 325,
                "country": "brazil"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "seasons" in data
        assert isinstance(data["seasons"], list)

    def test_get_seasons_extractor_not_ready(self, client, setup_dependencies):
        """Testa busca de temporadas quando Extractor não está ready."""
        deps.extractor = None
        
        response = client.get(
            "/seasons",
            params={
                "slug_tournament": "brasileirao-serie-a",
                "tournament_id": 325,
                "country": "brazil"
            }
        )
        assert response.status_code == 503

    def test_get_prediction_success(self, client, setup_dependencies):
        """Testa busca de predição com sucesso."""
        deps.database.read_data = Mock(return_value=[
            {
                'game_id': 1,
                'home_team': 'Flamengo',
                'away_team': 'São Paulo',
                'prediction': 0.65
            }
        ])

        response = client.get("/prediction/1")
        assert response.status_code == 200
        data = response.json()
        assert data["game_id"] == 1
        assert data["home_team"] == "Flamengo"

    def test_get_prediction_not_found(self, client, setup_dependencies):
        """Testa busca de predição que não existe."""
        deps.database.read_data = Mock(return_value=[])

        response = client.get("/prediction/999")
        assert response.status_code == 404

    def test_get_prediction_database_not_ready(self, client, setup_dependencies):
        """Testa busca de predição quando database não está ready."""
        deps.database = None
        
        response = client.get("/prediction/1")
        assert response.status_code == 503
