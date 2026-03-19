from utils.database import Database

class Load:

    def __init__(self, database=None):
        self.database = database or Database()

    def insert_data(self, data, collection):
        self.database.insert_data(data, collection)
    
