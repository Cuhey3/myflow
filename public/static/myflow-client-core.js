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
        this.element = element;
    };

    Exchange.prototype.update = function(obj) {
        this.internalObject = obj
    }
    Exchange.prototype.toJson = function() {
        return JSON.stringify(this.internalObject);
    };
    Exchange.fromJson = function(jsonText, element) {
        obj = JSON.parse(jsonText);
        return new Exchange(obj['body'], obj['header'], element);
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
