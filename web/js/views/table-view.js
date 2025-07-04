/**
 * Anzeige und Interaktion des Spieltisches.
 *
 * @type {View}
 */
const TableView = (() => {

    // --------------------------------------------------------------------------------------
    // DOM-Elemente
    // --------------------------------------------------------------------------------------

    /**
     * Der Container des Spieltisch-Bildschirms.
     *
     * @type {HTMLDivElement}
     */
    const _viewContainer = document.getElementById('table-screen');

    /**
     * Button zum Beenden des Spiels/Verlassen des Tisches.
     *
     * @type {HTMLButtonElement}
     */
    const _exitButton = document.getElementById('exit-button');

    /**
     * Button für Spieloptionen.
     *
     * @type {HTMLButtonElement}
     */
    const _settingsButton = document.getElementById('settings-button');

    /**
     * Die Anzeige des Punktestandes.
     *
     * @type {HTMLDivElement}
     */
    const _scoreDisplay = document.getElementById('score-display');

    /**
     * Die Namen der Spieler.
     *
     * @type {Array<HTMLElement>}
     */
    const _playerNames = [
        document.getElementById('player-name-bottom'),
        document.getElementById('player-name-right'),
        document.getElementById('player-name-top'),
        document.getElementById('player-name-left'),
    ];

    /**
     * Die Hände (Container für die Handkarten).
     *
     * @type {Array<HTMLElement>}
     */
    const _hands = [
        document.getElementById('hand-bottom'),
        document.getElementById('hand-right'),
        document.getElementById('hand-top'),
        document.getElementById('hand-left'),
    ];

    /**
     * Die Ablage-Zonen für die Tauschkarten.
     *
     * @type {Array<HTMLElement>}
     */
    const _schupfZones = [
        document.getElementById('schupf-zone-bottom'),
        document.getElementById('schupf-zone-right'),
        document.getElementById('schupf-zone-top'),
        document.getElementById('schupf-zone-left'),
    ];

    /**
     * Die Ablage-Zonen für den aktuellen Stich.
     *
     * @type {Array<HTMLElement>}
     */
    const _trickZones = [
        document.getElementById('trick-zone-bottom'),
        document.getElementById('trick-zone-right'),
        document.getElementById('trick-zone-top'),
        document.getElementById('trick-zone-left'),
    ];

    /**
     * Die Symbole für eine Tichu-Ansage.
     *
     * @type {Array<HTMLElement>}
     */
    const _tichuIcons = [
        document.getElementById('tichu-icon-bottom'),
        document.getElementById('tichu-icon-right'),
        document.getElementById('tichu-icon-top'),
        document.getElementById('tichu-icon-left'),
    ];

    /**
     * Das Hintergrundbild für den offenen Wunsch.
     *
     * @type {HTMLImageElement}
     */
    const _wishIcon = document.getElementById('wish-icon');

    /**
     * Die Anzeige des gewünschten Kartenwerts.
     *
     * @type {HTMLSpanElement}
     */
    const _wishText = document.getElementById('wish-text');

    /**
     * Das Bomben-Symbol.
     *
     * @type {HTMLImageElement}
     */
    const _bombIcon = document.getElementById('bomb-icon');

    /**
     * Button zum Passen.
     *
     * @type {HTMLButtonElement}
     */
    const _passButton = document.getElementById('pass-button');

    /**
     * Button zum Tich ansagen.
     *
     * @type {HTMLButtonElement}
     */
    const _tichuButton = document.getElementById('tichu-button');

    /**
     * Button zum schupfen, Tauschkarten aufnehmen und Karten ausspielen
     *
     * @type {HTMLButtonElement}
     */
    const _playButton = document.getElementById('play-button');

    // --------------------------------------------------------------------------------------
    // Interne Variablen
    // --------------------------------------------------------------------------------------

    /**
     * Wird gesetzt, wenn der Benutzer die drei Tauschkarten der Mitspieler aufgenommen hat.
     *
     * @type {boolean}
     */
    let _receivedSchupfCardsConfirmed = false;

    // --------------------------------------------------------------------------------------
    // Öffentliche Funktionen
    // --------------------------------------------------------------------------------------

    /**
     * Initialisiert den Spieltisch-Bildschirm.
     */
    function init() {
        // Netzwerk-Ereignisse
        //EventBus.on("network:message", _handleNetworkMessage);

        // Ereignishändler für Dialoge einrichten
        EventBus.on("exitDialog:select", _handleExitDialogSelect);

        // Ereignishändler für die Controls einrichten
        _exitButton.addEventListener('click', _handleExitButtonClick);
        _settingsButton.addEventListener('click', _handleSettingsButtonClick);
        _passButton.addEventListener('click', _handlePassButtonClick);
        _tichuButton.addEventListener('click', _handleTichuButtonClick);
        _playButton.addEventListener('click', _handlePlayButtonClick);
        _bombIcon.addEventListener('click', _handleBombIconClick);
        _hands[0].addEventListener('click', _handleHandClick);
        _schupfZones[0].addEventListener('click', _handleSchupfZoneClick);
    }

    /**
     * Rendert den Spieltisch-Bildschirm anhand des aktuellen Spielzustands.
     */
    function render() {
        _receivedSchupfCardsConfirmed = State.getReceivedSchupfCards() !== null
        _updateScore();
        for (let playerIndex= 0; playerIndex <= 3; playerIndex++) {
            _updatePlayerName(playerIndex);
            _updateHand(playerIndex);
            _updateSchupfZone(playerIndex);
            _updateTichuIcon(playerIndex);
        }
        _updateTrick();
        _updateCurrentPlayer();
        _updateWishIcon();
        _updateBombIcon();
        _updatePassButton();
        _updateTichuButton();
        _updatePlayButton();
    }

    /**
     * Rendert den Spieltisch-Bildschirm und zeigt ihn anschließend an.
     */
    function show() {
        render();
        _viewContainer.classList.add('active');
    }

    /**
     * Blendet den Spieltisch-Bildschirm aus.
     */
    function hide() {
        _viewContainer.classList.remove('active');
    }

    /**
     * Ermittelt, ob der Spieltisch-Bildschirm gerade angezeigt wird.
     *
     * @returns {boolean}
     */
    function isVisible() {
        return _viewContainer.classList.contains('active');
    }

    // --------------------------------------------------------------------------------------
    // Ereignishändler für Servernachrichten
    // --------------------------------------------------------------------------------------

    // /**
    //  * Wird aufgerufen, wenn eine Netzwerknachricht empfangen wurde.
    //  *
    //  * @param {NetworkMessage} message - Die Nachricht vom Server.
    //  */
    // function _handleNetworkMessage(message) {
    //     if (message.type === 'request') {
    //         //_handleServerRequest(/** @type {ServerRequest} */ message.payload);
    //     }
    //     else if (message.type === 'notification') {
    //         _handleServerNotification(/** @type {ServerNotification} */ message.payload);
    //     }
    // }
    //
    // /**
    //  * Wird aufgerufen, wenn der Server eine Benachrichtigung gesendet hat.
    //  *
    //  * @param {ServerNotification} notification - Die Nachricht.
    //  */
    // function _handleServerNotification(notification) {
    //     const context = notification.context || {};
    //     switch (notification.event) {
    //         case "player_joined": // Ein Spieler ist beigetreten.
    //         case "player_left": // Ein Spieler hat das Spiel verlassen; eine KI ist eingesprungen.
    //             // Wenn der Benutzer beigetreten ist, wird diese View durch den App-Controller neu gerendert.
    //             // Nur wenn ein Mitspieler beigetreten ist, wird player_index angegeben.
    //             if (context.player_index) {
    //                 _updatePlayerName(context.player_index);
    //             }
    //             break;
    //         case "players_swapped": // Der Index zweier Spieler wurde getauscht.
    //             break;  // Findet in der Lobby statt.
    //         case "game_started": // Das Spiel wurde gestartet.
    //             break;
    //         case "round_started": // Eine neue Runde beginnt. Die Karten werden gemischt.
    //             break;
    //         case "hand_cards_dealt": // Handkarten wurden an die Spieler verteilt.
    //             for (let playerIndex = 0; playerIndex <= 3; playerIndex++) {
    //                 _updateHand(playerIndex);
    //             }
    //             break;
    //         case "player_grand_announced": // Der Spieler hat ein großes Tichu angesagt oder abgelehnt.
    //         case "player_announced": // Der Spieler hat ein einfaches Tichu angesagt.
    //             _updateTichuIcon(context.player_index);
    //             _updateTichuButton();
    //             break;
    //         case "player_schupfed": // Der Spieler hat drei Karten zum Tausch abgegeben.
    //             _updateSchupfZone(context.player_index);
    //             break;
    //         case "schupf_cards_dealt": // Die Tauschkarten wurden an die Spieler verteilt.
    //             _updateSchupfZone(State.getPlayerIndex());
    //             for (let relativeIndex = 1; relativeIndex <= 3; relativeIndex++) {
    //                 const playerIndex = Lib.getCanonicalPlayerIndex(relativeIndex);
    //                 _updateHand(playerIndex);
    //                 _updateSchupfZone(playerIndex);
    //             }
    //             break;
    //         case "player_passed": // Der Spieler hat gepasst.
    //             // {player_index: int}
    //             break;
    //         case "player_played": // Der Spieler hat Karten ausgespielt.
    //             // {player_index: int, cards: Cards}
    //             _updateHand(context.player_index)
    //             _updateTrick();
    //             // _updatePlayButton();
    //             break;
    //         case "player_bombed": // Der Spieler hat eine Bombe geworfen.
    //             // {player_index: int, cards: Cards}
    //             _updateBombIcon();
    //             break;
    //         case "wish_made": // Ein Kartenwert wurde sich gewünscht.
    //         case "wish_fulfilled": // Der Wunsch wurde erfüllt.
    //             _updateWishIcon();
    //             break;
    //         case "trick_taken": // Der Spieler hat den Stich kassiert.
    //             // {player_index: int}
    //             _updateTrick();
    //             break;
    //         case "player_turn_changed": // Der Spieler ist jetzt am Zug.
    //             // {current_turn_index: int}
    //             _updateCurrentPlayer();
    //             _updatePassButton();
    //             _updatePlayButton();
    //             break;
    //         case "round_over": // Die Runde ist vorbei und die Karten werden neu gemischt.
    //             // {score_entry: (int, int), is_double_victory: bool}
    //             break;
    //         case "game_over": // Die Runde ist vorbei und die Partie ist entschieden.
    //             // {game_score: (list, list)}
    //             break;
    //         default:
    //             console.error('App: Unbehandelte Server-Notification:', notification.event);
    //     }
    // }

    // --------------------------------------------------------------------------------------
    // Ereignishändler für die Dialoge
    // --------------------------------------------------------------------------------------

    /**
     * Ereignishändler für den Exit-Dialog.
     *
     * @param {number} value - Der gedrückte Button (1 == ja, 0 == nein).
     */
    function _handleExitDialogSelect(value) {
        if (value) {
            EventBus.emit("tableView:exit");
        }
    }

    // --------------------------------------------------------------------------------------
    // Ereignishändler für Controls
    // --------------------------------------------------------------------------------------

    /**
     * Ereignishändler für den "Beenden"-Button.
     */
    function _handleExitButtonClick() {
        SoundManager.playSound('buttonClick');
        Modals.showExitDialog();
    }

    /**
     * Ereignishändler für den "Optionen"-Button.
     */
    function _handleSettingsButtonClick() {
        SoundManager.playSound('buttonClick');
        Modals.showErrorToast("Einstellungen sind noch nicht implementiert.");
    }

    /**
     * Ereignishändler für das Anklicken der eigenen Hand.
     *
     * @param {PointerEvent} event
     */
    function _handleHandClick(event) {
        if (!event.target.classList.contains('card')) {
            return; // es wurde auf keine Karte geklickt (sondern irgendwo anders innerhalb der Hand)
        }

        const cardElement = event.target;

        // Wenn die Schupfzone sichtbar ist, darf maximal nur eine Karte selektiert werden.
        if (!_schupfZones[0].classList.contains('hidden') && !cardElement.classList.contains("selected")) {
            if (_getSelectedCardsCount() > 0) {
                return;
            }
        }

        SoundManager.playSound('buttonClick');
        const card = /** @type Card */ cardElement.dataset.card.split(",").map(value => parseInt(value, 10));
        cardElement.classList.toggle('selected');
        _updatePlayButton();
    }

    /**
     * Ereignishändler für das Anklicken der Schupfzone.
     *
     * @param {PointerEvent} event
     */
    function _handleSchupfZoneClick(event) {
        if (event.target.classList.contains('schupf-subzone')) {
            // es wurde auf eine leere Ablagefläche geklickt
            const subzoneElement = event.target;
            const cardElement = _hands[0].querySelector('.card.selected');
            if (cardElement) {
                SoundManager.playSound('buttonClick');
                subzoneElement.appendChild(cardElement);
                cardElement.classList.remove('selected');
            }
            _updatePlayButton();
        }
        else if (event.target.classList.contains('card')) {
            // es wurde auf eine Karte in der Schupfzone geklickt
            const cardElement = event.target;

            // richtige Position in der Hand finden
            const [value, color] = /** @type Card */ cardElement.dataset.card.split(",").map(value => parseInt(value, 10));
            const cardElements = _hands[0].children;
            //const cardElements = Array.from(_hands[0].children);
            let referenceElement = null;
            for (const el of cardElements) {  // die Karten in der Hand sind aufsteigend sortiert
                const [v, c] = /** @type Card */ el.dataset.card.split(",").map(value => parseInt(value, 10));
                if (value < v || (value === v && color < c)) {
                    referenceElement = el;
                    break; // nächstgrößere Handkarte gefunden
                }
            }

            // Karte zurück in die Hand einsortieren
            SoundManager.playSound('buttonClick');
            if (referenceElement) {
                _hands[0].insertBefore(cardElement, referenceElement);
            }
            else {
                _hands[0].appendChild(cardElement);
            }

            _updatePlayButton();
        }
    }

    /**
     * Ereignishändler für das Bomben-Icon.
     */
    function _handleBombIconClick() {
        // Der Benutzer möchte eine Bombe ankündigen.
        _bombIcon.classList.add("disabled");
        SoundManager.playSound('buttonClick');
        EventBus.emit("tableView:bomb");
    }

    /**
     * Ereignishändler für den Pass-Button.
     */
    function _handlePassButtonClick() {
        _passButton.disabled = true;
        SoundManager.playSound('buttonClick');
        switch (_passButton.dataset.mode) {
            case "NO_GRAND_TICHU": // Der Benutzer möchte kein großes Tichu ansagen.
                EventBus.emit("tableView:grandTichu", false);
                break;
            case "PASS": // Der Benutzer möchte passen.
                EventBus.emit("tableView:play", []);
                break;
            default:
                console.error(`TableView: PlayButton-Mode ${_passButton.dataset.mode} nicht gehandelt.`);
            break;
        }
    }

    /**
     * Ereignishändler für den Tichu-Button.
     */
    function _handleTichuButtonClick() {
        _tichuButton.disabled = true;
        SoundManager.playSound('buttonClick');
        switch (_tichuButton.dataset.mode) {
            case "GRAND_TICHU": // Der Benutzer möchte ein großes Tichu ansagen.
                EventBus.emit("tableView:grandTichu", true);
                break;
            case "TICHU": // Der Benutzer möchte ein einfaches Tichu ansagen.
                EventBus.emit("tableView:tichu");
                break;
            default:
                console.error(`TableView: TichuButton-Mode ${_tichuButton.dataset.mode} nicht gehandelt.`);
            break;
        }
    }

    /**
     * Ereignishändler für den Play-Button.
     */
    function _handlePlayButtonClick() {
        _playButton.disabled = true;
        SoundManager.playSound('buttonClick');
        switch (_playButton.dataset.mode) {
            case "SCHUPF": // Der Benutzer möchte drei Tauschkarten für die Mitspieler abgeben.
                EventBus.emit("tableView:schupf", _getSchupfCards());
                break;
            case "RECEIVE": // Der Benutzer nimmt die drei Tauschkarten der Mitspieler auf.
                _receivedSchupfCardsConfirmed = true;
                const playerIndex = State.getPlayerIndex();
                _updateHand(playerIndex);
                _updateSchupfZone(playerIndex);
                _updatePlayButton();
                break;
            case "AUTOSELECT": // Die längste kleinstmögliche Kombination auswählen.
                _selectCards(State.getBestPlayableCombination()[0])
                _updatePlayButton();
                break;
            case "PLAY": // Der Benutzer möchte die ausgewählten Karten spielen.
                EventBus.emit("tableView:play", _getSelectedCards());
                break;
            default:
                console.error(`TableView: PlayButton-Mode ${_playButton.dataset.mode} nicht gehandelt.`);
            break;
        }
    }

    // --------------------------------------------------------------------------------------
    // Hilfsfunktionen
    // --------------------------------------------------------------------------------------

    /**
     * Aktualisiert den Punktestand in der Top-Bar.
     */
    function _updateScore() {
        const score = State.getTotalScore();
        const team20 = score[0].toString().padStart(4, '0');
        const team31 = score[1].toString().padStart(4, '0');
        _scoreDisplay.textContent = `${team20} : ${team31}`;
    }

    /**
     * Aktualisiert den Namen des angegebenen Spielers.
     *
     * @param {number} playerIndex - Der Index des Spielers.
     */
    function _updatePlayerName(playerIndex) {
        const relativeIndex = Lib.getRelativePlayerIndex(playerIndex);
        _playerNames[relativeIndex].textContent = State.getPlayerName(playerIndex).trim();
    }

    /**
     * Gibt die aktuell ausgewählten Karten zurück.
     *
     * @returns {Cards}
     */
    function _getSelectedCards() {
        let cards = [];
        _hands[0].querySelectorAll('.card.selected').forEach(cardElement => {
            cards.push(cardElement.dataset.card.split(",").map(value => parseInt(value, 10)));
        });
        return cards;
    }

    /**
     * Ermittelt die Anzahl der ausgewählten Handkarten.
     *
     * @returns {number}
     */
    function _getSelectedCardsCount() {
        return _hands[0].querySelectorAll('.card.selected').length;
    }

    /**
     * Setzt die ausgewählten Karten zurück.
     */
    function _clearSelectedCards() {
        _hands[0].querySelectorAll('.card.selected').forEach(cardElement => {
            cardElement.classList.remove('selected');
        });
    }

    /**
     * Wählt die gegebenen Karten in der Hand aus.
     *
     * @param {Cards} cards - Die Karten, die selektiert werden sollen.
     */
    function _selectCards(cards) {
        Array.from(_hands[0].children).forEach(cardElement => {
            const cardToFind = /** @type Card */ cardElement.dataset.card.split(",").map(value => parseInt(value, 10));
            if (Lib.includesCard(cardToFind, cards)) {
                cardElement.classList.add('selected');
            }
            else {
                cardElement.classList.remove('selected');
            }
        });
    }

    /**
     * Erzeugt eine Karte.
     *
     * @param {Card|null} card - Wert und Farbe der Karte. Wenn null, wird die Rückseite angezeigt.
     * @returns {HTMLDivElement}
     */
    function _createCardElement(card= null) {
        const cardElement = document.createElement('div');
        cardElement.className = 'card';
        if (card) {
            cardElement.style.backgroundImage = `url('images/cards/${Lib.stringifyCard(card)}.png')`;
            cardElement.dataset.card = card.toString();
        }
        else {
            cardElement.classList.add('back-site');
        }
        return cardElement;
    }

    /**
     * Aktualisiert die Hand des angegebenen Spielers.
     *
     * @param {number} playerIndex - Der Index des Spielers.
     */
    function _updateHand(playerIndex) {
        const relativeIndex = Lib.getRelativePlayerIndex(playerIndex);

        // Handkarten entfernen
        _hands[relativeIndex].replaceChildren();

        // wenn der Benutzer selbst keine Karten mehr hat, kann er in die Hände der Mitspieler sehen
        // todo Diese Feature ist serverseitig noch nicht umgesetzt. Es gibt noch keine Variable im State, um die Karten der Mitspieler zu speichern.
        //const revealed = State.getCountHandCards() === 0;  // Karten aufgedeckt

        // Handkarten neu generieren
        if (relativeIndex === 0) {
            State.getHandCards().forEach(card => {
                _hands[relativeIndex].appendChild(_createCardElement(card));
            });
        }
        else {
            const cardCount = State.getCountHandCards(playerIndex);
            for (let k = 0; k < cardCount; k++) {
                _hands[relativeIndex].appendChild(_createCardElement());
            }
        }
    }

    /**
     * Erzeugt einen Spielzug.
     *
     * @param {Cards} cards - Die im Zug ausgespielten Karten.
     * @returns {HTMLDivElement}
     */
    function _createTurnElement(cards) {
        const turnElement = document.createElement('div');
        turnElement.className = 'turn';
        cards.forEach(card => {
            const cardElement = _createCardElement(card);
            turnElement.appendChild(cardElement);
        });
        return turnElement;
    }

    /**
     * Aktualisiert den aktuellen Stich.
     */
    function _updateTrick() {
        // ausgespielte Karten entfernen
        for (let relativeIndex = 0; relativeIndex <= 3; relativeIndex++) {
            _trickZones[relativeIndex].replaceChildren();
        }

        if (State.getTrickOwnerIndex() === -1) {
            return; // kein offener Stich
        }

        // Spielzüge anzeigen
        const trick = State.getLastTrick();
        if (trick) {
            trick.forEach(turn => {
                if (turn[1]) { // Karten vorhanden (nicht gepasst?
                    const relativeIndex = Lib.getRelativePlayerIndex(turn[0]);
                    const turnElement = _createTurnElement(turn[1]);
                    _trickZones[relativeIndex].appendChild(turnElement);
                }
            });
            // den letzten Spielzug hervorheben
            const relativeIndex = Lib.getRelativePlayerIndex(State.getTrickOwnerIndex());
            if (relativeIndex !== -1) {
                const turnElement = _trickZones[relativeIndex].lastChild;
                if (turnElement) {
                    turnElement.classList.add("last");
                }
            }
        }
    }

    /**
     * Gibt die drei Karten zurück, die sich aktuell mit der Vorderseite in der Schupfzone des Benutzers befinden.
     *
     * Wenn nicht drei Karten mit der Vorderseite zu sehen sind, wird ein leeres Array zurückgegeben.
     *
     * @returns {Cards}
     */
    function _getSchupfCards() {
        if (_getSchupfCardsCount() !== 3) {
            return []
        }
        let cards = [];
        const cardElements = _schupfZones[0].querySelectorAll('.schupf-subzone .card:not(.back-site)');
        cardElements.forEach(cardElement => {
            cards.push(cardElement.dataset.card.split(",").map(value => parseInt(value, 10)));
        });
        return cards;
    }

    /**
     * Ermittelt die Anzahl der Karten, die mit der Vorderseite in der Schupfzone des Benutzers liegen.
     *
     * @returns {number}
     */
    function _getSchupfCardsCount() {
        return _schupfZones[0].querySelectorAll('.schupf-subzone .card:not(.back-site)').length;
    }

    /**
     * Leert die Schupfzone des Spielers.
     *
     * @param {number} playerIndex - Der Index des Spielers.
     */
    function _clearSchupfZone(playerIndex) {
        const relativeIndex = Lib.getRelativePlayerIndex(playerIndex);
        _schupfZones[relativeIndex].querySelectorAll('.schupf-subzone .card').forEach(cardElement => {
            cardElement.remove();
        });
    }

    /**
     * Aktualisiert die Schupfzone des angegebenen Spielers.
     *
     * @param {number} playerIndex - Der Index des Spielers.
     */
    function _updateSchupfZone(playerIndex) {
        const relativeIndex = Lib.getRelativePlayerIndex(playerIndex);
        const cardCount = State.getCountHandCards(playerIndex);
        if (!_receivedSchupfCardsConfirmed && cardCount > 8) {
            // Noch keine Tauschkarte aufgenommen und mehr als 8 Handkarten aufgenommen (Frage nach großes Tichu ist erfolgt).

            // Handelt es sich um den Benutzer, ausgewählte Karen zurücksetzen, denn beim Schupfen darf nicht mehr als eine Karte selektiert werden.
            if (relativeIndex === 0 && _getSelectedCardsCount() > 1) {
                _clearSelectedCards();
            }

            // Wenn alle Karten noch auf der Hand abgebildet sind, Schupfzone leeren.
            if (_hands[relativeIndex].children.length === 14) {
               _clearSchupfZone(playerIndex);  // todo in welchem Fall ist das notwendig?
            }

            // Schupfzone einblenden
            _schupfZones[relativeIndex].classList.remove('hidden');

            // Falls der Spieler nur noch 11 Karten in der Hand hat, müssen die übrigen drei in der Schupfzone liegen.
            if (cardCount === 11) {
                _clearSchupfZone(playerIndex);
                const receivedCards = State.getReceivedSchupfCards();
                if (relativeIndex === 0 && receivedCards) {
                    // Der Tausch hat stattgefunden. Der Benutzer muss die erhaltenen Karten bestätigen.
                    _schupfZones[relativeIndex].querySelectorAll('.schupf-subzone').forEach((subzoneElement, i) => {
                        subzoneElement.appendChild(_createCardElement(receivedCards[i]));
                    });
                }
                else {
                    // Drei verdeckte Karten zeigen.
                    _schupfZones[relativeIndex].querySelectorAll('.schupf-subzone').forEach(subzoneElement => {
                        subzoneElement.appendChild(_createCardElement());
                    });
                }
            }
        }
        else {
            // Schupfzone ausblenden
            _schupfZones[relativeIndex].classList.add('hidden');
        }
    }

    /**
     * Aktualisiert das Tichu-Icon des angegebenen Spielers.
     *
     * @param {number} playerIndex - Der Index des Spielers.
     */
    function _updateTichuIcon(playerIndex) {
        const relativeIndex = Lib.getRelativePlayerIndex(playerIndex);
        const announcement = State.getAnnouncement(playerIndex);
        if (announcement) {
            _tichuIcons.src = announcement === 2 ? "images/grand-tichu-icon.png" : "images/tichu-icon.png";
            _tichuIcons[relativeIndex].classList.remove('hidden');
        }
        else {
            _tichuIcons[relativeIndex].classList.add('hidden');
        }
    }

    /**
     * Bewegt das Turn-Symbol zum aktuellen Spieler.
     */
    function _updateCurrentPlayer() {
        for (let relativeIndex = 0; relativeIndex <= 3; relativeIndex++) {
            _playerNames[relativeIndex].classList.remove('current-player');
        }
        const relativeIndex = Lib.getRelativePlayerIndex(State.getCurrentTurnIndex());
        if (relativeIndex !== -1) {
            _playerNames[relativeIndex].classList.add('current-player');
        }
    }

    /**
     * Aktualisiert das Wunsch-Symbol.
     */
    function _updateWishIcon() {
        const wishValue = State.getWishValue();
        if (wishValue >= 2) {
            _wishText.textContent = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"][wishValue - 2];
            _wishIcon.classList.remove('hidden');
        }
        else {
            _wishIcon.classList.add('hidden');
        }
    }

    /**
     * Aktualisiert das Bomben-Symbol.
     */
    function _updateBombIcon() {
        if (State.hasBomb()) {
            _bombIcon.classList.remove('hidden');
        }
        else {
            _bombIcon.classList.add('hidden');
        }
    }

    /**
     * Aktualisiert den Pass-Button.
     */
    function _updatePassButton() {
        if (!State.getReceivedSchupfCards() && State.getCountHandCards() === 8) {
            // Der Benutzer kann ein großes Tichu ansagen.
            _passButton.dataset.mode = "NO_GRAND_TICHU";
            _passButton.textContent = "Weiter";
            _passButton.disabled = false;
        }
        else if (_receivedSchupfCardsConfirmed && State.isCurrentPlayer()) {
            // Der Benutzer ist am Zug.
            _passButton.dataset.mode = "PASS";
            _passButton.textContent = "Passen";
            _passButton.disabled = State.getTrickCombination()[2] === 0; // Anspiel oder Hund?
        }
        else {
            _passButton.dataset.mode = "PASS";
            _passButton.textContent = "Passen";
            _passButton.disabled = true;
        }
    }

    /**
     * Aktualisiert den Tichu-Button.
     */
    function _updateTichuButton() {
        if (!State.getReceivedSchupfCards() && State.getCountHandCards() === 8) {
            _tichuButton.dataset.mode = "GRAND_TICHU";
            _tichuButton.textContent = "Großes Tichu";
        }
        else {
            _tichuButton.dataset.mode = "TICHU";
            _tichuButton.textContent = "Tichu";
        }
        _tichuButton.disabled = State.getAnnouncement() > 0;
    }

    /**
     * Aktualisiert den Play-Button.
     */
    function _updatePlayButton() {
        const receivedSchupfCards = State.getReceivedSchupfCards();
        const isCurrentPlayer = State.isCurrentPlayer();
        if (!receivedSchupfCards && State.getCountHandCards() > 8) {
            // Der Benutzer muss drei Tauschkarten für die Mitspieler abgeben.
            _playButton.dataset.mode = "SCHUPF";
            _playButton.textContent = "Schupfen";
            _playButton.disabled = _getSchupfCardsCount() !== 3;
        }
        else if (receivedSchupfCards && !_receivedSchupfCardsConfirmed) {
            // Der Benutzer muss die drei Tauschkarten der Mitspieler aufnehmen.
            _playButton.dataset.mode = "RECEIVE";
            _playButton.textContent = "Aufnehmen";
            _playButton.disabled = false;
        }
        else if (isCurrentPlayer && !State.canPlayCards()) {
            // Der Benutzer ist am Zug, hat aber keine passende Kombination auf der Hand.
            _playButton.dataset.mode = "PLAY";
            _playButton.textContent = "Kein Zug";
            _playButton.disabled = true;
        }
        else if (isCurrentPlayer && _getSelectedCardsCount() === 0) {
            // Der Benutzer ist am Zug, hat mindestens eine passende Kombination, aber noch keine Karte ausgewählt.
            _playButton.dataset.mode = "AUTOSELECT";
            _playButton.textContent = "Auswählen"; // bei Klick wird die längste kleinstmögliche Kombination ausgewählt
            _playButton.disabled = false;
        }
        else if (isCurrentPlayer) {
            // Der Benutzer ist am Zug, hat mindestens eine passende Kombination und mindestens eine Karte ausgewählt.
            _playButton.dataset.mode = "PLAY";
            _playButton.textContent = "Spielen";
            _playButton.disabled = State.findPlayableCombination(_getSelectedCards()) === null;
        }
        else {
            // Karten werden ausgespielt, der Benutzer ist aber nicht am Zug.
            _playButton.dataset.mode = "PLAY";
            _playButton.textContent = "Spielen";
            _playButton.disabled = true;
        }
    }

    // Visuelle Effekte & Animationen
    // todo Bombe werfen
    // todo Tich ansagen (ein- oder 2mal Pulse-Effekt)
    // todo Karten ablegen (von der Hand dorthin, wo auch die Schupfzone liegt)
    // todo Karten kassieren (von der aktuellen Position der Karten zum Spieler, der die Karten bekommt)
    // todo Schupfkarten tauschen (von Zone zu Zone)
    // todo Sound

    // noinspection JSUnusedGlobalSymbols
    return {
        init,
        render,
        show,
        hide,
        isVisible,
    };
})();