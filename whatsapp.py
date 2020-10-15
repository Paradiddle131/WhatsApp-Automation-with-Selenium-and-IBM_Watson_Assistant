import pygetwindow as gw
import re
import sys
import time
import datetime
import datetime as dt
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, ElementNotVisibleException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options

from IBM_Watson_Assistant import Watson
from PIL import Image
# from wand.image import Image

try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:
    print(
        "Beautiful Soup Library is reqired to make this library work(For getting participants list for the specified group).\npip3 install beautifulsoup4")


RELOAD_TIMEOUT = 10
ERROR_TIMEOUT = 5
non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)
time_format = '%I:%M %p'

class WhatsApp():
    """
    This class is used to interact with your whatsapp [UNOFFICIAL API]
    """
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
        search = self.browser.find_element_by_css_selector(self.search_selector)
        search.send_keys(group_name + Keys.ENTER)  # we will send the name to the input key box
        # some say this two try catch below can be grouped into one
        # but I have some version specific issues with chrome [Other element would receive a click]
        # in older versions. So I have handled it spereately since it clicks and throws the exception
        # it is handled safely
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
        # time.sleep(4)  # sometimes it takes long to load

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
            # self.browser.find_element_by_tag_name()
            if message:
                message2 = message.find("span")
                if message2:
                    message_text = message2.text
                    # location = self.browser.page_source.find(message2.text)
            if self.do_contains_sender(str(tag)):
                sender = tag.find("div", class_=self.find_sender(str(tag)))
                if sender:
                    sender2 = sender.find('span')
                    if sender2:
                        message_sender = sender2.text
            # TODO: message_time has been changed, test it
            message_time = time.strptime(self.find_time(tag.text), time_format)
            # message_time = self.find_time(tag.text)
            if message_text != None:
                cnt += 1
                dict_messages.update(
                    {cnt:
                        {'sender': message_sender,
                        'message': message_text,
                        'time': message_time
                        }})
        return dict_messages
        # return sorted(dict_messages, key=lambda x: time.mktime(time.strptime(x['time'], '%d/%m/%Y %H:%M:%S')))

    def enter_chat_screen(self, chat_name):
        search = self.browser.find_element_by_css_selector(self.search_selector)
        search.send_keys(chat_name + Keys.ENTER)

    def get_messages_by_class(self, chat_name):
        self.enter_chat_screen(chat_name)
        scrollbar = self.find_wait('//*[@id="main"]/div[3]/div/div')
        self.browser.execute_script('arguments[0].scrollTop = ' + str(600), scrollbar)
        dict_messages = {}
        message_text, message_sender, message_time = ['' for x in range(3)]
        rows_xpath = '//*[@id="main"]/div[3]/div/div/div[3]'
        rows_element = self.browser.find_element_by_xpath(rows_xpath)
        html = rows_element.get_attribute('innerHTML')
        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup.find_all('span'):
            classid = tag.get('class')
            if classid == ['_3Whw5', 'selectable-text', 'invisible-space', 'copyable-text']:
                # TODO: if the list contains multiple text, combine them in message_text variable
                message_text = [tag.text.translate(non_bmp_map).replace('\n', '')][0]
            elif classid == ['_3UUTc']:
                message_sender = tag.text
            elif classid == ['_18lLQ']:
                message_time = tag.text
            print("@@@:", message_text, "\n", message_sender,"\n",  message_time)
            # if message_text != '':
            dict_messages.update({message_text: (message_sender, message_time)})
        return dict_messages

    def get_messages_by_attribute(self, chat_name):
        search = self.browser.find_element_by_css_selector(self.search_selector)
        search.send_keys(chat_name + Keys.ENTER)  # we will send the name to the input key box
        scrollbar = self.browser.find_element_by_xpath('//*[@id="main"]/div[3]/div/div')

        # loop through every message in the chat
        rows_xpath = '//*[@id="main"]/div[3]/div/div/div[3]'
        rows_element = self.browser.find_element_by_xpath(rows_xpath)
        html = rows_element.get_attribute('innerHTML')
        soup = BeautifulSoup(html, 'html.parser')
        children_rows = soup.findChildren(recursive=False)


        v = 0
        for message_element in children_rows:
            # skip first 2 element ("TODAY" and group menu bar)
            if v < 2:
                v += 1
                continue
            for i, message_attribute in enumerate(message_element.contents[1 if str(message_element.contents[0]).startswith('<span>') else 0].\
                contents[1 if str(message_element.contents[0]).startswith('<span>') else 0].contents[0].contents, 1):
                # TODO: time number ve belki message attrs altindan alinabilir split yerine
                # if the message is a reply to another
                # if "color" in str(message_attribute):
                # if message_attribute.contents[0]:
                if message_attribute.attrs['class'][1] == 'copyable-text':
                    print('Sender name/number found in element #'+str(i), " ->",
                          message_attribute.contents[1].contents[0].contents[0].text)
                          # str(message_attribute).split("button\">")[1].split("</span>")[0])
                    # print('Sender name/number found in element #'+str(i), " ->", str(message_attribute).split("button\">")[1].split("</span>")[0])
                elif "copyable-text" in str(message_attribute):
                    if 'data-plain-text' in str(message_attribute):
                        # if message_attribute
                        print('Message found in element #'+str(i), " ->", str(message_attribute).split("<span>")[1].split("<span class")[0])
                    else:
                        print('Message found in element #'+str(i), " ->", str(message_attribute).split("<span>")[1].split("</span>")[0])
                    # region save messages to json
                    # with open(chat_name+"_messages.json", "w+", encoding='utf-8') as f:
                    #     # TODO: TR karakterleri replace eden method yaz
                    #     json.dump(dict_messages, f, ensure_ascii=False)
                    #     print(f"INFO: Messages saved to {chat_name}_messages.json")
                    # endregion
                elif self.do_contains_time(str(message_attribute.contents[0].contents[0])):
                    print('Time found in element #'+str(i), " ->", self.find_time(str(message_attribute)))
                elif 'img class' in str(message_attribute):
                    print('Image found in element #'+str(i), " ->", str(message_attribute))
        exit()

        # chat_screen_element = self.browser.find_element_by_xpath(chat_screen_xpath)
        j = 20
        scroll_count = 0
        dict_messages = {}

        # Loop through every messages
        while True:
            j -= 1
            if j == 0:
                scroll_count += 1
                j = (scroll_count + 1) * 18
                self.browser.execute_script('arguments[0].scrollTop = ' + str(scroll_count * 300), scrollbar)
            if j == 150:
                break
            try:
                author_element = self.browser.find_element_by_xpath(rows_xpath + f"/div[{j}]/div/div/div/div/span")
                time_element = self.browser.find_element_by_xpath(rows_xpath + f"/div[{j}]/div/div/div/div[3]")
                message_element = self.browser.find_element_by_xpath(rows_xpath + f"/div[{j}]/div/div/div/div/div/span/span")
                if message_element.text in dict_messages and \
                        (author_element.text, time_element.text) in dict_messages[message_element.text]:
                    print(message_element.text)
                    j = 1
                    continue
                dict_messages.update({message_element.text: (author_element.text, time_element.text)})
            except:
                # if the message contains image
                message_element = self.browser.find_element_by_xpath(chat_screen_xpath + f"/div[{j}]/div/div[1]/div/div/div[3]/div/span[1]/span")
                image_element = self.browser.find_element_by_xpath(chat_screen_xpath + f"/div[{j}]/div/div[1]/div/div/div[2]/div/div[5]/img")
                html = image_element.get_attribute('innerHTML')
                print("html:", html)
                soup = BeautifulSoup(html, 'html.parser')
                print("soup:", soup)
                exit()
                continue
        print(dict_messages.keys())


        exit()
        v = 0
        while True:
            self.browser.execute_script('arguments[0].scrollTop = ' + str(v * 300), scrollbar)
            time.sleep(0.10)
            try:
                html = rows_element.get_attribute('innerHTML')
                soup = BeautifulSoup(html, "html.parser")
                for i in soup.find_all(lambda tag: tag.name == 'span' and
                                                   tag.get('dir') == 'ltr' and
                                                   '_3Whw5 selectable-text invisible-space copyable-text'
                                                   in tag.get('class')):
                    if i.text not in list_messages:
                        list_messages.append(i.text)
                v += 1
            except Exception as e:
                print(e)
                pass
            # elements = self.browser.find_elements_by_tag_name("div")
            # for element in elements:
            #     try:
            #         html = element.get_attribute('innerHTML')
            #         soup = BeautifulSoup(html, "html.parser")
            #         for i in soup.find_all("div", class_="_25Ooe"):
            #             j = i.find("span", class_="_1wjpf")
            #             if j:
            #                 j = j.text
            #                 if "\n" in j:
            #                     j = j.split("\n")
            #                     j = j[0]
            #                     j = j.strip()
            #                     if j not in list_participants:
            #                         list_participants.append(j)
            #                         print(j)
            #     except Exception as e:
            #         print(e)
            #         pass

    def do_contains_sender(self, text):
        return re.compile(r'\w{5,6} color-[0-9]{1,2} \w{5,6}').search(text)

    def find_sender(self, text):
        return [x.group() for x in re.finditer(r'\w{5,6} color-[0-9]{1,2} \w{5,6}', text)][0]

    def do_contains_time(self, text):
        return re.compile(r'(\d|1[0-2]):([0-5]\d) (am|pm)').search(text)

    def find_time(self, text):
        return [x.group() for x in re.finditer(r'(\d|1[0-2]):([0-5]\d) (am|pm)', text)][0]

    def valid_date(self, datestring):
        try:
            mat = re.match(r'(\d{2})[/.-](\d{2})[/.-](\d{4})$', datestring)
            if mat is not None:
                datetime.datetime(*(map(int, mat.groups()[-1::-1])))
                return True
        except ValueError:
            pass
        return False

    def quit(self):
        self.browser.quit()


if __name__ == '__main__':
    wa = WhatsApp(100, session="mysession")
    watson = Watson()
    # name = 'Genesis Best Grup'
    name = 'Babam'
    name_sandbox = 'Genesis Bot Sandbox'
    dct_last_messages = wa.get_last_messages(name)
    # print([dct_last_messages[i]['message'] for i in range(1, len(dct_last_messages)+1)])

    messages_to_read = [dct_last_messages[i]['message'] for i in range(1, len(dct_last_messages)+1)]
    for message_to_read in messages_to_read:
        message_to_send = watson.message_stateless(message_to_read, doPrint=True)
        if message_to_send:
            wa.send_message(name_sandbox, message_to_send['output']['generic'][0]['text'])

    wa.quit()

    #region unused ımage functions
    # from wand.image import Image
    # def get_element_screenshot(self, element: WebElement) -> bytes:
    #     driver = element._parent
    #     ActionChains(driver).move_to_element(element).perform()  # focus
    #     src_base64 = driver.get_screenshot_as_base64()
    #     scr_png = base64.b64decode(src_base64)
    #     scr_img = Image(blob=scr_png)
    #
    #     x = element.location["x"]
    #     y = element.location["y"]
    #     w = element.size["width"]
    #     h = element.size["height"]
    #     scr_img.crop(
    #         left=math.floor(x),
    #         top=math.floor(y),
    #         width=math.ceil(w),
    #         height=math.ceil(h),
    #     )
    #     return scr_img.make_blob()
    #
    # def capture_element(self, element, driver, count=''):
    #     location = element.location
    #     size = element.size
    #     img = driver.get_screenshot_as_png()
    #     # img = Image.open(StringIO(img))
    #     img = Image.open(str(img))
    #     left = location['x']
    #     top = location['y']
    #     right = location['x'] + size['width']
    #     bottom = location['y'] + size['height']
    #     img = img.crop((int(left), int(top), int(right), int(bottom)))
    #     img.save(f'screenshot_{count}.png')
#endregion