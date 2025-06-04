// js/app-controller.js

/**
 * Orchestriert die Anwendung.
 */
const AppController = (() => {
    let _activeServerRequest = null; // Die aktuelle Server-Anfrage, auf die eine Antwort erwartet wird.
    let _isAttemptingReconnect = false; // True, wenn ein automatischer Reconnect-Versuch läuft.

    /**
     * Initialisiert die Anwendung und alle Kernmodule.
     * Versucht einen automatischen Reconnect oder zeigt den Login-Screen.
     */
    function init() {
        console.log("APP: Initialisiere AppController...");
        State.init();
        SoundManager.init();
        ViewManager.init();
        Dialogs.init();
        CardHandler.init();

        // Netzwerk-Callbacks setzen
        Network.setOnOpen(_handleNetworkOpen);
        Network.setOnMessage(_handleNetworkMessage);
        Network.setOnError(_handleNetworkError);
        Network.setOnClose(_handleNetworkClose);

        // für TESTPHASE direkt zum Spieltisch springen!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        ViewManager.toggleView("gameTable");
        return

        // Logik für initialen Login oder Reconnect
        const sessionId = User.getSessionId();
        const urlParams = new URLSearchParams(window.location.search);
        const paramPlayerName = urlParams.get('player_name');
        const paramTableName = urlParams.get('table_name');

        if (sessionId && (!paramPlayerName || !paramTableName)) {
            console.log('APP: Versuche automatischen Reconnect mit Session ID:', sessionId);
            _isAttemptingReconnect = true;
            ViewManager.toggleView('loading');
            Network.connect(null, null, sessionId);
        }
        else if (paramPlayerName && paramTableName) {
            console.log('APP: Login mit URL-Parametern:', paramPlayerName, paramTableName);
            User.setSessionId(null); // Alte Session für expliziten URL-Login löschen
            User.setPlayerName(paramPlayerName); // Lokalen Namen setzen
            User.setTableName(paramTableName);   // Lokalen Tischnamen setzen
            _isAttemptingReconnect = false;
            ViewManager.toggleView('loading');
            Network.connect(paramPlayerName, paramTableName, null);
        }
        else {
            _isAttemptingReconnect = false;
            ViewManager.toggleView('login');
        }
    }

    /**
     * Wird aufgerufen, wenn die WebSocket-Verbindung erfolgreich geöffnet wurde.
     * @param {Event} _event - Das onopen-Event des WebSockets.
     */
    function _handleNetworkOpen(_event) {
        console.log("APP: Netzwerkverbindung geöffnet.");
        _isAttemptingReconnect = false; // Erfolgreich verbunden (ob Reconnect oder neu)
    }

    /**
     * Verarbeitet eingehende Nachrichten vom WebSocket-Server.
     * @param {object} message - Die geparste JSON-Nachricht vom Server.
     */
    function _handleNetworkMessage(message) {
        switch (message.type) {
            case 'request':
                _handleServerRequest(message.payload);
                break;
            case 'notification':
                _handleServerNotification(message.payload);
                break;
            case 'error':
                _handleServerError(message.payload);
                break;
            case 'pong': // Wird vom Peer direkt beantwortet, hier nur zur Kenntnisnahme.
                console.log('APP: Pong vom Server empfangen:', message.payload.timestamp);
                break;
            default:
                console.warn('APP: Unbekannter Nachrichtentyp vom Server:', message.type, message);
        }
    }

    /**
     * Verarbeitet eine 'request'-Nachricht vom Server.
     *
     * Aktualisiert den State und informiert die UI, eine Aktion vom Spieler anzufordern.
     *
     * @param {{request_id: string, action: string, public_state: PublicState, private_state: PrivateState}} payload - Der Payload der 'request'-Nachricht.
     */
    function _handleServerRequest(payload) {
        console.log("APP: Server Request empfangen:", payload.action, payload.request_id);
        State.setPublicState(payload.public_state)
        State.setPrivateState(payload.private_state)
        _activeServerRequest = { id: payload.request_id, action: payload.action, originalPayload: payload };
        ViewManager.renderCurrentView(); // Rendert aktuellen View mit neuem State

        switch (payload.action) {
            case 'announce_grand_tichu':
                Dialogs.showGrandTichuPrompt(payload.request_id);
                break;
            case 'schupf':
                ViewManager.toggleView('gameTable');
                CardHandler.enableSchupfMode(payload.request_id, State.getPrivateState().hand_cards);
                break;
            case 'play':
                ViewManager.toggleView('gameTable');
                GameTableView.enablePlayControls(true, payload.request_id);
                break;
            case 'wish':
                Dialogs.showWishDialog(payload.request_id);
                break;
            case 'give_dragon_away':
                Dialogs.showDragonDialog(payload.request_id);
                break;
            default:
                console.warn('APP: Unbehandelte Server-Request-Aktion:', payload.action);
        }
    }

    /**
     * Verarbeitet eine 'notification'-Nachricht vom Server.
     *
     * Aktualisiert den State und die UI entsprechend dem Ereignis.
     *
     * @param {object} payload - Der Payload der 'notification'-Nachricht. Enthält `event` und `context`.
     */
    function _handleServerNotification(payload) {
        console.log(`APP: Server Notification: '${payload.event}'`, payload.context || {});
        const eventName = payload.event;
        const context = payload.context || {};

        if (context.public_state) State.setPublicState(context.public_state);
        if (context.private_state) State.setPrivateState(context.private_state);

        const ownPlayerIndex = State.getPlayerIndex();
        let eventBelongsToCanonicalPlayerIndex = -1; // Index des Spielers des Events

        if (eventName === 'player_joined' && context.private_state && typeof context.private_state.player_index === 'number') {
            eventBelongsToCanonicalPlayerIndex = context.private_state.player_index;
        } else if (typeof context.player_index === 'number') { // Für andere Events (player_played etc.)
            eventBelongsToCanonicalPlayerIndex = context.player_index;
        }

        if (eventName === 'player_joined' && eventBelongsToCanonicalPlayerIndex === ownPlayerIndex && ownPlayerIndex !== -1) {
            if (context.session_id) User.setSessionId(context.session_id);
            const currentPublicState = State.getPublicState(); // Hole den gerade aktualisierten State
            if (currentPublicState && currentPublicState.player_names && currentPublicState.player_names[ownPlayerIndex]) {
                 //State.setPlayerName(currentPublicState.player_names[ownPlayerIndex]);
            }
            if (currentPublicState && currentPublicState.table_name) {
                 //State.setTableName(currentPublicState.table_name);
            }

            if (currentPublicState.is_running) {
                ViewManager.toggleView('gameTable');
            } else {
                ViewManager.toggleView('lobby');
            }
        } else if (eventName === 'player_left') {
            // Host-Index könnte sich geändert haben, wenn der Host gegangen ist.
            // Server-Doku sagt: context hat jetzt auch `host_index`.
            if (State.getPublicState() && typeof context.host_index === 'number') {
                State.getPublicState().host_index = context.host_index;
            }
            if (ViewManager.getCurrentViewName() === 'lobby') {
                ViewManager.renderCurrentView(); // Lobby neu rendern
            }
        }
        else if (eventName === 'players_swapped') {
            if (typeof context.player_index_1 === 'number' && typeof context.player_index_2 === 'number') {
                let name1 = State.getPublicState().player_names[context.player_index_1]
                State.getPublicState().player_names[context.player_index_1] = State.getPublicState().player_names[context.player_index_2]
                State.getPublicState().player_names[context.player_index_2] = name1
                if (State.getPlayerIndex() === context.player_index_1) {
                    State.setPlayerIndex(context.player_index_2)
                }
                else if (State.getPlayerIndex() === context.player_index_2) {
                    State.setPlayerIndex(context.player_index_1)
                }
            }
        }
        else if (eventName === 'game_started' || eventName === 'round_started') { // Auch bei round_started
            _activeServerRequest = null;
            Dialogs.closeAllDialogs();
            CardHandler.clearSelectedCards();
            CardHandler.disableSchupfMode();
            ViewManager.toggleView('gameTable'); // Bei round_started sind wir schon am Tisch
        }

        ViewManager.renderCurrentView();
        Dialogs.handleNotification(eventName, context);
        if (ViewManager.getCurrentViewName() === 'gameTable' && typeof GameTableView.handleNotification === 'function') {
            GameTableView.handleNotification(eventName, context);
        }

        SoundManager.playNotificationSound(eventName, eventBelongsToCanonicalPlayerIndex);

        // Interrupt-Logik (Basis-Event-Namen verwenden, die dann im SoundManager mit Index versehen werden)
        if (_activeServerRequest) {
            const activeRequestForPlayer = _activeServerRequest.originalPayload && _activeServerRequest.originalPayload.private_state
                ? _activeServerRequest.originalPayload.private_state.player_index
                : -1;
            let interrupt = false;
            if (['player_announced', 'player_grand_announced', 'player_bombed'].includes(eventName)) {
                if (eventBelongsToCanonicalPlayerIndex !== -1 && activeRequestForPlayer !== -1 && eventBelongsToCanonicalPlayerIndex !== activeRequestForPlayer) {
                    interrupt = true;
                }
            } else if (eventName === 'player_left') {
                if (eventBelongsToCanonicalPlayerIndex !== -1 && eventBelongsToCanonicalPlayerIndex === activeRequestForPlayer) {
                    interrupt = true;
                }
            } else if (['round_over', 'game_over', 'game_started', 'round_started'].includes(eventName)) {
                interrupt = true;
            }

            if (interrupt) {
                console.log(`APP: Aktiver Request '${_activeServerRequest.action}' (ID: ${_activeServerRequest.id}) durch Event '${eventName}' unterbrochen.`);
                if (_activeServerRequest.action === 'play') {
                    GameTableView.enablePlayControls(false);
                }
                if (_activeServerRequest.action === 'schupf') {
                    CardHandler.disableSchupfMode();
                }
                Dialogs.closeDialogByRequestId(_activeServerRequest.id);
                _activeServerRequest = null;
            }
        }
    }

    /**
     * Verarbeitet eine 'error'-Nachricht vom Server.
     *
     * Zeigt dem Benutzer eine Fehlermeldung an und behandelt spezifische Fehlercodes.
     *
     * @param {object} payload - Der Payload der 'error'-Nachricht (enthält message, code, context).
     */
    function _handleServerError(payload) {
        console.error(`APP: Server Fehler ${payload.code}: ${payload.message}`, payload.context || {});
        Dialogs.showErrorToast(`Fehler ${payload.code}: ${payload.message}`);

        // Spezifische Fehlerbehandlung für Session-Probleme
        if (payload.code === ErrorCode.SESSION_EXPIRED || payload.code === ErrorCode.SESSION_NOT_FOUND) {
            User.setSessionId(null); // Session ist ungültig oder nicht gefunden
            Network.disconnect(); // Aktive Verbindung trennen, falls noch vorhanden
            ViewManager.toggleView('login'); // Zurück zum Login
        }

        // Wenn der Fehler sich auf einen aktiven Request bezieht, diesen ggf. behandeln
        const requestIdOnError = payload.context ? payload.context.request_id : null;
        if (_activeServerRequest && _activeServerRequest.id === requestIdOnError) {
            console.log("APP: Aktiver Request ist aufgrund eines Server-Fehlers fehlgeschlagen:", _activeServerRequest.id, payload.code);
            // Hier könnte man entscheiden, ob der User die Aktion wiederholen darf.
            // Für kritische Fehler oder wenn der Request veraltet ist, sollte er zurückgesetzt werden.
            if (payload.code === ErrorCode.REQUEST_OBSOLETE || payload.code === ErrorCode.INVALID_ACTION) {
                if (_activeServerRequest.action === 'play') GameTableView.enablePlayControls(false); // Aktion nicht mehr gültig
                if (_activeServerRequest.action === 'schupf') CardHandler.disableSchupfMode();
                Dialogs.closeDialogByRequestId(_activeServerRequest.id);
                _activeServerRequest = null;
            } else {
                // Bei anderen Fehlern könnte man dem User erlauben, es erneut zu versuchen,
                // indem _activeServerRequest nicht genullt wird und die UI-Controls aktiv bleiben.
                // Das hängt von der gewünschten User Experience ab.
                // Fürs Erste: Bei den meisten Fehlern, die einen Request betreffen, die UI nicht blockieren.
                 if (_activeServerRequest.action === 'play') GameTableView.enablePlayControls(true, _activeServerRequest.id);
                 if (_activeServerRequest.action === 'schupf') CardHandler.enableSchupfMode(_activeServerRequest.id, State.getPrivateState().hand_cards);

            }
        }
    }

    function _handleNetworkError(errorEvent) {
        console.error("APP: Netzwerkfehler.", errorEvent.name, errorEvent.message);
        if (!_isAttemptingReconnect) {
            Dialogs.showErrorToast(errorEvent.message || "Verbindungsfehler zum Server.");
        } else {
            console.log("APP: Automatischer Reconnect fehlgeschlagen (Netzwerkfehler).");
        }
        _isAttemptingReconnect = false;
        User.setSessionId(null);
        ViewManager.toggleView('login');
    }

    /**
     * Wird aufgerufen, wenn die WebSocket-Verbindung geschlossen wird.
     * @param {CloseEvent} event - Das close-Event des WebSockets.
     * @param {boolean} wasConnected - True, wenn vor dem Schließen eine Verbindung bestand.
     */
    function _handleNetworkClose(event, wasConnected) {
        console.log(`APP: Netzwerkverbindung geschlossen. Code: ${event.code}, Reconnect-Versuch: ${_isAttemptingReconnect}, Grund: ${event.reason}`);
        const wasReconnectAttempt = _isAttemptingReconnect;
        _isAttemptingReconnect = false;
        _activeServerRequest = null;

        if (event.code === 1008) { // Policy Violation
            console.log("APP: Verbindung wegen Policy Violation geschlossen (Code 1008).");
            User.setSessionId(null);
            Dialogs.showErrorToast("Sitzung ungültig oder abgelaufen. Bitte neu anmelden.");
        } else if (wasConnected && event.code !== 1000 && !wasReconnectAttempt) {
            Dialogs.showErrorToast("Verbindung zum Server verloren.");
        } else if (wasReconnectAttempt && event.code !== 1000 && event.code !== 1008) {
            console.log("APP: Automatischer Reconnect fehlgeschlagen (Verbindung geschlossen).");
            User.setSessionId(null);
        }

        if (event.code !== 1000) { // Wenn nicht normal vom Client beendet
             ViewManager.toggleView('login');
        } else if (!wasConnected && event.code === 1000) { // Wenn initial abgelehnt
            ViewManager.toggleView('login');
        }
        // Wenn Code 1000 und wasConnected, dann hat der Client `leaveGame` aufgerufen,
        // was den View schon auf Login setzt.
    }

    // --- Öffentliche Methoden für UI-Interaktionen ---

    /**
     * Wird vom LoginView aufgerufen, wenn der Benutzer sich einloggen möchte.
     * @param {string} playerName - Der eingegebene Spielername.
     * @param {string} tableName - Der eingegebene Tischname.
     */
    function attemptLogin(playerName, tableName) {
        console.log("APP: Login-Versuch GESTARTET für:", playerName, tableName);
        User.setPlayerName(playerName); // Lokale Namen setzen
        User.setTableName(tableName);
        User.setSessionId(null);
        _isAttemptingReconnect = false;
        ViewManager.toggleView('loading');
        Network.connect(playerName, tableName, null);
    }

    /**
     * Sendet eine Antwort auf eine Server-Anfrage.
     * @param {string} requestId - Die ID der ursprünglichen Anfrage.
     * @param {object} responseData - Die Daten der Antwort.
     */
    function sendResponse(requestId, responseData) {
        if (_activeServerRequest && _activeServerRequest.id === requestId) {
            Network.send('response', {request_id: requestId, response_data: responseData});
            _activeServerRequest = null; // Anfrage gilt als beantwortet
        }
        else {
            console.warn("APP: Versuch, auf eine nicht (mehr) aktive Anfrage zu antworten:", requestId);
            // Ggf. Fehlermeldung an UI, dass die Aktion veraltet ist.
            Dialogs.showErrorToast("Aktion ist veraltet oder wurde bereits beantwortet.");
        }
    }

    /**
     * Sendet eine proaktive Nachricht (keine Antwort auf einen Request).
     * @param {string} type - Der Typ der Nachricht (z.B. 'announce', 'bomb', 'leave', 'lobby_action').
     * @param {object} [payload] - Der optionale Payload der Nachricht.
     */
    function sendProactiveMessage(type, payload) {
        Network.send(type, payload);
    }

    /**
     * Behandelt das Verlassen des Spiels/Tisches.
     */
    function leaveGame() {
        console.log("APP: Verlasse Spiel/Tisch.");
        AppController.sendProactiveMessage('leave');
        Network.disconnect(); // Führt zu _handleNetworkClose mit Code 1000
        ViewManager.toggleView('login'); // Explizit zum Login, da User Aktion
    }

    return {
        init,
        attemptLogin,
        sendResponse,
        sendProactiveMessage,
        leaveGame
    };
})();