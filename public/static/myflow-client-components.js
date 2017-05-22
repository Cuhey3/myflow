function to(routeId, exchange) {
    exchange = exchange || new Exchange();
    exchange = new Endpoints().sendTo(routeId, exchange);
}

function formToExchange(formElement) {
    return function(exchange) {
        exchange = exchange || new Exchange();
        toArray(formElement.querySelectorAll('[name]'))
            .forEach(function(element) {
                exchange.setHeader([element.name], element.value);
            });
        return exchange;
    };
}

function exchangeToForm(formElement) {
    return function(exchange) {
        toArray(formElement.querySelectorAll('[name]'))
            .forEach(function(element) {
                var value = exchange.getHeader(element.name);
                if (element.tagName.toLowerCase() == 'select') {
                    element.selectedIndex = value;
                }
                else {
                    element.value = value;
                }
            });
        return exchange;
    }
}

function log(params) {
    params = params || {};
    var logName = 'log';
    if (params['name']) {
        logName += ':' + params['name'];
    }
    var showBody = params['body'] || true;
    var showHeader = params['header'] || false;
    return function(exchange) {
        if (showBody) {
            console.log(logName, exchange.getBody());
        }
        if (showHeader) {
            console.log(logName, exchange.getHeaders());
        }
        return exchange;
    };
}

function request(uri) {
    return function(exchange) {
        var xhr = new XMLHttpRequest();
        var url = uri;
        xhr.open("POST", url, true);
        xhr.setRequestHeader("Content-type", "application/json");
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                exchange.update(JSON.parse(xhr.responseText));
                new RequestReply().sendTo(uri, exchange);
            }
        };
        console.log(exchange.toJson())
        xhr.send(exchange.toJson());
    }
}

function buttonEnable(elements, bool) {
    if (!elements.forEach) {
        elements = [elements];
    }
    var disable = bool === false;
    return function(exchange) {
        elements.forEach(function(element) {
            element.disabled = disable
        });
        return exchange;
    }
}

function pageReload() {
    return function(exchange) {
        document.location.reload();
    }
}

function pageTop() {
    return function(exchange) {
        window.scrollTo(0, 0);
        return exchange;
    }
}
