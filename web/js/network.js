/**
 * Enum für aiohttp-Fehlercodes.
 *
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
 * Verantwortlich für die WebSocket-Verbindung und Kommunikation mit dem Server.
 */
const Network = (() => {
    /** @type {WebSocket|null} websocket - Die aktive WebSocket-Instanz. */
    let websocket = null;

    /**
     * Stellt eine WebSocket-Verbindung zum Server her.
     *
     * @param {string | null} playerName - Der Name des Spielers (für neuen Login).
     * @param {string | null} tableName - Der Name des Tisches (für neuen Login).
     * @param {string | null} sessionId - Die Session-ID für einen Reconnect.
     */
    function connect(playerName, tableName, sessionId) {
        if (websocket && websocket.readyState !== WebSocket.CLOSED) {
            console.warn('Network: WebSocket-Verbindung besteht bereits oder wird aufgebaut.');
            return;
        }

        let wsUrl = Config.WEBSOCKET_URL || 'ws://localhost:8765/ws';
        
        if (sessionId) {
            wsUrl += `?session_id=${sessionId}`;
        }
        else if (playerName && tableName) {
            wsUrl += `?player_name=${encodeURIComponent(playerName)}&table_name=${encodeURIComponent(tableName)}`;
        }
        else {
            console.error('Network: Ungültige Parameter für WebSocket-Verbindung.');
            EventBus.emit("network:error", {name: "ClientSetupError", message: "Ungültige Verbindungsparameter."});
            return;
        }

        console.log(`Network: Versuche Verbindung zu: ${wsUrl}`);

        try {
            websocket = new WebSocket(wsUrl);
        }
        catch (e) {
            console.error("Network: Fehler beim Erstellen des WebSocket-Objekts:", e);
            EventBus.emit("network:error", {name: "WebSocketCreationError", message: e.message, context: {originalError: e}});
            return;
        }

        websocket.onopen = (event) => {
            console.log('Network: WebSocket-Verbindung geöffnet.');
            EventBus.emit("network:open", event);
        };

        websocket.onclose = (event) => {
            console.log(`Network: WebSocket-Verbindung geschlossen: Code ${event.code}, Grund: '${event.reason}', Clean: ${event.wasClean}`);
            EventBus.emit("network:close", event);
        };

        websocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('Network: Nachricht vom Server:', data);
                EventBus.emit("network:message", data);
            } 
            catch (e) {
                console.error('Network: Fehler beim Parsen der Server-Nachricht:', e, event.data);
                EventBus.emit("network:error", {name: "MessageParseError", message: "Ungültige Server-Nachricht empfangen.", context: event.data});
            }
        };

        websocket.onerror = (event) => {
            console.error('Network: WebSocket-Fehler.', event);
            EventBus.emit("network:error", {name: "WebSocketError", message: "WebSocket-Fehler aufgetreten.", context: event});
        };
    }

    /**
     * Sendet eine Nachricht an den Server.
     *
     * @param {string} type - Der Typ der Nachricht.
     * @param {object|null} payload - Der Inhalt der Nachricht.
     */
    function send(type, payload=null) {
        if (websocket && websocket.readyState === WebSocket.OPEN) {
            const message = {type, payload: payload || {}};
            // console.log('Network: Sende Nachricht', message); // Für Debugging
            try {
                websocket.send(JSON.stringify(message));
            }
            catch (e) {
                console.error("Network: Fehler beim Senden der WebSocket-Nachricht:", e);
                EventBus.emit("network:error", {name: "SendError", message: "Fehler beim Senden.", context: {originalError: e}});
            }
        }
        else {
            console.error('Network: WebSocket nicht verbunden oder nicht bereit zum Senden.');
            EventBus.emit("network:error", {name: "NotConnectedError", message: "Keine Verbindung zum Senden der Nachricht." });
        }
    }

    /**
     * Schließt die WebSocket-Verbindung, falls vorhanden.
     */
    function disconnect() {
        if (websocket) {
            console.log("Network: Schließe WebSocket-Verbindung clientseitig.");
            websocket.close(WSCloseCode.OK, "Client hat Verbindung aktiv beendet");
        }
    }

    /**
     * Prüft, ob die WebSocket-Verbindung aktiv ist.
     *
     * @returns {boolean} True, wenn verbunden und offen, sonst false.
     */
    function isConnected() {
        return websocket && websocket.readyState === WebSocket.OPEN;
    }

    // noinspection JSUnusedGlobalSymbols
    return {
        connect,
        send,
        disconnect,
        isConnected,
    };
})();