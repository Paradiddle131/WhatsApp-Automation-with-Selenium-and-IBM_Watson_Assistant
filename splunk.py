import json
import logging.config
import os
import time
from pprint import pprint

import pygetwindow as gw
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from splunk_helper import *


class Splunk:
    timeout = 10

    def __init__(self, session=None):
        load_dotenv(os.path.join(os.getcwd(), 'splunk-credentials.env'))
        chrome_options = Options()
        if session:
            chrome_options.add_argument("--user-data-dir={}".format(session))
            try:
                self.browser = webdriver.Chrome(options=chrome_options)
            except:
                # if previous session is left open, close it
                gw.getWindowsWithTitle('Search | Splunk 7.1.0')[0].close()
                logging.info("Session is already open. \"Home | Splunk 7.1.0\" is closing...")
                gw.getWindowsWithTitle('New Tab - Google Chrome')[0].close()
                logging.info("Session is already open. \"New Tab - Google Chrome\" is closing...")
                self.browser = webdriver.Chrome(options=chrome_options)
        else:
            self.browser = webdriver.Chrome()
        self.browser.get(os.getenv('URL'))
        self.browser.maximize_window()
        self.sign_in()

    def sign_in(self):
        try:
            self.browser.find_element_by_xpath('//*[@id="username"]').send_keys(os.getenv('name'))
            self.browser.find_element_by_xpath('//*[@id="password"]').send_keys(os.getenv('password') + Keys.ENTER)
        except NoSuchElementException:
            logging.info("Sign in screen is not loaded.", exc_info=False)
            pass

    def find_wait(self, element_xpath, timeout=timeout, by='xpath'):
        return WebDriverWait(self.browser, timeout=timeout).until(EC.presence_of_element_located(
            (By.XPATH if by.lower() == 'xpath' else By.CLASS_NAME, element_xpath)))

    def search(self, keyword):
        self.find_wait('app-icon-wrapper', by='class_name').click()
        self.find_wait('ace_editor.ace-spl-light', by='class_name').click()
        self.find_wait('icon-chevron-right', by='class_name').click()
        self.find_wait('search-query.text-clear ', by='class_name').send_keys(keyword)
        self.find_wait('search-link', 70, by='class_name').click()
        self.find_wait('search-button', by='class_name').click()
        WebDriverWait(self.browser, 50).until(EC.presence_of_element_located(
            (By.CLASS_NAME, "contrib-jg_lib-display-Element.contrib-jg_lib-graphics-Canvas")))
        soup = BeautifulSoup(self.browser.page_source, "html.parser")
        dict_events = {}
        time.sleep(10)
        tags = soup.find_all("tr", attrs={"class": "shared-eventsviewer-list-body-row"})
        for cnt, tag in enumerate(tags):
            dict_event = {}
            items = tag.find("div", class_="json-tree shared-jsontree") \
                .contents[5].find_all("span", class_="key level-1")
            if '{' == tag.find("span", attrs={"data-path": "RequestMessage"}).text[0]:  # JSON format (Outgoing)
                continue
                # request = json.loads(tag.find("span", attrs={"data-path": "RequestMessage"}).text)
                # response = json.loads(tag.find("span", attrs={"data-path": "ResponseMessage"}).text)
            else:  # Tag format (Incoming)
                request = find_attribute_from_tag(tag.find("span", attrs={"data-path": "RequestMessage"}).text)
                response = find_attribute_from_tag(tag.find("span", attrs={"data-path": "ResponseMessage"}).text)
            for item in items:
                key, value = item.contents[1].text, item.contents[3].text
                if key == 'RequestMessage':
                    dict_event.update(request)
                elif key == 'ResponseMessage':
                    dict_event.update(response)
                else:
                    dict_event.update({key: value})
            dict_events.update({cnt: dict_event})
            logging.debug("Scraped event ->", dict_event)
        return dict_events

    def get_merchantId(self, dict):
        try:
            merchantId = dict['Request']['MerchantId=']
        except:
            merchantId = ''
            logging.warning(f"Error finding merchantId", exc_info=True)
        logging.info(f"MerchantId: {merchantId} found")
        return merchantId

    def get_error_code(self, dict):
        try:
            error_code = dict['Response']['Header']['ErrorCode']['dialect']
        except:
            error_code = dict['Response']['ResponseCode=']
        logging.info(f"Error code: {error_code} found")
        return error_code

    def compare_merchantIds(self, response_watson):
        error_code, merchantId = ['' for _ in range(2)]
        for entity in response_watson['output']['entities']:
            if entity['entity'] == "HATA_KODLARI":
                error_code = entity['value']
            elif entity['entity'] == "BayiKodu":
                merchantId = entity['text']
        response_splunk = self.search(error_code)
        if merchantId == self.get_merchantId(response_splunk):
            logging.debug(f"MerchantIds match.")
        else:
            logging.debug(f"MerchantIds do not match.")
        logging.info(f"Error code: {error_code}\nMerchantId: {merchantId}")


if __name__ == '__main__':
    logging.basicConfig(handlers=[logging.FileHandler(encoding='utf-8', filename='splunk.log', mode='w')],
                        level=logging.DEBUG,
                        format=u'%(levelname)s - %(name)s - %(asctime)s: %(message)s')
    splunk = Splunk(session="splunk-session")
    # splunk.search(os.getenv("query1"))
    splunk.compare_merchantIds(os.getenv("query1"))
    # pprint(splunk.search(os.getenv("query1")))
