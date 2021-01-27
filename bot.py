from json import load
from logging import debug

from whatsapp import BotActions, Nodes


class Bot:

    def __init__(self, splunk=None):
        if splunk:
            self.splunk = splunk
        with open("bot_responses.json", encoding='utf-8') as f:
            self.bot_responses = load(f)

    def get_response(self, text, dialog, name):
        chat_data = dialog.tree[name]
        if chat_data["action"] == BotActions.GREET:
            dialog.set_data(name, {"action": ""})
            return self.bot_responses["greet"]
        elif chat_data["action"] == BotActions.MENU:
            dialog.set_data(name, {"action": ""})
            return self.bot_responses["menu"]
        else:
            # TODO: intent i yakalayip if yerine intent koy "A" check etmek yerine
            if not chat_data["node"]:
                if text == "a":  # Fatura Alamadim
                    dialog.set_data(name, {"node": Nodes.FATURA_ALAMADIM, "level": 1})
                    return self.bot_responses["A0"]
                elif text == "c":  # Paket Yuklenmemis
                    dialog.set_data(name, {"node": Nodes.PAKET_YUKLENMEMIS, "level": 1})
                    return self.bot_responses["C0"]
            elif chat_data["node"] == Nodes.FATURA_ALAMADIM:
                if chat_data["level"] == 1:
                    query = f"""sourcetype = GateLogger | search "MerchantId="{chat_data["data"]["merchant_id"]}"" | search "ResponseCode="{chat_data["data"]["error_code"]}"" | where like(Date, "%{chat_data["data"]["date"]}%")"""
                    success = self.splunk.search(query)
                    # TODO: Implement success logic
                    return f"""*"{chat_data["data"]["merchant_id"]}"* Bayi kodu ve *"{chat_data["data"]["error_code"]}"* hata kodu ile *"FMXXXXXXXX"* max kaydı oluşturuldu."""
            elif chat_data["node"] == Nodes.PAKET_YUKLENMEMIS:
                if chat_data["level"] == 1:
                    # TODO: chcek gsmno regex
                    response = self.splunk.check_package_not_loaded(text)
                    debug(f"Response from splunk search is -> {response}")
                    dialog.setup(name)
                    return response
