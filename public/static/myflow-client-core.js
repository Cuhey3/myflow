function Exchange(body, header, element) {
    this.internalObject = {};
    this.internalObject['body'] = (body || body == '') ? body : {};
    this.internalObject['header'] = header || {};
    this.element = element;
    Exchange.prototype.getBody = function() {
        return this.internalObject['body'];
    };

    Exchange.prototype.setBody = function(body) {
        this.internalObject['body'] = body;
    };

    Exchange.prototype.getHeader = function(key, value) {
        return (key in this.internalObject['header']) ? this.internalObject['header'][key] : value;
    };

    Exchange.prototype.setHeader = function(key, value) {
        this.internalObject['header'][key] = value;
    };

    Exchange.prototype.getHeaders = function() {
        return this.internalObject['header'];
    };

    Exchange.prototype.getElement = function(element) {
        return this.element;
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

Producer.prototype.getConsumer = function() {
    return this.consumer;
};

Producer.prototype.produce = function(exchange) {
    if (this.processor) {
        exchange = this.processor(exchange);
    }
    if (exchange) {
        if (this.next_producer) {
            exchange = this.next_producer.produce(exchange);
        }
    }
    return exchange;
};
