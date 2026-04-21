"""Testes para modelos ETL"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestExtractor:
    """Testes para a classe Extractor."""

    def test_extractor_initialization(self):
        """Testa inicialização do Extractor."""
        from etl.extractor import Extractor
        extractor = Extractor()
        assert extractor is not None
        assert hasattr(extractor, 'session')

    @patch('etl.extractor.requests.Session')
    def test_get_tournaments_success(self, mock_session_class):
        """Testa obtenção de torneios com sucesso."""
        from etl.extractor import Extractor
        
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        # Mock da resposta
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'uniqueTournaments': [
                {
                    'id': 325,
                    'name': 'Brasileirão Série A',
                    'slug': 'brasileirao-serie-a',
                    'category': {'slug': 'brazil'}
                }
            ]
        }
        mock_session.get.return_value = mock_response
        
        extractor = Extractor()
        tournaments = extractor.get_tournaments('football')
        
        assert len(tournaments) > 0
        assert tournaments[0]['id'] == 325
        assert tournaments[0]['name'] == 'Brasileirão Série A'

    def test_extractor_session_persistence(self):
        """Testa se a sessão persiste entre chamadas."""
        from etl.extractor import Extractor
        extractor = Extractor()
        session_1 = extractor.session
        session_2 = extractor.session
        assert session_1 is session_2


class TestLoad:
    """Testes para a classe Load."""

    @patch('etl.load.Database')
    def test_load_initialization(self, mock_db_class):
        """Testa inicialização do Load."""
        from etl.load import Load
        
        mock_db = MagicMock()
        load = Load(mock_db)
        
        assert load is not None
        assert load.database is not None


class TestDatabase:
    """Testes para a classe Database."""

    @patch('utils.database.MongoClient')
    @patch.dict('os.environ', {'PASSWORD_DB': 'test_pass', 'USER_DB': 'test_user'})
    def test_database_initialization(self, mock_client_class):
        """Testa inicialização do Database."""
        from utils.database import Database
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_database.return_value = MagicMock()
        
        db = Database()
        assert db is not None
        assert db.database is not None

    @patch('utils.database.MongoClient')
    @patch.dict('os.environ', {'PASSWORD_DB': 'test_pass', 'USER_DB': 'test_user'})
    def test_read_data(self, mock_client_class):
        """Testa leitura de dados."""
        from utils.database import Database
        
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_database.return_value.get_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client
        
        mock_collection.find.return_value = [
            {'id': 1, 'name': 'Game 1'}
        ]
        
        db = Database()
        result = db.read_data('games', {'id': 1})
        
        assert len(result) > 0
        assert result[0]['id'] == 1

    @patch('utils.database.MongoClient')
    @patch.dict('os.environ', {'PASSWORD_DB': 'test_pass', 'USER_DB': 'test_user'})
    def test_disconnect(self, mock_client_class):
        """Testa desconexão do banco."""
        from utils.database import Database
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_database.return_value = MagicMock()
        
        db = Database()
        db.disconnect()
        
        mock_client.close.assert_called_once()
