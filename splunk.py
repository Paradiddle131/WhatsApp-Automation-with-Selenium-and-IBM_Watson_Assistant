import json
import logging.config
import os
import time
from pprint import pprint

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
try:
    import pygetwindow as gw
except NotImplementedError:
    isLinux = True
path_home = os.getcwd()

def get_error_code(response):
    try:
        error_code = response['Response']['Header']['ErrorCode']['dialect']
    except:
        error_code = response['Response']['ResponseCode=']
    logging.info(f"Error code: {error_code} found")
    return error_code


def get_merchantId(response):
    try:
        merchantId = response['Request']['MerchantId=']
    except:
        merchantId = ''
        logging.warning(f"Error finding merchantId", exc_info=True)
    logging.debug(f"MerchantId: {merchantId} found on splunk logs.")
    return merchantId


class Splunk:
    timeout = 10

    def __init__(self, initialize_splunk=True, session=None):
        logging.basicConfig(handlers=[logging.FileHandler(encoding='utf-8', filename='splunk.log')],
                            level=logging.DEBUG,
                            format=u'%(levelname)s - %(name)s - %(asctime)s: %(message)s')
        load_dotenv(os.path.join(os.getcwd(), 'splunk-credentials.env'))
        chrome_options = Options()
        if session:
            chrome_options.add_argument("--user-data-dir={}".format(session))
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.binary_location = os.environ.get('GOOGLE_CHROME_PATH')
            try:
                self.browser = webdriver.Chrome(executable_path=os.environ.get('CHROMEDRIVER_PATH'), chrome_options=chrome_options)
            except:
                if isLinux:
                    os.system("TASKKILL /F /IM chrome.exe")
                else:
                    # if previous session is left open, close it
                    gw.getWindowsWithTitle('Search | Splunk 7.1.0')[0].close()
                    logging.info("Session is already open. \"Home | Splunk 7.1.0\" is closing...")
                    gw.getWindowsWithTitle('New Tab - Google Chrome')[0].close()
                    logging.info("Session is already open. \"New Tab - Google Chrome\" is closing...")
                self.browser = webdriver.Chrome(executable_path=os.environ.get('CHROMEDRIVER_PATH'), chrome_options=chrome_options)
        if initialize_splunk:
            self.browser = webdriver.Chrome()
            self.browser.get(os.getenv('URL'))
            self.browser.maximize_window()
            self.sign_in()

    def sign_in(self):
        try:
            self.browser.find_element_by_xpath('//*[@id="username"]').send_keys(os.getenv('name'))
            self.browser.find_element_by_xpath('//*[@id="password"]').send_keys(os.getenv('password_splunk') + Keys.ENTER)
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

    def compare_merchantIds(self, response_watson):
        error_code, merchantId = ['' for _ in range(2)]
        for entity in response_watson['output']['entities']:
            if entity['entity'] == "HATA_KODLARI":
                error_code = entity['value']
            elif entity['entity'] == "BayiKodu":
                merchantId = entity['text']
        response_splunk = self.search(error_code)
        [logging.debug(f"MerchantId {merchantId} matches with splunk log.")
         if merchantId == get_merchantId(response_splunk[i])
         else logging.debug(f"MerchantId {merchantId} does not match with any splunk log.")
         for i in response_splunk]
        logging.info(f"Error code: {error_code}\nMerchantId: {merchantId}")


if __name__ == '__main__':
    splunk = Splunk(session="splunk-session")
    pprint(splunk.search(os.getenv("query1")))
