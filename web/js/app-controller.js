/**
 * Orchestriert die Anwendung.
 */
const AppController = (() => {
    /**
     * UUID der aktuellen Anfrage.
     *
     * @type {string|null}
     */
    //let __requestId = null;

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

        // Netzwerk-Ereignisse
        EventBus.on("network:open", _handleNetworkOpen);
        EventBus.on("network:close", _handleNetworkClose);
        EventBus.on("network:error", _handleNetworkError);
        EventBus.on("network:message", _handleNetworkMessage);
        
        // LoginView-Ereignis
        EventBus.on("loginView:login", _handleLoginViewLogin);

        // LobbyView-Ereignisse
        EventBus.on("lobbyView:swap", _handleLobbyViewSwap);
        EventBus.on("lobbyView:start", _handleLobbyViewStart);
        EventBus.on("lobbyView:exit", _handleLobbyViewExit);

        // Spieltisch-Ereignisse
        EventBus.on("tableView:grandTichu", _handleTableViewGrandTichu);
        EventBus.on("tableView:tichu", _handleTableViewTichu);
        EventBus.on("tableView:schupf", _handleTableViewSchupf);
        EventBus.on("tableView:play", _handleTableViewPlay);
        EventBus.on("tableView:bomb", _handleTableViewBomb);
        EventBus.on("tableView:wish", _handleTableViewWish);
        EventBus.on("tableView:giveDragonAway", _handleTableViewGiveDragonAway);
        EventBus.on("tableView:gameOver", _handleTableViewGameOver);
        EventBus.on("tableView:exit", _handleTableViewExit);

        // Falls Login-Daten per URL übergeben wurde, direkt anmelden. Ansonsten LoginView anzeigen.
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
    // Netzwerk-Ereignisse
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
    
    // --------------------------------------------------------------------------------------
    // Server-Nachrichten
    // --------------------------------------------------------------------------------------
    
    /**
     * Wird aufgerufen, wenn der Server eine Anfrage gesendet hat.
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
            case 'announce_grand_tichu': // Der Spieler wird gefragt, ob er ein großes Tichu ansagen will.
                break;
            case 'schupf': // Der Spieler muss drei Karten zum Tausch abgeben. Diese Aktion kann durch ein Interrupt abgebrochen werden.
                break;
            case 'play': // Der Spieler muss Karten ausspielen oder passen. Diese Aktion kann durch ein Interrupt abgebrochen werden.
                break;
            case 'bomb': // Der Spieler kann eine Bombe werfen. Wenn der Client zuvor eine Bombe angekündigt hat, muss er eine Bombe auswählen. Ansonsten kann er auch passen.
                break;
            case 'wish': // Der Spieler muss sich einen Kartenwert wünschen.
                break;
            case 'give_dragon_away': // Der Spieler muss den Gegner benennen, der den Drachen bekommen soll.
                break;
            default:
                console.warn('App: Unbehandelte Server-Request:', request.action);
        }
    }

    /**
     * Wird aufgerufen, wenn der Server eine Benachrichtigung gesendet hat.
     *
     * @param {ServerNotification} notification - Die Nachricht.
     */
    function _handleServerNotification(notification) {
        console.log(`App: Server Notification: '${notification.event}'`, notification.context);
        const context = notification.context || {};
        switch (notification.event) {
            case "player_joined":
                if (context.public_state && context.private_state) { // Der Benutzer ist beigetreten.
                    State.setPublicState(context.public_state);
                    State.setPrivateState(context.private_state);
                    ViewManager.showLobbyView();
                }
                else { // Ein Mitspieler ist beigetreten.
                    State.setPlayerName(context.player_index, context.player_name)
                }
                break;
            case "player_left": // Der Spieler hat das Spiel verlassen; eine KI ist eingesprungen.
                State.setPlayerName(context.player_index, context.replaced_by_name);
                State.setHostIndex(context.host_index);
                break;
            case "players_swapped": // Der Index zweier Spieler wurde getauscht.
                //State.setPlayerIndex()
                // {player_index_1: int, player_index_2: int}
                break;
            case "game_started": // Das Spiel wurde gestartet.
                break;
            case "round_started": // Eine neue Runde beginnt. Die Karten werden gemischt.
                break;
            case "hand_cards_dealt": // Handkarten wurden an die Spieler verteilt.
                // `{count: int}` -> `{hand_cards: Cards}`
                break;
            case "player_grand_announced": // Der Spieler hat ein großes Tichu angesagt oder abgelehnt.
                // {player_index: int, announced: bool}
                break;
            case "player_announced": // Der Spieler hat ein einfaches Tichu angesagt.
                // {player_index: int}
                break;
            case "player_schupfed": // Der Spieler hat drei Karten zum Tausch abgegeben.
                // {player_index: int}
                break;
            case "schupf_cards_dealt": // Die Tauschkarten wurden an die Spieler verteilt.
                // `None` -> `{received_schupf_cards: [Card, Card, Card]}`
                break;
            case "player_passed": // Der Spieler hat gepasst.
                // {player_index: int}
                break;
            case "player_played": // Der Spieler hat Karten ausgespielt.
                // {player_index: int, cards: Cards}
                break;
            case "player_bombed": // Der Spieler hat eine Bombe geworfen.
                // {player_index: int, cards: Cards}
                break;
            case "wish_made": // Ein Kartenwert wurde sich gewünscht.
                // {wish_value: int}
                break;
            case "wish_fulfilled": // Der Wunsch wurde erfüllt.
                break;
            case "trick_taken": // Der Spieler hat den Stich kassiert.
                // {player_index: int}
                break;
            case "player_turn_changed": // Der Spieler ist jetzt am Zug.
                // {current_turn_index: int}
                break;
            case "round_over": // Die Runde ist vorbei und die Karten werden neu gemischt.
                // {score_entry: (int, int), is_double_victory: bool}
                break;
            case "game_over": // Die Runde ist vorbei und die Partie ist entschieden.
                // {game_score: (list, list)}
                break;
            default:
                console.warn('App: Unbehandelte Server-Notification:', notification.event);
        }

        ViewManager.renderCurrentView();
    }

    /**
     * Wird aufgerufen, wenn der Server eine Fehlermeldung gesendet hat.
     *
     * @param {ServerError} error - Die Fehlermeldung.
     */
    function _handleServerError(error) {
        console.error(`App: Server Fehler: ${error.message} (${error.code})`, error.context);
        Modals.showErrorToast(`Fehler ${error.message}`);
    }
    
    // --------------------------------------------------------------------------------------
    // LoginView-Ereignis
    // --------------------------------------------------------------------------------------

    /**
     * Wird aufgerufen, wenn der Benutzer sich einloggen möchte.
     * 
     * @param {string} playerName - Der eingegebene Spielername.
     * @param {string} tableName - Der eingegebene Tischname.
     */
    function _handleLoginViewLogin({playerName, tableName}) {
        console.log("App: _handleLoginViewLogin:", playerName, tableName);
        User.setPlayerName(playerName); // Lokale Namen setzen
        User.setTableName(tableName);
        ViewManager.showLoadingView();
        Network.open(playerName, tableName);
    }

    // --------------------------------------------------------------------------------------
    // Lobby-Ereignisse
    // --------------------------------------------------------------------------------------

    /**
     * Wird aufgerufen, wenn der Benutzer die Reihenfolge der Spieler vertauschen möchte.
     *
     * @param {number} playerIndex1 - Index des ersten Spielers.
     * @param {number} playerIndex2 - Index des zweiten Spielers.
     */
    function _handleLobbyViewSwap({playerIndex1, playerIndex2}) {
        Network.send('swap_players', {player_index_1: playerIndex1, player_index_2: playerIndex2});
    }

    /**
     * Wird aufgerufen, wenn der Benutzer das Spiel starten möchte.
     */
    function _handleLobbyViewStart() {
        Network.send('start_game');
    }

    /**
     * Wird aufgerufen, wenn der Benutzer die Lobby verlassen möchte.
     */
    function _handleLobbyViewExit() {
        console.log("App: Lobby Exit");
        Network.send('leave');
        ViewManager.showLoadingView();
    }

    // --------------------------------------------------------------------------------------
    // TableView-Ereignisse
    // --------------------------------------------------------------------------------------

    /**
     * Wird aufgerufen, wenn der Benutzer sich entschieden hat, ob er ein großes Tichu ansagen möchte oder nicht.
     *
     * @param {boolean} announced - True, wenn der Benutzer ein großes Tichu ansagen möchte.
     */
    function _handleTableViewGrandTichu(announced) {
        console.log(`app: GrandTichu: ${announced}`);
        /** @type {string} _requestId.grandTichu */
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

    /**
     * Wird aufgerufen, wenn der Benutzer ein einfaches Tichu ansagen möchte.
     */
    function _handleTableViewTichu() {
        console.log("app: Tichu");
        Network.send("announce");
    }

    /**
     * Wird aufgerufen, wenn der Benutzer Tauschkarten abgeben möchte.
     *
     * @param {Cards} givenSchupfCards - Die drei Tauschkarten, die der Benutzer abgeben möchte.
     */
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

    /**
     * Wird aufgerufen, wenn der Benutzer Karten ausspielen möchte.
     *
     * @param {Cards} cards - Die Karten, die der Benutzer spielen möchte.
     */
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

    /**
     * Wird aufgerufen, wenn der Benutzer eine Bombe ankündigen will.
     */
    function _handleTableViewBomb() {
        console.log("app: Bomb");
        Network.send("bomb");
    }

    /**
     * Wird aufgerufen, wenn der Benutzer sich einen Kartenwert wünschen möchte.
     *
     * @param wishValue - Der gewünschte Kartenwert.
     */
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

    /**
     * Wird aufgerufen, wenn der Benutzer den Gegner ausgewählt hat, der den Drachen geschenkt bekommen soll.
     *
     * @param {number} dragonRecipient - Der Index des Spielers, der den Drachen bekommt (kanonisch).
     */
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

    /**
     * Wird aufgerufen, wenn der Benutzer die Punktetabelle schließt und ein damit die Partie abgeschlossen ist.
     */
    function _handleTableViewGameOver() {
        ViewManager.showLobbyView();
    }

    /**
     * Wird aufgerufen, wenn der Benutzer den Spieltisch verlassen möchte
     */
    function _handleTableViewExit() {
        console.log("App: _handleTableViewExit");
        Network.send('leave');
        ViewManager.showLoadingView();
    }

    // --------------------------------------------------------------------------------------
    // Hilfsfunktionen
    // --------------------------------------------------------------------------------------

    return {
        init,
    };
})();