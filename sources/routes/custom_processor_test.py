from consumer import *
from components import *

#yapf: disable
(Timer()
    .process(lambda ex: ex.set_header('to_split', ['a','b','c']))
    .split({
        'from': header('to_split'),
        'to': Any().process(lambda ex: ex.set_body(ex.get_body()+ex.get_body()+ex.get_body())),
        'aggregate': lambda ls: [ex.get_body() for ex in ls]
    })
    .to(log())
)