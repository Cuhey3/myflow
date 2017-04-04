class Exchange:
    def __init__(self, body={}, header={}):
        self.body = body
        assert isinstance(header, dict), 'exchange header must be dict.'
        self.header = header

    def get_body(self):
        return self.body

    def set_body(self, body):
        self.body = body

    def get_header(self, key):
        return self.header.get(key, None)

    def set_header(self, key, value):
        self.header[key] = value

    def get_headers(self):
        return self.header
