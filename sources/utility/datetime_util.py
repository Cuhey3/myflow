from settings.antenna_settings import span_to_weekday
import pytz
from datetime import datetime


def calc_date_from_span(item, prev=False):
    span = item.get('span', '')
    if span == '' or span == 'sometime' or span == 'complete':
        next_ = ''
    else:
        from datetime import timedelta
        now = datetime.now(pytz.timezone('Asia/Tokyo'))
        if span == 'daily' or span == 'once' or span == 'priority':
            deltadays = 0 if prev else 1
            next_ = (now + timedelta(days=deltadays)).strftime("%Y/%m/%d")
        elif span.startswith('every_'):
            if prev:
                deltadays = 0
            elif span == 'every_1d':
                deltadays = 2
            elif span == 'every_2d':
                deltadays = 3
            elif span == 'every_3d':
                deltadays = 4
            elif span == 'every_10d':
                deltadays = 10
            next_ = (now + timedelta(days=deltadays)).strftime("%Y/%m/%d")
        elif span.startswith('w_'):
            deltadays = span_to_weekday.get(span) - now.weekday()
            if deltadays < 1:
                deltadays = deltadays + 7
            if prev:
                deltadays = deltadays - 7
            next_ = (now + timedelta(days=deltadays)).strftime("%Y/%m/%d")
        else:
            next_ = ''
    item['next'] = next_
    return item


def now_str(fmt):
    return datetime.now(pytz.timezone('Asia/Tokyo')).strftime(fmt)


def get_now(fmt):
    def now_func(exchange):
        return now_str(fmt)

    return now_func
