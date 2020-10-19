import json
import os
from base64 import b64encode
import requests


class OCR:
    def __init__(self):
        self.home_dir = os.getcwd()
        with open(os.path.join(self.home_dir, 'vision_api.json')) as f:
            self.api_key = json.load(f)["api_key"]
        self.endpoint_url = 'https://vision.googleapis.com/v1/images:annotate'

    def encode_image(self, image_path):
        with open(image_path, 'rb') as f:
            request = {
                'image': {
                    'content': b64encode(f.read()).decode()
                },
                'features': [{
                    'type': 'DOCUMENT_TEXT_DETECTION',
                    'maxResults': 1
                }]
            }
        return json.dumps({"requests": request}).encode()

    def request_ocr(self, image_path):
        return requests.post(self.endpoint_url,
                             data=self.encode_image(image_path),
                             params={'key': self.api_key},
                             headers={'Content-Type': 'application/json'})

    def image_to_text(self, image_path):
        extracted_text = []
        result = self.request_ocr(image_path)
        if result.status_code != 200 or result.json().get('error'):
            print("ERROR: Couldn't call the Google Vision API successfully.")
        else:
            result = result.json()['responses'][0]['textAnnotations']
            [extracted_text.append(result[i]['description']) for i in range(len(result))]
            return ''.join(extracted_text)


if __name__ == '__main__':
    ocr = OCR()
    # image_path = 'img_to_ocr.png'
    image_path = 'img_to_ocr_2.jpeg'
    # image_path = 'not_ocrable.jpg'
    print(ocr.image_to_text(image_path))
