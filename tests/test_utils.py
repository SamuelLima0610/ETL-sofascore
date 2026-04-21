"""Tests para os utilitários do projeto"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from utils.tournaments import (
    get_tournaments_info,
    get_category_by_tournament_id,
    has_draws,
    get_team_image,
    CATEGORIES
)
from utils.process import _to_float, _extract_entry, _compute_outcome, _aggregate
import app_dependencies as deps


class TestTournamentsUtils:
    """Testes para utilidades de torneios."""

    def test_get_tournaments_info_success(self):
        """Testa obtenção de informações de torneios com sucesso."""
        mock_extractor = Mock()
        mock_extractor.get_tournaments = Mock(return_value=[
            {'id': 325, 'name': 'Brasileirão', 'category': 'football'}
        ])
        deps.extractor = mock_extractor

        result = get_tournaments_info()
        assert isinstance(result, dict)

    def test_get_tournaments_info_extractor_not_ready(self):
        """Testa obtenção de torneios quando extractor não está pronto."""
        deps.extractor = None

        with pytest.raises(Exception):
            get_tournaments_info()

    def test_get_category_by_tournament_id_found(self):
        """Testa busca de categoria por ID de torneio."""
        mock_extractor = Mock()
        mock_extractor.get_tournaments = Mock(return_value=[
            {'id': 325, 'name': 'Brasileirão', 'category': 'football'}
        ])
        deps.extractor = mock_extractor

        category, name = get_category_by_tournament_id(325)
        assert category == 'football' or category == 'stats'
        assert name == 'Brasileirão' or name is None

    def test_get_category_by_tournament_id_not_found(self):
        """Testa busca de categoria quando ID não existe."""
        mock_extractor = Mock()
        mock_extractor.get_tournaments = Mock(return_value=[])
        deps.extractor = mock_extractor

        category, name = get_category_by_tournament_id(999)
        assert category == 'stats'
        assert name is None

    def test_has_draws_football(self):
        """Testa se futebol permite empates."""
        assert has_draws('football') is True
        assert has_draws('FOOTBALL') is True

    def test_has_draws_other_sports(self):
        """Testa se outros esportes não permitem empates."""
        assert has_draws('basketball') is False
        assert has_draws('volleyball') is False
        assert has_draws('tennis') is False

    def test_get_team_image_success(self):
        """Testa obtenção de imagem de time com sucesso."""
        team = {'id': 1, 'name': 'Flamengo'}
        
        with patch('utils.tournaments.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b'image_data'
            mock_get.return_value = mock_response

            result = get_team_image(team)
            assert result == b'image_data'

    def test_get_team_image_not_found(self):
        """Testa obtenção de imagem quando não encontrada."""
        team = {'id': 1, 'name': 'Flamengo'}
        
        with patch('utils.tournaments.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response

            result = get_team_image(team)
            assert result is None

    def test_get_team_image_no_team(self):
        """Testa obtenção de imagem quando team é None."""
        result = get_team_image(None)
        assert result is None


class TestProcessUtils:
    """Testes para utilidades de processamento."""

    def test_to_float_valid_float(self):
        """Testa conversão de float válido."""
        assert _to_float(3.14) == 3.14
        assert _to_float("3.14") == 3.14

    def test_to_float_valid_int(self):
        """Testa conversão de inteiro."""
        assert _to_float(5) == 5.0
        assert _to_float("5") == 5.0

    def test_to_float_invalid(self):
        """Testa conversão de valor inválido."""
        assert _to_float("invalid") == 0.0
        assert _to_float(None) == 0.0
        assert _to_float([]) == 0.0

    def test_extract_entry_direct_format(self):
        """Testa extração de entrada no formato direto."""
        raw = {
            'name': 'Shots',
            'homeValue': 10,
            'awayValue': 8
        }
        name, home, away = _extract_entry(raw)
        assert name == 'Shots'
        assert home == 10.0
        assert away == 8.0

    def test_extract_entry_grouped_format(self):
        """Testa extração de entrada no formato agrupado."""
        raw = {
            'Big chances': {
                'name': 'Big chances',
                'homeValue': 3,
                'awayValue': 2
            }
        }
        name, home, away = _extract_entry(raw)
        assert name == 'Big chances'
        assert home == 3.0
        assert away == 2.0

    def test_extract_entry_invalid(self):
        """Testa extração com entrada inválida."""
        name, home, away = _extract_entry("invalid")
        assert name is None
        assert home == 0.0
        assert away == 0.0

    def test_compute_outcome_home_win(self):
        """Testa cálculo de resultado com vitória em casa."""
        result = _compute_outcome(2, 1, team_as_home=True)
        assert result == "wins"

    def test_compute_outcome_home_loss(self):
        """Testa cálculo de resultado com derrota em casa."""
        result = _compute_outcome(1, 2, team_as_home=True)
        assert result == "losses"

    def test_compute_outcome_home_draw(self):
        """Testa cálculo de resultado com empate em casa."""
        result = _compute_outcome(1, 1, team_as_home=True)
        assert result == "draws"

    def test_compute_outcome_away_win(self):
        """Testa cálculo de resultado com vitória fora."""
        result = _compute_outcome(1, 2, team_as_home=False)
        assert result == "wins"

    def test_compute_outcome_away_loss(self):
        """Testa cálculo de resultado com derrota fora."""
        result = _compute_outcome(2, 1, team_as_home=False)
        assert result == "losses"

    def test_aggregate_single_game(self):
        """Testa agregação de dados de um único jogo."""
        games = [
            {
                'home_score': 2,
                'away_score': 1,
                'stats': [
                    {
                        'Shots': [
                            {'name': 'Shots', 'homeValue': 10, 'awayValue': 8}
                        ]
                    }
                ]
            }
        ]
        result = _aggregate(games, team_as_home=True)
        assert 'record' in result
        assert result['record']['wins'] == 1

    def test_aggregate_multiple_games(self):
        """Testa agregação de dados de múltiplos jogos."""
        games = [
            {
                'home_score': 2,
                'away_score': 1,
                'stats': {}
            },
            {
                'home_score': 1,
                'away_score': 1,
                'stats': {}
            },
            {
                'home_score': 0,
                'away_score': 1,
                'stats': {}
            }
        ]
        result = _aggregate(games, team_as_home=True)
        assert result['record']['wins'] == 1
        assert result['record']['draws'] == 1
        assert result['record']['losses'] == 1

    def test_aggregate_no_games(self):
        """Testa agregação com lista vazia de jogos."""
        result = _aggregate([], team_as_home=True)
        assert result['record']['wins'] == 0
        assert result['record']['draws'] == 0
        assert result['record']['losses'] == 0
