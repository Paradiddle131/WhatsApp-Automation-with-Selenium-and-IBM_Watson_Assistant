from json import loads
from logging import FileHandler, basicConfig, debug, info, warning, DEBUG, error
from os import path, getcwd, getenv
from time import sleep
from datetime import datetime

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
from ccb_connect import CCB, TABLE_NAME


date_splunk = None

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
    FATURA_ALAMADIM = "FATURA_ALAMADIM"
    PAKET_YUKLENMEMIS ="PAKET_YUKLENMEMIS"

class Splunk:
    timeout = 10
    isBalanceReduced, isKolayPackage = [False for _ in range(2)]
    date_splunk = None
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
        self.ccb = CCB()

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
        sleep(2.5)
        soup = BeautifulSoup(self.browser.page_source, "html.parser")
        tags = soup.find_all("tr", attrs={"class": "shared-eventsviewer-list-body-row"})
        for cnt, tag in enumerate(tags):
            try:
                items = tag.find("div", class_="json-tree shared-jsontree") \
                    .contents[5].find_all("span", class_="key level-1")
                if action == Action.OKC:
                    if query[0] == '9' and \
                        loads(items[5].contents[3].text).popitem()[1]['category'][2]['value'] == 'Accepted' and \
                        loads(items[6].contents[3].text).popitem()[1]['Status'] == 1:
                        return True
                    elif query[0] == '5' and items[4].contents[3].text == '<ReduceBalance>b__0':
                        # MethodName: <AddKolayPackage>b__0 bunu da kontrol et
                        return True
                    else:
                        return False
                elif action == Action.PAKET_YUKLENMEMIS:
                    if query[0] == '5':
                        self.date_splunk = items[0].contents[3].text
                        if items[4].contents[3].text == '<ReduceBalance>b__0':
                            self.isBalanceReduced = True
                        elif items[4].contents[3].text == '<AddKolayPackage>b__0':
                            self.isKolayPackage = True
                    else:
                        #Anything to do here?
                        pass
                else:
                    items = tag.find("div", class_="json-tree shared-jsontree") \
                        .contents[5].find("span", class_="key level-1")
                    return True if len(items) != 0 else False
            except:
                print("No information found on tag.")
                pass

    def check_okc(self, gsm_no):
        gsm_no_90x = "90"+gsm_no if gsm_no[0] == '5' else gsm_no
        gsm_no_5xx = gsm_no[2:] if gsm_no[0] == '9' else gsm_no
        is_sent_mccm = True if self.search(query=gsm_no_90x, action=Action.OKC) else False
        is_reduced_balance = True if self.search(query=gsm_no_5xx, action=Action.OKC) else False
        if is_sent_mccm and is_reduced_balance:
            # MCCM tarafi bilgilendirilir, mail atilacak, baska bizlik aksiyon yok
            print("Mail to MCCM")
        elif not is_reduced_balance:
            # bot says -> bayi bakjiyesinden dusum gerceklestirilmemistir. abone islemi tekrar deneyebilir
            print('Check CCB Logs for "ws_log" and "subscriber_option" and contact to IT CIS')
            # check_ccb()
        print("is_sent_mccm:", str(is_sent_mccm), "\nis_reduced_balance:", str(is_reduced_balance))
        return True

    def check_package_not_loaded(self, gsm_no):
        try:
            self.search(query=gsm_no, action=Action.PAKET_YUKLENMEMIS)
            if self.isBalanceReduced and self.isKolayPackage:
                ccb_response = self.ccb.check_ccb(gsm_no, TABLE_NAME.SUBSCRIBER_OPTION)
                date_splunk = datetime.strptime(self.date_splunk[:-4], "%m/%d/%Y %H:%M:%S")
                if ccb_response:
                    time_difference = (ccb_response["sw_date"] - date_splunk).seconds
                    if ccb_response["cr_user"] == "OKC" and time_difference <= 180:
                        print(ccb_response["option_status"])
                        date_converted = ccb_response['sw_date'].strftime('%d/%m/%Y %H:%M:%S')
                        if ccb_response["option_status"] == "S":
                            return f"Paketiniz *{date_converted}* tarihinde başarıyla yüklenmiştir."
                        elif ccb_response["option_status"] == "F":
                            print("mail -> IT CIS SSPM OPS")
                            print(f"{gsm_no} GSM numarasi {date_converted} tarihinde islem yapmistir. Paket icerigi yuklenmemis gorunuyor. Kontrol edebilir misiniz?")
                            return f"Paket yükleme sırasında oluşan hata ilgili ekibe (IM) iletilmiştir. Son durumdan haberdar edileceksiniz. Beklediğiniz için teşekkürler."
                        elif not ccb_response["option_status"] and not ccb_response['exp_date']:
                            print("mail -> IT CIS SSPM OPS")
                            print(f"{gsm_no} GSM numarasi {date_converted} tarihinde islem yapmistir. CCB'de exp_date atılmamış ve option_status boş görünüyor, paket yüklenmemiş. Kontrol edebilir misiniz?")
                            return f"İlgili ekip (IM) bilgilendirilmiştir. Son durumdan haberdar edileceksiniz. Beklediğiniz için teşekkürler."
                else:
                    ccb_response = self.ccb.check_ccb(gsm_no, TABLE_NAME.WS_LOG)
                    time_difference = (ccb_response["cr_date"] - date_splunk).seconds
                    if time_difference <= 180:
                        print("mail -> IT CIS SSPM OPS")
                        return f"İlgili ekip (IT CIS SSPM OPS) bilgilendirilmiştir. Son durumdan haberdar edileceksiniz. Beklediğiniz için teşekkürler."
            elif not self.isBalanceReduced and not self.isKolayPackage:
                print("mail -> IT CIS SSPM OPS")
                return f"İlgili ekip (IT CIS SSPM OPS) bilgilendirilmiştir. Son durumdan haberdar edileceksiniz. Beklediğiniz için teşekkürler."
            elif self.isBalanceReduced and not self.isKolayPackage:
                print("Disk capacity may be full on OKC (very unlikely)")
                return f"İlgili ekip (IT CIS SSPM OPS) bilgilendirilmiştir. Son durumdan haberdar edileceksiniz. Beklediğiniz için teşekkürler."
            else:
                print("Unexpected error occurred.")
                return f"Beklenmedik bir hata oluştu. Lütfen bilgileri kontrol edip daha sonra tekrar deneyiniz."
            return True
        except:
            error("Error:", exc_info=True)
            return f"Beklenmedik bir hata oluştu. Lütfen bilgileri kontrol edip daha sonra tekrar deneyiniz."

    # def check_ccb(self):


    def quit(self):
        info("Exiting Splunk...")
        self.browser.quit()


if __name__ == '__main__':
    splunk = Splunk()
    # splunk.search(query="905537935687", action=Action.PAKET_YUKLENMEMIS)  # 90'li cikiyor
    splunk.check_package_not_loaded("5363104196")
