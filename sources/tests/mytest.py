import unittest
from consumer import Any, RouteId, To
from exchange import Exchange
from components import direct, cache, log
from evaluator import body, header


class Mytest(unittest.TestCase):
    def test_exchange(self):
        ((Any()
            .assert_('test_exchange_0', self.assertEqual, body(), 'foo')
            .process(lambda ex: ex.set_body(True))
            .assert_('test_exchange_1', self.assertTrue, body())
            .process(lambda ex: ex.set_body({'dict': 'dddd'}))
            .assert_('test_exchange_2', self.assertEqual, body('dict'), 'dddd')
            .process(lambda ex: ex.set_header('foo', 'bar'))
            .assert_('test_exchange_3', self.assertEqual, header('foo'), 'bar'))
            .process(lambda ex: ex.set_header('boo', {'bar': 'yay'}))
            .assert_('test_exchange_4', self.assertEqual, header('boo.bar'), 'yay')
        ).send_to_sync(Exchange('foo')) #yapf: disable

    def test_direct(self):
        (RouteId('test_direct')
            .process(lambda ex: ex.set_body('test_direct_success'))) #yapf: disable
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
        (RouteId('test_direct_nest_third').process(lambda ex: ex.set_body('nest_success'))) #yapf: disable
        ((Any().to(direct('test_direct_nest_first'))
            .assert_('test_direct_nest_0', self.assertEqual, body(), 'nest_success'))
        ).send_to_sync() #yapf: disable

    def test_cache(self):
        from cachetools import LRUCache
        (RouteId('test_cache_request')
            .process(lambda ex: ex.set_header('process_flag', True))
            .process(lambda ex: ex.set_body('response'))) #yapf: disable
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
