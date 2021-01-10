from json import load, loads, dumps
from requests import post


class Bot:

    def __init__(self):
        with open("bot_responses.json", encoding='utf-8') as f:
            self.bot_responses = load(f)
        self.setup()

    def setup(self):
        self.isGreeted = False
        self.levelA = 0
        self.levelB = 0
        self.levelC = 0

    def get_response(self, text):
        if not self.isGreeted:
            self.isGreeted = True
            return self.bot_responses["greet"]
        else:
            if text == "C" or self.levelC > 0:
                if self.levelC == 0:
                    self.levelC += 1
                    return self.bot_responses["C0"]
                elif self.levelC == 1:
                    data = dumps({"node": "PAKET_YUKLENMEMIS", "GSMNo": "5363104196"})
                    response_http = post(url="http://bec0841541f2.ngrok.io/search", json=loads(data), verify=False)
                    print(response_http.json()["response_message"])
                    self.setup()
                    return response_http.json()["response_message"]

