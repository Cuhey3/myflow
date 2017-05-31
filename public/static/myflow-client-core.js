function Exchange(body, header, element) {
    var self = this;
    self.internalObject = {};
    self.internalObject['body'] = (body || body == '') ? body : {};
    self.internalObject['header'] = header || {};
    self.element = element;
    Exchange.prototype.getBody = function() {
        return self.internalObject['body'];
    };

    Exchange.prototype.setBody = function(body) {
        self.internalObject['body'] = body;
    };

    Exchange.prototype.getHeader = function(key, value) {
        return (key in self.internalObject['header']) ? self.internalObject['header'][key] : value;
    };

    Exchange.prototype.setHeader = function(key, value) {
        self.internalObject['header'][key] = value;
    };

    Exchange.prototype.setHeaders = function(obj) {
        Object.keys(obj).forEach(function(key) {
            self.internalObject['header'][key] = obj[key];
        });
    }

    Exchange.prototype.getHeaders = function() {
        return self.internalObject['header'];
    };

    Exchange.prototype.getElement = function(element) {
        return self.element;
    };

    Exchange.prototype.setElement = function(element) {
        self.element = element;
    };

    Exchange.prototype.update = function(obj) {
        self.internalObject.body = obj.body;
        self.internalObject.header = obj.header;
    };
    Exchange.prototype.toJson = function() {
        return JSON.stringify(self.internalObject);
    };
    Exchange.fromJson = function(jsonText, element) {
        var obj = JSON.parse(jsonText);
        return new Exchange(obj['body'], obj['header'], element);
    }
    Exchange.prototype.setContextName = function(contextName) {
        self.setHeader('__context_name', contextName);
    }
}

function Producer(processor, consumer) {
    this.next_producer = null;
    this.processor = processor;
    this.consumer = consumer;
}

Producer.prototype.to = function(processor) {
    this.next_producer = new Producer(processor, this.consumer);
    return this.next_producer;
};

Producer.prototype.contextId = function(id) {
    this.next_producer = new Producer(function(exchange) {
        exchange.setHeader('__context_id', id);
        return exchange;
    }, this.consumer);
    return this.next_producer;
};

Producer.prototype.contextName = function(name) {
    this.next_producer = new Producer(function(exchange) {
        exchange.setHeader('__context_name', name);
        return exchange;
    }, this.consumer);
    return this.next_producer;
};

Producer.prototype.task = function(processor) {
    this.next_producer = new Producer(processor, this.consumer);
    this.next_producer.isCallbackProcessor = true;
    return this.next_producer;
}
Producer.prototype.getConsumer = function() {
    return this.consumer;
};

Producer.prototype.produce = function(exchange) {
    if (this.isCallbackProcessor) {
        if (this.processor) {
            var next_producer = this.next_producer || new Producer(function() {}, this.consumer);
            this.processor(exchange, function() {
                next_producer.produce(exchange);
            });
        }
    }
    else {
        if (this.processor) {
            exchange = this.processor(exchange);
        }
        if (exchange) {
            if (this.next_producer) {
                exchange = this.next_producer.produce(exchange);
            }
        }
        return exchange;
    }
};

function Routes(routes) {
    this.routes = routes;
}

Routes.prototype.to = function(processor) {
    for (var i = 0; i < this.routes.length; i++) {
        var route = this.routes[i];
        route.next_producer = new Producer(processor, route.consumer)
        this.routes[i] = route.next_producer;
    }
    return this;
};

Routes.prototype.contextName = function(name) {
    for (var i = 0; i < this.routes.length; i++) {
        var route = this.routes[i];
        route.next_producer = new Producer(function(exchange) {
            exchange.setHeader('__context_name', name);
            return exchange;
        }, route.consumer);
        this.routes[i] = route.next_producer;
    }
    return this;
};
