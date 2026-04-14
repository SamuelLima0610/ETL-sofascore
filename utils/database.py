from dotenv import load_dotenv
import os, time
from pymongo import MongoClient

load_dotenv()

class Database:

    def __init__(self):
        password = os.getenv('PASSWORD_DB')
        user = os.getenv('USER_DB')
        self.client = MongoClient(f"mongodb+srv://{user}:{password}@cluster.bmwwbf1.mongodb.net/?appName=Cluster")
        self.database = self.client.get_database('Statistics')
    
    def insert_data(self, games, collection):
        self.collection = self.database.get_collection(collection)
        for game in games:
            try:
                game_searched = list(self.read_data(collection, {"id": game["id"]}))
                if len(game_searched) > 0:
                    if 'status' in list(game_searched[0].keys()) and 'status' not in list(game.keys()):
                        self.collection.replace_one({"id": game["id"]}, game)
                if len(game_searched) == 0:
                    self.collection.insert_one(game)
            except Exception as e:            
                pass

    def insert_prediction(self, prediction):
        self.collection = self.database.get_collection('predictions')
        self.collection.replace_one({"game_id": prediction["game_id"]}, prediction, upsert=True)

    def insert_player_stats(self, player_stats):
        self.collection = self.database.get_collection('players_stats')
        self.collection.insert_many(player_stats, ordered=False)
    
    def read_data(self, collection, query={}):
        self.collection = self.database.get_collection(collection)
        return list(self.collection.find(query))

    def read_last_games(self, collection, team_name: str, n: int = 5, lt_value=None, tournament_id=None, season_id=None):
        self.collection = self.database.get_collection(collection)
        team_clause = {
            "$and": [
                {"$or": [{"home_team": team_name}, {"away_team": team_name}]},
                {"status": {"$exists": False}}
            ]
        }

        if lt_value is not None:
            try:
                # tenta converter lt_value para int quando apropriado
                cmp_value = int(lt_value)
            except Exception:
                cmp_value = lt_value
            query = {"$and": [team_clause, {"time": {"$lt": cmp_value}}, {'tournament_id': {"$eq": tournament_id}}, {'season': {"$eq": season_id}}]}
        else:
            query = team_clause

        cursor = self.collection.find(query).sort("time", -1).limit(int(n))
        return list(cursor)

    def disconnect(self):
        self.client.close()