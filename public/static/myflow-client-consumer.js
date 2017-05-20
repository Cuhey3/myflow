function Consumer(processor, consumer) {
    Producer.call(this, processor, consumer);
}

Consumer.prototype = Object.create(Producer.prototype, {
    value: {
        constructor: Consumer
    }
});

Consumer.prototype.consume = function(exchange) {
    return this.produce(exchange);
};

function Endpoints() {
    if (Endpoints.dict == undefined) {
        Endpoints.dict = {};
    }
    Endpoints.prototype.putEndpoint = function(endpointName, producer) {
        Endpoints.dict[endpointName] = producer;
    };
    Endpoints.prototype.getEndpoint = function(endpointName) {
        return Endpoints.dict[endpointName];
    };
    Endpoints.prototype.sendTo = function(endpointName, exchange) {
        exchange = exchange || new Exchange();
        return this.getEndpoint(endpointName).produce(exchange);
    };
}

function RequestReply() {
    if (RequestReply.dict == undefined) {
        RequestReply.dict = {};
    }
    RequestReply.prototype.putHandle = function(handleName, producer) {
        console.log('put', handleName);
        RequestReply.dict[handleName] = producer;
    };
    RequestReply.prototype.getHandle = function(handleName) {
        console.log('get', handleName, RequestReply.dict);
        return RequestReply.dict[handleName];
    };
    RequestReply.prototype.sendTo = function(handleName, exchange) {
        exchange = exchange || new Exchange();
        return this.getHandle(handleName).produce(exchange);
    };
}

function EventGroup() {
    if (EventGroup.dict == undefined) {
        EventGroup.dict = {};
    }
    EventGroup.prototype.putGroupEvent = function(groupName, eventName, func) {
        var group = EventGroup.dict[groupName] || {};
        group[eventName] = func;
        EventGroup.dict[groupName] = group;
    };
    EventGroup.prototype.getGroupEvents = function(groupName) {
        return EventGroup.dict[groupName];
    };
    EventGroup.prototype.setEvent = function(element, groupName) {
        var dict = this.getGroupEvents(groupName) || {};
        var keys = Object.keys(dict);
        for (var i = 0; i < keys.length; i++) {
            var key = keys[i];
            element[key] = dict[key];
        }
    };
}

function RouteId(routeId) {
    Consumer.call(this, null, this);
    new Endpoints().putEndpoint(routeId, this);
}

RouteId.prototype = Object.create(Consumer.prototype, {
    value: {
        constructor: RouteId
    }
});

function Reply(handleName) {
    Consumer.call(this, null, this);
    new RequestReply().putHandle(handleName, this);
}

Reply.prototype = Object.create(Consumer.prototype, {
    value: {
        constructor: Reply
    }
});

function Event(eventName, elements, groupName) {
    Consumer.call(this, null, this);
    var consumer = this;
    if (!elements.forEach) {
        elements = [elements];
    }
    var func = function() {
                consumer.consume(new Exchange({}, {}, this));
    };
    elements.forEach(function(element){
        element[eventName] = func;
    });
    if (groupName) {
        new EventGroup().putGroupEvent(groupName, eventName, func);
    }
}

Event.prototype = Object.create(Consumer.prototype, {
    value: {
        constructor: Event
    }
});
