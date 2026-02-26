from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

class Load:

    def __init__(self):
        password = os.getenv('PASSWORD')
        self.client = MongoClient(f"mongodb+srv://mongo_db:{password}@cluster.bmwwbf1.mongodb.net/?appName=Cluster")
        database = self.client.get_database('Statistics')
        self.collection = database.get_collection('football_stats')

    def insert_data(self, data):
        self.collection.insert_many(data)

    def desconnect(self):
        self.client.close()