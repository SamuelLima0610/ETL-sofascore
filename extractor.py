import requests, json
from bs4 import BeautifulSoup

class Extractor:
    
    def __init__(self, competition_url):
        self.session = requests.Session()
        self.session.get("https://www.sofascore.com/pt/")
        response = self.session.get(competition_url)
        soup = BeautifulSoup(response.text, "html.parser")
        element = soup.find("script", {"id": "__NEXT_DATA__"})
        dados = json.loads(element.text)
        seasons = dados["props"]["pageProps"]["initialProps"]["seasons"]
        self.wanted_seasons = [season for season in seasons if int(season["year"].replace("/", "")) >= 2013]

    def get_seasons(self):
        return self.wanted_seasons
    
    def __get_game_basic_info(self, game, season_id, round):
        game_info = {}
        game_info['season'] = season_id
        game_info['round'] = round
        game_info['id'] = game['id']
        game_info['home_team'] = game['homeTeam']['name']
        game_info['away_team'] = game['awayTeam']['name']
        game_info['home_score'] = game['homeScore']['current']
        game_info['away_score'] = game['awayScore']['current']
        return game_info

    def __get_game_stats(self, game_id):
        response = self.session.get(f"https://www.sofascore.com/api/v1/event/{game_id}/statistics")
        statistics = response.json()
        return statistics['statistics'][0]['groups']
    
    def get_games_by_season(self, season_id):
        games = []
        for round in range(1, 39):
            response = self.session.get(f"https://www.sofascore.com/api/v1/unique-tournament/325/season/{season_id}/events/round/{round}")
            data = response.json()
            for game in data['events']:
                try:
                    game_info = self.__get_game_basic_info(game, season_id, round)
                except KeyError:
                    continue
                try:
                    game_info['stats'] = self.__get_game_stats(game['id'])
                except (KeyError, IndexError):
                    game_info['stats'] = None
                games.append(game_info)
        return games
    
    def get_games(self):
        games = []
        for season in self.wanted_seasons:
            games.extend(self.get_games_by_season(season['id']))
        return games
