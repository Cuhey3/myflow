url = 'a/b/c/d/e'
foo = lambda url: ('{}{}'.format(*(url.split('/')[i] for i in [0, 3])))

print(foo(url))

url2 = 'a/b/c/d/e?f'

print(url2.split('?')[0].split('/'))

url3 = 'https://ameblo.jp/kanataimi/entrylist-1.html'

print([
    '{}entrylist-{}.html'.format('foo', i)
    for i in range(1, int(url3.split('entrylist-')[1].split('.')[0]) + 2)
])
