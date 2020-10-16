import base64
from io import BytesIO

import pygetwindow as gw
import sys
import time
import datetime as dt
import json
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options

from IBM_Watson_Assistant import Watson
from whatsapp_helper import *

try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:
    print(
        "Beautiful Soup Library is reqired to make this library work(For getting participants list for the specified group).\npip3 install beautifulsoup4")


RELOAD_TIMEOUT = 10
ERROR_TIMEOUT = 5
non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)
time_format = '%I:%M %p'

#TODO:

class WhatsApp():
    emoji = {}  # This dict will contain all emojies needed for chatting
    browser = None
    timeout = 10  # The timeout is set for about ten seconds

    # This constructor will load all the emojies present in the json file and it will initialize the webdriver
    def __init__(self, wait, screenshot=None, session=None):
        chrome_options = Options()
        if session:
            chrome_options.add_argument("--user-data-dir={}".format(session))
            try:
                self.browser = webdriver.Chrome(options=chrome_options)  # we are using chrome as our webbrowser
            except:
                # if previous session is left open, close it
                gw.getWindowsWithTitle('WhatsApp - Google Chrome')[0].close()
                gw.getWindowsWithTitle('New Tab - Google Chrome')[0].close()
                self.browser = webdriver.Chrome(options=chrome_options)  # we are using chrome as our webbrowser
        else:
            self.browser = webdriver.Chrome()
        self.browser.get("https://web.whatsapp.com/")
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
            send_msg.send_keys(Keys.ENTER)
            return True
        except TimeoutException:
            raise TimeoutError("Your request has been timed out! Try overriding timeout!")
        except NoSuchElementException:
            return False
        except Exception:
            return False

    def participants_count_for_group(self, group_name):
        header_class_name = "_1iFv8"
        self.enter_chat_screen(group_name)
        try:
            click_menu = WebDriverWait(self.browser, self.timeout).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, f".{header_class_name}")))
            click_menu.click()
        except TimeoutException:
            raise TimeoutError("Your request has been timed out! Try overriding timeout!")
        except NoSuchElementException as e:
            return "None"
        except Exception as e:
            return "None"
        current_time = dt.datetime.now()
        participants_class = "_2y8MV"
        participants_selector = f"span.{participants_class}"
        time.sleep(5)
        try:
            list_participants_count = self.browser.find_elements_by_css_selector(participants_selector)
            print("There are", list_participants_count[2].text, "participants in group", group_name)
            return list_participants_count[2].text
        except Exception as e:
            print(e)
            pass
        new_time = dt.datetime.now()
        elapsed_time = (new_time - current_time).seconds
        if elapsed_time > self.timeout:
            return "NONE"

    def get_group_participants(self, group_name):
        header_class_name = "_1iFv8"
        participants_count = int(self.participants_count_for_group(group_name).split()[0])
        try:
            click_menu = self.find_wait('.'+header_class_name, 'css')
            click_menu.click()
        except TimeoutException:
            raise TimeoutError("Your request has been timed out! Try overriding timeout!")
        except NoSuchElementException as e:
            print(e)
            return "None"
        except Exception as e:
            print(e)
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
                print(e)
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
                print("Element couldn't be found.")
                break

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
            raise Exception("Request failed with status %s" % result)
        return base64.b64decode(result)

    def bytes_to_image(self, bytes):
        stream = BytesIO(bytes)
        image = Image.open(stream).convert("RGBA")
        stream.close()
        return image

    def get_last_messages(self, name):
        dict_messages = {}
        search = self.browser.find_element_by_css_selector(self.search_selector)
        search.send_keys(name + Keys.ENTER)
        time.sleep(3)
        soup = BeautifulSoup(self.browser.page_source, "html.parser")
        cnt = 0
        for tag in soup.find_all("div", class_="message-in"):
            message_text, message_sender, message_time, location = [None for x in range(4)]
            message = tag.find("span", class_="selectable-text")
            if message:
                message2 = message.find("span")
                if message2:
                    message_text = message2.text
                    # location = self.browser.page_source.find(message2.text)
            if do_contains_image(str(tag)) and not do_contains_audio(str(tag)):
                image_link = find_image(str(tag))
                image = self.bytes_to_image(self.get_file_content_chrome(image_link))
                image.save(f'output/image_{cnt}.png')
                # TODO: Insert OCR methods here
            if do_contains_sender(str(tag)):
                sender = tag.find("div", class_=find_sender(str(tag)))
                if sender:
                    sender2 = sender.find('span')
                    if sender2:
                        message_sender = sender2.text
            # TODO: message_time has been changed due to sorting purposes, test it
            message_time = time.strptime(find_time(tag.text), time_format)
            # message_time = find_time(tag.text)
            if message_text != None:
                cnt += 1
                dict_messages.update(
                    {cnt:
                        {'sender': message_sender,
                        'message': message_text,
                        'time': message_time
                        }})
        return dict_messages

    def enter_chat_screen(self, chat_name):
        search = self.browser.find_element_by_css_selector(self.search_selector)
        search.send_keys(chat_name + Keys.ENTER)

    def quit(self):
        self.browser.quit()


if __name__ == '__main__':
    wa = WhatsApp(100, session="mysession")
    watson = Watson()
    # name = 'Genesis Best Grup'
    name = 'Babam'
    name_sandbox = 'Genesis Bot Sandbox'
    dct_last_messages = wa.get_last_messages(name)

    messages_to_read = [dct_last_messages[i]['message'] for i in range(1, len(dct_last_messages)+1)]
    for message_to_read in messages_to_read:
        message_to_send = watson.message_stateless(message_to_read, doPrint=True)
        if message_to_send:
            # wa.send_message(name_sandbox, message_to_send['output']['generic'][0]['text'])
            pass

    wa.quit()