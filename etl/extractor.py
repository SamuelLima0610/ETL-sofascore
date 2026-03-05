import requests, json
from bs4 import BeautifulSoup

class Extractor:
    
    def __init__(self):
        self.session = requests.Session()

    def get_tournaments(self, category="football"):
        self.session.get("https://www.sofascore.com/pt/")
        response = self.session.get(f"https://www.sofascore.com/api/v1/config/default-unique-tournaments/BR/{category}")
        data = response.json()
        tournaments = []
        for tournament in data['uniqueTournaments']:
            info = {}
            info['name'] = tournament['name']
            info['slug'] = tournament['slug']
            info['id'] = tournament['id'] 
            info['country'] = tournament['category']['slug']
            info['category'] = category
            tournaments.append(info)
        return tournaments
    
    def get_seasons(self, competition_url):
        self.session.get("https://www.sofascore.com/pt/")
        response = self.session.get(competition_url)
        soup = BeautifulSoup(response.text, "html.parser")
        element = soup.find("script", {"id": "__NEXT_DATA__"})
        dados = json.loads(element.text)
        seasons = dados["props"]["pageProps"]["initialProps"]["seasons"]
        return seasons
    
    def __get_game_stats(self, game_id):
        response = self.session.get(f"https://www.sofascore.com/api/v1/event/{game_id}/statistics")
        statistics = response.json()
        return statistics['statistics'][0]['groups']
    
    def get_games_by_season(self, tournament_id, season_id):
        tag = 'round'
        games = []
        index = 1
        response = self.session.get(f"https://www.sofascore.com/api/v1/unique-tournament/{tournament_id}/season/{season_id}/events/{tag}/{index}")
        if response.status_code != 200:
            tag = 'last'
            index = 0
        while True:
            try:
                response = self.session.get(f"https://www.sofascore.com/api/v1/unique-tournament/{tournament_id}/season/{season_id}/events/last/{index}")
                if response.status_code != 200:
                    break
                data = response.json()
                for game in data['events']:
                    game_info = game
                    if 'current' not in list(game['homeScore'].keys()) and 'current' not in list(game['awayScore'].keys()):
                        continue
                    try:
                        game_info['season_id'] = season_id
                        game_info['stats'] = self.__get_game_stats(game['id'])
                        game_info['round'] = index
                    except (KeyError, IndexError):
                        game_info['stats'] = None
                    games.append(game_info)
                index += 1
            except Exception as e:
                print(f"Erro ao extrair jogos para {tag} {index}: {str(e)}")
                break
        return games