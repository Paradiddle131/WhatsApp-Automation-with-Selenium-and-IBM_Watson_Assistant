import re
from datetime import datetime


def find_emoji(text):
    return re.compile(r'crossorigin="anonymous"').search(text)


def do_contains_emoji(text):
    return [x.group() for x in re.finditer(r'crossorigin="anonymous"', text)][0]


def is_phone_number(text):
    return re.compile(r'^0*(5)([0-9]{2})\s?([0-9]{3})\s?([0-9]{2})\s?([0-9]{2})$').search(text)


def find_phone_number(text):
    return [x.group() for x in re.finditer(r'^0*(5)([0-9]{2})\s?([0-9]{3})\s?([0-9]{2})\s?([0-9]{2})$', text)][0]


def do_contains_audio(text):
    return re.compile(r'<audio preload=').search(text)


def find_audio(text):
    return [x.group() for x in re.finditer(r'<audio preload=', text)][0]


def do_contains_quoted_image(text):
    return re.compile(
        r'background-image: url\("blob:https://web.whatsapp.com/\w{8}-\w{4}-\w{4}-\w{4}-\w{12}"\);').search(text)


def find_quoted_image(text):
    return [x.group() for x in
            re.finditer(r'background-image: url\("blob:https://web.whatsapp.com/\w{8}-\w{4}-\w{4}-\w{4}-\w{12}"\);',
                        text)][0]


def do_contains_image(text):
    return re.compile(r'blob:https://web.whatsapp.com/\w{8}-\w{4}-\w{4}-\w{4}-\w{12}').search(text)


def find_image(text):
    return [x.group() for x in re.finditer(r'blob:https://web.whatsapp.com/\w{8}-\w{4}-\w{4}-\w{4}-\w{12}', text)][0]


def do_contains_quote(text):
    return re.compile(r'quoted-mention \w{5,6}').search(text)


def find_quote(text):
    return [x.group() for x in re.finditer(r'quoted-mention \w{5,6}', text)][0]


def do_contains_sender(text):
    return re.compile(r'\w{5,6} color-[0-9]{1,2} \w{5,6}').search(text)


def find_sender(text):
    return [x.group() for x in re.finditer(r'\w{5,6} color-[0-9]{1,2} \w{5,6}', text)][0]


def do_contains_time(text):
    return re.compile(r'(\d|1[0-2]):([0-5]\d) (am|pm)').search(text)


def find_time(text):
    return [x.group() for x in re.finditer(r'(\d|1[0-2]):([0-5]\d) (am|pm)', text)][0]


def find_date(text):
     return [x.group() for x in re.finditer(r'\b\d{1,2}/\d{1,2}/(\d{2}|\d{4})\b', text)][0]


def valid_date(date_string):
    try:
        mat = re.match(r'(\d{2})[/.-](\d{2})[/.-](\d{4})$', date_string)
        if mat is not None:
            datetime(*(map(int, mat.groups()[-1::-1])))
            return True
    except ValueError:
        pass
    return False


def str_to_datetime(date_string):
    """Ex: '02/11/2020 2:25 pm'"""
    return datetime.strptime(date_string, '%d/%m/%Y %I:%M %p')
