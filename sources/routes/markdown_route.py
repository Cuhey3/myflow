from consumer import Aiohttp
from components import file, markdown
from evaluator import set_header

(Aiohttp('/markdown')
    .to(file({'file_name': lambda ex: '../public/static/' + ex.get_header('file')}))
    .to(markdown())
    .process(set_header('content-type', 'text/html'))
) #yapf: disable
