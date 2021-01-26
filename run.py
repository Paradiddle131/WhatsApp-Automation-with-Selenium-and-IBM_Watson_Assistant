import enum
from json import dumps
from logging import basicConfig, FileHandler, DEBUG
from os import path, chdir
from threading import Thread
from time import sleep

from flask import Flask, request

app = Flask(__name__)


@app.route("/")
def hello():
    return "Welcome to Splunk validation page!"


class Nodes(enum.Enum):
    OKC = "OKC"
    WAIT = "WAIT"
    FATURA_ALAMADIM = "FATURA_ALAMADIM"
    PAKET_YUKLENMEMIS = "PAKET_YUKLENMEMIS"


@app.route("/search", methods=['POST'])
def search():
    response_message = ""
    req_data = request.get_json()
    success = False
    node = Nodes(req_data["node"]) if "node" in req_data.keys() else None
    print("JSON:", request.get_json())
    if node == Nodes.FATURA_ALAMADIM:
        query = f"""sourcetype = GateLogger | search "MerchantId="{req_data['merchant_id']}"" | search "ResponseCode="{req_data['error_code']}"" | where like(Date, "%{req_data['date']}%")"""
        success = True if splunk.search(query) else False
        response_message = f"*\"{req_data['merchant_id']}\"* Bayi kodu ve *\"{req_data['error_code']}\"* hata kodu ile *\"FMXXXXXXXX\"* max kaydı oluşturuldu."
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
            response_message = splunk.search(req_data["GSMNo"])
            success = True if response_message else False
    elif node == Nodes.PAKET_YUKLENMEMIS:
        response_message = splunk.check_package_not_loaded(req_data["GSMNo"])
        print(response_message)
        success = True if response_message else False
    return app.response_class(
        response=dumps({"response_message": response_message}),
        status=200 if success else 404,
        mimetype='application/json'
    )


def run_server():
    app.run(host="localhost", port=5002, debug=False)


if __name__ == "__main__":
    chdir(path.dirname(__file__))
    basicConfig(handlers=[FileHandler(encoding='utf-8', filename='whatsapp.log', mode='w')],
                level=DEBUG, format=u'%(levelname)s - %(name)s - %(asctime)s: %(message)s')
    from whatsapp import WhatsApp
    from splunk import Splunk

    whatsapp = WhatsApp(session="mysession")
    splunk = Splunk()
    t1 = Thread(target=whatsapp.run_bot)
    t2 = Thread(target=run_server)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
