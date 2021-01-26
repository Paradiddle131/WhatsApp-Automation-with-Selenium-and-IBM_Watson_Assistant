from base64 import b64decode
from io import BytesIO
from json import load
from logging import debug, info, error
from os import path, getcwd
from time import sleep

from PIL import Image
from bs4 import BeautifulSoup
from pandas import read_csv
from pygetwindow import getWindowsWithTitle
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from IBM_Watson_Assistant import Watson
from OCR import OCR
from whatsapp_helper import *

# TODO: Import Nodes on here instead of run.py

path_home = getcwd()
cnt = 0


class BotActions:
    WAIT_FOR_NODE_INPUT = "Wait for node input"
    GREET = "Greet"


def get_time_from_tag(tag):
    h, m = int(find_time(tag.text).split(':')[0]), int(find_time(tag.text).split(':')[1][:2])
    return datetime.now().replace(hour=h, minute=m)


def get_quote_from_tag(tag):
    message_quote_sender, message_quote_text = ['' for _ in range(2)]
    if do_contains_quote(str(tag)):
        quote = tag.find("span", class_=find_quote(str(tag)))
        if quote:
            message_quote_text = quote.text.replace("\n", ' ')
            message_quote_sender = quote.parent.previous_sibling.find('span').text
            debug(f"Quote Sender: \"{message_quote_sender}\"")
    return message_quote_sender, message_quote_text


def bytes_to_image(bytes, image_name=None):
    """Convert bytes into PIL Image"""
    try:
        stream = BytesIO(bytes)
        image = Image.open(stream).convert("RGBA")
        stream.close()
        if image_name:
            image.save(f'output/image_{image_name}.png')
        return image
    except:
        error(f"Bytes couldn't converted into an image. Bytes: {bytes}", exc_info=True)
        return None


def change_datetime_format(message_text):
    date = find_date(message_text)
    try:
        return message_text.replace(date, datetime.strptime(date, "%d/%m/%Y").strftime("%m/%d/%Y"))
    except ValueError:
        debug("Given date is already in mm/dd/yyyy format.", exc_info=True)


class WhatsApp:
    browser = None
    timeout = 10

    def __init__(self, initialize_whatsapp=True, session=None):
        chrome_options = Options()
        if session:
            chrome_options.add_argument("--user-data-dir={}".format(session))
            try:
                self.browser = webdriver.Chrome(options=chrome_options)
            except:
                # if previous session is left open, close it
                if getWindowsWithTitle('WhatsApp - Google Chrome'):
                    getWindowsWithTitle('WhatsApp - Google Chrome')[0].close()
                    info("Session is already open. \"WhatsApp - Google Chrome\" is closing...")
                if getWindowsWithTitle('New Tab - Google Chrome'):
                    getWindowsWithTitle('New Tab - Google Chrome')[0].close()
                    info("Session is already open. \"New Tab - Google Chrome\" is closing...")
                self.browser = webdriver.Chrome(options=chrome_options)
        else:
            self.browser = webdriver.Chrome()
            info("Chrome Driver is initialized successfully.")
        if initialize_whatsapp:
            self.browser.get("https://web.whatsapp.com/")
            info("WhatsApp Web Client is opening...")
            self.find_wait("copyable-text.selectable-text", By.CLASS_NAME, timeout=30)
            self.browser.maximize_window()
            self.OCR = OCR()
            self.Watson = Watson()
            self.participants_list_path = path.join(path_home, 'participants_list.csv')
            from bot import Bot
            self.bot = Bot()

    def find_wait(self, element_xpath, by=By.XPATH, timeout=10):
        return WebDriverWait(self.browser, timeout).until(
            EC.presence_of_element_located((by, element_xpath)))

    def send_message(self, name, message):
        print(f" MOCK SENDING MESSAGE {message} to {name}")
        '''if not self.in_chat_screen:
            self.enter_chat_screen(name)
        try:
            send_msg = self.find_wait("/html/body/div/div/div/div[4]/div/footer/div[1]/div[2]/div/div[2]", By.XPATH)
            messages = message.split("\n")
            for msg in messages:
                send_msg.send_keys(msg)
                send_msg.send_keys(Keys.SHIFT + Keys.ENTER)
                info(f"Message \"{msg}\" is sent to \"{name}\"")
            send_msg.send_keys(Keys.ENTER)
            return True
        except TimeoutException:
            error("Exception occurred", exc_info=True)
            raise TimeoutError("Your request has been timed out! Try overriding timeout!")
        except NoSuchElementException:
            error("Exception occurred", exc_info=True)
            return False
        except Exception:
            error("Exception occurred", exc_info=True)
            return False'''

    def scroll_up_panel(self, scroll_times=20, element=None):
        if not element:
            element = self.browser.find_element_by_xpath('//*[@id="main"]/div[3]/div/div/div[3]')
        for i in range(scroll_times):
            sleep(0.2)
            element.send_keys(Keys.ARROW_UP)
        sleep(3)
        info(f"Scrolled up for {scroll_times} times.")

    def get_file_content_chrome(self, uri):
        """Extracts blob content as bytes"""
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
            error(f"Couldn't get element from blob content on Chrome. Uri is: {uri}", exc_info=True)
            raise Exception("Request failed with status %s" % result)
        return b64decode(result)

    def is_trouble_shooter(self, GSM):
        """Classifies the sender as a trouble shooter or not"""
        try:
            GSM = GSM.split('+')[1] if '+' in GSM else GSM
            df = read_csv(self.participants_list_path)
            return GSM in df['Trouble_shooters'].values
        except:
            error(f"Error occurred during the Pandas DataFrame actions.", exc_info=True)
            return None

    # def get_ocr_from_tag(self, tag, message_text, save=False):
    #     """Extracts text from image using Google Vision API"""
    #     global cnt
    #     if do_contains_image(str(tag)) \
    #             and not do_contains_audio(str(tag)) \
    #             and not do_contains_quoted_image(str(tag)):
    #         image_link = find_image(str(tag))
    #         image_bytes = self.get_file_content_chrome(image_link)
    #         if save:
    #             bytes_to_image(image_bytes, cnt)  # Save the image on output folder
    #         message_text = message_text + " || " + self.OCR.image_to_text(image_bytes).replace("\n", ' ')
    #         debug(f"Message from the text: \"{message_text.split('||')[1]}\"")
    #     else:
    #         warning(f"No image found either.", exc_info=True)
    #     return message_text

    def get_sender_from_messageId(self, messageId):
        message_sender = find_phone_number(messageId)
        if self.is_trouble_shooter(message_sender):
            debug(
                f"GSM No: {message_sender} is classified as \"trouble shooter\". Skipping this message.")
            return None
        debug(f"GSM No: {message_sender} is classified as \"crew member\".")
        return message_sender


    def run_bot(self):
        name, message_text = ["" for _ in range(2)]
        message_div_class = "message-in"
        last_tag = None
        dialog_tree = {}
        while True:
            try:
                with open("bot_dialog_tree.json") as f:
                    dialog_tree = load(f)
                new_sender = self.get_new_sender()
                if self.get_new_sender() is not None:
                    self.enter_chat_screen(new_sender)
                    if new_sender not in dialog_tree.keys():
                        dialog_tree.update({new_sender: {"action": BotActions.GREET}})
                        name = new_sender
                        self.enter_chat_screen(name)
                if name != "":
                    soup = BeautifulSoup(self.browser.page_source, "html.parser")
                    tag = soup.find_all("div", class_=message_div_class)[-1]
                    tag_text = tag.find_all("div", class_="copyable-text")
                    if tag != last_tag:
                        debug(f"New message received.")
                        last_tag = tag
                        if tag_text:
                            tag_text = tag_text[-1]
                            message_text = tag_text.find("span", class_="selectable-text").find("span").text.replace(
                                "\n", ' ') \
                                if tag_text.find("span", class_="selectable-text") is not None \
                                else tag_text.find("img", class_="copyable-text").attrs['alt']
                        # message_text = self.get_ocr_from_tag(tag, message_text)
                        info(f"message_text: {message_text}")
                        if do_contains_date(message_text):
                            message_text = change_datetime_format(message_text)
                        try:
                            response_http = self.bot.get_response(message_text, dialog_tree[name])
                            debug("HTTP Response of bot -> " + response_http)
                            self.send_message(name=name, message=response_http)
                            last_tag = tag
                        except:
                            print("No response from bot.")
                    else:
                        sleep(.1)
                else:
                    sleep(.5)
            except:
                error(f"Some problem has occurred.", exc_info=True)
                print("Something wrong happened during the loop.")
                break

    def unread_messages(self):
        soup = BeautifulSoup(self.browser.page_source, "html.parser")
        tag = soup.find_all("span", attrs={"aria-label": re.compile(r"[0-9] unread message")})[-1]
        self.browser.find_elements_by_xpath(f'//*[contains(@aria-label, "unread message")]')
        tag_text = tag.find_all("div", class_="copyable-text")
        # TODO

    def check_new_sender(self):
        return self.browser.find_elements_by_xpath(f'//*[contains(@aria-label, "unread message")]')

    def get_new_sender(self):
        soup = BeautifulSoup(self.browser.page_source, "html.parser")
        try:
            return soup.find("span", attrs={
                "aria-label": re.compile(r"[0-9] unread message")}).parent.parent.parent.parent.parent.contents[
                0].contents[0].text
        except:
            return None

    def enter_chat_screen(self, chat_name):
        search = self.find_wait("copyable-text.selectable-text", by=By.CLASS_NAME, timeout=50)
        search.send_keys(chat_name + Keys.ENTER)
        self.find_wait("copyable-area", By.CLASS_NAME)
        sleep(.5)
        info(f"Entered into the chat: \"{chat_name}\".")

    def in_chat_screen(self):
        return True if self.find_wait("copyable-area", By.CLASS_NAME) is not None else False

    def quit(self):
        info("Exiting Whatsapp Web...")
        self.browser.quit()
