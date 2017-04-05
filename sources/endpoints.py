class Endpoints:
    _instance = None

    class EndpointsInner:
        def __init__(self):
            self.endpoints_dict = {}

        def put_endpoint(self, endpoint_name, producer):
            self.endpoints_dict[endpoint_name] = producer

        def get_endpoint(self, endpoint_name):
            return self.endpoints_dict[endpoint_name]

        from exchange import Exchange

        async def send_to(self, endpoint_uri, exchange=Exchange()):
            return await self.endpoints_dict[endpoint_uri].produce(exchange)

    def __init__(self):
        if Endpoints._instance is None:
            Endpoints._instance = Endpoints.EndpointsInner()

    def __getattr__(self, attr):
        return getattr(self._instance, attr)
