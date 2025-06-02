const UiManager = (() => {
    // Referenzen zu den View-Modulen, werden in main.js gesetzt
    let currentLobbyView = null;
    let currentTableView = null;

    function init(lobbyViewModule, tableViewModule) {
        currentLobbyView = lobbyViewModule;
        currentTableView = tableViewModule;
    }

    function showLobby() {
        if (currentTableView) {
            currentTableView.hide();
        }
        if (currentLobbyView) {
            currentLobbyView.show();
        }
    }

    function showTable() {
        if (currentLobbyView) {
            currentLobbyView.hide();
        }
        if (currentTableView) {
            currentTableView.show();
        }
    }

    return {
        init,
        showLobby,
        showTable
    };
})();