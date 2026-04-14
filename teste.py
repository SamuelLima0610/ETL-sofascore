from etl.extractor import Extractor
from etl.load import Load
from etl.transform import Transform
from utils.database import Database


database = Database()
loader = Load(database)


# Inicializa extractor
extractor = Extractor()
games = extractor.get_games_by_season(7, 76953)
if games:
    transformer = Transform(games, 7)
    
    # Carrega os times
    teams = transformer.transform_teams()
    loader.insert_data(teams, 'teams')
    
    #Carrega os jogadores
    player_stats = database.read_data(collection='players_stats', query={'game_id': games[0]['id']})
    if player_stats and len(player_stats) > 0:
        print('Informação dos jogadores da partida já existem no MongoDB. Pulando etapa de extração e carga dos jogadores')   
    else: 
        players_stats = transformer.transform_players_stats()
        database.insert_player_stats(players_stats)
        
    games = transformer.transform_games()

database.disconnect()