def expression_to_value(expression, exchange):
    if isinstance(expression, dict):
        result = {}
        for k, v in expression:
            e_k = expression_to_value(k, exchange)
            e_v = expression_to_value(v, exchange)
            result[e_k] = e_v
        return result
    elif isinstance(expression, list):
        result = []
        for v in expression:
            result.append(expression_to_value(v, exchange))
        return result
    elif isinstance(expression, tuple):
        result = []
        for v in expression:
            result.append(expression_to_value(v, exchange))
        return tuple(result)
    elif callable(expression):
        return expression(exchange)
    else:
        return expression
