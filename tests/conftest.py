"""Pytest configuration and shared fixtures."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient

import app_dependencies as deps


@pytest.fixture
def mock_extractor():
    """Fixture para mock do Extractor."""
    mock = Mock()
    mock.get_tournaments = Mock(return_value=[
        {
            'id': 325,
            'name': 'Brasileirão Série A',
            'slug': 'brasileirao-serie-a',
            'country': 'brazil',
            'category': 'football'
        }
    ])
    mock.get_seasons = Mock(return_value=[
        {'id': 1, 'year': 2023},
        {'id': 2, 'year': 2024}
    ])
    return mock


@pytest.fixture
def mock_database():
    """Fixture para mock do Database."""
    mock = Mock()
    mock.read_data = Mock(return_value=[
        {'id': 1, 'name': 'Flamengo', 'country': 'Brazil'}
    ])
    mock.disconnect = Mock()
    return mock


@pytest.fixture
def mock_load():
    """Fixture para mock do Load."""
    mock = Mock()
    return mock


@pytest.fixture
def setup_dependencies(mock_extractor, mock_database, mock_load):
    """Configura as dependências globais para testes."""
    original_extractor = deps.extractor
    original_database = getattr(deps, 'database', None)
    original_load = deps.load

    deps.extractor = mock_extractor
    deps.database = mock_database
    deps.load = mock_load

    yield

    # Cleanup
    deps.extractor = original_extractor
    deps.database = original_database
    deps.load = original_load


@pytest.fixture
def client(setup_dependencies):
    """Cliente de teste para FastAPI."""
    from api import app
    return TestClient(app)
