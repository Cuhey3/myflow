class Exchange:
    def __init__(self, body={}, header={}):
        self.body = body
        assert isinstance(header, dict), 'exchange header must be dict.'
        self.header = header
        self.children = []
        self.parent = None

    def get_body(self):
        return self.body

    def set_body(self, body):
        self.body = body

    def get_header(self, key, value=None):
        return self.header.get(key, value)

    def set_header(self, key, value):
        self.header[key] = value

    def get_headers(self):
        return self.header

    def create_child(self, exchange=None):
        if exchange is None:
            child = Exchange()
        else:
            child = exchange

        def access_parent():
            return self

        child.parent = access_parent
        return child
