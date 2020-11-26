from json import loads
from logging import FileHandler, basicConfig, debug, info, warning, DEBUG
from os import path, getcwd, getenv
from time import sleep

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pyautogui import click, typewrite
from pygetwindow import getWindowsWithTitle
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


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

class Action:
    OKC = "OKC"
    fis_iptal = "fis_iptal"

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

    def search(self, query, action=None):
        try:
            self.browser.find_element_by_class_name('label---pages-enterprise---7-1-0---1Xo01').click()
        except:
            self.find_wait('app-icon-wrapper', by='class_name').click()
        x_search_bar, y_search_bar = list(self.find_wait('ace_editor.ace-spl-light', by='class_name').location.values())
        click(x_search_bar, y_search_bar)
        typewrite(query)
        self.find_wait('search-button', by='class_name').click()
        self.find_wait("contrib-jg_lib-display-Element.contrib-jg_lib-graphics-Canvas", 3, by='class_name')
        sleep(0.5)
        soup = BeautifulSoup(self.browser.page_source, "html.parser")
        tags = soup.find_all("tr", attrs={"class": "shared-eventsviewer-list-body-row"})
        for cnt, tag in enumerate(tags):
            items = tag.find("div", class_="json-tree shared-jsontree") \
                .contents[5].find_all("span", class_="key level-1")
            for item in items:
                if item.contents[1].text == "RequestMessage" or item.contents[1].text == "ResponseMessage":
                    if action == Action.OKC:
                        if query[0] == '9' and \
                            loads(items[5].contents[3].text).popitem()[1]['category'][2]['value'] == 'Accepted' and \
                            loads(items[6].contents[3].text).popitem()[1]['Status'] == 1:
                            return True
                        elif query[0] == '5' and items[4].contents[3].text == '<ReduceBalance>b__0':
                            return True
                else:
                    items = tag.find("div", class_="json-tree shared-jsontree") \
                        .contents[5].find("span", class_="key level-1")
                    return True if len(items) != 0 else False

    def check_okc(self, gsm_no):
        gsm_no_5xx = gsm_no[2:] if gsm_no[0] == '9' else gsm_no
        gsm_no_90x = "90"+gsm_no if gsm_no[0] == '5' else gsm_no
        is_sent_mccm = True if self.search(query=gsm_no_90x, action=Action.OKC) else False
        is_reduced_balance = True if self.search(query=gsm_no_5xx, action=Action.OKC) else False
        if is_sent_mccm and is_reduced_balance:
            print("Mail to MCCM")
        elif is_sent_mccm and not is_reduced_balance:
            print('Check CCB Logs for "ws_log" and "subscriber_option" and contact to IT CIS')
        print("is_sent_mccm:", str(is_sent_mccm), "\nis_reduced_balance:", str(is_reduced_balance))

    def quit(self):
        info("Exiting Splunk...")
        self.browser.quit()