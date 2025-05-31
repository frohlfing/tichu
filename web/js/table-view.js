const TableView = (() => {
    const tableViewDiv = document.getElementById('table-view');

    function init() {
    }

    function hide() {
        tableViewDiv.style.display = 'none';
    }

    function show() {
        tableViewDiv.style.display = 'flex';
    }

    return {
        init,
        hide,
        show
    };
})();