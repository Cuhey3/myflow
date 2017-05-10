import unittest
from consumer import Any
from exchange import Exchange
from components import log
from evaluator import body, header


class Mytest(unittest.TestCase):
    def test_mytest(self):
        #yapf: disable
        ((Any().assert_('check0', self.assertEqual, body(), 'foo')
            .process(lambda ex: ex.set_body(True))
            .assert_('check1', self.assertTrue, body())
            .process(lambda ex: ex.set_header('foo', 'bar'))
            .assert_('check2', self.assertEqual, header('foo'), 'bar'))
        ).send_to_sync(Exchange('foo'))
