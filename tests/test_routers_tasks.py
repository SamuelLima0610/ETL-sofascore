"""Tests para o router tasks.py"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from celery.result import AsyncResult
import app_dependencies as deps


class TestTasksRouter:
    """Testes para os endpoints do router tasks."""

    def test_get_seasons_async(self, client, setup_dependencies):
        """Testa disparo de task assíncrona de seasons."""
        mock_task = MagicMock()
        mock_task.id = "test-task-id-123"

        with patch('routers.tasks.get_seasons_task') as mock_get_seasons:
            mock_get_seasons.delay.return_value = mock_task

            response = client.post("/async/seasons")
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "test-task-id-123"
            assert data["status"] == "processing"

    def test_get_games_by_season_async(self, client, setup_dependencies):
        """Testa disparo de extração assíncrona de jogos por temporada."""
        mock_task = MagicMock()
        mock_task.id = "test-task-id-456"

        with patch('routers.tasks.extract_games_by_season_task') as mock_extract, \
             patch('routers.tasks.get_category_by_tournament_id') as mock_get_category:
            
            mock_get_category.return_value = ('football', 'Brasileirão')
            mock_extract.delay.return_value = mock_task

            payload = {
                "tournament_id": 325,
                "season_id": 1
            }

            response = client.post("/async/games/season", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "test-task-id-456"
            assert data["season_id"] == 1
            assert data["tournament_id"] == 325
            assert data["category"] == "football"

    def test_get_all_games_async(self, client, setup_dependencies):
        """Testa disparo de extração assíncrona de todos os jogos."""
        mock_task = MagicMock()
        mock_task.id = "test-task-id-789"

        with patch('routers.tasks.extract_all_games_task') as mock_extract, \
             patch('routers.tasks.get_category_by_tournament_id') as mock_get_category:
            
            mock_get_category.return_value = ('football', 'Brasileirão')
            mock_extract.delay.return_value = mock_task

            payload = {
                "slug_tournament": "brasileirao-serie-a",
                "tournament_id": 325,
                "country": "brazil",
                "seasons_ids": [1, 2]
            }

            response = client.post("/async/games", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "test-task-id-789"
            assert data["status"] == "processing"

    def test_get_task_status_pending(self, client, setup_dependencies):
        """Testa consulta de status de task em estado PENDING."""
        with patch('routers.tasks.AsyncResult') as mock_async_result:
            mock_result = MagicMock()
            mock_result.state = "PENDING"
            mock_result.info = None
            mock_result.result = None
            mock_async_result.return_value = mock_result

            response = client.get("/tasks/test-task-id")
            assert response.status_code == 200
            data = response.json()
            assert data["state"] == "PENDING"
            assert "status" in data

    def test_get_task_status_progress(self, client, setup_dependencies):
        """Testa consulta de status de task em estado PROGRESS."""
        with patch('routers.tasks.AsyncResult') as mock_async_result:
            mock_result = MagicMock()
            mock_result.state = "PROGRESS"
            mock_result.info = {"current": 50, "total": 100, "status": "Processing"}
            mock_result.result = None
            mock_async_result.return_value = mock_result

            response = client.get("/tasks/test-task-id")
            assert response.status_code == 200
            data = response.json()
            assert data["state"] == "PROGRESS"
            assert data["progress"]["current"] == 50
            assert data["progress"]["total"] == 100

    def test_get_task_status_success(self, client, setup_dependencies):
        """Testa consulta de status de task em estado SUCCESS."""
        with patch('routers.tasks.AsyncResult') as mock_async_result:
            mock_result = MagicMock()
            mock_result.state = "SUCCESS"
            mock_result.info = None
            mock_result.result = {"total_games": 100, "season_id": 1}
            mock_async_result.return_value = mock_result

            response = client.get("/tasks/test-task-id")
            assert response.status_code == 200
            data = response.json()
            assert data["state"] == "SUCCESS"
            assert data["result"]["total_games"] == 100

    def test_get_task_status_failure(self, client, setup_dependencies):
        """Testa consulta de status de task em estado FAILURE."""
        with patch('routers.tasks.AsyncResult') as mock_async_result:
            mock_result = MagicMock()
            mock_result.state = "FAILURE"
            mock_result.info = "Error: Database connection failed"
            mock_result.result = None
            mock_async_result.return_value = mock_result

            response = client.get("/tasks/test-task-id")
            assert response.status_code == 200
            data = response.json()
            assert data["state"] == "FAILURE"
            assert "error" in data

    def test_cancel_task(self, client, setup_dependencies):
        """Testa cancelamento de task."""
        with patch('routers.tasks.AsyncResult') as mock_async_result:
            mock_result = MagicMock()
            mock_result.revoke = Mock()
            mock_async_result.return_value = mock_result

            response = client.delete("/tasks/test-task-id")
            assert response.status_code == 200
            mock_result.revoke.assert_called_once_with(terminate=True)

    def test_predict_game_winner_async(self, client, setup_dependencies):
        """Testa disparo de predição assíncrona de resultado de jogo."""
        mock_task = MagicMock()
        mock_task.id = "test-task-id-pred"

        with patch('routers.tasks.predict_match_task') as mock_predict, \
             patch('routers.tasks.get_category_by_tournament_id') as mock_get_category:
            
            mock_get_category.return_value = ('football', 'Brasileirão')
            mock_predict.delay.return_value = mock_task

            payload = {
                "tournament_id": 325,
                "season_id": 1,
                "game_id": 100,
                "home_team": "Flamengo",
                "away_team": "São Paulo"
            }

            response = client.post("/async/prediction", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "test-task-id-pred"
            assert data["category"] == "football"
