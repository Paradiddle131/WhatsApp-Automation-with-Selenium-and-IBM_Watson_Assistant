import json
import os
import logging
from base64 import b64encode
import requests


class OCR:
    def __init__(self):
        self.home_dir = os.getcwd()
        with open(os.path.join(self.home_dir, 'vision_api.json')) as f:
            self.api_key = json.load(f)["api_key"]
        self.endpoint_url = 'https://vision.googleapis.com/v1/images:annotate'

    def encode_image(self, image):
        request = {
            'image': {
                'content': b64encode(image).decode()
            },
            'features': [{
                'type': 'DOCUMENT_TEXT_DETECTION',
                'maxResults': 1
            }]
        }
        logging.debug(f"Image encoded before OCR.")
        return json.dumps({"requests": request}).encode()

    def request_ocr(self, image):
        logging.debug(f"Request is preparing for OCR.")
        return requests.post(self.endpoint_url,
                             data=self.encode_image(image),
                             params={'key': self.api_key},
                             headers={'Content-Type': 'application/json'})

    def image_to_text(self, image):
        extracted_text = []
        result = self.request_ocr(image)
        if result.status_code != 200 or result.json().get('error'):
            logging.error(f"Couldn't call the Google Vision API successfully. Result code is: {result.status_code}, "
                          f"result is -> {result}", exc_info=True)
        else:
            try:
                result = result.json()['responses'][0]['textAnnotations']
                [extracted_text.append(result[i]['description']) for i in range(len(result))]
                logging.info(f"Text is extracted from the image successfully.")
                return ' '.join(extracted_text[0].split("\n"))
            except Exception as e:
                logging.warning(f"\"textAnnotations\" couldn't retrieved from the result of Vision API. Result is -> {result}")
                raise Exception(e)


if __name__ == '__main__':
    ocr = OCR()
    # image_path = 'img_to_ocr.png'
    image_path = 'img_to_ocr_2.jpeg'
    # image_path = 'not_ocrable.jpg'
    with open(image_path, 'rb') as f:
        image = f.read()
    print(ocr.image_to_text(image))
