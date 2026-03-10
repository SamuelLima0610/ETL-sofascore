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
    
    def __get_games_by_round(self, rounds, tournament_id, season_id):
        games = []
        for round in rounds:
            try:
                key = 'round'
                if 'slug' in round.keys():
                    key = 'name'
                    response = self.session.get(f"https://www.sofascore.com/api/v1/unique-tournament/{tournament_id}/season/{season_id}/events/round/{round['round']}/slug/{round['slug']}")
                else:
                    response = self.session.get(f"https://www.sofascore.com/api/v1/unique-tournament/{tournament_id}/season/{season_id}/events/round/{round[key]}")
                data = response.json()
                for game in data['events']:
                    game_info = game
                    if 'current' not in list(game['homeScore'].keys()) and 'current' not in list(game['awayScore'].keys()):
                        continue
                    try:
                        game_info['season_id'] = season_id
                        game_info['stats'] = self.__get_game_stats(game['id'])
                        game_info['round'] = round[key]
                        game_info['time'] = game['time']['currentPeriodStartTimestamp']
                    except (KeyError, IndexError):
                        game_info['stats'] = None
                    games.append(game_info)
            except Exception as e:
                print(f"Erro ao extrair jogos para round {round[key]}: {str(e)}")
                continue
        return games
    
    def __get_games_by_last(self, tournament_id, season_id):
        games = []
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
                        game_info['time'] = game['time']['currentPeriodStartTimestamp']
                    except (KeyError, IndexError):
                        game_info['stats'] = None
                    games.append(game_info)
                index += 1
            except Exception as e:
                print(f"Erro ao extrair jogos para last {index}: {str(e)}")
                break
        bigger = max(games, key=lambda x: x["round"])
        max_round = bigger["round"]
        for game in games:
            game["round"] = max_round - game["round"]
        return games

    def get_games_by_season(self, tournament_id, season_id):
        response = self.session.get(f"https://www.sofascore.com/api/v1/unique-tournament/{tournament_id}/season/{season_id}/rounds")
        if response.status_code != 200:
            return self.__get_games_by_last(tournament_id, season_id)
        else:
            return self.__get_games_by_round(response.json()['rounds'], tournament_id, season_id)