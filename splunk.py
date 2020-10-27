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


class Splunk:
    timeout = 10

    def __init__(self, session=None):
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
        self.browser.get('http://10.86.71.216:8000')
        self.browser.maximize_window()
        self.sign_in()

    def sign_in(self):
        try:
            load_dotenv(os.path.join(os.getcwd(), 'splunk-credentials.env'))
            self.browser.find_element_by_xpath('//*[@id="username"]').send_keys(os.getenv('name'))
            self.browser.find_element_by_xpath('//*[@id="password"]').send_keys(os.getenv('password') + Keys.ENTER)
        except NoSuchElementException:
            logging.warning("Sign in screen is not loaded.", exc_info=False)
            pass

    def find_wait(self, element_xpath, timeout=timeout, by='xpath'):
        return WebDriverWait(self.browser, timeout=timeout).until(EC.presence_of_element_located(
            (By.XPATH if by.lower() == 'xpath' else By.CLASS_NAME, element_xpath)))

    def search(self, keyword):
        self.find_wait('app-icon-wrapper', by='class_name').click()
        self.find_wait('ace_editor.ace-spl-light', by='class_name').click()
        self.find_wait('icon-chevron-right', by='class_name').click()
        self.find_wait('search-query.text-clear ', by='class_name').send_keys(keyword)
        self.find_wait('search-link', 50, by='class_name').click()
        self.find_wait('search-button', by='class_name').click()

        WebDriverWait(self.browser, 50).until(EC.presence_of_element_located(
            (By.CLASS_NAME, "contrib-jg_lib-display-Element.contrib-jg_lib-graphics-Canvas")))
        soup = BeautifulSoup(self.browser.page_source, "html.parser")
        tags = soup.find_all("tbody", attrs={"class": "shared-eventsviewer-list-body"})
        cnt = 0
        dict_events = {}
        time.sleep(10)
        for tag in tags:
            logging.debug(f"Tag is scraped: {tag}")
            dict_event = {}
            items = tag.find("div", class_="json-tree shared-jsontree").contents[5].find_all("span",
                                                                                             class_="key level-1")
            for item in items:
                request = json.loads(tag.find("span", attrs={"data-path": "RequestMessage"}).text)
                response = json.loads(tag.find("span", attrs={"data-path": "ResponseMessage"}).text)
                key, value = item.contents[1].text, item.contents[3].text
                logging.debug(f"Key-value pair found for event: {cnt} as: "+"{"+key+":"+" "+value+"}")
                if key == 'RequestMessage':
                    dict_event.update(request)
                elif key == 'ResponseMessage':
                    dict_event.update(response)
                else:
                    dict_event.update({key: value})
            dict_events.update({cnt: dict_event})
            pprint(dict_events)
        # TODO: scroll down to fetch new elements


if __name__ == '__main__':
    logging.basicConfig(handlers=[logging.FileHandler(encoding='utf-8', filename='splunk.log')],
                        level=logging.DEBUG,
                        format=u'%(levelname)s - %(name)s - %(asctime)s: %(message)s')
    splunk = Splunk(session="splunk-session")
    splunk.search("ekos_40")
