import unittest
from consumer import Any, RouteId, To, Composer
from exchange import Exchange
from components import direct, cache, log, composer, file, markdown
from evaluator import *


class Mytest(unittest.TestCase):
    def test_exchange(self):
        ((Any()
            .assert_('test_exchange_0', self.assertEqual, body(), 'foo')
            .process(set_body(True))
            .assert_('test_exchange_1', self.assertTrue, body())
            .process(set_body({'dict': 'dddd'}))
            .assert_('test_exchange_2', self.assertEqual, body('dict'), 'dddd')
            .process(set_header('foo', 'bar'))
            .assert_('test_exchange_3', self.assertEqual, header('foo'), 'bar'))
            .process(set_header('boo', {'bar': 'yay'}))
            .assert_('test_exchange_4', self.assertEqual, header('boo.bar'), 'yay')
            .process(set_header('poyo', get_body()))
            .assert_('test_exchange_5', self.assertEqual, header('poyo'), {'dict': 'dddd'})
        ).send_to_sync(Exchange('foo')) #yapf: disable

    def test_direct(self):
        (RouteId('test_direct')
            .process(set_body('test_direct_success'))) #yapf: disable
        ((Any()
            .assert_('test_direct_0', self.assertEqual, body(), 'boo')
            .to(direct('test_direct'))
            .assert_('test_direct_1', self.assertEqual, body(), 'test_direct_success'))
        ).send_to_sync(Exchange('boo')) #yapf: disable

        (RouteId('test_direct_blank'))
        ((Any()
            .to(direct('test_direct_blank'))
            .assert_('test_direct_blank_1', self.assertEqual, body(), 'bar'))
        ).send_to_sync(Exchange('bar'))  #yapf: disable

        (RouteId('test_direct_nest_first').to(direct('test_direct_nest_second'))) #yapf: disable
        (RouteId('test_direct_nest_second').to(direct('test_direct_nest_third'))) #yapf: disable
        (RouteId('test_direct_nest_third').process(set_body('nest_success'))) #yapf: disable
        ((Any().to(direct('test_direct_nest_first'))
            .assert_('test_direct_nest_0', self.assertEqual, body(), 'nest_success'))
        ).send_to_sync() #yapf: disable

    def test_cache(self):
        from cachetools import LRUCache
        (RouteId('test_cache_request')
            .process(set_header('process_flag', True))
            .process(set_body('response'))) #yapf: disable
        route = (Any().to(cache({
                'to': To(direct('test_cache_request')),
                'keys': [header('key')],
                'cache_object': LRUCache(maxsize=1000)
            })))#yapf: disable

        ex1 = route.send_to_sync(Exchange(header={'key': 'foo'}))
        self.assertEqual(ex1.get_body(), 'response')
        self.assertEqual(ex1.get_header('process_flag'), True)
        ex2 = route.send_to_sync(Exchange(header={'key': 'foo'}))
        self.assertEqual(ex2.get_body(), 'response')
        self.assertEqual(ex2.get_header('process_flag'), None)
        ex3 = route.send_to_sync(Exchange(header={'key': 'bar'}))
        self.assertEqual(ex3.get_body(), 'response')
        self.assertEqual(ex3.get_header('process_flag'), True)

    def test_split(self):
        send_body = [1, True, 3, 'foo']
        part_func = lambda sp: str(sp * 3)
        aggregated_body = ''.join([part_func(sp) for sp in send_body])
        print('aggregated_body', aggregated_body)
        (Any()
            .split({
                'from': body(),
                'to': Any().process(lambda ex: ex.set_body(part_func(ex.get_body())))
            })
            .assert_('test_split_no_aggregate_1', self.assertEqual, body(), send_body)
            .split({
                'from': body(),
                'to': Any().process(lambda ex: ex.set_body(part_func(ex.get_body()))),
                'aggregate': lambda gatherd: ''.join([ex.get_body() for ex in gatherd])
            })
            .assert_('test_split_aggregate_1', self.assertEqual, body(), aggregated_body)
        ).send_to_sync(Exchange(send_body)) #yapf: disable

    def test_sleep(self):
        from datetime import datetime
        sleep_time = 0.1
        now = datetime.now()
        (Any().sleep(sleep_time)).send_to_sync()
        self.assertTrue(sleep_time * 1000000 <=
                        (datetime.now() - now).microseconds)

    def test_composer(self):
        (Composer({
            'id': 'test_composer',
            'from': ['source_1', 'source_2', 'source_3'],
            'compose':
                lambda exchanges: ' and '.join([exchange.get_body() for exchange in exchanges]),
            'wait_for_all': True,
        }).assert_('test_composer_1', self.assertEqual, body(),'foo and bar and wao'))

        #yapf: disable
        (To(composer('test_composer', 'source_1'))).send_to_sync(Exchange('foo'))
        (To(composer('test_composer', 'source_2'))).send_to_sync(Exchange('bar'))
        (To(composer('test_composer', 'source_3'))).send_to_sync(Exchange('wao'))

    def test_file_and_markdown(self):
        (Any()
            .to(file({
                'mode': 'read',
                'file_name': '../public/static/test_file.md'
            }))
            .assert_('test_file_and_markdown_1', self.assertEqual, body(), '# this is markdown file')
            .to(markdown())
            .assert_('test_file_and_markdown_2', self.assertEqual, body(), '<h1>this is markdown file</h1>')
        ).send_to_sync() #yapf: disalbe