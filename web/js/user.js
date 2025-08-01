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

    // /**
    //  * Initialisiert den Zustand, lädt Werte aus dem LocalStorage.
    //  */
    // function init() {
    //     const urlParams = new URLSearchParams(window.location.search);
    //     const paramPlayerName = urlParams.get('player_name');
    //     const paramTableName = urlParams.get('table_name');
    //     if (paramPlayerName && paramTableName) {
    //         User.setPlayerName(paramPlayerName);
    //         User.setTableName(paramTableName);
    //     }
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

    return {
        getPlayerName, setPlayerName,
        getTableName, setTableName,
    };
})();