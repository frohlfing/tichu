/**
 * Verantwortlich für die WebSocket-Verbindung und Kommunikation mit dem Server.
 */
const Network = (() => {
    /** @let {WebSocket|null} websocket - Die aktive WebSocket-Instanz. */
    let websocket = null;
    /** @type {function|null} _onOpen - Callback für erfolgreiche Verbindung. */
    let _onOpen = null;
    /** @type {function|null} _onMessage - Callback für empfangene Nachrichten. */
    let _onMessage = null;
    /** @type {function|null} _onError - Callback für WebSocket-Fehler. */
    let _onError = null;
    /** @type {function|null} _onClose - Callback für geschlossene Verbindung. */
    let _onClose = null;

    /**
     * Stellt eine WebSocket-Verbindung zum Server her.
     * @param {string | null} playerName - Der Name des Spielers (für neuen Login).
     * @param {string | null} tableName - Der Name des Tisches (für neuen Login).
     * @param {string | null} sessionId - Die Session-ID für einen Reconnect.
     */
    function connect(playerName, tableName, sessionId) {
        if (websocket && websocket.readyState !== WebSocket.CLOSED) {
            console.warn('WebSocket-Verbindung besteht bereits oder wird aufgebaut.');
            return;
        }

        // Nimm die URL aus der globalen Config (server-generiert in config.js)
        let wsUrl = (typeof Config !== 'undefined' && Config.WEBSOCKET_URL)
            ? Config.WEBSOCKET_URL
            : 'ws://localhost:8765/ws'; // Fallback

        if (sessionId) {
            wsUrl += `?session_id=${sessionId}`;
        }
        else if (playerName && tableName) {
            wsUrl += `?player_name=${encodeURIComponent(playerName)}&table_name=${encodeURIComponent(tableName)}`;
        }
        else {
            console.error('Ungültige Parameter für WebSocket-Verbindung.');
            if (_onError) {
                _onError({name: "ClientSetupError", message: "Ungültige Verbindungsparameter."});
            }
            return;
        }

        console.log(`CLIENT: Versuche Verbindung zu: ${wsUrl}`);
        try {
            websocket = new WebSocket(wsUrl);
        } catch (e) {
            console.error("CLIENT: Fehler beim Erstellen des WebSocket-Objekts:", e);
            if (_onError) {
                _onError({name: "WebSocketCreationError", message: e.message, originalError: e});
            }
            return;
        }

        websocket.onopen = (event) => {
            console.log('CLIENT: WebSocket-Verbindung geöffnet.');
            if (_onOpen) {
                _onOpen(event);
            }
        };

        websocket.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                console.log('CLIENT: Nachricht vom Server:', message); // Für Debugging
                if (_onMessage) {
                    _onMessage(message);
                }
            } catch (e) {
                console.error('CLIENT: Fehler beim Parsen der Server-Nachricht:', e, event.data);
                if (_onError) {
                    _onError({name: "MessageParseError", message: "Ungültige Server-Nachricht empfangen.", data: event.data});
                }
            }
        };

        websocket.onerror = (event) => {
            // WebSocket onerror liefert oft nur ein generisches Event, keine detaillierte Fehlermeldung
            console.error('CLIENT: WebSocket-Fehler.', event);
            if (_onError) {
                _onError({name: "WebSocketError", message: "WebSocket-Fehler aufgetreten."});
            }
        };

        websocket.onclose = (event) => {
            console.log(`CLIENT: WebSocket-Verbindung geschlossen: Code ${event.code}, Grund: '${event.reason}', Clean: ${event.wasClean}`);
            const wasConnected = !!websocket; // War vorher eine Instanz da?
            websocket = null;
            if (_onClose) {
                _onClose(event, wasConnected);
            }
        };
    }

    /**
     * Sendet eine Nachricht an den Server.
     * @param {string} type - Der Typ der Nachricht.
     * @param {object} payload - Der Inhalt der Nachricht.
     */
    function send(type, payload) {
        if (websocket && websocket.readyState === WebSocket.OPEN) {
            const message = {type, payload: payload || {}};
            // console.log('CLIENT: Sende Nachricht:', message); // Für Debugging
            try {
                websocket.send(JSON.stringify(message));
            } catch (e) {
                console.error("CLIENT: Fehler beim Senden der WebSocket-Nachricht:", e);
                if (_onError) {
                    _onError({name: "SendError", message: "Fehler beim Senden.", originalError: e});
                }
            }
        }
        else {
            console.error('CLIENT: WebSocket nicht verbunden oder nicht bereit zum Senden.');
            if (_onError) {
                _onError({name: "NotConnectedError", message: "Keine Verbindung zum Senden der Nachricht."});
            }
        }
    }

    /**
     * Schließt die WebSocket-Verbindung, falls vorhanden.
     */
    function disconnect() {
        if (websocket) {
            console.log("CLIENT: Schließe WebSocket-Verbindung clientseitig.");
            websocket.close(1000, "Client hat Verbindung aktiv beendet"); // 1000 = Normal closure
        }
    }

    /**
     * Prüft, ob die WebSocket-Verbindung aktiv ist.
     * @returns {boolean} True, wenn verbunden und offen, sonst false.
     */
    function isConnected() {
        return websocket && websocket.readyState === WebSocket.OPEN;
    }

    // Setter für die Callbacks
    /** @param {function} cb - Funktion, die bei geöffneter Verbindung aufgerufen wird. */
    function setOnOpen(cb) {
        _onOpen = cb;
    }

    /** @param {function} cb - Funktion, die bei Nachrichtenempfang aufgerufen wird. */
    function setOnMessage(cb) {
        _onMessage = cb;
    }

    /** @param {function} cb - Funktion, die bei Fehlern aufgerufen wird. */
    function setOnError(cb) {
        _onError = cb;
    }

    /** @param {function} cb - Funktion, die bei geschlossener Verbindung aufgerufen wird. */
    function setOnClose(cb) {
        _onClose = cb;
    }

    return {
        connect,
        send,
        disconnect,
        isConnected,
        setOnOpen,
        setOnMessage,
        setOnError,
        setOnClose
    };
})();