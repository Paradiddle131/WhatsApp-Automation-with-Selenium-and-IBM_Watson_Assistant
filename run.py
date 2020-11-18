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
    req_data = request.get_json()
    print("JSON:", request.get_json())
    query = f"""sourcetype = GateLogger | search "MerchantId="{req_data['merchant_id']}"" | search "ResponseCode="{req_data['error_code']}"" | where like(Date, "%{req_data['date']}%")"""
    return app.response_class(
        response=dumps({"success": True}) if splunk.search(query) else dumps({"success": False}),
        status=200,
        mimetype='application/json'
    )

if __name__ == "__main__":
    app.run(host="localhost", port=5002, debug=False)
