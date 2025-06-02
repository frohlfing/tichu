// js/state.js

/**
 * @module State
 * Verwaltet den clientseitigen Spielzustand. Dient als reiner Datencontainer.
 * Werte wie Spielername, Tischname, Spielerindex und Host-Status werden
 * direkt aus publicState und privateState abgeleitet oder dort gespeichert.
 */
const State = (() => {
    let publicState = null;     // Der öffentliche Spielzustand vom Server.
    let privateState = null;    // Der private Spielzustand vom Server.
    let localPlayerName = '';   // Der Name des lokalen Spielers, wie im LocalStorage oder bei Login angegeben.
                                // Wird mit publicState.player_names[playerIndex] synchronisiert.
    let currentTableName = '';  // Der Name des aktuellen Tisches, wie im LocalStorage oder bei Login angegeben.
                                // Wird mit publicState.table_name synchronisiert.
    let sessionId = null;       // Die aktuelle Session-ID des Spielers.


    /**
     * Initialisiert den Zustand, lädt Werte aus dem LocalStorage.
     * `publicState` und `privateState` werden vom Server initialisiert.
     */
    function init() {
        localPlayerName = localStorage.getItem('tichuPlayerName') || '';
        currentTableName = localStorage.getItem('tichuTableName') || '';
        sessionId = localStorage.getItem('tichuSessionId') || null;
    }

    // --- Getter ---
    /** @returns {object|null} Den aktuellen öffentlichen Spielzustand. */
    function getPublicState() {
        return publicState;
    }

    /** @returns {object|null} Den aktuellen privaten Spielzustand. */
    function getPrivateState() {
        return privateState;
    }

    /** @returns {string|null} Die aktuelle Session-ID. */
    function getSessionId() {
        return sessionId;
    }

    /** @returns {string} Den Namen des lokalen Spielers. */
    function getPlayerName() {
        const pIdx = getPlayerIndex();
        if (publicState && publicState.player_names && pIdx !== -1 && publicState.player_names[pIdx]) {
            return publicState.player_names[pIdx];
        }
        return localPlayerName; // Fallback auf den Namen, den der User eingegeben/gespeichert hat
    }

    /** @returns {string} Den Namen des aktuellen Tisches. */
    function getTableName() {
        if (publicState && publicState.table_name) {
            return publicState.table_name;
        }
        return currentTableName; // Fallback
    }

    /**
     * Setzt den Index des Spielers.
     * @param {string} index - Der neue Index des Spielers.
     */
    function setPlayerIndex(index) {
        privateState.player_index = index;
    }

    /** @returns {number} Den kanonischen Index des lokalen Spielers. */
    function getPlayerIndex() {
        if (privateState && typeof privateState.player_index === 'number') {
            return privateState.player_index;
        }
        // Fallback, falls privateState (noch) nicht player_index hat, aber wir es aus publicState ableiten könnten
        // (z.B. wenn Server bei player_joined nur public_state und session_id sendet, und player_index in public_state.players wäre)
        // Für Tichu ist player_index aber im private_state des player_joined context.
        return -1;
    }

    /** @returns {boolean} True, wenn der lokale Spieler Host ist, sonst false. */
    function getIsHost() {
        const pIdx = getPlayerIndex();
        if (publicState && typeof publicState.host_index === 'number' && pIdx !== -1) {
            return publicState.host_index === pIdx;
        }
        return false;
    }


    // --- Setter für Kernzustände (primär vom AppController aufgerufen) ---
    /**
     * Setzt den öffentlichen und privaten Spielzustand.
     * @param {object|null} newPublicState - Das neue publicState Objekt vom Server.
     * @param {object|null} newPrivateState - Das neue privateState Objekt vom Server.
     */
    function setGameStates(newPublicState, newPrivateState) {
        publicState = newPublicState;
        privateState = newPrivateState;
        // Synchronisiere lokale Namen, falls Server sie bereitstellt
        if (newPublicState && newPublicState.table_name) {
            currentTableName = newPublicState.table_name;
        }
        const pIdx = getPlayerIndex(); // Nutzt den gerade gesetzten privateState
        if (newPublicState && newPublicState.player_names && pIdx !== -1 && newPublicState.player_names[pIdx]) {
            localPlayerName = newPublicState.player_names[pIdx];
        }
    }

    /**
     * Aktualisiert den öffentlichen Spielzustand.
     * @param {object} updatedPublicState - Das (möglicherweise partielle) publicState Objekt.
     */
    function updatePublicState(updatedPublicState) {
        if (updatedPublicState) {
            publicState = updatedPublicState;
            if (publicState.table_name) { // Tischname aus publicState übernehmen
                currentTableName = publicState.table_name;
            }
            const pIdx = getPlayerIndex();
            if (publicState.player_names && pIdx !== -1 && publicState.player_names[pIdx]) {
                localPlayerName = publicState.player_names[pIdx];
            }
        }
    }

    /**
     * Aktualisiert den privaten Spielzustand.
     * @param {object} updatedPrivateState - Das (möglicherweise partielle) privateState Objekt.
     */
    function updatePrivateState(updatedPrivateState) {
        if (updatedPrivateState) {
            privateState = updatedPrivateState;
            // PlayerIndex wird durch getPlayerIndex() direkt aus privateState gelesen
        }
    }

    // --- Setter für lokale Konfigurationsdaten (vom User oder Initialisierung) ---
    /**
     * Setzt den Namen des lokalen Spielers (z.B. bei Login-Eingabe) und speichert ihn.
     * @param {string} name - Der neue Spielername.
     */
    function setLocalPlayerName(name) {
        localPlayerName = name.trim();
        localStorage.setItem('tichuPlayerName', localPlayerName);
    }
     /** @returns {string} Den lokal gespeicherten/eingegebenen Spielernamen. */
    function getLocalPlayerName() {
        return localPlayerName;
    }


    /**
     * Setzt den Namen des Tisches (z.B. bei Login-Eingabe) und speichert ihn.
     * @param {string} name - Der neue Tischname.
     */
    function setLocalTableName(name) {
        currentTableName = name.trim();
        localStorage.setItem('tichuTableName', currentTableName);
    }
    /** @returns {string} Den lokal gespeicherten/eingegebenen Tischnamen. */
    function getLocalTableName() {
        return currentTableName;
    }


    /**
     * Setzt die Session-ID und speichert sie im LocalStorage (oder entfernt sie, falls null).
     * @param {string|null} id - Die neue Session-ID.
     */
    function setSessionId(id) {
        sessionId = id;
        if (sessionId) {
            localStorage.setItem('tichuSessionId', sessionId);
        }
        else {
            localStorage.removeItem('tichuSessionId');
        }
    }

    // isHost wird intern durch setGameStates oder updatePublicState aktualisiert.
    // Ein direkter Setter ist nicht vorgesehen, da es vom Server-Zustand abhängt.

    return {
        init,
        getPublicState,
        getPrivateState,
        getSessionId,
        getPlayerName,    // Abgeleitet
        getTableName,     // Abgeleitet
        setPlayerIndex,
        getPlayerIndex,   // Abgeleitet
        getIsHost,        // Abgeleitet
        setGameStates,
        updatePublicState,
        updatePrivateState,
        setLocalPlayerName, // Für Login-Formular
        getLocalPlayerName, // Für Login-Formular Pre-Fill
        setLocalTableName,  // Für Login-Formular
        getLocalTableName,  // Für Login-Formular Pre-Fill
        setSessionId
    };
})();