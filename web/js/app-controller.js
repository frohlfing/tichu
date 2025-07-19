/**
 * Aktualisiert den Spielzustand und schaltet zwischen den Views um.
 */
const AppController = (() => {

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
        //EventBus.on("tableView:bomb", _handleTableViewBomb);
        EventBus.on("tableView:gameOver", _handleTableViewGameOver);
        EventBus.on("tableView:exit", _handleTableViewExit);

        // Ereignishändler für Dialoge einrichten
        EventBus.on("wishDialog:select", _handleWishDialogSelect);
        EventBus.on("dragonDialog:select", _handleDragonDialogSelect);

        Network.init();
        Sound.init();
        Modal.init();
        ViewManager.init();

        // QueryString der URL auswerten
        const urlParams = new URLSearchParams(window.location.search);
        const paramPlayerName = urlParams.get('player_name');
        if (paramPlayerName) {
            console.debug('paramPlayerName:', paramPlayerName);
            User.setPlayerName(paramPlayerName);
        }
        const paramTableName = urlParams.get('table_name');
        if (paramTableName) {
            console.debug('paramTableName:', paramTableName);
            User.setTableName(paramTableName);
        }
        // Sound deaktivieren, falls gewünscht
        Sound.setEnabled(urlParams.get('sound') !== 'false');

        // Ansicht aktualisieren
        _renderView();
    }

    /**
     * Wird aufgerufen, wenn ein Fehler auftritt.
     */
    window.addEventListener("error", function(event) {
        //console.error("Fehler abgefangen", event.message, event.filename, event.lineno);
    });

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
        console.debug("App._handleNetworkClose()", Network.getWSCloseCodeName(event.code), event.reason, event.wasClean);
        _renderView();
    }

    /**
     * Wird aufgerufen, wenn ein Netzwerkfehler auftritt.
     *
     * @param {NetworkError} error - Der Netzwerkfehler.
     */
    function _handleNetworkError(error) {
        console.error("App._handleNetworkError()", error);
        Modal.showErrorToast(error.message);
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
        console.log("App._handleServerRequest()", request.action, request.context);
        State.setPendingAction(request.action)
        const context = request.context || {};
        switch (request.action) {
            case 'announce_grand_tichu': // Der Spieler wird gefragt, ob er ein großes Tichu ansagen will.
                break;
            case 'schupf': // Der Spieler muss drei Karten zum Tausch abgeben. Diese Aktion kann durch ein Interrupt abgebrochen werden.
                State.setHandCards(context.hand_cards);
                break;
            case 'play': // Der Spieler muss Karten ausspielen oder passen. Diese Aktion kann durch ein Interrupt abgebrochen werden.
                State.setHandCards(context.hand_cards);
                State.setTrickCombination(context.trick_combination);
                State.setWishValue(context.wish_value);
                break;
            case 'wish': // Der Spieler muss sich einen Kartenwert wünschen.
                break;
            case 'give_dragon_away': // Der Spieler muss den Gegner benennen, der den Drachen bekommen soll.
                break;
            default:
                console.warn('App: Unbehandelte Server-Request:', request.action);
        }
        _renderView();
    }

    /**
     * Wird aufgerufen, wenn der Server eine Benachrichtigung gesendet hat.
     *
     * @param {ServerNotification} notification - Die Nachricht.
     */
    function _handleServerNotification(notification) {
        console.debug("App._handleServerNotification()", notification.event, notification.context, State.getCountHandCards(0), State.getCountHandCards(1), State.getCountHandCards(2), State.getCountHandCards(3));
        const context = notification.context || {};

        // Spielzustand aktualisieren
        switch (notification.event) {
            case "player_joined":
                if (context.public_state && context.private_state) { // Der Benutzer ist beigetreten.
                    State.setPublicState(context.public_state);
                    State.setPrivateState(context.private_state);
                    if (State.getReceivedSchupfCards()) {
                        State.confirmReceivedSchupfCards()
                    }
                    if (context.pending_action) {
                        State.setPendingAction(context.pending_action);
                    }
                    else {
                        State.removePendingAction();
                    }
                }
                else { // Ein Mitspieler ist beigetreten.
                    State.setPlayerName(context.player_index, context.player_name);
                }
                break;
            case "player_left": // Ein Spieler hat das Spiel verlassen; eine KI ist eingesprungen.
                State.setPlayerName(context.player_index, context.player_name);
                State.setHostIndex(context.host_index);
                break;
            case "players_swapped": // Die Position zweier Spieler wurde getauscht.
                State.swapPlayerNames(context.player_index_1, context.player_index_2);
                break;
            case "game_started": // Das Spiel wurde gestartet.
                State.setRunning(true);
                State.resetGame();
                break;
            case "round_started": // Eine neue Runde beginnt. Die Karten werden gemischt.
                State.resetRound();
                break;
            case "hand_cards_dealt": // Handkarten wurden an die Spieler verteilt.
                if (context.hand_cards) { // Der Benutzer hat Karten bekommen.
                    State.setHandCards(context.hand_cards);
                }
                else { // Ein Mitspieler hat Karten bekommen.
                    State.setCountHandCards(context.player_index, context.count);
                }
                break;
            case "player_announced": // Ein Spieler hat ein Tichu angesagt.
                State.setAnnouncement(context.player_index, context.grand ? 2 : 1);
                if (context.grand && context.player_index === State.getPlayerIndex()) {
                    State.removePendingAction();
                }
                break;
            case "player_schupfed": // Ein Spieler hat drei Karten zum Tausch abgegeben.
                if (context.given_schupf_cards) { // Der Benutzer hat geschupft.
                    // todo Handkarten besser übergeben?
                    const cards = State.getHandCards().filter(card => !Lib.includesCard(card, context.given_schupf_cards));
                    State.setHandCards(cards);
                    State.setGivenSchupfCards(context.given_schupf_cards);
                    State.removePendingAction();
                }
                else { // Ein Mitspieler hat geschupft.
                    State.setCountHandCards(context.player_index, 11);
                }
                break;
            case "start_playing": // Die Karten können nun ausgespielt werden.
                State.setReceivedSchupfCards(context.received_schupf_cards);
                // todo Handkarten besser übergeben?
                const cards = State.getHandCards().concat(context.received_schupf_cards);
                Lib.sortCards(cards)
                State.setHandCards(cards);
                for (let relativeIndex = 1; relativeIndex <= 3; relativeIndex++) {
                    State.setCountHandCards(Lib.getCanonicalPlayerIndex(relativeIndex), 14);
                }
                State.setStartPlayerIndex(context.start_player_index);
                State.setCurrentTurnIndex(context.start_player_index);
                break;
            case "player_passed": // Ein Spieler hat gepasst.
                if (context.player_index === State.getPlayerIndex()) {
                    State.removePendingAction();
                }
                break;
            case "player_played": // Ein Spieler hat Karten ausgespielt.
                if (context.turn[0] === State.getPlayerIndex()) { // Der Benutzer hat Karten ausgespielt.
                    // todo Handkarten besser übergeben?
                    let cards = State.getHandCards().filter(card => !Lib.includesCard(card, context.turn[1]));
                    State.setHandCards(cards);
                    if (context.turn[0] !== State.getCurrentTurnIndex()) { // Benutzer war nicht am Zug, hat also eine Bombe geworfen
                        State.setCurrentTurnIndex(context.turn[0]);
                    }
                    State.removePendingAction();
                }
                else { // Ein Mitspieler hat Karten ausgespielt.
                    // todo Anzahl Handkarten besser übergeben?
                    State.setCountHandCards(context.turn[0], State.getCountHandCards(context.turn[0]) - context.turn[1].length);
                    if (context.turn[0] !== State.getCurrentTurnIndex()) { // Der Mitspieler war nicht am Zug, hat also eine Bombe geworfen
                        State.setCurrentTurnIndex(context.turn[0]);
                        State.removePendingAction();
                    }
                }
                State.setPlayedCards(State.getPlayedCards().concat(context.turn[1]));
                // todo eine Funktion State.addTurn() bereitstellen
                if (State.getTrickOwnerIndex() === -1) { // neuer Stich?
                    State.addTrick([context.turn]);
                }
                else {
                    State.getLastTrick().push(context.turn);
                }
                State.setTrickOwnerIndex(context.turn[0]);
                State.setTrickCards(context.turn[1]);
                State.setTrickCombination(context.turn[2]);
                State.setTrickPoints(context.trick_points);
                State.setWinnerIndex(context.winner_index);
                break;
            case "wish_made": // Ein Kartenwert wurde gewünscht.
                State.setWishValue(context.wish_value);
                if (State.isCurrentPlayer()) {
                    State.removePendingAction();
                }
                break;
            case "wish_fulfilled": // Der Wunsch wurde erfüllt.
                // todo wish_value besser übergeben?
                State.setWishValue(-State.getWishValue());
                break;
            case "trick_taken": // Der Spieler hat den Stich kassiert.
                State.setTrickOwnerIndex(-1);
                State.setTrickCards([]);
                State.setTrickCombination( /** @type Combination */[CombinationType.PASS, 0, 0]);
                State.setTrickPoints(0);
                State.incTrickCounter();
                State.setPoints(context.player_index, context.points);
                State.setDragonRecipient(context.dragon_recipient);
                if (State.isCurrentPlayer() && State.getPendingAction() === "give_dragon_away") {
                    State.removePendingAction();
                }
                break;
            case "player_turn_changed": // Der Spieler ist jetzt am Zug.
                State.setCurrentTurnIndex(context.current_turn_index);
                break;
            case "round_over": // Die Runde ist vorbei und die Karten werden neu gemischt.
                for (let playerIndex = 0; playerIndex <= 3; playerIndex++) {
                    State.setPoints(playerIndex, context.points[playerIndex]);
                }
                State.setLoserIndex(context.loser_index);
                State.setRoundOver(true);
                State.setDoubleVictory(context.is_double_victory);
                // todo TotalScore sollte ebenfalls oder statt GameScore übergeben werden (sonst würde ein Fehleintrag nicht korrigiert werden)
                State.addGameScoreEntry([context.points[2] + context.points[0], context.points[3] + context.points[1]])
                State.incRoundCounter();
                Modal.showRoundOverDialog()
                break;
            case "game_over": // Die Runde ist vorbei und die Partie ist entschieden.
                State.setRunning(false);
                Modal.showGameOverDialog()
                break;
            default:
                console.error('App: Unbehandelte Server-Notification:', notification.event);
        }

        // Ansicht aktualisieren
        _renderView();
    }

    /**
     * Wird aufgerufen, wenn die Game-Engine eine Fehlermeldung gesendet hat.
     *
     * @param {ServerError} error - Die Fehlermeldung.
     */
    function _handleServerError(error) {
        console.error("App._handleServerError()", error.message, Network.getServerErrorCodeName(error.code), error.context);
        Modal.showErrorToast(`Fehler ${error.message}`);
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
        if (State.getPendingAction() !== "announce_grand_tichu") {
            Modal.showErrorToast("Keine Anfrage für große Tichu-Ansage erhalten.");
            return
        }
        Network.send("response", {
            action: State.getPendingAction(),
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
        if (State.getPendingAction() !== "schupf") {
            Modal.showErrorToast("Keine Anfrage für Schupfen erhalten.");
            return
        }
        Network.send("response", {
            action: State.getPendingAction(),
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
        if (State.getPendingAction() !== "play") {
            if (State.isPlayableBomb(cards)) {
                Network.send("bomb", {cards: cards});
            }
            else {
                Modal.showErrorToast("Keine Anfrage für Ausspielen erhalten.");
            }
            return
        }
        Network.send("response", {
            action: State.getPendingAction(),
            response_data: {
                cards: cards
            }
        });
    }

    // /**
    //  * Wird aufgerufen, wenn der Benutzer außerhalb seines regulären Zuges eine Bombe werfen will.
    //  *
    //  * @param {Cards} cards - Die Karten, die der Benutzer spielen möchte.
    //  */
    // function _handleTableViewBomb(cards) {
    //     Network.send("bomb", {cards: cards});
    // }

    /**
     * Wird aufgerufen, wenn der Benutzer die Punktetabelle schließt und damit die Partie abgeschlossen ist.
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
    // Ereignishändler für die Dialoge
    // --------------------------------------------------------------------------------------

    /**
     * Ereignishändler für den Wish-Dialog.
     *
     * @param {number} value - Der gewählte Kartenwert (2 bis 14).
     */
    function _handleWishDialogSelect(value) {
        if (State.getPendingAction() !== "wish") {
            Modal.showErrorToast("Keine Anfrage für Wünschen erhalten.");
            return
        }
        Network.send("response", {
            action: State.getPendingAction(),
            response_data: {
                wish_value: value
            }
        });
    }

    /**
     * Ereignishändler für den Dragon-Dialog.
     *
     * @param {number} value - Der zum Benutzer relative Index des gewählten Gegners (1 == rechts, 3 == links).
     */
    function _handleDragonDialogSelect(value) {
        if (State.getPendingAction() !== "give_dragon_away") {
            Modal.showErrorToast("Keine Anfrage für Wünschen erhalten.");
            return
        }
        const dragonRecipient = Lib.getCanonicalPlayerIndex(value);
        Network.send("response", {
            action: State.getPendingAction(),
            response_data: {
                dragon_recipient: dragonRecipient
            }
        });
    }

    // --------------------------------------------------------------------------------------
    // Hilfsfunktionen
    // --------------------------------------------------------------------------------------

    /**
     * Rendert die View.
     */
    function _renderView() {
        console.debug("Render", State.getCountHandCards(0), State.getCountHandCards(1), State.getCountHandCards(2), State.getCountHandCards(3))
        if (Network.isReady()) {
            if (State.isRunning()) {
                ViewManager.showTableView();
                // todo besser über TableView steuern:
                if (State.getPendingAction() === "wish") {
                    Modal.showWishDialog();
                }
                else if (State.getPendingAction() === "give_dragon_away") {
                    Modal.showDragonDialog();
                }
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
    }

    return {
        init,
    };
})();