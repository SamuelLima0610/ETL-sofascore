from dotenv import load_dotenv
import os
from pymongo import MongoClient

load_dotenv()

class Database:

    def __init__(self):
        password = os.getenv('PASSWORD_DB')
        user = os.getenv('USER_DB')
        self.client = MongoClient(f"mongodb+srv://{user}:{password}@cluster.bmwwbf1.mongodb.net/?appName=Cluster")
        self.database = self.client.get_database('Statistics')
    
    def insert_data(self, data, collection):
        self.collection = self.database.get_collection(collection)
        try:
            self.collection.insert_many(data, ordered=False)
        except Exception as e:            
            pass

    def read_data(self, collection, query={}):
        self.collection = self.database.get_collection(collection)
        return list(self.collection.find(query))

    def read_last_games(self, collection, team_name: str, n: int = 5, lt_value=None, tournament_id=None, season_id=None):
        self.collection = self.database.get_collection(collection)
        team_clause = {"$or": [{"home_team": team_name}, {"away_team": team_name}]}

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