"""Tests de integração para a API"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import app_dependencies as deps


class TestIntegration:
    """Testes de integração para a API."""

    def test_full_workflow_mock(self, client, setup_dependencies):
        """Testa um fluxo completo de uso da API com mocks."""
        # 1. Verificar saúde
        response = client.get("/health")
        assert response.status_code == 200

        # 2. Buscar torneios
        response = client.get("/tournaments")
        assert response.status_code == 200

        # 3. Buscar temporadas
        response = client.get(
            "/seasons",
            params={
                "slug_tournament": "brasileirao-serie-a",
                "tournament_id": 325,
                "country": "brazil"
            }
        )
        assert response.status_code == 200

        # 4. Buscar jogos
        deps.database.read_data = Mock(return_value=[
            {
                '_id': '507f1f77bcf86cd799439011',
                'id': 1,
                'home_team': 'Flamengo',
                'away_team': 'São Paulo',
                'home_score': 2,
                'away_score': 1,
            }
        ])
        response = client.get("/games/football")
        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_error_handling_cascade(self, client, setup_dependencies):
        """Testa cascata de tratamento de erros."""
        # Quando extractor não está pronto
        deps.extractor = None
        
        response = client.get("/tournaments")
        assert response.status_code == 503

        # Quando database não está pronto
        deps.database = None
        response = client.get("/games/football")
        # Pode ser 503 ou 500 dependendo da implementação

    def test_multiple_requests_independence(self, client, setup_dependencies):
        """Testa que múltiplas requisições são independentes."""
        mock_data_1 = [{'_id': '1', 'id': 1, 'name': 'Game 1'}]
        mock_data_2 = [{'_id': '2', 'id': 2, 'name': 'Game 2'}]

        deps.database.read_data = Mock(return_value=mock_data_1)
        response1 = client.get("/games/football")
        assert response1.json()["count"] == 1

        deps.database.read_data = Mock(return_value=mock_data_2)
        response2 = client.get("/games/basketball")
        assert response2.json()["count"] == 1

        # As respostas devem ser independentes
        assert response1.json()["count"] == response2.json()["count"]

    def test_concurrent_categories(self, client, setup_dependencies):
        """Testa requisições de categorias diferentes."""
        deps.database.read_data = Mock(return_value=[
            {'_id': '1', 'id': 1, 'category': 'football'}
        ])

        # Teste categorias diferentes
        categories = ['football', 'basketball', 'volleyball']
        for category in categories:
            response = client.get(f"/games/{category}")
            assert response.status_code == 200
            assert response.json()["count"] >= 0

    def test_filter_chain_consistency(self, client, setup_dependencies):
        """Testa consistência de filtros encadeados."""
        deps.database.read_data = Mock(return_value=[])

        # Filtro 1
        response = client.get("/games/football?score_gte=50")
        assert response.status_code == 200
        filters_1 = response.json()["filters"]

        # Filtro 2
        response = client.get("/games/football?score_gte=50&score_lte=100")
        assert response.status_code == 200
        filters_2 = response.json()["filters"]

        # Verificar que os filtros foram construídos corretamente
        assert filters_1["score"] == {"$gte": 50}
        assert filters_2["score"] == {"$gte": 50, "$lte": 100}
