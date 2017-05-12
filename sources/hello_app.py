from consumer import Aiohttp
from components import log
from evaluator import set_body

# /helloにアクセスすると、'hello myflow!'と表示される。
# コンソールにも'hello myflow!'とログメッセージが表示される。
(Aiohttp('/hello')  # Aiohttp Consumerはブラウザからのリクエストを受け取り、以下のフローを実行する
 .process(set_body('hello myflow!'))  # Exchangeのbodyにメッセージを設定
 .to(log())  # logコンポーネントを使用
 )
Aiohttp().run()
