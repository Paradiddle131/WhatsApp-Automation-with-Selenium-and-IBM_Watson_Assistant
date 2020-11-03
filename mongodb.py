import os
from pymongo import MongoClient
from dotenv import load_dotenv


class MongoDB:
    def __init__(self):
        load_dotenv(os.path.join(os.getcwd(), 'mongodb-credentials.env'))
        self.user = os.getenv('user')
        self.password = os.getenv('password')
        self.dbname = os.getenv('dbname')

        self.cluster = MongoClient(
            f"mongodb+srv://botAdmin:{self.password}@whatsappcluster.p1ato.mongodb.net/{self.dbname}?retryWrites=true&w=majority")
        self.db = self.cluster['WhatsApp']
        self.collection = self.db['Messages']

    def insert(self, dictionary):
        return self.collection.insert_one(dictionary)


if __name__ == '__main__':
    mongo = MongoDB()

    post1 = {"name": "lasagna"}
    post2 = {"_id": 5, "name": "joe"}
    post3 = {'sample1': {
        "message": "sample-message",
        "sender": "905001234567",
        "time": "03:14",
        "ibm": {
            "intent": "",
            "entity": "sample-entity"
        }
    }}

    x = mongo.insert(post3)