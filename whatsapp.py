import base64
import datetime as dt
import logging.config
import sys
import time
import argparse
from io import BytesIO
from pprint import pprint

import pandas as pd
from PIL import Image
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from IBM_Watson_Assistant import Watson
from OCR import *
from mongodb import MongoDB
from whatsapp_helper import *

try:
    import pygetwindow as gw
except NotImplementedError:
    isLinux = True
try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:
    print(
        "Beautiful Soup Library is reqired to make this library work(For getting participants list for the specified group).\npip3 install beautifulsoup4")

RELOAD_TIMEOUT = 10
ERROR_TIMEOUT = 5
non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)
time_format = '%I:%M %p'
path_home = os.getcwd()
cnt = 0


class WhatsApp:
    emoji = {}  # This dict will contain all emojies needed for chatting
    browser = None
    timeout = 10  # The timeout is set for about ten seconds

    # This constructor will load all the emojies present in the json file and it will initialize the webdriver
    def __init__(self, initialize_whatsapp=True, wait=100, screenshot=None, session=None):
        chrome_options = Options()
        if session:
            chrome_options.add_argument("--user-data-dir={}".format(session))
            try:
                self.browser = webdriver.Chrome(os.path.join(path_home, 'chromedriver.exe'), options=chrome_options)
            except:
                if isLinux:
                    os.system("TASKKILL /F /IM chrome.exe")
                else:
                    # if previous session is left open, close it
                    gw.getWindowsWithTitle('WhatsApp - Google Chrome')[0].close()
                    logging.info("Session is already open. \"WhatsApp - Google Chrome\" is closing...")
                    gw.getWindowsWithTitle('New Tab - Google Chrome')[0].close()
                    logging.info("Session is already open. \"New Tab - Google Chrome\" is closing...")
                self.browser = webdriver.Chrome(os.path.join(path_home, 'chromedriver.exe'), options=chrome_options)
        else:
            self.browser = webdriver.Chrome()
            logging.info("Chrome Driver is initialized successfully.")
        if initialize_whatsapp:
            self.browser.get("https://web.whatsapp.com/")
            logging.info("WhatsApp Web Client is opening...")
            # emoji.json is a json file which contains all the emojis
            with open("emoji.json") as emojies:
                self.emoji = json.load(emojies)  # This will load the emojies present in the json file into the dict
            WebDriverWait(self.browser, wait).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, '._3FRCZ')))
            if screenshot is not None:
                self.browser.save_screenshot(screenshot)  # This will save the screenshot to the specified file location
            # CSS SELECTORS AND XPATHS
            self.search_selector = ".cBxw- > div:nth-child(2)"
            self.browser.maximize_window()
            self.OCR = OCR()
            self.Watson = Watson()
            self.Mongo = MongoDB(db_name='WhatsApp', collection_name='messages', initialize_splunk=False)
            self.participants_list_path = os.path.join(path_home, 'participants_list.csv')

    def get_driver(self):
        return self.browser

    # This method is used to emojify all the text emoji's present in the message
    def emojify(self, message):
        for emoji in self.emoji:
            message = message.replace(emoji, self.emoji[emoji])
        return message

    def find_wait(self, element_xpath, by='xpath'):
        return WebDriverWait(self.browser, self.timeout).until(EC.presence_of_element_located(
            (By.XPATH if by.lower() == 'xpath' else By.CSS_SELECTOR, element_xpath)))

    def send_message(self, name, message):
        message = self.emojify(message)  # this will emojify all the emoji which is present as the text in string
        self.enter_chat_screen(name)
        try:
            send_msg = WebDriverWait(self.browser, self.timeout).until(EC.presence_of_element_located(
                (By.XPATH, "/html/body/div/div/div/div[4]/div/footer/div[1]/div[2]/div/div[2]")))
            messages = message.split("\n")
            for msg in messages:
                send_msg.send_keys(msg)
                send_msg.send_keys(Keys.SHIFT + Keys.ENTER)
                logging.info(f"Message \"{msg}\" is sent to \"{name}\"")
            send_msg.send_keys(Keys.ENTER)
            return True
        except TimeoutException:
            logging.error("Exception occurred", exc_info=True)
            raise TimeoutError("Your request has been timed out! Try overriding timeout!")
        except NoSuchElementException:
            logging.error("Exception occurred", exc_info=True)
            return False
        except Exception:
            logging.error("Exception occurred", exc_info=True)
            return False

    def participants_count_for_group(self, group_name):
        header_class_name = "_1iFv8"
        self.enter_chat_screen(group_name)
        try:
            click_menu = WebDriverWait(self.browser, self.timeout).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, f".{header_class_name}")))
            click_menu.click()
        except TimeoutException:
            logging.error("Exception occurred", exc_info=True)
            raise TimeoutError("Your request has been timed out! Try overriding timeout!")
        except NoSuchElementException as e:
            logging.error("Exception occurred", exc_info=True)
            return "None"
        except Exception as e:
            logging.error("Exception occurred", exc_info=True)
            return "None"
        current_time = dt.datetime.now()
        participants_class = "_2y8MV"
        participants_selector = f"span.{participants_class}"
        time.sleep(5)
        try:
            list_participants_count = self.browser.find_elements_by_css_selector(participants_selector)
            logging.info("There are", list_participants_count[2].text, "participants in group", group_name)
            return list_participants_count[2].text
        except Exception as e:
            logging.error("Exception occurred", exc_info=True)
            pass
        new_time = dt.datetime.now()
        elapsed_time = (new_time - current_time).seconds
        if elapsed_time > self.timeout:
            logging.warning(f"Timeout reached. {elapsed_time}/{self.timeout}")
            return "NONE"

    def get_group_participants(self, group_name):
        header_class_name = "_1iFv8"
        participants_count = int(self.participants_count_for_group(group_name).split()[0])
        try:
            click_menu = self.find_wait('.' + header_class_name, 'css')
            click_menu.click()
        except TimeoutException:
            logging.error("Exception occurred", exc_info=True)
            raise TimeoutError("Your request has been timed out! Try overriding timeout!")
        except NoSuchElementException as e:
            logging.error("Exception occurred", exc_info=True)
            return "None"
        except Exception as e:
            logging.error("Exception occurred", exc_info=True)
            return "None"
        list_participants = []

        # Click on "X more" button to load the whole participants
        more_element = self.browser.find_element_by_xpath(
            '//*[@id="app"]/div/div/div[2]/div[3]/span/div/span/div/div/div[1]/div[5]/div[3]/div[2]/div/div')
        more_element.click()

        participants_element, participants_xpath = self.find_classless_element(
            '//*[@id="app"]/div/div/div[2]/div[3]/span/div/span/div/div/div[1]/div[5]', '/div')
        scrollbar = self.browser.find_element_by_css_selector(
            "#app > div > div > div.YD4Yw > div._1-iDe._14VS3 >span > div > span > div > div")
        # Scroll through the participants list
        v = 0
        while len(list_participants) != participants_count:
            self.browser.execute_script('arguments[0].scrollTop = ' + str(v * 300), scrollbar)
            time.sleep(0.10)
            try:
                html = participants_element.get_attribute('innerHTML')
                soup = BeautifulSoup(html, "html.parser")
                for i in soup.find_all(lambda tag: tag.name == 'span' and
                                                   tag.get('dir') == 'auto' and
                                                   '_5h6Y_' in tag.get('class')):
                    if i.text not in list_participants:
                        list_participants.append(i.text)
                v += 1
            except Exception as e:
                logging.error("Exception occurred", exc_info=True)
                pass
        return list_participants

    def find_classless_element(self, xpath, suffix=''):
        """Returns WebElement and xPath of the WebElement.
        Used when only the classless div is the required element."""
        i = 0
        while True:
            try:
                i += 1
                element_xpath = f'{xpath}/div[{i}]'
                element = self.browser.find_element_by_xpath(element_xpath)
                if element.get_attribute('class') == "":
                    return self.browser.find_element_by_xpath(element_xpath + suffix), element_xpath + suffix
                continue
            except:
                logging.warning(f"Element couldn't be found from xpath: {xpath}.", exc_info=True)
                break

    def scroll_up_panel(self, scroll_times=20, element=None):
        if not element:
            element = self.browser.find_element_by_xpath('//*[@id="main"]/div[3]/div/div/div[3]')
        for i in range(scroll_times):
            time.sleep(0.2)
            element.send_keys(Keys.ARROW_UP)
        time.sleep(3)
        logging.info(f"Scrolled up for {scroll_times} times.")

    # extracts blob content as bytes
    def get_file_content_chrome(self, uri):
        result = self.browser.execute_async_script("""
        var uri = arguments[0];
        var callback = arguments[1];
        var toBase64 = function(buffer){for(var r,n=new Uint8Array(buffer),t=n.length,a=new Uint8Array(4*Math.ceil(t/3)),i=new Uint8Array(64),o=0,c=0;64>c;++c)i[c]="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/".charCodeAt(c);for(c=0;t-t%3>c;c+=3,o+=4)r=n[c]<<16|n[c+1]<<8|n[c+2],a[o]=i[r>>18],a[o+1]=i[r>>12&63],a[o+2]=i[r>>6&63],a[o+3]=i[63&r];return t%3===1?(r=n[t-1],a[o]=i[r>>2],a[o+1]=i[r<<4&63],a[o+2]=61,a[o+3]=61):t%3===2&&(r=(n[t-2]<<8)+n[t-1],a[o]=i[r>>10],a[o+1]=i[r>>4&63],a[o+2]=i[r<<2&63],a[o+3]=61),new TextDecoder("ascii").decode(a)};
        var xhr = new XMLHttpRequest();
        xhr.responseType = 'arraybuffer';
        xhr.onload = function(){ callback(toBase64(xhr.response)) };
        xhr.onerror = function(){ callback(xhr.status) };
        xhr.open('GET', uri);
        xhr.send();
        """, uri)
        if type(result) == int:
            logging.error(f"Couldn't get element from blob content on Chrome. Uri is: {uri}", exc_info=True)
            raise Exception("Request failed with status %s" % result)
        return base64.b64decode(result)

    def bytes_to_image(self, bytes, image_name=None):
        try:
            stream = BytesIO(bytes)
            image = Image.open(stream).convert("RGBA")
            stream.close()
            if image_name:
                image.save(f'output/image_{image_name}.png')
            return image
        except:
            logging.error(f"Bytes couldn't converted into an image. Bytes: {bytes}", exc_info=True)
            return None

    def is_trouble_shooter(self, GSM):
        try:
            GSM = GSM.split('+')[1] if '+' in GSM else GSM
            df = pd.read_csv(self.participants_list_path)
            return GSM in df['Trouble_shooters'].values
        except:
            logging.error(f"Error occurred during the Pandas DataFrame actions.", exc_info=True)
            return None

    def get_last_messages(self, name):
        dict_messages = {}
        self.enter_chat_screen(name)
        # time.sleep(3)
        self.scroll_up_panel(30)
        soup = BeautifulSoup(self.browser.page_source, "html.parser")
        cnt = 0
        message_text, message_sender = ['' for _ in range(2)]
        for tag in soup.find_all("div", class_="message-in"):
            logging.debug(f"Tag is scraped: {tag}")
            new_sender = False
            # message_time, location = [None for _ in range(2)]
            message_quote_sender, message_quote_text = [None for _ in range(2)]
            message = tag.find("span", class_="selectable-text")
            if do_contains_sender(str(tag)):
                new_sender = True
                message_text = ''
                sender = tag.find("div", class_=find_sender(str(tag)))
                if sender:
                    sender2 = sender.find('span')
                    if sender2:
                        message_sender = sender2.text
                        if self.is_trouble_shooter(message_sender):
                            logging.debug(
                                f"GSM No: {message_sender} is classified as \"trouble shooter\". Skipping this message.")
                            continue
                        logging.debug(f"GSM No: {message_sender} is classified as \"crew member\".")
            if do_contains_quote(str(tag)):
                quote = tag.find("span", class_=find_quote(str(tag)))
                if quote:
                    message_quote_text = quote.text
                    quote_sender = quote.parent.previous_sibling
                    if quote_sender:
                        quote_sender2 = quote_sender.find('span')
                        if quote_sender2:
                            message_quote_sender = quote_sender2.text
                        logging.debug(f"Quote Sender: \"{message_quote_sender}\"")
            if message:
                message2 = message.find("span")
                if message2:
                    message_text = message_text + " | " + message2.text.replace("\n",
                                                                                ' ') if message_text != '' else message2.text.replace(
                        "\n", ' ')
                    logging.debug(f"Message: \"{message_text}\"")
                    # location = self.browser.page_source.find(message2.text)
            if do_contains_image(str(tag)) \
                    and not do_contains_audio(str(tag)) \
                    and not do_contains_quoted_image(str(tag)):
                image_link = find_image(str(tag))
                image_bytes = self.get_file_content_chrome(image_link)
                # self.bytes_to_image(image_bytes, cnt)  # Save the image on output folder
                message_text = message_text + " || " + self.OCR.image_to_text(image_bytes).replace("\n", ' ')
                logging.debug(f"Message from the text: \"{message_text.split('||')[1]}\"")
            message_time = time.strptime(find_time(tag.text), time_format)
            logging.debug(f"Message time is captured as: \"{message_time}\"")
            # message_time = find_time(tag.text)
            if message_text is not '':
                if new_sender:
                    logging.debug(f"Consecutive messages from the same sender is detected.")
                    cnt += 1
                # TODO: Separate ocr_captured from message_text?
                dict_messages.update(
                    {cnt:
                         {'sender': message_sender,
                          'message': message_text,
                          'time': message_time,
                          'quote': {'sender': message_quote_sender,
                                    'message': message_quote_text}
                          }})
        logging.info(f"Message object(s) successfully captured.")
        return dict_messages

    def get_ocr_from_tag(self, tag, message_text, save=False):
        global cnt
        if do_contains_image(str(tag)) \
                and not do_contains_audio(str(tag)) \
                and not do_contains_quoted_image(str(tag)):
            image_link = find_image(str(tag))
            image_bytes = self.get_file_content_chrome(image_link)
            if save:
                self.bytes_to_image(image_bytes, cnt)  # Save the image on output folder
            message_text = message_text + " || " + self.OCR.image_to_text(image_bytes).replace("\n", ' ')
            logging.debug(f"Message from the text: \"{message_text.split('||')[1]}\"")
        return message_text

    def get_sender_from_messageId(self, messageId):
        message_sender = find_phone_number(messageId)
        if self.is_trouble_shooter(message_sender):
            logging.debug(
                f"GSM No: {message_sender} is classified as \"trouble shooter\". Skipping this message.")
            return None
        logging.debug(f"GSM No: {message_sender} is classified as \"crew member\".")
        return message_sender

    def get_time_from_tag(self, tag):
        return time.strptime(find_time(tag.text), time_format)

    def get_quote_from_tag(self, tag):
        message_quote_sender, message_quote_text = ['' for _ in range(2)]
        if do_contains_quote(str(tag)):
            quote = tag.find("span", class_=find_quote(str(tag)))
            if quote:
                message_quote_text = quote.text.replace("\n", ' ')
                message_quote_sender = quote.parent.previous_sibling.find('span').text
                logging.debug(f"Quote Sender: \"{message_quote_sender}\"")
        return message_quote_sender, message_quote_text

    def check_new_message(self, name, run_forever=True):
        global cnt
        self.enter_chat_screen(name)
        time.sleep(4)
        message_text, message_sender, message_datetime, message_time, message_info = ['' for _ in range(5)]
        last_tag = None
        dict_messages = {}
        while True:
            try:
                soup = BeautifulSoup(self.browser.page_source, "html.parser")
                tag = soup.find_all("div", class_="message-out")[-1]
                message_id = tag.attrs["data-id"]
                message_sender = self.get_sender_from_messageId(message_id)
                if message_sender is None:
                    continue
                tag_text = tag.find_all("div", class_="copyable-text")
                if tag != last_tag:
                    logging.debug(f"New message received at: {time.time()}")
                    last_tag = tag
                    if tag_text:
                        tag_text = tag_text[-1]
                        message_info = tag_text.attrs["data-pre-plain-text"]
                        message_datetime = str_to_datetime(find_date(message_info) + ' ' + find_time(message_info))
                        message_text = tag_text.find("span", class_="selectable-text").find("span").text.replace("\n", ' ')
                    else:
                        message_datetime = self.get_time_from_tag(tag)
                    logging.debug(f"Message: \"{message_text}\"")
                    message_quote_sender, message_quote_text = self.get_quote_from_tag(tag)
                    message_text = self.get_ocr_from_tag(tag, message_text)
                    watson_response = self.Watson.message_stateless(message_text, doPrint=True)
                    dict_messages.update(
                        {"_id": message_id,
                         'sender': message_sender,
                         'message': message_text,
                         'datetime': message_datetime,
                         'quote': {'sender': message_quote_sender,
                                   'message': message_quote_text},
                         'watson_response': watson_response
                         })
                    logging.debug("Final Message Dictionary ->", dict_messages)
                    # pprint(dict_messages)
                    try:
                        self.Mongo.insert(dict_messages)
                    except:
                        logging.warning(f"Tried to insert into mongo but error occured.", exc_info=True)
                    if not run_forever:
                        logging.info("breaking due to lac of passed argument: run_forever")
                        print("breaking due to lac of passed argument: run_forever")
                        break
                else:
                    print("Sleeping for 3 seconds...")
                    time.sleep(3)
                    logging.info("Slept for 3 seconds since there is no new message.")
            except:
                logging.error(f"Some problem has occured.", exc_info=True)
                print("Something wrong happened during the loop.")
                break

    def enter_chat_screen(self, chat_name):
        search = self.browser.find_element_by_css_selector(self.search_selector)
        search.send_keys(chat_name + Keys.ENTER)
        logging.info(f"Entered into the chat: \"{name}\".")

    def quit(self):
        logging.info("Exiting Whatsapp Web...")
        self.browser.quit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-rf', '--run_forever', dest='run_forever', action='store_true',
                        help='running forever or not')
    args = parser.parse_args()
    logging.basicConfig(handlers=[logging.FileHandler(encoding='utf-8', filename='whatsapp.log')],
                        level=logging.DEBUG,
                        format=u'%(levelname)s - %(name)s - %(asctime)s: %(message)s')
    wa = WhatsApp(session="mysession")
    name = 'Genesis Bot Sandbox'
    wa.check_new_message(name, run_forever=args.run_forever)
    wa.quit()
