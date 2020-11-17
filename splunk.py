from logging import FileHandler, basicConfig, debug, info, warning, DEBUG
from os import path, getcwd, getenv
from time import sleep
from pyautogui import click, typewrite
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pygetwindow import getWindowsWithTitle
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from splunk_helper import *


def get_error_code(response):
    try:
        error_code = response['Response']['Header']['ErrorCode']['dialect']
    except:
        error_code = response['Response']['ResponseCode=']
    info(f"Error code: {error_code} found")
    return error_code


def get_merchantId(response):
    try:
        merchantId = response['Request']['MerchantId=']
    except:
        merchantId = ''
        warning(f"Error finding merchantId", exc_info=True)
    debug(f"MerchantId: {merchantId} found on splunk logs.")
    return merchantId


class Splunk:
    timeout = 10

    def __init__(self, initialize_splunk=True, session=None):
        basicConfig(handlers=[FileHandler(encoding='utf-8', filename='splunk.log')],
                            level=DEBUG,
                            format=u'%(levelname)s - %(name)s - %(asctime)s: %(message)s')
        load_dotenv(path.join(getcwd(), 'splunk-credentials.env'))
        chrome_options = Options()
        if session:
            chrome_options.add_argument("--user-data-dir={}".format(session))
            try:
                self.browser = webdriver.Chrome(options=chrome_options)
            except:
                # if previous session is left open, close it
                getWindowsWithTitle('Search | Splunk 7.1.0 - Google Chrome')[0].close()
                info("Session is already open. \"Search | Splunk 7.1.0 - Google Chrome\" is closing...")
                getWindowsWithTitle('New Tab - Google Chrome')[0].close()
                info("Session is already open. \"New Tab - Google Chrome\" is closing...")
                self.browser = webdriver.Chrome(options=chrome_options)
        if initialize_splunk:
            self.browser = webdriver.Chrome()
            self.browser.get(getenv('URL'))
            self.browser.maximize_window()
            self.sign_in()

    def sign_in(self):
        try:
            self.browser.find_element_by_xpath('//*[@id="username"]').send_keys(getenv('name'))
            self.browser.find_element_by_xpath('//*[@id="password"]').send_keys(
                getenv('password_splunk') + Keys.ENTER)
        except NoSuchElementException:
            info("Sign in screen is not loaded.", exc_info=False)
            pass

    def find_wait(self, element_xpath, timeout=timeout, by='xpath'):
        return WebDriverWait(self.browser, timeout=timeout).until(EC.presence_of_element_located(
            (By.XPATH if by.lower() == 'xpath' else By.CLASS_NAME, element_xpath)))

    def search(self, query):
        try:
            self.find_wait('app-icon-wrapper', by='class_name', timeout=3).click()
        except:
            self.find_wait('label---pages-enterprise---7-1-0---1Xo01', by='class_name').click()
        x_search_bar, y_search_bar = list(self.find_wait('ace_editor.ace-spl-light', by='class_name').location.values())
        click(x_search_bar, y_search_bar)
        typewrite(query)
        self.find_wait('search-button', by='class_name').click()
        WebDriverWait(self.browser, 50).until(EC.presence_of_element_located(
            (By.CLASS_NAME, "contrib-jg_lib-display-Element.contrib-jg_lib-graphics-Canvas")))
        sleep(2)
        soup = BeautifulSoup(self.browser.page_source, "html.parser")
        dict_events = {}
        tags = soup.find_all("tr", attrs={"class": "shared-eventsviewer-list-body-row"})
        for cnt, tag in enumerate(tags):
            dict_event = {}
            items = tag.find("div", class_="json-tree shared-jsontree") \
                .contents[5].find_all("span", class_="key level-1")
            if '{' == tag.find("span", attrs={"data-path": "RequestMessage"}).text[0]:  # Outgoing
                continue
            else:  # Incoming
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
            debug(f"Scraped event -> {dict_event}")
        return dict_events
