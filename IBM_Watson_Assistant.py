import os
import json
from dotenv import load_dotenv
from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator


class Watson():
    session_id = ''

    def __init__(self):
        load_dotenv(os.path.join(os.getcwd(), 'ibm-credentials.env'))
        self.ASSISTANT_APIKEY = os.getenv('ASSISTANT_APIKEY')
        self.ASSISTANT_IAM_APIKEY = os.getenv('ASSISTANT_IAM_APIKEY')
        self.ASSISTANT_URL = os.getenv('ASSISTANT_URL')
        self.ASSISTANT_AUTH_TYPE = os.getenv('ASSISTANT_AUTH_TYPE')

        load_dotenv(os.path.join(os.getcwd(), 'ibm-assistant.env'))
        self.ASSISTANT_NAME = os.getenv('ASSISTANT_NAME')
        self.ASSISTANT_ID = os.getenv('ASSISTANT_ID')
        self.ASSISTANT_VERSION = os.getenv('ASSISTANT_VERSION')

        self.authenticator = IAMAuthenticator(self.ASSISTANT_IAM_APIKEY)
        self.ASSISTANT = self.create_assistant()
        self.auth()

    def create_assistant(self):
        return AssistantV2(
            version=self.ASSISTANT_VERSION,
            authenticator=self.authenticator
        )

    def auth(self):
        self.ASSISTANT.set_service_url(self.ASSISTANT_URL)

    def create_session(self):
        response = self.ASSISTANT.create_session(
            assistant_id=self.ASSISTANT_ID
        ).get_result()
        # print(json.dumps(response, indent=2))
        self.session_id = response['session-id']

    def delete_session(self):
        return self.ASSISTANT.delete_session(
            assistant_id=self.ASSISTANT_ID,
            session_id=self.session_id
        ).get_result()

    def message_stateless(self, text, doPrint=False):
        print("ERROR HERE:", text)
        response = self.ASSISTANT.message_stateless(
            assistant_id=self.ASSISTANT_ID,
            input={
                'message_type': 'text',
                'text': text
            }
        ).get_result()
        if doPrint:
            self.print_reply_with_intent(response, text)
        return response

    def print_reply_with_intent(self, response, text=''):
        print("------------------------")
        if len(response['output']['intents']) != 0:
            print(f"Response of the text \"{text}\" is below: \n" +
                  "Captured Intent:", response['output']['intents'][0]['intent'], "\n" +
                  "Reply:", response['output']['generic'][0]['text'])
        else:
            print(f"Response for the text: \"{text}\"\n" + response['output']['generic'][0]['text'])


if __name__ == '__main__':
    watson = Watson()
    watson.message_stateless('OKC den fatura alamıyoruz', doPrint=True)
    watson.message_stateless('something', doPrint=True)
