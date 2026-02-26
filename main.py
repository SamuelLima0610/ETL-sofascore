from extractor import Extractor
from transform import Transform


extractor = Extractor("https://www.sofascore.com/pt/football/tournament/brazil/brasileirao-serie-a/325#id:87678")

seasons = extractor.get_seasons()
games = extractor.get_games_by_season(seasons[0]['id'])
transform = Transform(games)
filtered_games = transform.transform()