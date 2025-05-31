const GameState = (() => {
    let sessionId = localStorage.getItem('tichuSessionId');
    let playerName = localStorage.getItem('tichuPlayerName');
    let tableName = localStorage.getItem('tichuTableName');
    let publicState = null;
    let privateState = null;

    function setSessionId(id) {
        sessionId = id;
        if (id) {
            localStorage.setItem('tichuSessionId', id);
        }
        else {
            localStorage.removeItem('tichuSessionId');
        }
    }

    function getSessionId() {
        return sessionId;
    }

    function setPlayerName(name) {
        playerName = name;
        if (name) {
            localStorage.setItem('tichuPlayerName', name);
        } else {
            localStorage.removeItem('tichuPlayerName');
        }
    }

    function getPlayerName() {
        return playerName;
    }

    function setTableName(name) {
        tableName = name;
        if (name) {
            localStorage.setItem('tichuTableName', name);
        } else {
            localStorage.removeItem('tichuTableName');
        }
    }

    function getTableName() {
        return tableName;
    }

    function updateStates(newPublicState, newPrivateState) {
        publicState = newPublicState;
        privateState = newPrivateState;
        console.log("GameState aktualisiert:", { publicState, privateState });
    }

    function getPublicState() {
        return publicState;
    }

    function getPrivateState() {
        return privateState;
    }

    function getPlayerIndex() {
        return privateState ? privateState.player_index : -1;
    }

    return {
        setSessionId,
        getSessionId,
        setPlayerName,
        getPlayerName,
        setTableName,
        getTableName,
        updateStates,
        getPublicState,
        getPrivateState,
        getPlayerIndex,
    };
})();