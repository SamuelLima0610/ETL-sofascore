from const.const_football import MATCH_OVER_VIEW, SHOTS, PASSES, DUELS, DEFENDING, GOALKEEPING

class Transform:

    def __init__(self, data, tournament_id):
        self.data = data
        self.tournament_id = tournament_id

    def transform_games(self):
        transformed_data = []
        for game in self.data:
            if game['stats'] is not None:
                transformed_data.append(self.__get_game_basic_info(game))
        return transformed_data
    
    def transform_teams(self):
        teams = []
        for game in self.data:
            home_team = self.__get_teams_info(game, 'homeTeam')
            if teams.count(home_team) == 0:
                teams.append(home_team)
            away_team = self.__get_teams_info(game, 'awayTeam')
            if teams.count(away_team) == 0:
                teams.append(away_team)
        return teams
    
    def transform_players_stats(self):
        players_stats = []
        for game in self.data:
            if 'players_stats' in list(game.keys()) and game['players_stats'] is not None:
                players_stats.extend(self.__get_players_stats_info(game, 'home'))
                players_stats.extend(self.__get_players_stats_info(game, 'away'))
        return players_stats
    
    def __get_game_basic_info(self, game):
        game_info = {}
        game_info['season'] = game['season_id']
        game_info['tournament_id'] = self.tournament_id
        game_info['round'] = game['round']
        game_info['id'] = game['id']
        game_info['home_team'] = game['homeTeam']['name']
        game_info['away_team'] = game['awayTeam']['name']
        game_info['home_team_id'] = game['homeTeam']['id']
        game_info['away_team_id'] = game['awayTeam']['id']
        try:
            game_info['home_score'] = game['homeScore']['current']
            game_info['away_score'] = game['awayScore']['current']
            game_info['stats'] = game['stats']
        except KeyError:
            game_info['home_score'] = ''
            game_info['away_score'] = ''
            game_info['stats'] = []
            game_info['status'] = game['status']['type']
        game_info['time'] = game['time']
        return game_info
    
    def __get_teams_info(self, game, key):
        team_info = {}
        team_info['id'] = game[key]['id']
        team_info['name'] = game[key]['name']
        team_info['slug'] = game[key]['slug']
        return team_info
    
    def __get_players_stats_info(self, game, team_key):
        players_stats = []
        games_stats = game['players_stats'][team_key]['players']
        for player in games_stats:
            player_info = {
                'game_id': game['id'],
                'team': player['teamId'],
                'player_name': player['player']['name'],
                'position': player['player']['position'],
                'statistics': player.get('statistics', []),
                'jersey_number': player.get('jerseyNumber', '')
            }
            players_stats.append(player_info)
        return players_stats