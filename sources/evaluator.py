def body(key=None):
    def evaluater(exchange):
        return __dig_dict(key, exchange.get_body())

    return evaluater


def header(key=None):
    def evaluater(exchange):
        return __dig_dict(key, exchange.get_headers())

    return evaluater


def exists(func):
    def evaluater(exchange):
        if callable(func):
            return func(exchange) is not None
        else:
            return func is not None

    return evaluater


# header('foo.bar') => value
def __dig_dict(key, value):
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


# [body(), header('foo.bar')] => [value1, value2]
def evaluate_expression(expression, exchange):
    if isinstance(expression, dict):
        result = {}
        for k, v in expression.items():
            e_k = evaluate_expression(k, exchange)
            e_v = evaluate_expression(v, exchange)
            result[e_k] = e_v
        return result
    elif isinstance(expression, list):
        result = []
        for v in expression:
            result.append(evaluate_expression(v, exchange))
        return result
    elif isinstance(expression, tuple):
        result = []
        for v in expression:
            result.append(evaluate_expression(v, exchange))
        return tuple(result)
    elif callable(expression):
        return expression(exchange)
    else:
        return expression
