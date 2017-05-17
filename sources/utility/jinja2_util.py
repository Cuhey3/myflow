from settings.antenna_settings import span_option
import pytz
from datetime import datetime


def create_util():

    span_key_text_dict = {dic['key']: dic['text'] for dic in span_option}
    now = datetime.now(pytz.timezone('Asia/Tokyo')).strftime("%Y/%m/%d %H:%M")

    def span_key_to_text(key):
        return span_key_text_dict.get(key, '')

    def is_future(item):
        return item.get('next', '') > now

    def is_current(item):
        return item.get('next', '') <= now

    def is_future_uncomplete(item):
        return is_future(item) and item.get('span') != 'complete'

    def is_current_uncomplete(item):
        return is_current(item) and item.get('span') != 'complete'

    def count(items, func):
        return len([item for item in items if func(item)])

    return {
        'span_key_to_text': span_key_to_text,
        'is_future': is_future,
        'is_current': is_current,
        'is_future_uncomplete': is_future_uncomplete,
        'is_current_uncomplete': is_current_uncomplete,
        'count': count
    }
