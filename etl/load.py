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

    def desconnect(self):
        self.client.close()