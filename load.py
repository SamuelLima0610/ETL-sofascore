from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

class Load:

    def __init__(self):
        password = os.getenv('PASSWORD_DB')
        user = os.getenv('USER_DB')
        collection = os.getenv('MONGODB_COLLECTION')
        self.client = MongoClient(f"mongodb+srv://{user}:{password}@cluster.bmwwbf1.mongodb.net/?appName=Cluster")
        database = self.client.get_database('Statistics')
        self.collection = database.get_collection(collection)

    def insert_data(self, data):
        # Filtra jogos que ainda não existem no banco
        games_to_insert = []
        for game in data:
            # Verifica se já existe um jogo com o mesmo season, round, home_team e away_team
            existing_game = self.collection.find_one({
                'season': game['season'],
                'round': game['round'],
                'home_team': game['home_team'],
                'away_team': game['away_team']
            })
            
            if existing_game is None:
                games_to_insert.append(game)
        
        # Insere apenas os jogos que não existem
        if games_to_insert:
            self.collection.insert_many(games_to_insert)

    def read_data(self, query={}):
        return list(self.collection.find(query))

    def desconnect(self):
        self.client.close()