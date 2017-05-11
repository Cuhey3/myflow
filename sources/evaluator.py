def body(key=None):
    def evaluater(exchange):
        return __dig_dict(key, exchange.get_body())

    return evaluater


def get_body():
    def func(exchange):
        return exchange.get_body()

    return func


def set_body(expression):
    if callable(expression):

        def func(exchange):
            exchange.set_body(expression(exchange))

        return func
    else:

        def func(exchange):
            exchange.set_body(expression)

        return func


def header(key=None):
    def evaluater(exchange):
        return __dig_dict(key, exchange.get_headers())

    return evaluater


def get_header(header_key):
    def func(exchange):
        return exchange.get_header(header_key)

    return func


def set_header(header_key, expression):
    if callable(expression):

        def func(exchange):
            exchange.set_header(header_key, expression(exchange))

        return func
    else:

        def func(exchange):
            exchange.set_header(header_key, expression)

        return func


def exists(expression):
    def evaluater(exchange):
        if callable(expression):
            return expression(exchange) is not None
        else:
            return expression is not None

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
        return {
            evaluate_expression(k, exchange): evaluate_expression(v, exchange)
            for k, v in expression.items()
        }
    elif isinstance(expression, list):
        return [evaluate_expression(v, exchange) for v in expression]
    elif isinstance(expression, tuple):
        return tuple([evaluate_expression(v, exchange) for v in expression])
    elif callable(expression):
        return expression(exchange)
    else:
        return expression
