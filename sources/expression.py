def body(key=None):
    def processor(exchange):
        return dig_dict(key, exchange.get_body())

    return processor


def header(key=None):
    def processor(exchange):
        return dig_dict(key, exchange.get_headers())

    return processor


def dig_dict(key, value):
    if key is None:
        return value
    assert isinstance(
        value, dict), 'key is not None, but ' + str(value) + ' is not dict.'
    if '.' not in key:
        return value.get(key, None)
    else:
        for k in key.split('.'):
            if k in value:
                value = value[k]
            else:
                value = None
                break
        return value
