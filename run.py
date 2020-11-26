from flask import Flask, request
from splunk import Splunk
from json import dumps
from time import sleep
import enum

app = Flask(__name__)


@app.route("/")
def hello():
    return "Welcome to Splunk validation page!"


splunk = Splunk()


class Nodes(enum.Enum):
    OKC = "OKC"
    WAIT = "WAIT"
    FATURA_ALAMADIM = "FATURA_ALAMADIM"


@app.route("/search", methods=['POST'])
def search():
    req_data = request.get_json()
    success = False
    node = Nodes(req_data["node"]) if "node" in req_data.keys() else None
    print("JSON:", request.get_json())
    if node == Nodes.FATURA_ALAMADIM:
            query = f"""sourcetype = GateLogger | search "MerchantId="{req_data['merchant_id']}"" | search "ResponseCode="{req_data['error_code']}"" | where like(Date, "%{req_data['date']}%")"""
            success = True if splunk.search(query) else False
    elif node == Nodes.WAIT:
        print(req_data['wait'])
        if req_data['wait']:
            print("Sleeping for ten seconds...")
            sleep(10)
            print("Slept.")
        else:
            print("won't sleep because it passed false.")
        success = True
    elif node == Nodes.OKC:
        if "GSMNo" in req_data.keys():
            success = True if splunk.check_okc(req_data["GSMNo"]) else False

    return app.response_class(
        response=dumps({"success": success}),
        status=200 if success else 404,
        mimetype='application/json'
    )


if __name__ == "__main__":
    app.run(host="localhost", port=5002, debug=False)
