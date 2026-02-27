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
        self.collection.insert_many(data)

    def desconnect(self):
        self.client.close()