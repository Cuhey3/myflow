def ret_func(func_1):
    def func(exchange):
        func_1(exchange)
        return exchange

    return func


def compose(*functions):
    def func(exchange):
        for f in functions:
            exchange = ret_func(f)(exchange)
        return exchange

    return func


def compose_logic(params):
    composed = compose(lambda exchange: exchange,
                       lambda exchange: print('params:', params))
    if params['body']:
        composed = compose(composed, lambda ex: print(ex['body']))
    if params['header']:
        composed = compose(composed, lambda ex: print(ex['header']))
    return composed


exchange = {'body': 'this is body', 'header': 'this is header'}

print('exchange:', exchange)
compose_logic({'body': True, 'header': True})(exchange)
compose_logic({'body': True, 'header': False})(exchange)
compose_logic({'body': False, 'header': True})(exchange)
compose_logic({'body': False, 'header': False})(exchange)
