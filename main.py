from extractor import Extractor
from transform import Transform
from load import Load

extractor = Extractor("https://www.sofascore.com/pt/football/tournament/brazil/brasileirao-serie-a/325#id:87678")

seasons = extractor.get_seasons()
games = extractor.get_games_by_season(seasons[1]['id'])
transform = Transform(games)
filtered_games = transform.transform()
loader = Load()
loader.insert_data(filtered_games)
loader.desconnect()

print("Concluido com sucesso!")