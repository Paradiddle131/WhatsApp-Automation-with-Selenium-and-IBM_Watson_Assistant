from flask import Flask, jsonify, render_template
import time
import random
import datetime
import whatsapp
from threading import Thread

app = Flask(__name__)


class Service(Thread):
    def run(self):
        whatsapp.start()


s1 = Service()
WhatsApp = whatsapp.WhatsApp()


# def print_message_on_web(message):
#     return jsonify(message)


@app.route('/forever/', methods=['GET'])
def forever(message):
    # cur_time = datetime.datetime.fromtimestamp(time.time())
    last_tag = None
    while True:
        try:
            last_tag = WhatsApp.fetch_messages_continuously(last_tag)
            time.sleep(3)
            print(f"Sleeping for 3 seconds in app.py...")
            # print_message_on_web(message)
        except:
            print(f"Problem occured during the forever loop in app.py.")
    # whatsapp.run()
    # print("@@@ cur_time:", cur_time)
    # print("@@@ message:", message)
    # return jsonify({'TIME': f"Time is: {cur_time}",
    #                 'NUMBER': f"Message is: {message}"})


@app.route("/start")
def serve():
    s1.start()
    whatsapp.setup()
    return 'service started.<br><br>To Stop Click <a href="./stop">here</a><br><br>To start fetching messages,' \
           'Click <a href="./forever">here</a>'


@app.route("/stop")
def stp():
    exit()
    return 'service ended'


@app.route('/')
def index():
    # return "<h1>Welcome to WhatsApp Genesis Bot!</h1>"
    return render_template('index.html', rval=random.randint(11111, 22222))


if __name__ == '__main__':
    app.run(threaded=True, port=5000)
