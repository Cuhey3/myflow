if (!String.prototype.startsWith) {
    String.prototype.startsWith = function(searchString, position) {
        position = position || 0;
        return this.substr(position, searchString.length) === searchString;
    };
}

Number.isInteger = Number.isInteger || function(value) {
    return typeof value === "number" &&
        isFinite(value) &&
        Math.floor(value) === value;
};

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

function Options(element) {
    this.options = toArray((element || document).querySelectorAll('option'));
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

function CookieObject() {
    if (!CookieObject.obj) {
        console.log('cookie object initialized.')
        if (document.cookie && document.cookie.startsWith('%7B')) {
            CookieObject.obj = JSON.parse(decodeURI(document.cookie.split(' ')[0]));
        }
        else {
            CookieObject.obj = {};
        }
    }
    CookieObject.prototype.set = function(key, value) {
        CookieObject.obj[key] = value;
        console.log('cookie set', CookieObject.obj)
        document.cookie = encodeURI(JSON.stringify(CookieObject.obj)) + ' ;max-age=31536000';
        console.log(encodeURI(JSON.stringify(CookieObject.obj)))
    }
    CookieObject.prototype.get = function(key, defaultValue) {
        if (key in CookieObject.obj) {
            console.log('get from cookie', CookieObject.obj)
            return CookieObject.obj[key];
        }
        else {
            if (defaultValue) {
                this.set(key, defaultValue);
            }
            return defaultValue;
        }
    }
}

function ElementReader(readerCreator) {
    var self = this;
    self.readerCreator = readerCreator;
    self.functionObject = {};

    ElementReader.prototype.create = function(exchange) {
        var reader = new ElementReader(self.readerCreator); //違和感
        reader.functionObject = self.readerCreator(exchange);
        reader.exchange = exchange;
        return reader;
    };
    ElementReader.prototype.read = function(key) {
        return self.functionObject[key]();
    };
    ElementReader.prototype.updateExchange = function(keys) {
        if (!keys) {
            keys = Object.keys(self.functionObject);
        }
        else if (!Array.isArray(keys)) {
            keys = [keys];
        }
        keys.forEach(function(key) {
            self.exchange.setHeader(key, self.read(key));
        });
    };
}
