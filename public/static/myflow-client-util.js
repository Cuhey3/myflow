function byid(id) {
    return document.getElementById(id);
}

function element(tagName) {
    return document.createElement(tagName);
}

function selectAll(selector) {
    var elements = document.querySelectorAll(selector);
    return toArray(elements);
}

function getOr(object, attr, value) {
    if (object && attr in object) {
        return object[attr];
    }
    else {
        return value;
    }
}

function Options(selector) {
    this.options = toArray(document.querySelectorAll((selector || 'option')));
    Options.prototype.getIndexByText = function(text) {
        var result = -1
        this.options.forEach(function(option, index) {
            if (option.innerText == text) {
                result = index;
            }
        })
        return result;
    }
}

function toArray(nodeList) {
    if (nodeList.forEach) {
        return nodeList;
    }
    else {
        var result = [];
        for (var i = 0; i < nodeList.length; i++) {
            result.push(nodeList[i])
        }
        return result;
    }
}

function collectNthChild(elements, selector, nth) {
    var result = []
    if (nth == 0) {
        toArray(elements).forEach(function(element) {
            result.push(element.querySelector(selector));
        });
    }
    else {
        toArray(elements).forEach(function(element) {
            result.push(element.querySelectorAll(selector)[nth]);
        });
    }
    return result;
}

function Mapper(mapperObject) {
    this.mapperObject = mapperObject;
    Mapper.prototype.get = function(key) {
        return this.mapperObject[key]();
    }
    var self = this;
    Mapper.prototype.updateExchange = function(exchange, keys) {
        if (!Array.isArray(keys)) {
            keys = [keys];
        }
        keys.forEach(function(key) {
            exchange.setHeader(key, self.get(key));
        });
        return exchange;
    };
}

function MapperCreator(mappingFunc, tagName) {
    MapperCreator.prototype.create = function(exchange) {
        var element = exchange.getElement();
        while (element.tagName.toLowerCase() !== tagName) {
            element = element.parentNode;
        }
        return new Mapper(mappingFunc(element));
    }
}
