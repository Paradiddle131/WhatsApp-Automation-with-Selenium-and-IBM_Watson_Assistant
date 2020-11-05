import os
from pymongo import MongoClient


class MongoDB:
    def __init__(self, db_name='WhatsApp', collection_name='messages'):
        self.user = os.getenv('mongo_user')
        self.password = os.getenv('mongo_password')
        self.dbname = os.getenv('mongo_dbname')

        self.cluster = MongoClient(
            f"mongodb+srv://botAdmin:{self.password}@whatsappcluster.p1ato.mongodb.net/{self.dbname}?retryWrites=true&w=majority")
        self.db = self.cluster[db_name]
        self.collection = self.db[collection_name]

    def insert(self, dictionary):
        return self.collection.insert_one(dictionary)
