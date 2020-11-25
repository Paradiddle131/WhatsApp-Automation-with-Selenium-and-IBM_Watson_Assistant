import re
from datetime import datetime


def is_phone_number(text):
    return re.compile(r'\+*9*0*5([0-9]{2})\s?([0-9]{3})\s?([0-9]{2})\s?([0-9]{2})').search(text)


def find_phone_number(text):
    return [x.group() for x in re.finditer(r'\+*9*0*5([0-9]{2})\s?([0-9]{3})\s?([0-9]{2})\s?([0-9]{2})', text)][0]


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


def find_time(text):
    return [x.group() for x in re.finditer(r'(\d|1[0-2]):([0-5]\d) (am|pm)', text)][0]


def find_date(text):
     return [x.group() for x in re.finditer(r'\b\d{1,2}/\d{1,2}/(\d{2}|\d{4})\b', text)][0]


def do_contains_date(text):
    return re.compile(r'\b\d{1,2}/\d{1,2}/(\d{2}|\d{4})\b').search(text)


def str_to_datetime(date_string):
    """Ex: '02/11/2020 2:25 pm'"""
    return datetime.strptime(date_string, '%d/%m/%Y %I:%M %p')
