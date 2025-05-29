const GameState = (() => {
    let publicState = null;
    let privateState = null;
    let sessionId = null;
    let自分のPlayerIndex = -1; // Wichtig für die UI-Ausrichtung

    function updateStates(newPublicState, newPrivateState) {
        publicState = newPublicState;
        privateState = newPrivateState;
        if (privateState && privateState.player_index !== undefined) { // Oder playerIndex je nach Konvention
            自分のPlayerIndex = privateState.player_index;
        }
        console.log("GameState aktualisiert:", { publicState, privateState });
    }

    function setSessionId(id) {
        sessionId = id;
        // Optional: sessionId im localStorage speichern für Reconnects
        // localStorage.setItem('tichuSessionId', id);
    }

    function getSessionId() {
        // Optional: Aus localStorage laden, wenn nicht gesetzt
        // if (!sessionId) sessionId = localStorage.getItem('tichuSessionId');
        return sessionId;
    }

    function getPlayerIndex() {
        return自分のPlayerIndex;
    }

    function getPublicState() {
        return publicState;
    }

    function getPrivateState() {
        return privateState;
    }


    return {
        updateStates,
        setSessionId,
        getSessionId,
        getPlayerIndex,
        getPublicState,
        getPrivateState
    };
})();