※このReadmeは書きかけです。


# Myflow（仮）
Myflow（仮）はPython用のデータフローフレームワークです。

## 概要

- [Apache Camel](https://camel.apache.org)ライクにワンライナーで（一つの文で）データフローを定義
- asyncio.coroutineベースで非同期、軽量に実行可能
- 各種Pythonライブラリのラッパーを記述することでデータフローに組み込むことが可能
    - 実装済みラッパー: aiohttp, jinja2, markdown, cachetools, beautifulsoup
- [Enterprise Integration Patterns](http://camel.apache.org/enterprise-integration-patterns.html)の多くを実装。
し、複雑なデータの分岐、集約、イベント処理が可能
<br>
<br>
## フレームワークの構成要素

### Exchange
Exchangeはデータフロー上に流されるデータの入れ物です。
実体はdictで、body(object)とheader(dict)から構成されます。

### Processor
ProcessorはExchangeを引数に取り、Exchangeを返すcoroutine（asyncな関数）です。
Processorを順序どおりに実行することでMyflowはデータフローを実装します。

### Component
パラメータを受け取りProcessorを返す関数です。

### Producer
Processorは単なる関数ですので、Processor同士を連結するためにProducerクラスでラップされます。

### Consumer
フロー開始の基点となる、特別なProducerです。

## Hello World


```python:hello_app.py

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


```

