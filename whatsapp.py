import re
import time
import datetime as dt
import json

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, ElementNotVisibleException
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlencode

from PIL import Image
# from wand.image import Image


try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:
    print(
        "Beautiful Soup Library is reqired to make this library work(For getting participants list for the specified group).\npip3 install beautifulsoup4")


RELOAD_TIMEOUT = 10
ERROR_TIMEOUT = 5

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

    def find_wait(self, element_xpath, by='xpath'):
        return WebDriverWait(self.browser, self.timeout).until(EC.presence_of_element_located(
            (By.XPATH if by.lower() == 'xpath' else By.CSS_SELECTOR, element_xpath)))

    # This method is used to send the message to the individual person or a group
    # will return true if the message has been sent, false else
    def send_message(self, name, message):
        message = self.emojify(message)  # this will emojify all the emoji which is present as the text in string
        search = self.browser.find_element_by_css_selector(self.search_selector)
        search.send_keys(name + Keys.ENTER)  # we will send the name to the input key box
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

    # This method will count the no of participants for the group name provided
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

    # This method is used to get all the participants
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

    def get_messages(self, chat_name):
        search = self.browser.find_element_by_css_selector(self.search_selector)
        search.send_keys(chat_name + Keys.ENTER)  # we will send the name to the input key box
        scrollbar = self.browser.find_element_by_xpath('//*[@id="main"]/div[3]/div/div')

        # loop through every message in the chat
        rows_element = self.browser.find_element_by_xpath('//*[@id="main"]/div[3]/div/div/div[3]')
        html = rows_element.get_attribute('innerHTML')
        soup = BeautifulSoup(html, 'html.parser')
        children_rows = soup.findChildren(recursive=False)

        v = 0
        for message_element in children_rows:
            # skip first 2 element ("TODAY" and group menu bar)
            if v < 2:
                v += 1
                continue
            for x in message_element.contents[1 if str(message_element.contents[0]).startswith('<span>') else 0].\
                contents[1 if str(message_element.contents[0]).startswith('<span>') else 0].contents[0]:
                print(str(x))
            print()

        for message_element in children_rows:
            str(message_element)

            # loop through every element in a message box
            message_box_element = self.browser.find_element_by_xpath('//*[@id="main"]/div[3]/div/div/div[3]/div[4]/div/div/div/div')
            html = message_box_element.get_attribute('innerHTML')
            soup = BeautifulSoup(html, 'html.parser')
            children = soup.findChildren(recursive=False)
            # TODO: -
            for i, child in enumerate(children, 1):
                if "color-16" in str(child):
                    print('Sender name/number found in element #'+str(i), " ->", str(child).split("button\">")[0].split("</span>")[0])
                elif "copyable-text" in str(child):
                    print('Message found in element #'+str(i), " ->", str(child).split("<span>")[0].split("</span>")[0])
                    # region save messages to json
                    # with open(chat_name+"_messages.json", "w+", encoding='utf-8') as f:
                    #     # TODO: TR karakterleri replace eden method yaz
                    #     json.dump(dict_messages, f, ensure_ascii=False)
                    #     print(f"INFO: Messages saved to {chat_name}_messages.json")
                    # endregion
                elif self.do_contains_time(str(child.contents[0].contents[0])):
                    print('Time found in element #'+str(i), " ->", str(child).split("<\"auto\">")[0].split("</span>")[0])
                    # print('time is:', )
                elif 'img class' in str(child):
                    print('Image found in element #'+str(i), " ->", str(child))

        exit()

        # html = rows_element.get_attribute('innerHTML')
        # soup = BeautifulSoup(html, "html.parser")
        # soup.find_all(lambda tag: tag.name == 'span' and
        #                           tag.get('dir') == 'ltr' and
        #                           '_3Whw5 selectable-text invisible-space copyable-text'
        #                           in tag.get('class'))
        chat_screen_xpath = '//*[@id="main"]/div[3]/div/div/div[3]'
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
                author_element = self.browser.find_element_by_xpath(chat_screen_xpath + f"/div[{j}]/div/div/div/div/span")
                time_element = self.browser.find_element_by_xpath(chat_screen_xpath + f"/div[{j}]/div/div/div/div[3]")
                message_element = self.browser.find_element_by_xpath(chat_screen_xpath + f"/div[{j}]/div/div/div/div/div/span/span")
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


    #region sample get_message method
    # def print_last_msg(NAME, list_of_chatters):
    #     message = []
    #     for l in list_of_chatters:
    #
    #         name = l.find('span', {'class': "emojitext ellipsify"}).get("title")
    #         if name == NAME:
    #             times = l.findAll("span", {"class": "chat-time"})
    #             msgs = l.findAll("span", {'class': "emojitext ellipsify"})
    #             tlist = ['\n' + t.getString() for t in times]
    #             mlist = [msg.getString() for msg in msgs]
    #             mlist.remove(name)
    #
    #             from_me = l.findAll("span", {"class": "icon icon-status-dblcheck"}) + l.findAll("span", {
    #                 "class": "icon icon-status-check"})
    #             if len(from_me) > 0:
    #                 mlist.insert(0, u'Me')
    #             else:
    #                 mlist.insert(0, name)
    #
    #             message = message + tlist + mlist
    #     return message
    #
    # def get_Messages(self, group_name):
    #     # self.participants_count_for_group(group_name)
    #     # search = self.browser.find_element_by_css_selector(self.search_selector)
    #     # search.send_keys(group_name + Keys.ENTER)  # we will send the name to the input key box
    #
    #     wf = open("messages.log", "a")
    #     counter = 0
    #     GLOBAL_MSG = []
    #     url = "https://web.whatsapp.com/"
    #
    #     # EXTRACT CURRENT PAGE SOURCE
    #     html_source = self.browser.page_source
    #     soup = BeautifulSoup(html_source, "html.parser")
    #
    #     try:
    #         list_of_chatters = soup.body.div.div('div', {'class': 'h70RQ two'})[0]('div', {'id': 'side'})[0].findAll(
    #             'div', {'class': "chat-body"})
    #
    #         ext_msg_time = self.print_last_msg(group_name, list_of_chatters)
    #
    #         WRITE_TO_FILE = False
    #         for m in ext_msg_time:
    #             if m not in GLOBAL_MSG:
    #                 GLOBAL_MSG.append(m)
    #                 print(GLOBAL_MSG)
    #                 WRITE_TO_FILE = True
    #
    #         if WRITE_TO_FILE:
    #             # print ext_msg_time
    #             for m in ext_msg_time:
    #                 wf.write(m)
    #                 wf.write('|')
    #
    #     except:
    #         self.browser.get(url)
    #         time.sleep(ERROR_TIMEOUT)
    #endregion

    # This method is used to get the main page
    def goto_main(self):
        try:
            self.browser.refresh()
            Alert(self.browser).accept()
        except Exception as e:
            print(e)
        WebDriverWait(self.browser, self.timeout).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, '._3FRCZ')))

    # get the status message of a person
    # TimeOut is approximately set to 10 seconds
    def get_status(self, name):
        # scrollbar = self.browser.find_element_by_css_selector("#app > div > div > div.MZIyP > div._3q4NP._2yeJ5 > span > div > span > div > div")
        # self.browser.execute_script('arguments[0].scrollTop = '+str(v*300), scrollbar)

        search = self.browser.find_element_by_css_selector(self.search_selector)
        search.send_keys(name + Keys.ENTER)  # we will send the name to the input key box
        try:
            # group_xpath = "/html/body/div/div/div/div[3]/header/div[1]/div/span/img"
            group_xpath = "/html/body/div/div/div/div[4]/div/header/div[1]/div/img"
            click_menu = WebDriverWait(self.browser, self.timeout).until(EC.presence_of_element_located(
                (By.XPATH, group_xpath)))
            click_menu.click()
        except TimeoutException:
            raise TimeoutError("Your request has been timed out! Try overriding timeout!")
        except NoSuchElementException:
            return "None"
        except Exception:
            return "None"
        try:
            # self.browser.execute_script("window.scrollBy(0,250)", "")
            status_xpath = '//*[@id="app"]/div/div/div[2]/div[3]/span/div/span/div/div/div[1]/div[4]/div[2]/div/div/span/span'
            # status_css_selector = ".drawer-section-body > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > span:nth-child(1) > span:nth-child(1)"   # This is the css selector for status
            WebDriverWait(self.browser, self.timeout).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, status_xpath)))
            status = self.browser.find_element_by_css_selector(status_xpath).text
            # We will try for 100 times to get the status
            for i in range(10):
                if len(status) > 0:
                    return status
                else:
                    time.sleep(1)  # we need some delay
            return "None"
        except TimeoutException:
            raise TimeoutError("Your request has been timed out! Try overriding timeout!")
        except NoSuchElementException:
            return "None"
        except Exception:
            return "None"

    # to get the last seen of the person
    def get_last_seen(self, name, timeout=10):
        search = self.browser.find_element_by_css_selector(self.search_selector)
        search.send_keys(name + Keys.ENTER)  # we will send the name to the input key box
        last_seen_css_selector = "._315-i"
        start_time = dt.datetime.now()
        try:
            WebDriverWait(self.browser, self.timeout).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, last_seen_css_selector)))
            while True:
                last_seen = self.browser.find_element_by_css_selector(last_seen_css_selector).text
                if last_seen and "click here" not in last_seen:
                    return last_seen
                end_time = dt.datetime.now()
                elapsed_time = (end_time - start_time).seconds
                if elapsed_time > 10:
                    return "None"
        except TimeoutException:
            raise TimeoutError("Your request has been timed out! Try overriding timeout!")
        except NoSuchElementException:
            return "None"
        except Exception:
            return "None"

    # This method does not care about anything, it sends message to the currently active chat
    # you can use this method to recursively send the messages to the same person
    def send_blind_message(self, message):
        try:
            message = self.emojify(message)
            send_msg = WebDriverWait(self.browser, self.timeout).until(EC.presence_of_element_located(
                (By.XPATH, "/html/body/div/div/div/div[4]/div/footer/div[1]/div[2]/div/div[2]")))
            messages = message.split("\n")
            for msg in messages:
                send_msg.send_keys(msg)
                send_msg.send_keys(Keys.SHIFT + Keys.ENTER)
            send_msg.send_keys(Keys.ENTER)
            return True
        except NoSuchElementException:
            return "Unable to Locate the element"
        except Exception as e:
            print(e)
            return False

    # This method will send you the picture
    def send_picture(self, name, picture_location, caption=None):
        search = self.browser.find_element_by_css_selector(self.search_selector)
        search.send_keys(name + Keys.ENTER)  # we will send the name to the input key box
        try:
            attach_xpath = '//*[@id="main"]/header/div[3]/div/div[2]/div'
            send_file_xpath = '/html/body/div[1]/div/div/div[2]/div[2]/span/div/span/div/div/div[2]/span/div/div/span'
            attach_type_xpath = '/html/body/div[1]/div/div/div[4]/div/header/div[3]/div/div[2]/span/div/div/ul/li[1]/button/input'
            # open attach menu
            attach_btn = self.browser.find_element_by_xpath(attach_xpath)
            attach_btn.click()

            # Find attach file btn and send screenshot path to input
            time.sleep(1)
            attach_img_btn = self.browser.find_element_by_xpath(attach_type_xpath)

            # TODO - might need to click on transportation mode if url doesn't work
            attach_img_btn.send_keys(picture_location)  # get current script path + img_path
            time.sleep(1)
            if caption:
                caption_xpath = "/html/body/div[1]/div/div/div[2]/div[2]/span/div/span/div/div/div[2]/div/span/div/div[2]/div/div[3]/div[1]/div[2]"
                send_caption = self.browser.find_element_by_xpath(caption_xpath)
                send_caption.send_keys(caption)
            send_btn = self.browser.find_element_by_xpath(send_file_xpath)
            send_btn.click()

        except (NoSuchElementException, ElementNotVisibleException) as e:
            print(str(e))

    # For sending documents
    def send_document(self, name, document_location):
        search = self.browser.find_element_by_css_selector(self.search_selector)
        search.send_keys(name + Keys.ENTER)  # we will send the name to the input key box
        try:
            attach_xpath = '//*[@id="main"]/header/div[3]/div/div[2]/div'
            send_file_xpath = '/html/body/div[1]/div/div/div[2]/div[2]/span/div/span/div/div/div[2]/span/div/div/span'
            attach_type_xpath = '/html/body/div[1]/div/div/div[4]/div/header/div[3]/div/div[2]/span/div/div/ul/li[3]/button/input'
            # open attach menu
            attach_btn = self.browser.find_element_by_xpath(attach_xpath)
            attach_btn.click()

            # Find attach file btn and send screenshot path to input
            time.sleep(1)
            attach_img_btn = self.browser.find_element_by_xpath(attach_type_xpath)

            # TODO - might need to click on transportation mode if url doesn't work
            attach_img_btn.send_keys(document_location)  # get current script path + img_path
            time.sleep(1)
            send_btn = self.browser.find_element_by_xpath(send_file_xpath)
            send_btn.click()

        except (NoSuchElementException, ElementNotVisibleException) as e:
            print(str(e))

    # Clear the chat
    def clear_chat(self, name):
        self.browser.find_element_by_css_selector("._3FRCZ").send_keys(name + Keys.ENTER)
        menu_xpath = "/html/body/div[1]/div/div/div[4]/div/header/div[3]/div/div[3]/div/span"
        WebDriverWait(self.browser, self.timeout).until(EC.presence_of_element_located(
            (By.XPATH, menu_xpath)))
        menu = self.browser.find_element_by_xpath(menu_xpath)
        menu.click()
        chains = ActionChains(self.browser)
        for i in range(4):
            chains.send_keys(Keys.ARROW_DOWN)
        chains.send_keys(Keys.ENTER)
        chains.perform()
        clear_xpath = '//*[@id="app"]/div/span[2]/div/div/div/div/div/div/div[2]/div[2]'
        WebDriverWait(self.browser, self.timeout).until(EC.presence_of_element_located(
            (By.XPATH, clear_xpath)))
        self.browser.find_element_by_xpath(clear_xpath).click()

    # override the timeout
    def override_timeout(self, new_timeout):
        self.timeout = new_timeout

    # This method is used to emojify all the text emoji's present in the message
    def emojify(self, message):
        for emoji in self.emoji:
            message = message.replace(emoji, self.emoji[emoji])
        return message

    def get_profile_pic(self, name):
        search = self.browser.find_element_by_css_selector(self.search_selector)
        search.send_keys(name + Keys.ENTER)
        try:
            open_profile = WebDriverWait(self.browser, self.timeout).until(EC.presence_of_element_located(
                (By.XPATH, "/html/body/div[1]/div/div/div[3]/div/header/div[1]/div/img")))
            open_profile.click()
        except:
            print("nothing found")
        try:
            open_pic = WebDriverWait(self.browser, self.timeout).until(EC.presence_of_element_located(
                (By.XPATH, "/html/body/div[1]/div/div/div[1]/div[3]/span/div/span/div/div/div/div[1]/div[1]/div/img")))
            open_pic.click()
        except:
            print("Nothing found")
        try:
            img = WebDriverWait(self.browser, self.timeout).until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="app"]/div/span[2]/div/div/div[2]/div/div/div/div/img')))
        except:
            print("Couldn't find the URL to the image")
        img_src_url = img.get_attribute('src')
        self.browser.get(img_src_url)
        self.browser.save_screenshot(name + "_img.png")

    def create_group(self, group_name, members):
        more = self.browser.find_element_by_css_selector(
            "#side > header > div._20NlL > div > span > div:nth-child(3) > div > span")
        more.click()
        chains = ActionChains(self.browser)
        chains.send_keys(Keys.ARROW_DOWN + Keys.ENTER)
        chains.perform()
        for member in members:
            contact_name = self.browser.find_element_by_css_selector("._16RnB")
            contact_name.send_keys(member + Keys.ENTER)
        time.sleep(3)  # little delay to make the process robust
        next_step = self.browser.find_element_by_css_selector("._3hV1n > span:nth-child(1)")
        next_step.click()
        group_text = self.browser.find_element_by_css_selector(".bsmJe > div:nth-child(2)")
        group_text.send_keys(group_name + Keys.ENTER)

    def set_group_picture(self, group_name, picture_location):
        search = self.browser.find_element_by_css_selector(self.search_selector)
        search.send_keys(group_name + Keys.ENTER)  # we will send the group name to the input key box
        try:
            menu_xpath = '/html/body/div[1]/div/div/div[4]/div/header/div[3]/div/div[3]/div/span'
            group_info_xpath = '/html/body/div[1]/div/div/div[4]/div/header/div[3]/div/div[3]/span/div/ul/li[1]/div'
            image_input_xpath = '/html/body/div[1]/div/div/div[2]/div[3]/span/div/span/div/div/div[1]/div[1]/div[1]/div/input'
            zoom_out_xpath = '/html/body/div[1]/div/span[2]/div/div/div/div/div/div/span/div/div/div[1]/div[1]/div[2]/span'
            save_btn_xpath = '/html/body/div[1]/div/span[2]/div/div/div/div/div/div/span/div/div/div[2]/span/div/div'
            exit_group_info_xpath = '/html/body/div[1]/div/div/div[2]/div[3]/span/div/span/div/header/div/div[1]/button/span'

            # open group info
            menu = self.browser.find_element_by_xpath(menu_xpath)
            menu.click()
            time.sleep(1)
            group_info = self.browser.find_element_by_xpath(group_info_xpath)
            group_info.click()

            # find image input and send picutre path
            time.sleep(1)
            image_input = self.browser.find_element_by_xpath(image_input_xpath)
            image_input.send_keys(picture_location)

            # zoom out picture and save
            time.sleep(1)
            zoom_out = self.browser.find_element_by_xpath(zoom_out_xpath)
            for i in range(0, 5):
                zoom_out.click()
            save_btn = self.browser.find_element_by_xpath(save_btn_xpath)
            save_btn.click()

            # close the group info
            time.sleep(1)
            exit_group_info = self.browser.find_element_by_xpath(exit_group_info_xpath)
            exit_group_info.click()
        except (NoSuchElementException, ElementNotVisibleException) as e:
            print(str(e))

    def join_group(self, invite_link):
        self.browser.get(invite_link)
        try:
            Alert(self.browser).accept()
        except:
            print("No alert Found")
        join_chat = self.browser.find_element_by_css_selector("#action-button")
        join_chat.click()
        WebDriverWait(self.browser, self.timeout).until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div/span[3]/div/div/div/div/div/div/div[2]/div[2]')))
        join_group = self.browser.find_element_by_xpath(
            '//*[@id="app"]/div/span[3]/div/div/div/div/div/div/div[2]/div[2]')
        join_group.click()

    # This method is used to get an invite link for a particular group
    def get_invite_link_for_group(self, groupname):
        search = self.browser.find_element_by_css_selector("._3FRCZ")
        search.send_keys(groupname + Keys.ENTER)
        self.browser.find_element_by_css_selector("#main > header > div._5SiUq > div._16vzP > div > span").click()
        try:
            # time.sleep(3)
            WebDriverWait(self.browser, self.timeout).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR,
                 "#app > div > div > div.MZIyP > div._3q4NP._2yeJ5 > span > div > span > div > div > div > div:nth-child(5) > div:nth-child(3) > div._3j7s9 > div > div")))
            invite_link = self.browser.find_element_by_css_selector(
                "#app > div > div > div.MZIyP > div._3q4NP._2yeJ5 > span > div > span > div > div > div > div:nth-child(5) > div:nth-child(3) > div._3j7s9 > div > div")
            invite_link.click()
            WebDriverWait(self.browser, self.timeout).until(EC.presence_of_element_located(
                (By.ID, "group-invite-link-anchor")))
            link = self.browser.find_element_by_id("group-invite-link-anchor")
            return link.text
        except:
            print("Cannot get the link")

    # This method is used to exit a group
    def exit_group(self, group_name):
        search = self.browser.find_element_by_css_selector(self.search_selector)
        search.send_keys(group_name + Keys.ENTER)
        self.browser.find_element_by_css_selector("._2zCDG > span:nth-child(1)").click()
        WebDriverWait(self.browser, self.timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR,
                                                                                        "div._1CRb5:nth-child(6) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > span:nth-child(1)")))
        time.sleep(3)
        _exit = self.browser.find_element_by_css_selector(
            "div._1CRb5:nth-child(6) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > span:nth-child(1)")
        _exit.click()
        WebDriverWait(self.browser, self.timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div._1WZqU:nth-child(2)")))
        confirm_exit = self.browser.find_element_by_css_selector("div._1WZqU:nth-child(2)")
        confirm_exit.click()

    # Send Anonymous message
    def send_anon_message(self, phone, text):
        payload = urlencode({"phone": phone, "text": text, "source": "", "data": ""})
        self.browser.get("https://api.whatsapp.com/send?" + payload)
        try:
            Alert(self.browser).accept()
        except:
            print("No alert Found")
        WebDriverWait(self.browser, self.timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#action-button")))
        send_message = self.browser.find_element_by_css_selector("#action-button")
        send_message.click()
        confirm = WebDriverWait(self.browser, self.timeout + 5).until(EC.presence_of_element_located(
            (By.XPATH, "/html/body/div/div/div/div[4]/div/footer/div[1]/div[2]/div/div[2]")))
        confirm.clear()
        confirm.send_keys(text + Keys.ENTER)

    # Check if the message is present in an user chat
    def is_message_present(self, username, message):
        search = self.browser.find_element_by_css_selector(self.search_selector)
        search.send_keys(username + Keys.ENTER)
        search_bar = WebDriverWait(self.browser, self.timeout).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "._1i0-u > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > span:nth-child(1)")))
        search_bar.click()
        message_search = self.browser.find_element_by_css_selector(
            "._1iopp > div:nth-child(1) > label:nth-child(4) > input:nth-child(1)")
        message_search.clear()
        message_search.send_keys(message + Keys.ENTER)
        try:
            WebDriverWait(self.browser, self.timeout).until(EC.presence_of_element_located((By.XPATH,
                                                                                            "/html/body/div[1]/div/div/div[2]/div[3]/span/div/div/div[2]/div/div/div/div/div[1]/div/div/div/div[2]/div[1]/span/span/span")))
            return True
        except TimeoutException:
            return False

    # Get all starred messages
    def get_starred_messages(self, delay=10):
        starred_messages = []
        self.browser.find_element_by_css_selector(
            "div.rAUz7:nth-child(3) > div:nth-child(1) > span:nth-child(1)").click()
        chains = ActionChains(self.browser)
        time.sleep(2)
        for i in range(4):
            chains.send_keys(Keys.ARROW_DOWN)
        chains.send_keys(Keys.ENTER)
        chains.perform()
        time.sleep(delay)
        messages = self.browser.find_elements_by_class_name("MS-DH")
        for message in messages:
            try:
                message_html = message.get_attribute("innerHTML")
                soup = BeautifulSoup(message_html, "html.parser")
                _from = soup.find("span", class_="_1qUQi")["title"]
                to = soup.find("div", class_="copyable-text")["data-pre-plain-text"]
                message_text = soup.find("span", class_="selectable-text invisible-space copyable-text").text
                message.click()
                selector = self.browser.find_element_by_css_selector(
                    "#main > header > div._5SiUq > div._16vzP > div > span")
                title = selector.text
                selector.click()
                time.sleep(2)
                WebDriverWait(self.browser, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR,
                                                                                     "div._14oqx:nth-child(3) > div:nth-child(1) > div:nth-child(1) > span:nth-child(1) > span:nth-child(1)")))
                phone = self.browser.find_element_by_css_selector(
                    "div._14oqx:nth-child(3) > div:nth-child(1) > div:nth-child(1) > span:nth-child(1) > span:nth-child(1)").text
                if title in _from:
                    _from = _from.replace(title, phone)
                else:
                    to = to.replace(title, phone)
                starred_messages.append([_from, to, message_text])
            except Exception as e:
                print("Handled: ", e)
        return starred_messages

    # Getting usernames which has unread messages
    def unread_usernames(self, scrolls=100):
        self.goto_main()
        initial = 10
        usernames = []
        for i in range(0, scrolls):
            self.browser.execute_script("document.getElementById('pane-side').scrollTop={}".format(initial))
            soup = BeautifulSoup(self.browser.page_source, "html.parser")
            for i in soup.find_all("div", class_="eJ0yJ _8Uqu5"):
                if i.find("div", class_="_3dtfX"):
                    username = i.find("div", class_="_3CneP").text
                    usernames.append(username)
            initial += 10
        # Remove duplicates
        usernames = list(set(usernames))
        return usernames

    # Get the driver object
    def get_driver(self):
        return self.browser

    # Get last messages
    def get_last_message_for(self, name):
        messages = list()
        search = self.browser.find_element_by_css_selector(self.search_selector)
        search.send_keys(name + Keys.ENTER)
        time.sleep(3)
        soup = BeautifulSoup(self.browser.page_source, "html.parser")
        for i in soup.find_all("div", class_="message-in"):
            message = i.find("span", class_="selectable-text")
            if message:
                message2 = message.find("span")
                if message2:
                    messages.append(message2.text)
        messages = list(filter(None, messages))
        return messages

    # This method is used to quit the browser
    def quit(self):
        self.browser.quit()

    def do_contains_time(self, text):
        return re.compile(r'(\d|1[0-2]):([0-5]\d) (am|pm)').search(text)

#region unused functions
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