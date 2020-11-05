from flask import Flask, render_template
from os import remove
import time
import random
import whatsapp

app = Flask(__name__)


WhatsApp = whatsapp.WhatsApp(session="mysession")


@app.route('/forever/', methods=['GET'])
def forever():
    last_tag = None
    while True:
        try:
            last_tag = WhatsApp.fetch_messages_continuously(last_tag)
            time.sleep(3)
            print(f"Sleeping for 3 seconds in app.py...")
        except:
            print(f"Problem occured during the forever loop in app.py.")


@app.route("/start")
def serve():
    name = 'Genesis Bot Sandbox'
    WhatsApp.enter_chat_screen(name)
    return 'service started.<br><br>To Stop Click <a href="./stop">here</a><br><br>To start fetching messages,' \
           'Click <a href="./forever">here</a>'


@app.route("/stop")
def stp():
    exit()
    return 'service ended'


@app.route('/')
def index():
    return render_template('index.html', rval=random.randint(11111, 22222))


if __name__ == '__main__':
    app.run(threaded=True, port=5000)
