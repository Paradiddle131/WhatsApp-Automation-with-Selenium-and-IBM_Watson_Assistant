import os
from pymongo import MongoClient, CursorType
from dotenv import load_dotenv
import time
from splunk import Splunk


class MongoDB:
    def __init__(self, db_name='WhatsApp', collection_name='messages', initialize_splunk=True):
        load_dotenv(os.path.join(os.getcwd(), 'mongodb-credentials.env'))
        self.user = os.getenv('user')
        self.password = os.getenv('password')
        self.dbname = os.getenv('dbname')

        self.cluster = MongoClient(
            f"mongodb+srv://botAdmin:{self.password}@whatsappcluster.p1ato.mongodb.net/{self.dbname}?retryWrites=true&w=majority")
        self.db = self.cluster[db_name]
        self.collection = self.db[collection_name]

        self.Splunk = Splunk(initialize_splunk=initialize_splunk)

    def insert(self, dictionary):
        return self.collection.insert_one(dictionary)

    def listen(self):
        cursor = self.collection.find(cursor_type=CursorType.TAILABLE_AWAIT)
        while cursor.alive:
            try:
                doc = cursor.next()
                print(doc)
                try:
                    self.Splunk.compare_merchantIds(doc['watson_response'])
                except Exception as e:
                    print(e)
                    print(f"No watson_response found.")
            except StopIteration:
                time.sleep(1)


if __name__ == '__main__':
    mongo = MongoDB(db_name='WhatsApp', collection_name='messages', initialize_splunk=True)

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
    # mongo.insert(post3)
    mongo.listen()
