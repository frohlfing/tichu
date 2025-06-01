// js/state.js

/**
 * @module State
 * Verwaltet den clientseitigen Spielzustand. Dient als reiner Datencontainer.
 */
const State = (() => {
    /** @let {object|null} publicState - Der öffentliche Spielzustand vom Server. */
    let publicState = null;
    /** @let {object|null} privateState - Der private Spielzustand vom Server. */
    let privateState = null;
    /** @let {string} playerName - Der Name des lokalen Spielers. */
    let playerName = '';
    /** @let {string} tableName - Der Name des aktuellen Tisches. */
    let tableName = '';
    /** @let {string|null} sessionId - Die aktuelle Session-ID des Spielers. */
    let sessionId = null;
    /** @let {number} playerIndex - Der kanonische Index des lokalen Spielers am Tisch (0-3). -1, falls unbekannt. */
    let playerIndex = -1;
    /** @let {boolean} isHost - Gibt an, ob der lokale Spieler der Host der Lobby ist. */
    let isHost = false;

    /**
     * Initialisiert den Zustand, lädt gespeicherte Werte aus dem LocalStorage.
     */
    function init() {
        playerName = localStorage.getItem('tichuPlayerName') || '';
        tableName = localStorage.getItem('tichuTableName') || '';
        sessionId = localStorage.getItem('tichuSessionId') || null;
        // playerIndex und isHost werden dynamisch vom Server gesetzt.
    }

    // --- Getter ---
    /** @returns {object|null} Den aktuellen öffentlichen Spielzustand. */
    function getPublicState() { return publicState; }
    /** @returns {object|null} Den aktuellen privaten Spielzustand. */
    function getPrivateState() { return privateState; }
    /** @returns {string} Den Namen des lokalen Spielers. */
    function getPlayerName() { return playerName; }
    /** @returns {string} Den Namen des aktuellen Tisches. */
    function getTableName() { return tableName; }
    /** @returns {string|null} Die aktuelle Session-ID. */
    function getSessionId() { return sessionId; }
    /** @returns {number} Den kanonischen Index des lokalen Spielers. */
    function getPlayerIndex() { return playerIndex; }
    /** @returns {boolean} True, wenn der lokale Spieler Host ist, sonst false. */
    function getIsHost() { return isHost; }

    // --- Setter ---
    /**
     * Setzt den öffentlichen und privaten Spielzustand, typischerweise nach einer `request`-Nachricht.
     * Aktualisiert auch `playerIndex` und `isHost`.
     * @param {object} newPublicState - Das neue publicState Objekt vom Server.
     * @param {object} newPrivateState - Das neue privateState Objekt vom Server.
     */
    function setGameStates(newPublicState, newPrivateState) {
        publicState = newPublicState;
        privateState = newPrivateState;

        if (privateState && typeof privateState.player_index === 'number') {
            playerIndex = privateState.player_index;
        } else if (newPublicState && typeof newPublicState.player_names === 'object' && newPublicState.player_names.indexOf(playerName) > -1 && playerIndex === -1) {
            // Fallback: Versuche Index über Namen zu finden, wenn privateState player_index fehlt (sollte nicht passieren)
            playerIndex = newPublicState.player_names.indexOf(playerName);
        }


        if (publicState && typeof publicState.host_index === 'number' && playerIndex !== -1) {
            isHost = publicState.host_index === playerIndex;
        }
    }

    /**
     * Aktualisiert den öffentlichen Spielzustand, oft bei Notifications.
     * @param {object} updatedPublicState - Das (möglicherweise partielle) publicState Objekt.
     */
    function updatePublicState(updatedPublicState) {
        if (updatedPublicState) { // Direkte Zuweisung, da Server oft den vollen Kontext sendet
            publicState = updatedPublicState;
            if (typeof publicState.host_index === 'number' && playerIndex !== -1) {
                isHost = publicState.host_index === playerIndex;
            }
        }
    }

    /**
     * Aktualisiert den privaten Spielzustand, wenn z.B. nur dieser Teil in einer Notification kommt.
     * @param {object} updatedPrivateState - Das (möglicherweise partielle) privateState Objekt.
     */
    function updatePrivateState(updatedPrivateState) {
        if (updatedPrivateState) { // Direkte Zuweisung
            privateState = updatedPrivateState;
            if (privateState && typeof privateState.player_index === 'number') {
                playerIndex = privateState.player_index;
            }
        }
    }

    /**
     * Setzt den Namen des lokalen Spielers und speichert ihn im LocalStorage.
     * @param {string} name - Der neue Spielername.
     */
    function setPlayerName(name) {
        playerName = name.trim();
        localStorage.setItem('tichuPlayerName', playerName);
    }

    /**
     * Setzt den Namen des Tisches und speichert ihn im LocalStorage.
     * @param {string} name - Der neue Tischname.
     */
    function setTableName(name) {
        tableName = name.trim();
        localStorage.setItem('tichuTableName', tableName);
    }

    /**
     * Setzt die Session-ID und speichert sie im LocalStorage (oder entfernt sie, falls null).
     * @param {string|null} id - Die neue Session-ID.
     */
    function setSessionId(id) {
        sessionId = id;
        if (sessionId) {
            localStorage.setItem('tichuSessionId', sessionId);
        } else {
            localStorage.removeItem('tichuSessionId');
        }
    }

    // isHost wird intern durch setGameStates oder updatePublicState aktualisiert.
    // Ein direkter Setter ist nicht vorgesehen, da es vom Server-Zustand abhängt.

    return {
        init,
        getPublicState,
        getPrivateState,
        getPlayerName,
        getTableName,
        getSessionId,
        getPlayerIndex,
        getIsHost,
        setGameStates,
        updatePublicState,
        updatePrivateState,
        setPlayerName,
        setTableName,
        setSessionId
    };
})();