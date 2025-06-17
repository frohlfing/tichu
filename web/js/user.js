/**
 * Datencontainer für die Benutzerdaten.
 */
const User = (() => {
    /**
     * Der Name, den der Benutzer beim Login eingegeben oder gespeichert hat.
     *
     * @type {string}
     */
    let _playerName = localStorage.getItem("tichuPlayerName") || "";

    /**
     * Der Tischname, den der Benutzer beim Login eingegeben oder gespeichert hat.
     *
     * @type {string}
     */
    let _tableName = localStorage.getItem("tichuTableName") || "";

    /**
     * Die aktuelle Session-ID des Spielers.
     *
     * @type {string | null}
     */
    let _sessionId = localStorage.getItem("tichuSessionId") || null;

    // /**
    //  * Initialisiert den Zustand, lädt Werte aus dem LocalStorage.
    //  */
    // function init() {
    //     _playerName = localStorage.getItem("tichuPlayerName") || "";
    //     _tableName = localStorage.getItem("tichuTableName") || "";
    //     _sessionId = localStorage.getItem("tichuSessionId") || null;
    // }

    /** @returns {string} Den lokal gespeicherten/eingegebenen Spielernamen. */
    function getPlayerName() {
        return _playerName;
    }

    /**
     * Setzt den Namen des lokalen Spielers (z.B. bei Login-Eingabe) und speichert ihn.
     * @param {string} playerName - Der neue Spielername.
     */
    function setPlayerName(playerName) {
        _playerName = playerName.trim();
        localStorage.setItem('tichuPlayerName', _playerName);
    }

    /** @returns {string} Den lokal gespeicherten/eingegebenen Tischnamen. */
    function getTableName() {
        return _tableName;
    }

    /**
     * Setzt den Namen des Tisches (z.B. bei Login-Eingabe) und speichert ihn.
     * @param {string} tableName - Der neue Tischname.
     */
    function setTableName(tableName) {
        _tableName = tableName.trim();
        localStorage.setItem('tichuTableName', _tableName);
    }

    /** @returns {string|null} Die aktuelle Session-ID. */
    function getSessionId() {
        return _sessionId;
    }

    /**
     * Setzt die Session-ID und speichert sie im LocalStorage (oder entfernt sie, falls null).
     * @param {string|null} sessionId - Die neue Session-ID.
     */
    function setSessionId(sessionId) {
        _sessionId = sessionId;
        if (sessionId) {
            localStorage.setItem('tichuSessionId', sessionId);
        }
        else {
            localStorage.removeItem('tichuSessionId');
        }
    }

    return {
        getPlayerName, setPlayerName,
        getTableName, setTableName,
        getSessionId, setSessionId,
    };
})();