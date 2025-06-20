/**
 * Orchestriert die Anwendung.
 */
const AppController = (() => {
    /**
     * UUID der aktuellen Anfrage.
     *
     * @type {string|null}
     */
    //let _requestId = null;

    /**
     * UUID der aktuellen Anfrage.
     *
     * @type {Object<string, any>}
     */
    const _requestId = {
        grandTichu: "4711",
        schupf: "4713",
        play: "4714",
        bomb: "4715",
        wish: "4716",
        giveDragonAway: "4717",
    };

    /**
     * Initialisiert die Anwendung und alle Kernmodule.
     *
     * Wird durch main() aufgerufen.
     */
    function init() {
        console.log("App: Initialisiere AppController...");

        //Config
        //Lib
        //State.init();
        //User.init();
        //EventBus
        Network.init();
        SoundManager.init();
        Modals.init();
        ViewManager.init();

        EventBus.on("network:open", _handleNetworkOpen);
        EventBus.on("network:close", _handleNetworkClose);
        EventBus.on("network:message", _handleNetworkMessage);
        EventBus.on("network:error", _handleNetworkError);

        EventBus.on("gameTableView:grandTichu", _handleTableViewGrandTichu);
        EventBus.on("gameTableView:tichu", _handleTableViewTichu);
        EventBus.on("gameTableView:schupf", _handleTableViewSchupf);
        EventBus.on("gameTableView:play", _handleTableViewPlay);
        EventBus.on("gameTableView:bomb", _handleTableViewBomb);
        EventBus.on("gameTableView:wish", _handleTableViewWish);
        EventBus.on("gameTableView:giveDragonAway", _handleTableViewGiveDragonAway);
        EventBus.on("gameTableView:gameOver", _handleTableViewGameOver);
        EventBus.on("gameTableView:exit", _handleTableViewExit);

        // Logik für initialen Login oder Reconnect
        const urlParams = new URLSearchParams(window.location.search);
        const paramPlayerName = urlParams.get('player_name');
        const paramTableName = urlParams.get('table_name');
        if (paramPlayerName && paramTableName) {
            console.log('App: Login mit URL-Parametern:', paramPlayerName, paramTableName);
            User.setPlayerName(paramPlayerName);
            User.setTableName(paramTableName);
            ViewManager.showLoadingView();
            Network.open(paramPlayerName, paramTableName);
        }
        else {
            ViewManager.showLoginView();
        }
    }

    // --------------------------------------------------------------------------------------
    // Network-Ereignisse
    // --------------------------------------------------------------------------------------

    /**
     * Wird aufgerufen, wenn die WebSocket-Verbindung erfolgreich geöffnet wurde.
     *
     * @param {Event} event - Das Event der WebSocket.
     */
    function _handleNetworkOpen(event) {
        console.log("App: Netzwerkverbindung geöffnet.", event);
    }

    /**
     * Wird aufgerufen, wenn die WebSocket-Verbindung geschlossen wird.
     *
     * @param {CloseEvent} event - Das CloseEvent der WebSocket (siehe https://developer.mozilla.org/en-US/docs/Web/API/CloseEvent).
     */
    function _handleNetworkClose(event) {
        console.log(`App: Netzwerkverbindung geschlossen. Code: ${event.code}, Grund: ${event.reason}, Wurde sauber geschlossen: ${event.wasClean}`);
        if (Network.getSessionId()) {
            ViewManager.showLoadingView();
        }
        else {
            ViewManager.showLoginView();
        }
    }

    /**
     * Wird aufgerufen, wenn eine Netzwerknachricht empfangen wurde.
     *
     * @param {NetworkMessage} message - Die Nachricht vom Server.
     */
    function _handleNetworkMessage(message) {
        switch (message.type) {
            case 'request':
                _handleServerRequest(/** @type {ServerRequest} */ message.payload);
                break;
            case 'notification':
                _handleServerNotification(/** @type {ServerNotification} */ message.payload);
                break;
            case 'error':
                _handleServerError(/** @type {ServerError} */ message.payload);
                break;
            case 'pong':
                console.log('App: Pong vom Server empfangen:', message.payload.timestamp);
                break;
            default:
                console.error('App: Unbekannter Nachrichtentyp vom Server:', message.type);
        }
    }

    /**
     * Wird aufgerufen, wenn ein Netzwerkfehler auftritt.
     *
     * @param {NetworkError} error - Der Netzwerkfehler.
     */
    function _handleNetworkError(error) {
        console.error("App: Netzwerkfehler.", error);
        Modals.showErrorToast(error.message);
        Network.close();
        ViewManager.showLoginView();
    }

    /**
     * Verarbeitet eine Anfrage vom Server.
     *
     * @param {ServerRequest} request - Die Serveranfrage.
     */
    function _handleServerRequest(request) {
        console.log("App: Server Request empfangen:", request.request_id, request.action);
        State.setPublicState(request.public_state)
        State.setPrivateState(request.private_state)
        _requestId[request.action] = request.request_id;
        ViewManager.renderCurrentView();
        switch (request.action) {
            case 'announce_grand_tichu':
                break;
            case 'schupf':
                break;
            case 'play':
                break;
            // case 'bomb':
            //     break;
            case 'wish':
                break;
            case 'give_dragon_away':
                break;
            default:
                console.warn('App: Unbehandelte Server-Request-Aktion:', request.action);
        }
    }

    /**
     * Verarbeitet eine Benachrichtigung vom Server.
     *
     * @param {ServerNotification} notification - Die Nachricht.
     */
    function _handleServerNotification(notification) {
        console.log(`App: Server Notification: '${notification.event}'`, notification.context || {});
        if (context.public_state) {
            State.setPublicState(context.public_state);
        }
        if (context.private_state) {
            State.setPrivateState(context.private_state);
        }
        ViewManager.renderCurrentView();
    }

    /**
     * Verarbeitet eine Fehlermeldung vom Server.
     *
     * @param {ServerError} error - Die Fehlermeldung.
     */
    function _handleServerError(error) {
        console.error(`App: Server Fehler: ${error.message} (${error.code})`, error.context);
        Modals.showErrorToast(`Fehler ${error.message}`);
    }

    // --------------------------------------------------------------------------------------
    // TableView-Ereignisse
    // --------------------------------------------------------------------------------------

    function _handleTableViewGrandTichu(announced) {
        console.log(`app: GrandTichu: ${announced}`);
        if (!_requestId.grandTichu) {
            Modals.showErrorToast("Keine Anfrage für große Tichu-Ansage erhalten.");
            return
        }
        Network.send("response", {
            request_id: _requestId.grandTichu,
            response_data: {
                announced: announced
            }
        });
        _requestId.grandTichu = null;
    }

    function _handleTableViewTichu() {
        console.log("app: Tichu");
        Network.send("announce");
    }

    function _handleTableViewSchupf(givenSchupfCards) {
        console.log(`app: Schupf: ${givenSchupfCards}`);
        if (!_requestId.schupf) {
            Modals.showErrorToast("Keine Anfrage für Schupfen erhalten.");
            return
        }
        Network.send("response", {
            request_id: _requestId.schupf,
            response_data: {
                given_schupf_cards: givenSchupfCards
            }
        });
        _requestId.schupf = null;
    }

    function _handleTableViewPlay(cards) {
        console.log(`app: Play: ${cards}`);
        if (!_requestId.play) {
            Modals.showErrorToast("Keine Anfrage für Ausspielen erhalten.");
            return
        }
        Network.send("response", {
            request_id: _requestId.play,
            response_data: {
                cards: cards
            }
        });
        _requestId.play = null;
    }

    function _handleTableViewBomb() {
        console.log("app: Bomb");
        Network.send("bomb");
    }

    function _handleTableViewWish(wishValue) {
        console.log(`app: Wish: ${wishValue}`);
        if (!_requestId.wish) {
            Modals.showErrorToast("Keine Anfrage für Wünschen erhalten.");
            return
        }
        Network.send("response", {
            request_id: _requestId.wish,
            response_data: {
                wish_value: wishValue
            }
        });
        _requestId.wish = null;
    }

    function _handleTableViewGiveDragonAway(dragonRecipient) {
        console.log(`app: GiveDragonAway: ${dragonRecipient}`);
        if (!_requestId.giveDragonAway) {
            Modals.showErrorToast("Keine Anfrage für Wünschen erhalten.");
            return
        }
        Network.send("response", {
            request_id: _requestId.giveDragonAway,
            response_data: {
                dragon_recipient: dragonRecipient
            }
        });
        _requestId.giveDragonAway = null;
    }

    function _handleTableViewGameOver() {
        ViewManager.showLobbyView();
    }

    function _handleTableViewExit() {

    }

    // --------------------------------------------------------------------------------------
    // Sonstiges
    // --------------------------------------------------------------------------------------

    // --- Öffentliche Methoden für UI-Interaktionen ---

    /**
     * Wird vom LoginView aufgerufen, wenn der Benutzer sich einloggen möchte.
     * @param {string} playerName - Der eingegebene Spielername.
     * @param {string} tableName - Der eingegebene Tischname.
     */
    function attemptLogin(playerName, tableName) {
        console.log("App: Login-Versuch GESTARTET für:", playerName, tableName);
        User.setPlayerName(playerName); // Lokale Namen setzen
        User.setTableName(tableName);
        ViewManager.showLoadingView();
        Network.open(playerName, tableName);
    }

    /**
     * Sendet eine Antwort auf eine Server-Anfrage.
     * @param {string} requestId - Die ID der ursprünglichen Anfrage.
     * @param {Object<string, any>} responseData - Die Daten der Antwort.
     */
    function sendResponse(requestId, responseData) {
        if (_activeServerRequest && _activeServerRequest.id === requestId) {
            Network.send('response', {request_id: requestId, response_data: responseData});
            _activeServerRequest = null; // Anfrage gilt als beantwortet
        }
        else {
            console.warn("App: Versuch, auf eine nicht (mehr) aktive Anfrage zu antworten:", requestId);
            // Ggf. Fehlermeldung an UI, dass die Aktion veraltet ist.
            Modals.showErrorToast("Aktion ist veraltet oder wurde bereits beantwortet.");
        }
    }

    /**
     * Sendet eine proaktive Nachricht (keine Antwort auf einen Request).
     * @param {string} type - Der Typ der Nachricht (z.B. 'announce', 'bomb', 'leave', 'lobby_action').
     * @param {Object<string, any>} [payload] - Der optionale Payload der Nachricht.
     */
    function sendProactiveMessage(type, payload) {
        Network.send(type, payload);
    }

    /**
     * Behandelt das Verlassen des Spiels/Tisches.
     */
    function leaveGame() {
        console.log("App: Verlasse Spiel/Tisch.");
        AppController.sendProactiveMessage('leave');
        Network.close(); // Führt zu _handleNetworkClose mit Code 1000
        ViewManager.showLoginView(); // Explizit zum Login, da User Aktion
    }

    return {
        init,
        attemptLogin,
        sendResponse,
        sendProactiveMessage,
        leaveGame
    };
})();