from flask import Flask, request
from splunk import Splunk
from json import dumps

app = Flask(__name__)


@app.route("/")
def hello():
    return "Welcome to Splunk validation page!"


splunk = Splunk()


@app.route("/search", methods=['POST'])
def search():
    print("Query on /search ->", request.get_json()['query'])
    return dumps({"status": "OK"}) if splunk.search(request.get_json()['query']) else dumps({"status": "Fail"})


if __name__ == "__main__":
    app.run(host="localhost", port=5002, debug=False)
