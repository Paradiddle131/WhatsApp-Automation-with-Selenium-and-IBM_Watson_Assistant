import re
import datetime


def is_phone_number(text):
    return re.compile(r'^(5)([0-9]{2})\s?([0-9]{3})\s?([0-9]{2})\s?([0-9]{2})$').search(text)


def find_phone_number(text):
    return [x.group() for x in re.finditer(r'^(5)([0-9]{2})\s?([0-9]{3})\s?([0-9]{2})\s?([0-9]{2})$', text)][0]


def do_contains_audio(text):
    return re.compile(r'<audio preload=').search(text)


def find_audio(text):
    return [x.group() for x in re.finditer(r'<audio preload=', text)][0]


def do_contains_image(text):
    return re.compile(r'blob:https://web.whatsapp.com/\w{8}-\w{4}-\w{4}-\w{4}-\w{12}').search(text)


def find_image(text):
    return [x.group() for x in re.finditer(r'blob:https://web.whatsapp.com/\w{8}-\w{4}-\w{4}-\w{4}-\w{12}', text)][0]


def do_contains_sender(text):
    return re.compile(r'\w{5,6} color-[0-9]{1,2} \w{5,6}').search(text)


def find_sender(text):
    return [x.group() for x in re.finditer(r'\w{5,6} color-[0-9]{1,2} \w{5,6}', text)][0]


def do_contains_time(text):
    return re.compile(r'(\d|1[0-2]):([0-5]\d) (am|pm)').search(text)


def find_time(text):
    return [x.group() for x in re.finditer(r'(\d|1[0-2]):([0-5]\d) (am|pm)', text)][0]


def valid_date(datestring):
    try:
        mat = re.match(r'(\d{2})[/.-](\d{2})[/.-](\d{4})$', datestring)
        if mat is not None:
            datetime.datetime(*(map(int, mat.groups()[-1::-1])))
            return True
    except ValueError:
        pass
    return False