function direct(routeId) {
    return function(exchange) {
        exchange = exchange || new Exchange();
        exchange = new Endpoints().sendTo(routeId, exchange);
        return exchange;
    }
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
                var value = exchange.getHeader(element.name, '');
                if (element.tagName.toLowerCase() == 'select') {
                    element.selectedIndex = value || 0;
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
            console.log(logName, 'body', exchange.getBody());
        }
        if (showHeader) {
            console.log(logName, 'header', exchange.getHeaders());
        }
        return exchange;
    };
}

function request(uri, headers) {
    return function(exchange, func) {
        if (headers) {
            exchange.setHeaders(headers);
        }
        var xhr = new XMLHttpRequest();
        var url = uri;
        xhr.open("POST", url, true);
        xhr.setRequestHeader("Content-type", "application/json");
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                exchange.update(JSON.parse(xhr.responseText));
                func()
            }
        };
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

function delay(t) {
    if (Number.isInteger(t)) {
        t = 0;
    }
    t *= 1000
    return function(exchange, func) {
        window.setTimeout(func, t);
    }
}


function cookie(action, key, value) {
    if (action === 'get') {
        return function(exchange) {
            var v = new CookieObject().get(key, value)
            exchange.setHeader(key, v);
            return exchange
        }
    }
    else if (action === 'set') {
        return function(exchange) {
            var v = exchange.getHeader(key, value);
            new CookieObject().set(key, v);
            return exchange
        }

    }
    else {
        return function(exchange) {
            return exchange
        }
    }
}

function modal(modalElement, action) {
    if (action === 'open') {
        return function(exchange) {
            modalElement.style.visibility = 'visible';
            toArray(modalElement.querySelectorAll('[data-header],[data-header-from]'))
                .forEach(function(element) {
                    var key = element.getAttribute('data-header') || element.getAttribute('data-header-from');
                    var tagName = element.tagName.toLocaleLowerCase();
                    var value = exchange.getHeader(key, '');
                    if (tagName === 'input' || tagName === 'textarea' || tagName === 'select') {
                        element.value = value;
                    }
                    else {
                        element.textContent = value;
                    }
                });
            return exchange;
        }
    }
    else if (action === 'close') {
        return function(exchange) {
            toArray(modalElement.querySelectorAll('[data-header], [data-header-to]'))
                .forEach(function(element) {
                    var key = element.getAttribute('data-header') || element.getAttribute('data-header-to');
                    var tagName = element.tagName.toLocaleLowerCase();
                    if (tagName === 'input' || tagName === 'textarea' || tagName === 'select') {
                        exchange.setHeader(key, element.value);
                    }
                    else {
                        exchange.setHeader(key, element.textContent);
                    }
                });
            modalElement.style.visibility = 'hidden';
            return exchange;
        }
    }
}

function loadElement(element, headers) {

    return function(exchange) {
        if (headers) {
            exchange.setHeaders(headers);
        }
        toArray(element.querySelectorAll('[data-header], [data-header-to]')).forEach(function(node) {
            var tagName = node.tagName.toLocaleLowerCase();
            var key = node.getAttribute('data-header') || node.getAttribute('data-header-to')
            if (tagName === 'input' || tagName === 'textarea' || tagName === 'select') {
                exchange.setHeader(key, node.value);
            }
            else {
                exchange.setHeader(key, node.textContent);
            }
        })
        return exchange;
    }
}
