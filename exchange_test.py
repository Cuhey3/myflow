from sources.exchange import Exchange

ex1 = Exchange()
ex1_1 = ex1.create_child()
ex1_2 = ex1.create_child()
ex1_1.parent().set_header('foo', 'bar')
ex1_2.parent().set_header('bar', 'wao')
print(ex1.get_headers())
print(ex1_1.parent().get_headers())
print(ex1_2.parent().get_headers())

print(ex1.children)
