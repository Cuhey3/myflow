class Endpoints:
    _instance = None

    class EndpointsInner:
        def __init__(self):
            self.endpoints_dict = {}

        def put_endpoint(self, endpoint_name, producer):
            assert endpoint_name not in self.endpoints_dict, 'route: ' + endpoint_name + ' is already exist.'
            self.endpoints_dict[endpoint_name] = producer

        def get_endpoint(self, endpoint_name):
            return self.endpoints_dict[endpoint_name]

        from exchange import Exchange

        def send_to(self, endpoint_uri, exchange=Exchange()):
            return self.endpoints_dict[endpoint_uri].produce(exchange)

    def __init__(self):
        if Endpoints._instance is None:
            Endpoints._instance = Endpoints.EndpointsInner()

    def __getattr__(self, attr):
        return getattr(self._instance, attr)
