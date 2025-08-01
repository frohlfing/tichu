/**
 * Enum für WebSocket Close Codes.
 *
 * Diese Codes sind auch im Python-Paket aiohttp definiert.
 * Siehe auch: https://www.rfc-editor.org/rfc/rfc6455.html#section-7.4.1
 */
const WSCloseCode = {
    // Kein Fehler.
    OK: 1000,
    // Server Shutdown oder ein Client hat die Seite verlassen.
    GOING_AWAY: 1001,
    // Protokollfehler.
    PROTOCOL_ERROR: 1002,
    // Typ der Daten in einer Nachricht nicht akzeptiert (z.B. binär statt Text).
    UNSUPPORTED_DATA: 1003,
    // Verbindung nicht ordnungsgemäß geschlossen.
    ABNORMAL_CLOSURE: 1006,
    // Daten in einer Nachricht nicht konsistent mit dem Typ der Nachricht (z.B. nicht-UTF-8 RFC 3629-Daten in einer Textnachricht).
    INVALID_TEXT: 1007,
    // Generell gegen eine Richtlinie verstoßen (kein anderer Statuscode passt).
    POLICY_VIOLATION: 1008,
    // Nachricht zu groß.
    MESSAGE_TOO_BIG: 1009,
    // Client hat Verbindung geschlossen wegen Handshake-Fehler (der Server verwendet diesen Code nicht).
    MANDATORY_EXTENSION: 1010,
    // Server hat einen internen Fehler.
    INTERNAL_ERROR: 1011,
    // Server wird neu gestartet.
    SERVICE_RESTART: 1012,
    // Server ist überlastet.
    TRY_AGAIN_LATER: 1013,
     // Server empfing eine ungültige Antwort vom Upstream-Server (wie HTTP-Statuscode 502).
    BAD_GATEWAY: 1014,
};

/**
 * Typdefinition für einen Netzwerkfehler.
 *
 * @typedef {Object} NetworkError
 * @property {string} message - Die Fehlermeldung.
 * @property {Record<string, any>} [context] - Zusätzliche Informationen (optional).
 */

/**
 * Typdefinition für eine Netzwerknachricht.
 *
 * @typedef {Object} NetworkMessage
 * @property {string} type - Der Typ der Nachricht.
 * @property {Record<string, any>} [payload] - Nachrichtenspezifische Daten (optional).
 */

// ------------------------------------------------------
// Projektspezifische Typen.
// ------------------------------------------------------

/**
 * Typdefinition für eine Anfrage des Servers.
 *
 * @typedef {Object} ServerRequest
 * @property {string} action - Die angefragte Aktion.
 * @property {Record<string, any>} [context] - Zusätzliche Informationen (optional).
 */

/**
 * Typdefinition für eine Benachrichtigung des Servers.
 *
 * @typedef {Object} ServerNotification
 * @property {string} event - Das Ereignis.
 * @property {Record<string, any>} [context] - Zusätzliche Informationen (optional).
 */

/**
 * Typdefinition für eine Fehlermeldung des Servers.
 *
 * @typedef {Object} ServerError
 * @property {string} message - Die Fehlermeldung.
 * @property {number} code - Der Fehlercode des Servers.
 * @property {Record<string, any>} [context] - Zusätzliche Informationen (optional).
 */

/**
 * Enum für Fehlercodes des Servers.
 */
const ServerErrorCode = {
    // Ein unbekannter Fehler ist aufgetreten.
    UNKNOWN_ERROR: 100,
    // Ungültiges Nachrichtenformat empfangen.
    INVALID_MESSAGE: 101,
    // Mindestens eine Karte ist unbekannt.
    UNKNOWN_CARD: 102,
    // Mindestens eine Karte ist keine Handkarte.
    NOT_HAND_CARD: 103,
    // Server wurde heruntergefahren.
    SERVER_DOWN: 106,
    // Deine Session ist abgelaufen. Bitte neu verbinden.
    SESSION_EXPIRED: 200,
    // Session nicht gefunden.
    SESSION_NOT_FOUND: 201,
    // Ungültige Aktion
    INVALID_ACTION: 300,
    // Keine wartende Anfrage für die Antwort gefunden.
    INVALID_RESPONSE: 301,
    // Mindestens zwei Karten sind identisch.
    NOT_UNIQUE_CARDS: 302,
    // Die Karten bilden keine spielbare Kombination.
    INVALID_COMBINATION: 303,
    // Ungültiger Kartenwunsch.
    INVALID_WISH: 306,
    // Tichu-Ansage nicht möglich.
    INVALID_ANNOUNCE: 307,
    // Wahl des Spielers, der den Drachen bekommt, ist ungültig.
    INVALID_DRAGON_RECIPIENT: 308,
    // Zeit für Aktion abgelaufen.
    REQUEST_OBSOLETE: 310,
    // Das Spiel an diesem Tisch hat bereits begonnen.
    GAME_ALREADY_STARTED: 400,
};

/**
 * Verantwortlich für die WebSocket-Verbindung und Kommunikation mit dem Server.
 */
const Network = (() => {
    /**
     * Die aktive WebSocket-Instanz.
     *
     * @type {WebSocket|null}
     */
    let _websocket = null;

    /**
     * Die Session-UUID der aktuellen Verbindung.
     *
     * @type {string|null}
     */
    let _sessionId = localStorage.getItem("tichuSessionId") || null;

    // ------------------------------------------------------
    // Öffentliche Funktionen und Ereignishändler
    // ------------------------------------------------------

    /**
     * Initialisiert das Netzwerk und versucht, die letzte Session wieder aufzubauen.
     */
    function init() {
        if (_sessionId) {
            _open(`session_id=${_sessionId}`);
        }
    }

    /**
     * Öffnet eine WebSocket-Verbindung.
     *
     * @param {string | null} playerName - Der Name des Spielers (für neuen Login).
     * @param {string | null} tableName - Der Name des Tisches (für neuen Login).
     */
    function open(playerName, tableName) {
        _removeSessionId();
        _open(`player_name=${encodeURIComponent(playerName)}&table_name=${encodeURIComponent(tableName)}`);
    }

    /**
     * Schließt die WebSocket-Verbindung, falls vorhanden.
     */
    function close() {
        _removeSessionId();
        if (_websocket && _websocket.readyState !== WebSocket.CLOSING && _websocket.readyState !== WebSocket.CLOSED) {
            _websocket.close(WSCloseCode.OK, "Client hat Verbindung aktiv beendet");
        }
    }

    /**
     * Gibt an, ob die WebSocket bereit zum Senden und Empfangen von Nachrichten ist.
     *
     * @returns {boolean} True, wenn die Verbindung bereit zum Senden und Empfangen ist, sonst false.
     */
    function isReady() {
        return _websocket && _websocket.readyState === WebSocket.OPEN;
    }

    /** @returns {string|null} Die Session-UUID der aktuellen Verbindung. */
    function getSessionId() {
        return _sessionId;
    }

    /**
     * Sendet eine Nachricht an den Server.
     *
     * @param {string} type - Der Typ der Nachricht.
     * @param {Record<string, any>|null} payload - Der Inhalt der Nachricht.
     */
    function send(type, payload=null) {
        if (!isReady()) {
            console.error('Network: WebSocket nicht bereit zum Senden.');
            EventBus.emit("network:error", {message: "WebSocket nicht bereit zum Senden."});
            return;

        }
        const message = payload !== null ? {type: type, payload: payload} : {type: type};
        try {
            _websocket.send(JSON.stringify(message));
        }
        catch (e) {
            console.error("Network: Fehler beim Senden der WebSocket-Nachricht:", e);
            EventBus.emit("network:error", {message: "Fehler beim Senden.", context: e});
        }
    }

    /**
     * Reverse-Mapping-Funktion für WebSocket Close Codes.
     *
     * @param {number} code - WebSocket Close Code.
     * @returns {string} - Fehlerschlüssel
     */
    function getWSCloseCodeName(code) {
        return Object.keys(WSCloseCode).find(key => WSCloseCode[key] === code) || code;
    }

    /**
     * Reverse-Mapping-Funktion für Fehlercodes des Servers.
     *
     * @param {number} code - Fehlercode des Servers
     * @returns {string} - Fehlerschlüssel
     */
    function getServerErrorCodeName(code) {
        return Object.keys(ServerErrorCode).find(key => ServerErrorCode[key] === code) || code;
    }

    // ------------------------------------------------------
    // Hilfsfunktionen
    // ------------------------------------------------------

    /**
     * Stellt eine WebSocket-Verbindung her.
     *
     * @param {string} queryString - Die Abfragezeichenfolge der URL.
     */
    function _open(queryString) {
        if (_websocket && _websocket.readyState === WebSocket.OPEN) {
            console.warn('Network: WebSocket-Verbindung besteht bereits oder wird aufgebaut.');
            return;
        }

        const url = `${Config.WEBSOCKET_URL}?${queryString}`;
        console.log(`Network: Verbinde ${url}...`);
        try {
            _websocket = new WebSocket(url);
        }
        catch (e) {
            console.error("Network: Verbindungsaufbau fehlgeschlagen:", e);
            EventBus.emit("network:error", {message: "Verbindungsaufbau fehlgeschlagen", context: e});
            return;
        }

        _websocket.onopen = (event) => {
            console.log('Network: WebSocket-Verbindung geöffnet.');
            EventBus.emit("network:open", event);
        };

        _websocket.onclose = (event) => {
            if ([WSCloseCode.OK, WSCloseCode.GOING_AWAY, WSCloseCode.POLICY_VIOLATION].includes(event.code)) {
                _removeSessionId();
            }
            EventBus.emit("network:close", event);
            if (_sessionId) {
                // versuche, die Verbindung automatisch wiederherzustellen
                setTimeout(() => {
                    _open(`session_id=${_sessionId}`);
                }, Config.RECONNECT_DELAY);
            }
        };

        _websocket.onerror = (event) => {
            console.error('Network: WebSocket-Fehler.', event);
            EventBus.emit("network:error", {message: "WebSocket-Fehler aufgetreten.", context: event});
        };

        _websocket.onmessage = (event) => {
            try {
                /** @param {NetworkMessage} data */
                const data = JSON.parse(event.data);
                if (data.type === 'notification' && data.payload.event === 'player_joined' && data.payload.context.session_id !== undefined) {
                    /** @param {{payload: {context: {session_id: string}}}} data */
                    _setSessionId(data.payload.context.session_id);
                }
                EventBus.emit("network:message", data);
            }
            catch (_e) {
                console.error('Network: Fehler beim Parsen der Server-Nachricht:', event.data);
                EventBus.emit("network:error", {message: "Ungültige Nachricht empfangen.", context: event.data});
            }
        };
    }

    /**
     * Setzt die Session-ID.
     *
     * @param {string} sessionId - Die neue Session-ID.
     */
    function _setSessionId(sessionId) {
        _sessionId = sessionId;
        localStorage.setItem('tichuSessionId', sessionId);
        console.debug("Network._setSessionId()", sessionId);
    }

    /**
     * Löscht die Session-ID.
     */
    function _removeSessionId() {
        _sessionId = null;
        localStorage.removeItem('tichuSessionId');
        console.debug("Network._removeSessionId()");
    }

    // noinspection JSUnusedGlobalSymbols
    return {
        init,
        open,
        close,
        isReady,
        getSessionId,
        send,
        getWSCloseCodeName,
        getServerErrorCodeName,
    };
})();