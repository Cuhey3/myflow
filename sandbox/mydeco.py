def deco(message):
    def d(func):
        def ireco(*args):
            func(*args)
            print('this is deco message', message)

        return ireco

    return d


@deco('foo')
def foo(*foo_message):
    print('this is foo message', *foo_message)


foo()


def deco_no_param(func):
    def do_func(*args):
        func(*args)
        print('deco')

    return do_func


@deco_no_param
def bar(*args):
    print('bar', *args)


bar()