// js/app-controller.js

/**
 * @module AppController
 * Orchestriert die gesamte Tichu-Frontend-Anwendung.
 * Verantwortlich für die Initialisierung von Modulen, den Nachrichtenfluss
 * zwischen Backend und UI sowie die Steuerung der Views.
 */
const AppController = (() => {
    /** @let {object|null} _activeServerRequest - Speichert die aktuelle Server-Anfrage, auf die eine Antwort erwartet wird. */
    let _activeServerRequest = null; // { id: string, action: string, originalPayload: object }

    /**
     * Initialisiert die Anwendung und alle Kernmodule.
     * Versucht einen automatischen Reconnect oder zeigt den Login-Screen.
     */
    function init() {
        console.log("APP: Initialisiere AppController...");
        State.init();
        SoundManager.init();
        ViewManager.init(); // Initialisiert auch die einzelnen View-Module
        Dialogs.init(); // Initialisiert die Dialog-Handler
        CardHandler.init(); // Initialisiert Karten-Interaktionslogik

        // Netzwerk-Callbacks setzen
        Network.setOnOpen(_handleNetworkOpen);
        Network.setOnMessage(_handleNetworkMessage);
        Network.setOnError(_handleNetworkError);
        Network.setOnClose(_handleNetworkClose);

        // Logik für initialen Login oder Reconnect
        const sessionId = State.getSessionId();
        const urlParams = new URLSearchParams(window.location.search);
        const paramPlayerName = urlParams.get('player_name');
        const paramTableName = urlParams.get('table_name');

        if (sessionId && (!paramPlayerName || !paramTableName)) {
            console.log('APP: Versuche Reconnect mit Session ID:', sessionId);
            ViewManager.showView('loading');
            Network.connect(null, null, sessionId);
        } else if (paramPlayerName && paramTableName) {
            console.log('APP: Login mit URL-Parametern:', paramPlayerName, paramTableName);
            // Alte Session löschen, da expliziter Login über URL erfolgt
            State.setSessionId(null);
            State.setPlayerName(paramPlayerName);
            State.setTableName(paramTableName);
            ViewManager.showView('loading');
            Network.connect(paramPlayerName, paramTableName, null);
        } else {
            ViewManager.showView('login');
        }
    }

    /**
     * Wird aufgerufen, wenn die WebSocket-Verbindung erfolgreich geöffnet wurde.
     * @param {Event} event - Das onopen-Event des WebSockets.
     */
    function _handleNetworkOpen(event) {
        console.log("APP: Netzwerkverbindung geöffnet.");
        // Normalerweise passiert hier nichts direkt, da der Server nach dem Joinen
        // eine 'player_joined' Notification sendet, die dann den View-Wechsel auslöst.
        // Der Ladebildschirm bleibt aktiv, bis diese erste maßgebliche Nachricht kommt.
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
     * Aktualisiert den State und informiert die UI, eine Aktion vom Spieler anzufordern.
     * @param {object} payload - Der Payload der 'request'-Nachricht.
     */
    function _handleServerRequest(payload) {
        console.log("APP: Server Request empfangen:", payload.action, payload.request_id);
        State.setGameStates(payload.public_state, payload.private_state);
        _activeServerRequest = { id: payload.request_id, action: payload.action, originalPayload: payload };

        ViewManager.updateViewsBasedOnState(); // Generelles Update für alle sichtbaren Elemente

        switch (payload.action) {
            case 'announce_grand_tichu':
                Dialogs.showGrandTichuPrompt(payload.request_id);
                break;
            case 'schupf':
                ViewManager.showView('gameTable'); // Sicherstellen, dass der Tisch sichtbar ist
                // Logik zum Aktivieren der Schupf-UI in GameTableView oder CardHandler
                CardHandler.enableSchupfMode(payload.request_id, State.getPrivateState().hand_cards);
                break;
            case 'play':
                ViewManager.showView('gameTable');
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
     * Aktualisiert den State und die UI entsprechend dem Ereignis.
     * @param {object} payload - Der Payload der 'notification'-Nachricht. Enthält `event` und `context`.
     */
    function _handleServerNotification(payload) {
        console.log(`APP: Server Notification: '${payload.event}'`, payload.context || {});

        const eventName = payload.event;
        const context = payload.context || {}; // Sicherstellen, dass context immer ein Objekt ist

        const oldPublicState = State.getPublicState() ? JSON.parse(JSON.stringify(State.getPublicState())) : null; // Tiefe Kopie für Vergleich

        // 1. State aktualisieren
        if (context.public_state) State.updatePublicState(context.public_state);
        if (context.private_state) State.updatePrivateState(context.private_state);

        if (eventName === 'player_joined') {
            // SessionID speichern, wenn es der eigene Join ist und eine SessionID gesendet wurde
            if (context.session_id && State.getPlayerIndex() === context.player_index) {
                State.setSessionId(context.session_id);
            }
            // Player Name im State aktualisieren (könnte durch Server korrigiert/ergänzt worden sein)
            if (State.getPlayerIndex() === context.player_index && State.getPublicState() && State.getPublicState().player_names) {
                 State.setPlayerName(State.getPublicState().player_names[context.player_index]);
            }
        } else if (eventName === 'hand_cards_dealt' && context.hand_cards && State.getPrivateState()) {
            const parsedCards = Helpers.parseCards(context.hand_cards); // Erwartet Array von Arrays: [[v,s],...]
            State.getPrivateState().hand_cards = parsedCards;
            // Aktualisiere auch die Kartenanzahl im Public State für den eigenen Spieler, falls nicht schon im context.public_state geschehen
            if (State.getPublicState() && State.getPublicState().count_hand_cards) {
                State.getPublicState().count_hand_cards[State.getPlayerIndex()] = parsedCards.length;
            }
        } else if (eventName === 'schupf_cards_dealt' && context.received_schupf_cards && State.getPrivateState()) {
            const parsedSchupf = Helpers.parseCards(context.received_schupf_cards);
            State.getPrivateState().received_schupf_cards = parsedSchupf;
            // Die Handkarten des Spielers sollten danach ebenfalls aktualisiert werden (wahrscheinlich durch ein folgendes 'hand_cards_dealt')
        }

        // 2. View-Management und UI-Updates
        const currentPublicState = State.getPublicState();
        const currentView = ViewManager.getCurrentViewName();

        // Entscheidungen für View-Wechsel
        if (eventName === 'player_joined' && context.player_index === State.getPlayerIndex()) {
            // Eigener Spieler ist beigetreten -> Ladebildschirm verlassen
            if (currentPublicState && (currentPublicState.current_phase === "setup" || currentPublicState.current_phase === "init" || !currentPublicState.current_phase)) {
                ViewManager.showView('lobby');
            } else if (currentPublicState) { // Spiel läuft bereits
                ViewManager.showView('gameTable');
            } else {
                // Sollte nicht passieren, wenn Server korrekte Daten sendet
                console.warn("APP: 'player_joined' ohne gültigen publicState.current_phase empfangen.");
                ViewManager.showView('lobby'); // Fallback zur Lobby
            }
        } else if (eventName === 'lobby_update') {
            if (currentView !== 'lobby' && currentView !== 'loading') { // Wenn nicht schon in Lobby oder beim initialen Laden
                ViewManager.showView('lobby');
            } else {
                ViewManager.updateViewsBasedOnState(); // Nur aktuellen View (Lobby) rendern
            }
        } else if (eventName === 'game_started') {
            _activeServerRequest = null; // Alte Requests beim Spielstart löschen
            Dialogs.closeAllDialogs(); // Alle Dialoge schließen
            CardHandler.clearSelectedCards(); // Ausgewählte Karten zurücksetzen
            CardHandler.disableSchupfMode(); // Schupf-Modus beenden
            ViewManager.showView('gameTable');
        } else if (eventName === 'game_over') {
            _activeServerRequest = null;
            Dialogs.handleNotification(eventName, context); // Zeigt Game-Over-Dialog
            // ViewManager.showView('lobby'); // Dialog hat Button "Zur Lobby"
        } else {
            // Für andere Notifications: Nur den aktuellen View neu rendern, falls er aktiv ist
            // und falls sich relevante Daten geändert haben könnten.
            // ViewManager.updateViewsBasedOnState() kümmert sich darum.
        }
        ViewManager.updateViewsBasedOnState();

        // 3. Spezifische Handler für Dialoge und Spieltisch (falls aktiv)
        Dialogs.handleNotification(eventName, context);
        if (currentView === 'gameTable' && typeof GameTableView.handleNotification === 'function') {
            GameTableView.handleNotification(eventName, context);
        }
        // LobbyView könnte auch einen spezifischen Handler bekommen, wenn nötig:
        // else if (currentView === 'lobby' && typeof LobbyView.handleNotification === 'function') {
        //     LobbyView.handleNotification(eventName, context);
        // }

        // 4. Soundeffekte abspielen
        let soundToPlay = null;
        const eventPlayerIndex = (typeof context.player_index === 'number') ? context.player_index : -1;
        const ownPlayerIndex = State.getPlayerIndex();

        // Standard-Event-Name als Sound-Name
        if (eventName === 'announce' || eventName === 'dealout' || eventName === 'schuffle' ||
            eventName === 'round_over' || eventName === 'game_over' || eventName === 'wish_made' ||
            eventName === 'wish_fulfilled' || eventName === 'trick_taken') {
            soundToPlay = eventName; // Generische Sounds
        } else if (['played', 'bombed', 'passed', 'schupf0', 'schupf1', 'schupf2', 'schupf3'].includes(eventName)) {
            // Dies sind Sounds, die bereits spielerspezifisch im Event-Namen sein könnten (aus Doku)
            // oder wir leiten sie hier ab.
            soundToPlay = eventName;
        } else if (['schupfed', 'take0', 'take1', 'take2', 'take3'].includes(eventName)) {
             soundToPlay = eventName;
        }
        // Spezifische Sounds für Spieleraktionen (wenn nicht der eigene Spieler)
        // Die Server-Doku listet play0, bomb0 etc. auf. Wir müssen hier ggf. mappen oder
        // der Server sendet schon den richtigen Event-Namen für den Sound.
        // Annahme: Wenn `context.player_index` da ist, ist es eine Spieleraktion.
        if (eventPlayerIndex !== -1 && ownPlayerIndex !== -1) {
            const relativeIdx = Helpers.getRelativePlayerIndex(eventPlayerIndex);
            if (eventName === 'played') soundToPlay = 'play' + relativeIdx;
            else if (eventName === 'bombed') soundToPlay = 'bomb' + relativeIdx;
            else if (eventName === 'passed') soundToPlay = 'pass' + relativeIdx;
            else if (eventName === 'player_schupfed') soundToPlay = 'schupf' + relativeIdx; // Annahme, dass 'player_schupfed' für einzelne Spieler kommt
            else if (eventName === 'trick_taken') soundToPlay = 'take' + relativeIdx; // Wenn 'trick_taken' spielerspezifisch ist
            else if (eventName === 'tichu_announced' || eventName === 'grand_tichu_announced') {
                 // Sound für Tichu-Ansage (generisch oder spielerspezifisch, wenn `announce0-3` existieren)
                 soundToPlay = 'announce'; // Oder 'announce' + relativeIdx, falls verfügbar
            }
        }

        if (soundToPlay) {
            SoundManager.playSound(soundToPlay);
        }

        // 5. Interrupt-Logik für aktive Server-Requests
        // Ein Request wird unterbrochen, wenn ein anderer Spieler eine Aktion ausführt,
        // die den Spielzug übernimmt (Tichu, Bombe) oder wenn der Spieler, dessen
        // Aktion erwartet wird, das Spiel verlässt.
        if (_activeServerRequest) {
            const activeRequestForPlayer = _activeServerRequest.originalPayload && _activeServerRequest.originalPayload.private_state
                                         ? _activeServerRequest.originalPayload.private_state.player_index
                                         : -1;

            let interrupt = false;
            if (eventName === 'tichu_announced' || eventName === 'bombed') {
                // Interrupt, wenn ein *anderer* Spieler Tichu/Bombe spielt
                if (eventPlayerIndex !== -1 && activeRequestForPlayer !== -1 && eventPlayerIndex !== activeRequestForPlayer) {
                    interrupt = true;
                }
            } else if (eventName === 'player_left') {
                // Interrupt, wenn der Spieler, dessen Aktion erwartet wird, geht
                if (eventPlayerIndex !== -1 && eventPlayerIndex === activeRequestForPlayer) {
                    interrupt = true;
                }
            } else if (eventName === 'round_over' || eventName === 'game_over' || eventName === 'game_started') {
                // Interrupt, wenn die Runde/Spiel/Partie endet/startet, während ein Request offen ist
                interrupt = true;
            }

            if (interrupt) {
                console.log(`APP: Aktiver Request '${_activeServerRequest.action}' (ID: ${_activeServerRequest.id}) durch Event '${eventName}' unterbrochen.`);
                // UI informieren, dass die aktuelle Aktion abgebrochen wurde
                if (_activeServerRequest.action === 'play') {
                    GameTableView.enablePlayControls(false); // Spiel-Buttons deaktivieren
                } else if (_activeServerRequest.action === 'schupf') {
                    CardHandler.disableSchupfMode(); // Schupf-Modus UI zurücksetzen
                }
                // Alle relevanten Dialoge schließen, die mit diesem Request verbunden sein könnten
                Dialogs.closeDialogByRequestId(_activeServerRequest.id);
                _activeServerRequest = null; // Aktiven Request zurücksetzen
            }
        }
    }

    /**
     * Verarbeitet eine 'error'-Nachricht vom Server.
     * Zeigt dem Benutzer eine Fehlermeldung an.
     * @param {object} payload - Der Payload der 'error'-Nachricht.
     */
    function _handleServerError(payload) {
        console.error(`APP: Server Fehler ${payload.code}: ${payload.message}`, payload.context);
        Dialogs.showErrorToast(`Fehler ${payload.code}: ${payload.message}`);

        if (payload.code === ErrorCode.SESSION_EXPIRED || payload.code === ErrorCode.SESSION_NOT_FOUND) {
            State.setSessionId(null); // Session ist ungültig
            ViewManager.showView('login'); // Zurück zum Login
        }

        // Wenn der Fehler sich auf einen aktiven Request bezieht, diesen ggf. zurücksetzen
        const requestIdOnError = payload.context ? payload.context.request_id : null;
        if (_activeServerRequest && _activeServerRequest.id === requestIdOnError) {
            console.log("APP: Aktiver Request aufgrund eines Fehlers fehlgeschlagen:", _activeServerRequest.id);
            // UI für die Aktion ggf. wieder aktivieren, damit der User es erneut versuchen kann
            // (oder eine andere Fehlerbehandlung)
             if (_activeServerRequest.action === 'play') GameTableView.enablePlayControls(true, _activeServerRequest.id); // Erneut versuchen lassen
             if (_activeServerRequest.action === 'schupf') CardHandler.enableSchupfMode(_activeServerRequest.id, State.getPrivateState().hand_cards);

            // _activeServerRequest = null; // Nicht unbedingt nullen, User soll es ggf. korrigieren
        }
    }

    /**
     * Wird bei einem WebSocket-Fehler aufgerufen.
     * @param {Event|object} errorEvent - Das Fehlerobjekt.
     */
    function _handleNetworkError(errorEvent) {
        console.error("APP: Netzwerkfehler.", errorEvent);
        Dialogs.showErrorToast(errorEvent.message || "Verbindungsfehler zum Server.");
        //  ViewManager.showView('login'); // Nicht immer zum Login, Server könnte noch da sein
    }

    /**
     * Wird aufgerufen, wenn die WebSocket-Verbindung geschlossen wird.
     * @param {CloseEvent} event - Das close-Event des WebSockets.
     * @param {boolean} wasConnected - True, wenn vor dem Schließen eine Verbindung bestand.
     */
    function _handleNetworkClose(event, wasConnected) {
        console.log("APP: Netzwerkverbindung geschlossen.");
        _activeServerRequest = null; // Keine offenen Anfragen mehr möglich

        if (wasConnected && event.code !== 1000) { // 1000 = Normal Closure
            Dialogs.showErrorToast("Verbindung zum Server verloren.");
        }
        ViewManager.showView('login'); // Zurück zum Login, User muss neu verbinden
    }

    // --- Öffentliche Methoden für UI-Interaktionen ---

    /**
     * Wird vom LoginView aufgerufen, wenn der Benutzer sich einloggen möchte.
     * @param {string} playerName - Der eingegebene Spielername.
     * @param {string} tableName - Der eingegebene Tischname.
     */
    function attemptLogin(playerName, tableName) {
        console.log("APP: Login-Versuch:", playerName, tableName);
        State.setPlayerName(playerName);
        State.setTableName(tableName);
        State.setSessionId(null); // Alte Session bei manuellem Login löschen
        ViewManager.showView('loading');
        Network.connect(playerName, tableName, null);
    }

    /**
     * Sendet eine Antwort auf eine Server-Anfrage.
     * @param {string} requestId - Die ID der ursprünglichen Anfrage.
     * @param {object} responseData - Die Daten der Antwort.
     */
    function sendResponse(requestId, responseData) {
        if (_activeServerRequest && _activeServerRequest.id === requestId) {
            Network.send('response', { request_id: requestId, response_data: responseData });
            _activeServerRequest = null; // Anfrage gilt als beantwortet
        } else {
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
        sendProactiveMessage('leave');
        Network.disconnect(); // Clientseitig Verbindung trennen
    }

    return {
        init,
        attemptLogin,
        sendResponse,
        sendProactiveMessage,
        leaveGame
        // Ggf. weitere Methoden, die von Views direkt aufgerufen werden
    };
})();