from logging import debug, info
from os import path, getcwd, getenv

from dotenv import load_dotenv
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import AssistantV2


class Watson():
    session_id = ''

    def __init__(self):
        load_dotenv(path.join(getcwd(), 'ibm-credentials.env'))
        self.ASSISTANT_APIKEY = getenv('ASSISTANT_APIKEY')
        self.ASSISTANT_IAM_APIKEY = getenv('ASSISTANT_IAM_APIKEY')
        self.ASSISTANT_URL = getenv('ASSISTANT_URL')
        self.ASSISTANT_AUTH_TYPE = getenv('ASSISTANT_AUTH_TYPE')

        load_dotenv(path.join(getcwd(), 'ibm-assistant.env'))
        self.ASSISTANT_NAME = getenv('ASSISTANT_NAME')
        self.ASSISTANT_ID = getenv('ASSISTANT_ID')
        self.ASSISTANT_VERSION = getenv('ASSISTANT_VERSION')

        self.authenticator = IAMAuthenticator(self.ASSISTANT_IAM_APIKEY)
        self.ASSISTANT = self.create_assistant()
        info(f"IBM Watson Assistant session is created successfully.")
        self.auth()
        debug(f"IBM Watson Assistant session is authenticated successfully.")

    def create_assistant(self):
        return AssistantV2(
            version=self.ASSISTANT_VERSION,
            authenticator=self.authenticator
        )

    def auth(self):
        self.ASSISTANT.set_service_url(self.ASSISTANT_URL)

    def message_stateless(self, text, doPrint=False):
        response = self.ASSISTANT.message_stateless(
            assistant_id=self.ASSISTANT_ID,
            input={
                'message_type': 'text',
                'text': text
            }
        ).get_result()
        debug(f"Response from IBM Watson -> {response}")
        try:
            if (len(response['output']['intents']) == 0 and
                len(response['output']['entities']) == 0 and
                len(response['output']['generic']) == 0) or \
                    response['output']['generic'][0]['response_type'] == 'suggestion' or \
                    'Çözüldü' in [entity['entity'] for entity in response['output']['entities']]:
                info(f"Nothing captured from text {text}.")
                return ''
        except:
            pass
        if doPrint:
            self.print_reply_with_intent(response, text)
        entities = response['output']['entities']
        [response['output']['entities'][i].update(
            {'text': text[entity['location'][0]-1: entity['location'][1]-1]}) for i, entity in enumerate(entities)]
        return response

    def print_reply_with_intent(self, response, text=''):
        print(f"== {text}")
        bot_reply = []
        assistant_reply = ''
        intents = response['output']['intents']
        entities = response['output']['entities']
        if len(intents) != 0:
            bot_reply.append("Captured Intent: " + intents[0]['intent'] + "\n")
        if len(entities) != 0:
            for entity in entities:
                debug(f"Entity found on location: {entity['location']}")
                bot_reply.append("Captured Entity: " + entity['entity'] + " -> " + text[entity['location'][0]-1:entity['location'][1]] + "\n")
        bot_reply.append("Reply: " + assistant_reply) if assistant_reply is not '' else None
        debug(f"Bot reply is -> {bot_reply}")
        print(''.join(bot_reply))
