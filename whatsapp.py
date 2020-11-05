from base64 import b64decode
from time import strptime, time, sleep
from os import environ, path, getcwd, remove, system
from io import BytesIO
from pandas import read_csv
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from IBM_Watson_Assistant import Watson
from OCR import OCR
from mongodb import MongoDB
from whatsapp_helper import *


try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:
    print(
        "Beautiful Soup Library is reqired to make this library work(For getting participants list for the specified group).\npip3 install beautifulsoup4")

cnt = 0


def get_quote_from_tag(tag):
    message_quote_sender, message_quote_text = ['' for _ in range(2)]
    if do_contains_quote(str(tag)):
        quote = tag.find("span", class_=find_quote(str(tag)))
        if quote:
            message_quote_text = quote.text.replace("\n", ' ')
            message_quote_sender = quote.parent.previous_sibling.find('span').text
            print(f"Quote Sender: \"{message_quote_sender}\"")
    return message_quote_sender, message_quote_text


def get_time_from_tag(tag):
    return strptime(find_time(tag.text), '%I:%M %p')


def bytes_to_image(bytes, image_name=None):
    try:
        stream = BytesIO(bytes)
        image = Image.open(stream).convert("RGBA")
        stream.close()
        if image_name:
            image.save(f'output/image_{image_name}.png')
        return image
    except:
        print(f"Bytes couldn't converted into an image. Bytes: {bytes}")
        return None


class WhatsApp:
    browser = None

    def __init__(self, session):
        chrome_options = Options()
        if session:
            chrome_options.add_argument("--user-data-dir={}".format(session))
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--headless')
            # chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument(
                "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36")
            chrome_options.binary_location = environ.get('GOOGLE_CHROME_BIN')
            try:
                self.browser = webdriver.Chrome(executable_path=environ.get('CHROMEDRIVER_PATH'),
                                                chrome_options=chrome_options)
            except:
                system("TASKKILL /F /IM chrome.exe")
                print("Session is already open. \"WhatsApp - Google Chrome\" is closing...")
                self.browser = webdriver.Chrome(executable_path=environ.get('CHROMEDRIVER_PATH'),
                                                chrome_options=chrome_options)
        self.browser.get("https://web.whatsapp.com/")
        soup = BeautifulSoup(self.browser.page_source, "html.parser")
        print(soup)  # DEBUGGING
        self.get_qr()
        print("WhatsApp Web Client is opening...")
        WebDriverWait(self.browser, 30).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, '._3FRCZ')))
        self.browser.maximize_window()
        self.OCR = OCR()
        self.Watson = Watson()
        self.Mongo = MongoDB(db_name='WhatsApp', collection_name='messages', initialize_splunk=False)
        self.participants_list_path = path.join(getcwd(), 'participants_list.csv')

    def get_qr(self):
        try:
            element = WebDriverWait(self.browser, 20).until(EC.presence_of_element_located(
                (By.XPATH, '//canvas[@aria-label = "Scan me!"]')))
        except:
            print("No QR Code.")
            return

        location = element.location
        size = element.size
        self.browser.save_screenshot("shot.png")

        x = location['x']
        y = location['y']
        w = size['width']
        h = size['height']
        width = x + w
        height = y + h

        im = Image.open('shot.png')
        im = im.crop((int(x), int(y), int(width), int(height)))
        im.save('static/qr.png')
        remove("shot.png")

    def find_wait(self, element_xpath, by='xpath'):
        return WebDriverWait(self.browser, 10).until(EC.presence_of_element_located(
            (By.XPATH if by.lower() == 'xpath' else By.CSS_SELECTOR, element_xpath)))

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
                print(f"Element couldn't be found from xpath: {xpath}.")
                break

    def scroll_up_panel(self, scroll_times=20, element=None):
        if not element:
            element = self.browser.find_element_by_xpath('//*[@id="main"]/div[3]/div/div/div[3]')
        for i in range(scroll_times):
            sleep(0.2)
            element.send_keys(Keys.ARROW_UP)
        sleep(3)
        print(f"Scrolled up for {scroll_times} times.")

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
            print(f"Couldn't get element from blob content on Chrome. Uri is: {uri}")
            raise Exception("Request failed with status %s" % result)
        return b64decode(result)

    def is_trouble_shooter(self, GSM):
        try:
            GSM = GSM.split('+')[1] if '+' in GSM else GSM
            df = read_csv(self.participants_list_path)
            return GSM in df['Trouble_shooters'].values
        except:
            print(f"Error occurred during the Pandas DataFrame actions.")
            return None

    def get_ocr_from_tag(self, tag, message_text, save=False):
        global cnt
        if do_contains_image(str(tag)) \
                and not do_contains_audio(str(tag)) \
                and not do_contains_quoted_image(str(tag)):
            image_link = find_image(str(tag))
            image_bytes = self.get_file_content_chrome(image_link)
            if save:
                bytes_to_image(image_bytes, cnt)  # Save the image on output folder
            message_text = message_text + " || " + self.OCR.image_to_text(image_bytes).replace("\n", ' ')
            print(f"Message from the text: \"{message_text.split('||')[1]}\"")
        return message_text

    def get_sender_from_messageId(self, messageId):
        message_sender = find_phone_number(messageId)
        if self.is_trouble_shooter(message_sender):
            print(f"GSM No: {message_sender} is classified as \"trouble shooter\". Skipping this message.")
            return None
        print(f"GSM No: {message_sender} is classified as \"crew member\".")
        return message_sender

    def fetch_messages_continuously(self, last_tag=None):
        global cnt
        sleep(4)
        message_text, message_sender, message_datetime, message_time, message_info = ['' for _ in range(5)]
        dict_messages = {}
        try:
            soup = BeautifulSoup(self.browser.page_source, "html.parser")
            tag = soup.find_all("div", class_="message-out")[-1]
            message_id = tag.attrs["data-id"]
            message_sender = self.get_sender_from_messageId(message_id)
            if message_sender is None:
                return
            tag_text = tag.find_all("div", class_="copyable-text")
            if tag != last_tag:
                print(f"New message received at: {time()}")
                if tag_text:
                    tag_text = tag_text[-1]
                    message_info = tag_text.attrs["data-pre-plain-text"]
                    message_datetime = str_to_datetime(find_date(message_info) + ' ' + find_time(message_info))
                    message_text = tag_text.find("span", class_="selectable-text").find("span").text.replace("\n", ' ')
                else:
                    message_datetime = get_time_from_tag(tag)
                print(f"Message: \"{message_text}\"")
                message_quote_sender, message_quote_text = get_quote_from_tag(tag)
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
                print("Final Message Dictionary ->", dict_messages)
                try:
                    self.Mongo.insert(dict_messages)
                    return tag
                except:
                    print(f"Tried to insert into mongo but error occurred.")
            else:
                print("Sleeping for 3 seconds...")
                sleep(3)
        except:
            print("Something wrong happened during the loop.")
            return

    def enter_chat_screen(self, chat_name):
        search = self.browser.find_element_by_css_selector(".cBxw- > div:nth-child(2)")
        search.send_keys(chat_name + Keys.ENTER)
        print(f"Entered into the chat: \"{chat_name}\".")

    def quit(self):
        print("Exiting Whatsapp Web...")
        self.browser.quit()
