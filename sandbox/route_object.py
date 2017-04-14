import copy


def set_route_obj_func():
    obj = {}

    def route_obj_func(key=None, value=None):
        if value is None:
            if key is None:
                return obj
            else:
                return obj.get(key, None)
        else:
            if key is None:
                raise Exception()
            else:
                obj[key] = value

    return route_obj_func


obj = {'property': set_route_obj_func()}

obj2 = copy.deepcopy(obj)
obj['foo'] = 'bar'
obj['property']('key', 'value')

print(obj)
#=> {'property': <function set_route_obj_func.<locals>.route_obj_func at 0x7fa1320ea598>, 'foo': 'bar'}
print(obj2)
#=> {'property': <function set_route_obj_func.<locals>.route_obj_func at 0x7fa1320ea598>}
print(obj['property']())
#=> {'key': 'value'}
print(obj2['property']())
#=> {'key': 'value'}
