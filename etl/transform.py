from const.const_football import MATCH_OVER_VIEW, SHOTS, PASSES, DUELS, DEFENDING, GOALKEEPING

class Transform:

    def __init__(self, data, tournament_id):
        self.data = data
        self.tournament_id = tournament_id

    def transform(self):
        transformed_data = []
        for game in self.data:
            if game['stats'] is not None:
                transformed_data.append(self.__get_game_basic_info(game))
        return transformed_data
    
    def __get_game_basic_info(self, game):
        game_info = {}
        game_info['season'] = game['season_id']
        game_info['tournament_id'] = self.tournament_id
        game_info['round'] = game['round']
        game_info['id'] = game['id']
        game_info['home_team'] = game['homeTeam']['name']
        game_info['away_team'] = game['awayTeam']['name']
        game_info['home_score'] = game['homeScore']['current']
        game_info['away_score'] = game['awayScore']['current']
        game_info['stats'] = game['stats']
        return game_info