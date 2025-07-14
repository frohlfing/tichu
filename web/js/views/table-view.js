/**
 * Anzeige und Interaktion des Spieltisches.
 *
 * @type {View}
 */
const TableView = (() => {

    // --------------------------------------------------------------------------------------
    // DOM-Elemente
    // --------------------------------------------------------------------------------------

    // /**
    //  * Der Hauptcontainer, der mit einer Ausgangsgröße von 1080x1920 in den Viewport des Browsers skaliert wird.
    //  *
    //  * @type {HTMLElement}
    //  */
    // const _wrapper = document.getElementById('wrapper');

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
        _updateScore();
        for (let playerIndex = 0; playerIndex <= 3; playerIndex++) {
            _updatePlayerName(playerIndex);
            _updateSchupfZoneAndHand(playerIndex);
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
    // Netzwerk-Ereignisse
    // --------------------------------------------------------------------------------------

    // /**
    //  * Wird aufgerufen, wenn eine Netzwerknachricht empfangen wurde.
    //  *
    //  * @param {NetworkMessage} message - Die Nachricht vom Server.
    //  */
    // function _handleNetworkMessage(message) {
    //     if (message.type !== 'notification') {
    //         return;
    //     }
    //     //const context = message.payload.context || {};
    //     // Animation abspielen
    //     switch (message.payload.event) {
    //         case "player_played": // Der Spieler hat Karten ausgespielt.
    //         case "player_bombed": // Der Spieler hat außerhalb seines regulären Zuges eine Bombe geworfen.
    //             if (State.getTrickCombination()[0] === CombinationType.BOMB) {
    //                 EventBus.pause();
    //                 Animation.explodeBomb(() => {
    //                     EventBus.resume();
    //                 });
    //             }
    //             break;
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
        Sound.play('click');
        Modal.showExitDialog();
    }

    /**
     * Ereignishändler für den "Optionen"-Button.
     */
    function _handleSettingsButtonClick() {
        Modal.showErrorToast("Einstellungen sind noch nicht implementiert.");
    }


    // ------------------------------------------------------------------------------------------------------

    // function testUI() {
    //     State.resetRound();
    //     State.setGivenSchupfCards(/** @type Cards */ [[4,1], [5,1], [14,3]]);
    //     State.setReceivedSchupfCards(/** @type Cards */ [[10,1], [11,2], [12,2]]);
    //     State.confirmReceivedSchupfCards()
    //     let cards = /** @type Cards */ [[0,0], [1,0], [2,1], [2,2], [2,3], [2,4], [3,4], [10,1], [11,2], [12,2], [13,3], [14,3], [15,0], [16,0]];
    //     //cards.length = 11;
    //     State.setHandCards(cards);
    //     for (let i = 0; i <= 3; i++) {
    //         State.setCountHandCards(i, 14);
    //         _updateSchupfZoneAndHand(i);
    //     }
    //     _updateBombIcon();
    //     _updatePlayButton();
    // }

    // ------------------------------------------------------------------------------------------------------

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

        // Beim Schupfen darf maximal nur eine Karte selektiert werden.
        if (!_schupfZones[0].classList.contains('hidden') && !cardElement.classList.contains("selected")) {
            if (_getCountSelectedCards() > 0 || State.getReceivedSchupfCards()) {
                return; // es ist bereits eine Karte selektiert oder die Tauschkarten wurden bereits verteilt und müssen nur noch bestätigt werden
            }
        }

        Sound.play('click');
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
                Sound.play('click');
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
            for (const el of cardElements) {  // die Karten in der Hand sind absteigend sortiert (werden aber von rechts nach links aufgeblättert)
                const [v, c] = /** @type Card */ el.dataset.card.split(",").map(value => parseInt(value, 10));
                if (v < value || (value === v && c < color)) {
                    referenceElement = el; // die erste Karte in der Hand, die kleiner ist als die einzufügende Karte
                    break;
                }
            }

            // Karte zurück in die Hand einsortieren
            Sound.play('click');
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
     *
     * Das Icon ist nur anklickbar, wenn eine spielbare Bombe ausgewählt werden kann.
     */
    function _handleBombIconClick() {
        if (_bombIcon.classList.contains("disabled")) {
            return;
        }
        Sound.play('click');
        _selectCards(State.getBestPlayableBomb()[0])
        _updatePlayButton();
    }

    /**
     * Ereignishändler für den Pass-Button.
     */
    function _handlePassButtonClick() {
        _passButton.disabled = true;
        Sound.play('click');
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
        Sound.play('click');
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
        Sound.play('click');
        switch (_playButton.dataset.mode) {
            case "SCHUPF": // Der Benutzer möchte drei Tauschkarten für die Mitspieler abgeben.
                EventBus.emit("tableView:schupf", _getHandCardsInSchupfZone());
                break;
            case "RECEIVE": // Der Benutzer nimmt die drei Tauschkarten der Mitspieler auf.
                State.confirmReceivedSchupfCards();
                _updateSchupfZoneAndHand(State.getPlayerIndex());
                _updatePassButton();
                _updatePlayButton();
                break;
            case "AUTOSELECT": // Die längste rangniedrigste Kombination auswählen.
                _selectCards(State.getBestPlayableCombination()[0])
                _updatePlayButton();
                break;
            case "PLAY": // Der Benutzer möchte die ausgewählten Karten spielen.
                EventBus.emit("tableView:play", _getSelectedCards());
                break;
            case "BOMB": // Der Benutzer möchte außerhalb seines regulären Zuges die ausgewählte Bombe spielen.
                EventBus.emit("tableView:bomb", _getSelectedCards());
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
        let score = State.getTotalScore();
        if (State.getPlayerIndex() === 1 || State.getPlayerIndex() === 3) {
            [score[0], score[1]] = [score[1], score[0]];
        }
        const oldScore = _scoreDisplay.textContent.split(":").map(value => parseInt(value.trim()));
        if (oldScore[0] !== score[0] || oldScore[1] !== score[1]) {
            _scoreDisplay.textContent = Lib.formatScore(score);
            Animation.flashScoreDisplay();
        }
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
    function _getCountSelectedCards() {
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
    function _createCardElement(card = null) {
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
        if (State.getTrickOwnerIndex() === -1) {
            // Stich kassieren

            // Der Spielzustand hält die abgeräumte Situation fest. Es wird nicht festgehalten, wer den Stich bekommen hat.
            // Wir können den Gewinner des Stichs aber an der View erkennen.
            let lastTurnIndex = -1; // der Index des Spielers mit dem letzten Spielzug
            for (let relativeIndex = 0; relativeIndex <= 3; relativeIndex++) {
                const lastTurn = _trickZones[relativeIndex].querySelector(".turn.last");
                if (lastTurn) {
                    if (Array.from(lastTurn.children).some(cardElement => cardElement.dataset.card === '15,0')) {
                        lastTurnIndex = State.getDragonRecipient(); // der Spieler des letzten Spielzugs bekommt den Stich
                    }
                    else {
                        lastTurnIndex = Lib.getCanonicalPlayerIndex(relativeIndex); // Stich wurde verschenkt
                    }
                }
            }

            // Animation starten (dadurch werden die Spielzüge gelöscht)
            EventBus.pause();
            Animation.takeTrick(lastTurnIndex, () => {
                EventBus.resume();
            });

            return;
        }

        let countTurnDiff = 0; // Anzahl der neuen Spielzüge

        // bisherige Spielzüge entfernen
        for (let relativeIndex = 0; relativeIndex <= 3; relativeIndex++) {
            countTurnDiff -= _trickZones[relativeIndex].children.length;
            _trickZones[relativeIndex].replaceChildren();
        }

        // aktuelle Spielzüge anzeigen
        const trick = State.getLastTrick();
        if (trick) {
            trick.forEach(turn => {
                if (turn[1]) { // Karten vorhanden (nicht gepasst?
                    const relativeIndex = Lib.getRelativePlayerIndex(turn[0]);
                    const turnElement = _createTurnElement(turn[1]);
                    _trickZones[relativeIndex].appendChild(turnElement);
                    countTurnDiff++;
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

        // falls eine neue Bombe liegt, dies animieren
        if (State.getTrickCombination()[0] === CombinationType.BOMB && countTurnDiff) {
            //Sound.play(`bomb${State.getTrickOwnerIndex()}`);
            Sound.play("bomb");
            EventBus.pause();
            Animation.explodeBomb(() => {
                EventBus.resume();
            });
        }
    }

    /**
     * Gibt die Handkarten des Benutzers zurück, die in der Schupfzone dargestellt sind.
     *
     * Wenn Karten in der Schupfzone offen liegen, wurden sie entweder noch nicht geschupft oder gerade entgegengenommen.
     * In beiden Fällen zählen sie zu den Handkarten.
     *
     * @returns {Cards} Karten in der Schupfzone (bei drei Karten: für bzw. vom rechten Gegner, Partner, linken Gegner).
     */
    function _getHandCardsInSchupfZone() {
        let cards = [];
        const cardElements = _schupfZones[0].querySelectorAll('.schupf-subzone .card:not(.back-site)');
        cardElements.forEach(cardElement => { // linker Gegner, Partner, rechter Gegner
            cards.push(cardElement.dataset.card.split(",").map(value => parseInt(value, 10)));
        });
        return cards.reverse(); // Reihenfolge umdrehen!
    }

    /**
     * Ermittelt die Anzahl der Handkarten des Benutzers, die in der Schupfzone dargestellt sind.
     *
     * Wenn Karten in der Schupfzone offen liegen, wurden sie entweder noch nicht geschupft oder gerade entgegengenommen.
     * In beiden Fällen zählen sie zu den Handkarten.
     *
     * @returns {number}
     */
    function _getCountHandCardsInSchupfZone() {
        return _schupfZones[0].querySelectorAll('.schupf-subzone .card:not(.back-site)').length;
    }

    /**
     * Leert die Schupfzone des Spielers.
     *
     * @param {number} playerIndex - Der Index des Spielers.
     */
    function _clearSchupfZone(playerIndex) {
        const relativeIndex = Lib.getRelativePlayerIndex(playerIndex);
        const cardElements = _schupfZones[relativeIndex].querySelectorAll('.schupf-subzone .card');
        cardElements.forEach(cardElement => {
            cardElement.remove();
        });
    }

    /**
     * Aktualisiert die Schupfzone und die Hand des angegebenen Spielers.
     *
     * @param {number} playerIndex - Der Index des Spielers.
     */
    function _updateSchupfZoneAndHand(playerIndex) {
        const relativeIndex = Lib.getRelativePlayerIndex(playerIndex);
        if (State.getCountHandCards(playerIndex) <= 8) {
            // Es wurden noch nicht alle Karten ausgeteilt oder die Karten werden bereits ausgespielt. Schupfzone ausblenden.
            _clearSchupfZone(playerIndex);
            _schupfZones[relativeIndex].classList.add('hidden');
        }
        else {
            // Alle Handkarten wurden ausgeteilt.
            if (!State.getReceivedSchupfCards()) {
                // Die Tauschkarten wurden noch nicht verteilt. Schupfzone einblenden.
                _schupfZones[relativeIndex].classList.remove('hidden');
                if (relativeIndex === 0) {
                    if (!State.getGivenSchupfCards()) {
                        // Der Benutzer wählt Karten aus, die er schupfen möchte.

                        // Sicherstellen, dass alle offenen Karten in der Schupfzone zu den Handkarten gehören.
                        const schupfCards = _getHandCardsInSchupfZone();
                        const hand = State.getHandCards();
                        if (schupfCards.some(card => !Lib.includesCard(card, hand))) {
                            _clearSchupfZone(playerIndex);
                        }

                        // Verdeckte Karten entfernen
                        const backSideCardElements = _schupfZones[relativeIndex].querySelectorAll('.schupf-subzone .card.back-site');
                        backSideCardElements.forEach(cardElement => {
                            cardElement.remove();
                        });

                        // Sicherstellen, dass maximal eine Handkarte selektiert ist.
                        if (_getCountSelectedCards() > 1) {
                            _clearSelectedCards();
                        }
                    }
                    else {
                        // Der Benutzer hat geschupft. Drei verdeckte Karten in seiner Schupfzone anzeigen.
                        _clearSchupfZone(playerIndex);
                        _schupfZones[0].querySelectorAll('.schupf-subzone').forEach(subzoneElement => {
                            subzoneElement.appendChild(_createCardElement());
                        });
                    }
                }
                else {
                    // Wenn der Mitspieler 11 Handkarten hat, drei verdeckte Karten anzeigen, sonst keine.
                    _clearSchupfZone(playerIndex);
                    if (State.getCountHandCards(playerIndex) === 11) {
                        _schupfZones[relativeIndex].querySelectorAll('.schupf-subzone').forEach(subzoneElement => {
                            subzoneElement.appendChild(_createCardElement());
                        });
                    }
                }
            }
            else {
                // Der Benutzer hat Tauschkarten bekommen.
                if (relativeIndex === 0) {
                    if (!State.isConfirmedReceivedSchupfCards()) {
                        // Der Benutzer hat die erhaltenen Tauschkarten noch nicht bestätigt.
                        _clearSelectedCards();
                        _schupfZones[0].classList.remove('hidden');
                        if (!_getCountHandCardsInSchupfZone()) {
                            // Die erhaltenen Tauschkarten werden noch nicht angezeigt.
                            // Wie starten die Animation, in der die Karten unter den Spielern ausgetauscht werden.
                            EventBus.pause();
                            Animation.schupfCards(() => {
                                // Tauschkarten mit der Vorderseite zeigen
                                _clearSchupfZone(playerIndex);
                                const receivedCards = State.getReceivedSchupfCards().toReversed(); // linker Gegner, Partner, rechter Gegner
                                _schupfZones[0].querySelectorAll('.schupf-subzone').forEach((subzoneElement, i) => {
                                    subzoneElement.appendChild(_createCardElement(receivedCards[i]));
                                });
                                EventBus.resume();
                            });
                        }
                    }
                    else {
                        // Schupfzone des Benutzers ausblenden
                        _clearSchupfZone(playerIndex);
                        _schupfZones[0].classList.add('hidden');
                    }
                }
                else {
                    // Schupfzone des Mitspielers ausblenden
                    _clearSchupfZone(playerIndex);
                    _schupfZones[relativeIndex].classList.add('hidden');
                }
            }
        }

        // Handkarten außerhalb der Schupfzone aktualisieren.
        if (relativeIndex === 0) {
            // Handkarten des Benutzers, die nicht in der Schupfzone sind, ermitteln, und anzeigen
            let handCards = State.getHandCards();
            const schupfCards = _getHandCardsInSchupfZone();
            if (schupfCards.length) {
                handCards = handCards.filter(card => !Lib.includesCard(card, schupfCards));
            }
            const selectedCards = _getSelectedCards()
            _hands[relativeIndex].replaceChildren(); // Handkarten entfernen
            handCards.forEach(card => {
                const cardElement = _createCardElement(card);
                if (Lib.includesCard(card, selectedCards)) {
                    cardElement.classList.add('selected');
                }
                _hands[relativeIndex].appendChild(cardElement);
            });
        }
        else {
            // Die Anzahl der Handkarten des Mitspielers mit der Rückseite anzeigen
            const cardCount = State.getCountHandCards(playerIndex);
            if (cardCount !== _hands[relativeIndex].children.length) {
                _hands[relativeIndex].replaceChildren(); // Handkarten entfernen
                for (let k = 0; k < cardCount; k++) {
                    _hands[relativeIndex].appendChild(_createCardElement());
                }
            }
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
            if (State.canPlayBomb()) {
                _bombIcon.classList.remove("disabled");
            }
            else {
                _bombIcon.classList.add("disabled");
            }
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
            _passButton.disabled = State.getAnnouncement() > 0;
        }
        else {
            _passButton.dataset.mode = "PASS";
            _passButton.textContent = "Passen";
            _passButton.disabled = !State.isConfirmedReceivedSchupfCards() || !State.isCurrentPlayer() || State.getTrickCombination()[2] === 0; // Nicht am Zug oder Anspiel
        }
    }

    /**
     * Aktualisiert den Tichu-Button.
     */
    function _updateTichuButton() {
        if (!State.getReceivedSchupfCards() && State.getCountHandCards() === 8) {
            _tichuButton.dataset.mode = "GRAND_TICHU";
            _tichuButton.textContent = "Großes Tichu";
            _tichuButton.disabled = State.getAnnouncement() > 0;
        }
        else  {
            _tichuButton.dataset.mode = "TICHU";
            _tichuButton.textContent = "Tichu";
            _tichuButton.disabled = State.getCountHandCards() < 14 || State.getAnnouncement() > 0;
        }
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
            _playButton.disabled = _getCountHandCardsInSchupfZone() !== 3;
        }
        else if (receivedSchupfCards && !State.isConfirmedReceivedSchupfCards()) {
            // Der Benutzer muss die drei Tauschkarten der Mitspieler aufnehmen.
            _playButton.dataset.mode = "RECEIVE";
            _playButton.textContent = "Aufnehmen";
            _playButton.disabled = false;
        }
        else if (!isCurrentPlayer && State.isPlayableBomb(_getSelectedCards())) {
            // Der Benutzer hat außerhalb seines regulären Zuges eine spielbare Bombe ausgewählt.
            _playButton.dataset.mode = "BOMB";
            _playButton.textContent = "Bomben";
            _playButton.disabled = false;
        }
        else if (isCurrentPlayer && !State.canPlayCards()) {
            // Der Benutzer ist am Zug, hat aber keine passende Kombination auf der Hand.
            _playButton.dataset.mode = "PLAY";
            _playButton.textContent = "Kein Zug";
            _playButton.disabled = true;
        }
        else if (isCurrentPlayer && _getCountSelectedCards() === 0) {
            // Der Benutzer ist am Zug, hat mindestens eine passende Kombination, aber noch keine Karte ausgewählt.
            _playButton.dataset.mode = "AUTOSELECT";
            _playButton.textContent = "Auswählen"; // bei Klick wird die längste kleinstmögliche Kombination ausgewählt
            _playButton.disabled = false;
        }
        else {
            _playButton.dataset.mode = "PLAY";
            _playButton.textContent = "Spielen";
            _playButton.disabled = !isCurrentPlayer || !State.isPlayableCombination(_getSelectedCards()); // nicht am Zug oder keine Spielbare Kombination ausgewählt
        }
    }

    // noinspection JSUnusedGlobalSymbols
    return {
        init,
        render,
        show,
        hide,
        isVisible,
    };
})();