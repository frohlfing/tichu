/**
 * Aktualisiert den Spielzustand und schaltet zwischen den Views um.
 */
const AppController = (() => {
    /**
     * Aktuellen Anfrage.
     *
     * @type {object|null}
     * @property {string} id - UUID der Anfrage.
     * @property {string} action - Angefragte Aktion.
     */
    let _request = {
        id:  localStorage.getItem("tichuRequestId"),
        action:  localStorage.getItem("tichuRequestAction")
    };

    /**
     * Initialisiert die Anwendung und alle Kernmodule.
     *
     * Wird durch main() aufgerufen.
     */
    function init() {
        console.debug("App.init()");

        //Config
        //Lib
        //State.init();
        //User.init();
        //EventBus

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

        Network.init();
        SoundManager.init();
        Modals.init();
        ViewManager.init();

        // QueryString der URL auswerten
        const urlParams = new URLSearchParams(window.location.search);
        const paramPlayerName = urlParams.get('player_name');
        const paramTableName = urlParams.get('table_name');
        if (paramPlayerName && paramTableName) {
            console.debug('URL-Parameter:', paramPlayerName, paramTableName);
            User.setPlayerName(paramPlayerName);
            User.setTableName(paramTableName);
        }

        // Ansicht aktualisieren
        _renderView();
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
        console.debug("App._handleNetworkOpen()", event);
        _renderView();
    }

    /**
     * Wird aufgerufen, wenn die WebSocket-Verbindung geschlossen wird.
     *
     * @param {CloseEvent} event - Das CloseEvent der WebSocket (siehe https://developer.mozilla.org/en-US/docs/Web/API/CloseEvent).
     */
    function _handleNetworkClose(event) {
        console.debug("App._handleNetworkClose()", event.code, event.reason, event.wasClean);
        _renderView();
    }

    /**
     * Wird aufgerufen, wenn ein Netzwerkfehler auftritt.
     *
     * @param {NetworkError} error - Der Netzwerkfehler.
     */
    function _handleNetworkError(error) {
        console.debug("App._handleNetworkError()", error);
        _renderView(error.message);
        Modals.showErrorToast(`Fehler ${error.message}`);
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
        console.log("App._handleServerRequest()", request.request_id, request.action);
        _setRequest(request.request_id, request.action);
        State.setPublicState(request.public_state)
        State.setPrivateState(request.private_state)
        // switch (request.action) {
        //     case 'announce_grand_tichu': // Der Spieler wird gefragt, ob er ein großes Tichu ansagen will.
        //         break;
        //     case 'schupf': // Der Spieler muss drei Karten zum Tausch abgeben. Diese Aktion kann durch ein Interrupt abgebrochen werden.
        //         break;
        //     case 'play': // Der Spieler muss Karten ausspielen oder passen. Diese Aktion kann durch ein Interrupt abgebrochen werden.
        //         break;
        //     case 'bomb': // Der Spieler kann eine Bombe werfen. Wenn der Client zuvor eine Bombe angekündigt hat, muss er eine Bombe auswählen. Ansonsten kann er auch passen.
        //         break;
        //     case 'wish': // Der Spieler muss sich einen Kartenwert wünschen.
        //         break;
        //     case 'give_dragon_away': // Der Spieler muss den Gegner benennen, der den Drachen bekommen soll.
        //         break;
        //     default:
        //         console.warn('App: Unbehandelte Server-Request:', request.action);
        // }
        _renderView();
    }

    /**
     * Wird aufgerufen, wenn der Server eine Benachrichtigung gesendet hat.
     *
     * @param {ServerNotification} notification - Die Nachricht.
     */
    function _handleServerNotification(notification) {
        console.debug("App._handleServerNotification()", notification.event, notification.context);
        const context = notification.context || {};

        // Spielzustand aktualisieren
        switch (notification.event) {
            case "player_joined":
                if (context.public_state && context.private_state) { // Der Benutzer ist beigetreten.
                    State.setPublicState(context.public_state);
                    State.setPrivateState(context.private_state);
                }
                else { // Ein Mitspieler ist beigetreten.
                    State.setPlayerName(context.player_index, context.player_name);
                }
                break;
            case "player_left": // Der Spieler hat das Spiel verlassen; eine KI ist eingesprungen.
                State.setPlayerName(context.player_index, context.player_name);
                State.setHostIndex(context.host_index);
                break;
            case "players_swapped": // Der Index zweier Spieler wurde getauscht.
                const name1 = State.getPlayerName(context.player_index_1);
                const name2 = State.getPlayerName(context.player_index_2);
                State.setPlayerName(context.player_index_1, name2);
                State.setPlayerName(context.player_index_2, name1);
                if (State.getPlayerIndex() === context.player_index_1) {
                    State.setPlayerIndex(context.player_index_2);
                }
                else if (State.getPlayerIndex() === context.player_index_2) {
                    State.setPlayerIndex(context.player_index_1);
                }
                break;
            case "game_started": // Das Spiel wurde gestartet.
                State.setRunning(true);
                State.resetGameScore();
                break;
            case "round_started": // Eine neue Runde beginnt. Die Karten werden gemischt.
                // todo State zurücksetzen
                break;
            case "hand_cards_dealt": // Handkarten wurden an die Spieler verteilt.
                State.setHostIndex(context.hand_cards);
                const count = context.hand_cards;
                State.setCountHandCards(1, count);
                State.setCountHandCards(2, count);
                State.setCountHandCards(3, count);
                break;
            case "player_grand_announced": // Der Spieler hat ein großes Tichu angesagt oder abgelehnt.
                State.setAnnouncement(context.player_index, context.announced ? 2 : 0);
                if (context.player_index === State.getPlayerIndex()) {
                    _removeRequest();
                }
                break;
            case "player_announced": // Der Spieler hat ein einfaches Tichu angesagt.
                State.setAnnouncement(context.player_index, 1);
                break;
            case "player_schupfed": // Der Spieler hat drei Karten zum Tausch abgegeben.
                if (context.given_schupf_cards) { // Der Benutzer hat geschupft.
                    State.setGivenSchupfCards(context.given_schupf_cards);
                    _removeRequest();
                }
                else {
                    State.setCountHandCards(context.player_index, 11);
                }
                break;
            case "schupf_cards_dealt": // Die Tauschkarten wurden an die Spieler verteilt.
                State.setReceivedSchupfCards(context.received_schupf_cards);
                break;
            case "player_passed": // Der Spieler hat gepasst.
                // {player_index: int}
                if (context.player_index === State.getPlayerIndex()) {
                    _removeRequest();
                }
                break;
            case "player_played": // Der Spieler hat Karten ausgespielt.
            case "player_bombed": // Der Spieler hat eine Bombe geworfen.
                // {player_index: int, cards: Cards}
                State.setTrickOwnerIndex(context.player_index);
                State.setTrickCards(context.cards);
                // State.setTricks() todo addTrick()
                if (context.player_index === State.getPlayerIndex()) {
                    _removeRequest();
                    // todo Karten von der Hand nehmen.
                }
                else {
                    State.setCountHandCards(context.player_index, State.getCountHandCards() - context.cards.length);
                }
                break;
            case "wish_made": // Ein Kartenwert wurde sich gewünscht.
                State.setWishValue(context.wish_value);
                if (State.isCurrentPlayer()) {
                    _removeRequest();
                }
                break;
            case "wish_fulfilled": // Der Wunsch wurde erfüllt.
                State.setWishValue(-State.getWishValue());
                break;
            case "trick_taken": // Der Spieler hat den Stich kassiert.
                // {player_index: int}
                // State.setTricks() todo addTrick()
                if (State.isCurrentPlayer()) {
                    _removeRequest();
                }
                break;
            case "player_turn_changed": // Der Spieler ist jetzt am Zug.
                State.setCurrentTurnIndex(context.current_turn_index);
                break;
            case "round_over": // Die Runde ist vorbei und die Karten werden neu gemischt.
                const entry20 = context.score_entry[0].toString().padStart(4, '0');
                const entry31 = context.score_entry[1].toString().padStart(4, '0');
                Modals.showRoundOverDialog(`${entry20} : ${entry31}`)
                break;
            case "game_over": // Die Runde ist vorbei und die Partie ist entschieden.
                const score20 = Lib.sum(context.game_score[0]).toString().padStart(4, '0');
                const score31 = Lib.sum(context.game_score[1]).toString().padStart(4, '0');
                Modals.showGameOverDialog(`${score20} : ${score31}`)
                break;
            default:
                console.error('App: Unbehandelte Server-Notification:', notification.event);
        }

        // Ansicht aktualisieren
        _renderView();
    }

    /**
     * Wird aufgerufen, wenn der Server eine Fehlermeldung gesendet hat.
     *
     * @param {ServerError} error - Die Fehlermeldung.
     */
    function _handleServerError(error) {
        console.debug("App._handleServerError()", error.message, error.code, error.context);
        _renderView(error.message);
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
        User.setPlayerName(playerName); // Lokale Namen setzen
        User.setTableName(tableName);
        Network.open(playerName, tableName);
        ViewManager.showLoadingView();
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
        ViewManager.showLoadingView();
    }

    /**
     * Wird aufgerufen, wenn der Benutzer die Lobby verlassen möchte.
     */
    function _handleLobbyViewExit() {
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
        if (!_request || _request.action  !== "announce_grand_tichu") {
            Modals.showErrorToast("Keine Anfrage für große Tichu-Ansage erhalten.");
            return
        }
        Network.send("response", {
            request_id: _request.id,
            response_data: {
                announced: announced
            }
        });
    }

    /**
     * Wird aufgerufen, wenn der Benutzer ein einfaches Tichu ansagen möchte.
     */
    function _handleTableViewTichu() {
        Network.send("announce");
    }

    /**
     * Wird aufgerufen, wenn der Benutzer Tauschkarten abgeben möchte.
     *
     * @param {Cards} givenSchupfCards - Die drei Tauschkarten, die der Benutzer abgeben möchte.
     */
    function _handleTableViewSchupf(givenSchupfCards) {
        if (!_request || _request.action  !== "schupf") {
            Modals.showErrorToast("Keine Anfrage für Schupfen erhalten.");
            return
        }
        Network.send("response", {
            request_id: _request.id,
            response_data: {
                given_schupf_cards: givenSchupfCards
            }
        });
    }

    /**
     * Wird aufgerufen, wenn der Benutzer Karten ausspielen möchte.
     *
     * @param {Cards} cards - Die Karten, die der Benutzer spielen möchte.
     */
    function _handleTableViewPlay(cards) {
        if (!_request || _request.action  !== "play") {
            Modals.showErrorToast("Keine Anfrage für Ausspielen erhalten.");
            return
        }
        Network.send("response", {
            request_id: _request.id,
            response_data: {
                cards: cards
            }
        });
    }

    /**
     * Wird aufgerufen, wenn der Benutzer eine Bombe ankündigen will.
     */
    function _handleTableViewBomb() {
        Network.send("bomb");
    }

    /**
     * Wird aufgerufen, wenn der Benutzer sich einen Kartenwert wünschen möchte.
     *
     * @param wishValue - Der gewünschte Kartenwert.
     */
    function _handleTableViewWish(wishValue) {
        if (!_request || _request.action  !== "wish") {
            Modals.showErrorToast("Keine Anfrage für Wünschen erhalten.");
            return
        }
        Network.send("response", {
            request_id: _request.id,
            response_data: {
                wish_value: wishValue
            }
        });
    }

    /**
     * Wird aufgerufen, wenn der Benutzer den Gegner ausgewählt hat, der den Drachen geschenkt bekommen soll.
     *
     * @param {number} dragonRecipient - Der Index des Spielers, der den Drachen bekommt (kanonisch).
     */
    function _handleTableViewGiveDragonAway(dragonRecipient) {
        if (!_request || _request.action  !== "give_dragon_away") {
            Modals.showErrorToast("Keine Anfrage für Wünschen erhalten.");
            return
        }
        Network.send("response", {
            request_id: _request.id,
            response_data: {
                dragon_recipient: dragonRecipient
            }
        });
    }

    /**
     * Wird aufgerufen, wenn der Benutzer die Punktetabelle schließt und ein damit die Partie abgeschlossen ist.
     */
    function _handleTableViewGameOver() {
        _renderView();
    }

    /**
     * Wird aufgerufen, wenn der Benutzer den Spieltisch verlassen möchte
     */
    function _handleTableViewExit() {
        Network.send('leave');
        ViewManager.showLoadingView();
    }

    // --------------------------------------------------------------------------------------
    // Hilfsfunktionen
    // --------------------------------------------------------------------------------------

    /**
     * Rendert die View.
     */
    function _renderView() {
        if (Network.isReady()) {
            if (State.isRunning()) {
                ViewManager.showTableView();
            }
            else {
                ViewManager.showLobbyView();
            }
        }
        else {
            if (Network.getSessionId()) {
                // es wird automatisch versucht, die Verbindung wieder aufzubauen.
                ViewManager.showLoadingView();
            }
            else {
                ViewManager.showLoginView();
            }
        }

        if (_request && _request.action === "wish") {
            Modals.showWishDialog();
        }
        else if (_request && _request.action === "give_dragon_away") {
            Modals.showDragonDialog();
        }
    }

    /**
     * Speichert die aktuelle Anfrage.
     *
     * @param {string} requestId - Die neue Request-ID.
     * @param {string} requestAction - Die neue angefragte Aktion.
     */
    function _setRequest(requestId, requestAction) {
        _request = {
            id: requestId,
            action: requestAction,
        };
        localStorage.setItem('tichuRequestId', requestId);
        localStorage.setItem('tichuRequestAction', requestAction);
        console.debug("App._setRequest()", requestId, requestAction);
    }

    /**
     * Löscht die aktuelle Anfrage.
     */
    function _removeRequest() {
        _request = null;
        localStorage.removeItem('tichuRequestId');
        localStorage.removeItem('tichuRequestAction');
        console.debug("App._removeRequest()");
    }

    return {
        init,
    };
})();