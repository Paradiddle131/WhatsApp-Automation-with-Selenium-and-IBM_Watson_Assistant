import os
import time
from pprint import pprint
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import CollectionInvalid
from splunk import Splunk


def do_dates_match(date_db, date_splunk):
    return date_db < datetime.strptime(date_splunk, '%m/%d/%Y %H:%M:%S.%f')


def get_watson_response_values(response_watson):
    watson_values = {}
    entities = response_watson['output']['user_defined']
    for entity in entities:
        if entity == 'errorCode':
            error_code = entities['errorCode']
            if isinstance(error_code, list):
                error_code = entities['errorCode'][0]
            else:
                error_code = entities['errorCode']
            watson_values.update({"errorCode": error_code})
        if entity == 'merchantId':
            merchantId = entities['merchantId']
            if isinstance(merchantId, list):
                merchantId = entities['merchantId'][0]
            else:
                merchantId = entities['merchantId']
            watson_values.update({"merchantId": merchantId})
    return watson_values


class MongoDB:
    def __init__(self, db_name='WhatsApp', collection_name='Messages', initialize_splunk=True):
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
            print(e)
            self.collection = self.db[collection_name]
        self.Splunk = Splunk(initialize_splunk=initialize_splunk)

    def insert(self, dictionary):
        return self.collection.insert_one(dictionary)

    def listen(self):
        cursor = self.collection.find()
        splunk_event_dict = {}
        splunk_dict = {}
        while cursor.alive:
            try:
                doc = cursor.next()
                pprint(doc['message'])
                response_watson = get_watson_response_values(doc['watson_response'])
                #TODO: error_code user_defined yerine entities'den alinabilir case sensitive olmamasi icin
                error_code = response_watson['errorCode'] if 'errorCode' in response_watson.keys() else ''
                merchant_id = response_watson['merchantId'] if 'merchantId' in response_watson.keys() else ''
                if error_code not in splunk_dict.keys():
                    splunk_event_dict = self.Splunk.search(keyword=error_code)
                [print(merchant_id+" matched!") if merchant_id == event['Request']['MerchantId='] and
                                       do_dates_match(doc['datetime'], event['Date'])
                 else '' for event in splunk_event_dict.values()]
                splunk_dict.update({error_code: splunk_event_dict})
                # for entry in splunk_event_dict.values():
                #     merchants_on_splunk.append(tuple([entry['Request']['MerchantId='], do_dates_match(doc['datetime'], entry['Date'])]))
                # pprint(merchants_on_splunk)

                # try:
                #     self.Splunk.compare_merchantIds(error_code, merchant_id)
                # except Exception as e:
                #     print(e)
                #     print(f"No watson_response found.")
                # self.collection.delete_one(doc)
            except StopIteration as e:
                print("STOP ITERATION EXCEPTION:", e)
                time.sleep(2)


if __name__ == '__main__':
    mongo = MongoDB(db_name='WhatsApp', collection_name='messages_capped', initialize_splunk=True)

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
    # TODO: Implement listen method for splunk that fetches new logs
