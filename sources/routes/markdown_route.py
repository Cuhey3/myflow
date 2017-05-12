from consumer import Aiohttp
from components import file, markdown, jinja2
from evaluator import body, set_header

(Aiohttp('/markdown')
    .to(file({'file_name': lambda ex: '../public/static/' + ex.get_header('file')}))
    .to(markdown())
    .to(jinja2({
        'template': 'markdown.html',
        'data': {
            'markdown_body': body()
        }
    }))
) #yapf: disable

Aiohttp().application().router.add_static(
    prefix='/public/static', path='../public/static')
