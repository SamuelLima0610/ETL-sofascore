from extractor import Extractor


extractor = Extractor()

seasons = extractor.get_seasons()
games = extractor.get_games_by_season(seasons[0]['id'])
print(games)