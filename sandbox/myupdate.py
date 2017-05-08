class Foo():
    def __init__(self, obj):
        self.foo = obj

    def update(self, foo):
        if self.foo != foo.foo:
            print('update...', 'from:', self.foo, 'to', foo.foo)
            self.foo = foo.foo


foo = Foo({})
foo.update(Foo({'boo': 'bar'}))
print(foo.foo)