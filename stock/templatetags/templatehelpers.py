from django import template
import datetime
from django.utils.timezone import localtime

register = template.Library()

@register.simple_tag
def my_url(value, field_name, urlencode=None):
    url = '?{}={}'.format(field_name, value)
    if urlencode:
        querystring = urlencode.split('&')
        filtered_querystring = filter(lambda p: p.split('=')[0] != field_name, querystring)
        encoded_querystring = '&'.join(filtered_querystring)
        url = '{}&{}'.format(url, encoded_querystring)
    return url

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, None)

@register.filter
def format_datetime(value):
    if isinstance(value, datetime.datetime):
        if value.time() == datetime.time(0, 0, 0):
            return localtime(value).strftime("%d/%m/%Y")
        return localtime(value).strftime("%d/%m/%Y %H:%M")
    return value

@register.filter
def first_chars(value, num=2):
    return value[:num] if value else ''