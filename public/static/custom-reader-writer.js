var trReader = new ElementReader(function(exchange) {
    var element = exchange.getElement();
    while (element.tagName.toLowerCase() !== 'tr') {
        element = element.parentNode;
    }
    var thtdElements = element.querySelectorAll('th, td');
    return {
        'id': function() {
            return thtdElements[0].innerText;
        },
        'past': function() {
            return thtdElements[3].textContent;
        },
        'next': function() {
            return thtdElements[4].textContent;
        },
        'name': function() {
            return thtdElements[5].children[0].innerText;
        },
        'url': function() {
            return getOr(element.querySelector('.external'), 'href', '');
        },
        'memo': function() {
            return thtdElements[6].innerText;
        },
        'span': function() {
            return options.getIndexByText(thtdElements[1].innerHTML);
        },
        'current': function() {
            return thtdElements[4].innerText <= env.now;
        },
        'future': function() {
            return thtdElements[4].innerText > env.now;
        },
        'finish': function() {
            return (thtdElements[1].innerText === '一度' || thtdElements[1].innerText === '優先') && thtdElements[4].innerText <= env.now;
        },
        'completed': function() {
            return thtdElements[1].innerText === '完了';
        },
    }
});
