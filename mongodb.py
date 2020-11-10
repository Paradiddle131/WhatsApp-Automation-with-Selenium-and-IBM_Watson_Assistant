import os
import time
from datetime import datetime

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.cursor import CursorType
from pymongo.errors import CollectionInvalid
from pymongo.errors import DuplicateKeyError

from splunk import Splunk


def do_dates_match(date_db, date_splunk):
    return date_db < datetime.strptime(date_splunk, '%m/%d/%Y %H:%M:%S.%f')


def get_watson_response_values(response_watson):
    watson_values = {}
    try:
        for entity in response_watson['output']['entities']:
            if entity['entity'] == 'HATA_KODLARI':
                error_code = entity['value']
                watson_values.update({"errorCode": error_code})
        entities = response_watson['output']['user_defined']
        for entity in entities:
            if entity == 'merchantId':
                merchantId = entities['merchantId']
                if isinstance(merchantId, list):
                    merchantId = entities['merchantId'][0]
                else:
                    merchantId = entities['merchantId']
                watson_values.update({"merchantId": merchantId})
    except Exception as e:
        print("Error ->", e)
    return watson_values


class MongoDB:
    def __init__(self, db_name, collection_name, initialize_splunk=True):
        load_dotenv(os.path.join(os.getcwd(), 'mongodb-credentials.env'))
        self.user = os.getenv('user')
        self.password = os.getenv('password')
        self.dbname = os.getenv('dbname')

        self.cluster = MongoClient(
            f"mongodb+srv://botAdmin:{self.password}@whatsappcluster.p1ato.mongodb.net/{self.dbname}?retryWrites=true&w=majority")
        self.db = self.cluster[db_name]
        try:
            self.db.create_collection(collection_name, capped=True, size=100000, max=100)
            self.collection = self.db[collection_name]
        except CollectionInvalid as e:
            print("CollectionInvalid ->", e)
            self.collection = self.db[collection_name]
        self.Splunk = Splunk(initialize_splunk=initialize_splunk)

    def insert(self, dictionary):
        try:
            return self.collection.insert_one(dictionary)
        except DuplicateKeyError:
            print(f"Document already exists.")

    def listen(self):
        cursor = self.collection.find(cursor_type=CursorType.TAILABLE)
        splunk_event_dict = {}
        splunk_dict = {}
        error_code = ''
        while cursor.alive:
            try:
                doc = cursor.next()
                print(doc['message'])
                response_watson = get_watson_response_values(doc['watson_response'])
                merchant_id = response_watson['merchantId'] if 'merchantId' in response_watson.keys() else ''
                if error_code not in splunk_dict.keys():
                    splunk_event_dict = self.Splunk.search(keyword=error_code)
                [print("-->" + merchant_id + " matched!") if merchant_id == event['Request']['MerchantId='] and
                                                             do_dates_match(doc['datetime'], event['Date'])
                 else '' for event in splunk_event_dict.values()]
                splunk_dict.update({error_code: splunk_event_dict})
            except StopIteration:
                time.sleep(5)


if __name__ == '__main__':
    load_dotenv(os.path.join(os.getcwd(), 'db.env'))
    mongo = MongoDB(db_name=os.getenv("db_name"),
                    collection_name=os.getenv("collection_name"),
                    initialize_splunk=True)
    mongo.listen()
    # TODO: Implement listen method for splunk that fetches new logs
