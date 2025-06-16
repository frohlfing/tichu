/**
 * Anzeige und Interaktion des Spieltisches.
 *
 * @type {View}
 */
const GameTableView = (() => {

    // --------------------------------------------------------------------------------------
    // DOM-Elemente
    // --------------------------------------------------------------------------------------
    
    /**
     * Der Container des Spieltisch-Bildschirms.
     *
     * @type {HTMLDivElement}
     */
    const _viewContainer = document.getElementById('game-table-screen');

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
    const _optionsButton = document.getElementById('options-button');

    /**
     * Die Anzeige des Punktestandes.
     *
     * @type {HTMLDivElement}
     */
    const _scoreDisplay = document.getElementById('score-display');

    /**
     * Die Namen der Spieler.
     *
     * @type {HTMLElement[]}
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
     * @type {HTMLElement[]}
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
     * @type {HTMLElement[]}
     */
    const _schupfZones = [
        document.getElementById('schupf-zone-bottom'),
        document.getElementById('schupf-zone-right'),
        document.getElementById('schupf-zone-top'),
        document.getElementById('schupf-zone-left'),
    ];

    /**
     * Die Ablage-Zonen für Stiche.
     *
     * @type {HTMLElement[]}
     */
    const _playedCardsAreas = [
        document.getElementById('played-cards-area-bottom'),
        document.getElementById('played-cards-area-right'),
        document.getElementById('played-cards-area-top'),
        document.getElementById('played-cards-area-left'),
    ];

    /**
     * Das Turn-Symbol.
     *
     * @type {HTMLElement[]}
     */
    const _turnIcon = [
        document.getElementById('turn-icon-bottom'),
        document.getElementById('turn-icon-right'),
        document.getElementById('turn-icon-top'),
        document.getElementById('turn-icon-left'),
    ];

    /**
     * Die Symbole für eine Tichu-Ansage.
     *
     * @type {HTMLElement[]}
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

    /**
     * Wird gesetzt, wenn der Benutzer eine passende Kombination auf der Hand hat.
     *
     * @type {boolean}
     */
    let _canPlay = false;

    /**
     * Wird gesetzt, wenn der Benutzer eine Bombe hat.
     *
     * @type {boolean}
     */
    let _hasBomb = true;

    // --------------------------------------------------------------------------------------
    // Öffentliche Funktionen
    // --------------------------------------------------------------------------------------
    
    /**
     * Initialisiert den Spieltisch-Bildschirm.
     */
    function init() {
        console.log("GAMETABLEVIEW: Initialisiere GameTableView (minimal)...");

        // Event-Listener einrichten
        _exitButton.addEventListener('click', _exitButtonClick);
        _optionsButton.addEventListener('click', _optionsButtonClick);
        _passButton.addEventListener('click', _passButtonClick);
        _tichuButton.addEventListener('click', _tichuButtonClick);
        _playButton.addEventListener('click', _playButtonClick);
        _bombIcon.addEventListener('click', _bombIconClick);
        _hands[0].addEventListener('click', _handClick);
        _schupfZones[0].addEventListener('click', _schupfZoneClick);

        // Event-Listener für Test-Buttons todo: nach Testphase entfernen
        document.getElementById('test-controls-container').addEventListener('click', _handleTestButtonClick);
    }

    /**
     * Rendert den Spieltisch-Bildschirm.
     */
    function render() {
        _receivedSchupfCardsConfirmed = State.getReceivedSchupfCards() !== null
        _updateScore();
        for (let playerIndex= 0; playerIndex <= 3; playerIndex++) {
            _updatePlayerName(playerIndex);
            _updateHand(playerIndex);
            _updateSchupfZone(playerIndex);
            _updatePlayedCards(playerIndex);
            _updateTichuIcon(playerIndex);
        }
        _updateTurnIcon();
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
    // Ereignishändler
    // --------------------------------------------------------------------------------------

    /**
     * Ereignishändler für das Anklicken auf den "Beenden"-Button.
     */
    function _exitButtonClick() {
        SoundManager.playSound('buttonClick');
        Dialogs.showExitDialog();
    }

    /**
     * Ereignishändler für das Anklicken auf den "Optionen"-Button.
     */
    function _optionsButtonClick() {
        SoundManager.playSound('buttonClick');
        Dialogs.showErrorToast("Optionen sind noch nicht implementiert.");
    }

    /**
     * Ereignishändler für das Anklicken der eigenen Hand.
     *
     * @param {PointerEvent} event
     */
    function _handClick(event) {
        if (!event.target.classList.contains('card-face')) {
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
        console.debug(`_handClick: Karte ${Lib.stringifyCard(card)} (${card})`);
        cardElement.classList.toggle('selected');
        _updatePlayButton();
    }

    /**
     * Ereignishändler für das Anklicken der Schupfzone.
     *
     * @param {PointerEvent} event
     */
    function _schupfZoneClick(event) {
        if (event.target.classList.contains('schupf-subzone')) {
            // es wurde auf eine leere Ablagefläche geklickt
            const subzoneElement = event.target;
            const cardElement = _hands[0].querySelector('.card-face.selected');
            if (cardElement) {
                SoundManager.playSound('buttonClick');
                subzoneElement.appendChild(cardElement);
                cardElement.classList.remove('selected');
            }
            _updatePlayButton();
            //_playButton.disabled = _getSchupfCardsCount() !== 3;
        }
        else if (event.target.classList.contains('card-face')) {
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
            console.log("Karte zurückgelegt");

            _updatePlayButton();
            //_playButton.disabled = _getSchupfCardsCount() !== 3;
        }
    }

    /**
     * Ereignishändler für das Anklicken auf das Bomben-Icon.
     */
    function _bombIconClick() {
        SoundManager.playSound('buttonClick');
        console.log("_bombIconClick");
    }

    /**
     * Ereignishändler für das Anklicken auf den "Passen"-Button.
     */
    function _passButtonClick() {
        SoundManager.playSound('buttonClick');
        console.log("_passButtonClick");
    }

    /**
     * Ereignishändler für das Anklicken auf den "Tichu"-Button.
     */
    function _tichuButtonClick() {
        SoundManager.playSound('buttonClick');
        console.log("_tichuButtonClick");
    }

    /**
     * Ereignishändler für das Anklicken auf den "Spielen"-Button.
     */
    function _playButtonClick() {
        SoundManager.playSound('buttonClick');
        console.log("_playButtonClick");
    }

    // --------------------------------------------------------------------------------------
    // Hilfsfunktionen
    // --------------------------------------------------------------------------------------

    /**
     * Aktualisiert den Punktestand in der Top-Bar.
     */
    function _updateScore() {
        const score = State.getTotalScore();
        let team20 = score[0].toString().padStart(4, '0');
        let team31 = score[1].toString().padStart(4, '0');
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
        _hands[0].querySelectorAll('.card-face.selected').forEach(cardElement => {
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
        return _hands[0].querySelectorAll('.card-face.selected').length;
    }

    /**
     * Setzt die ausgewählten Karten zurück.
     */
    function _clearSelectedCards() {
        _hands[0].querySelectorAll('.card-face.selected').forEach(cardElement => {
            cardElement.classList.remove('selected');
        });
    }

    /**
     * Erzeugt eine offene Karte.
     *
     * @param {Card} card - Wert und Farbe der Karte
     * @returns {HTMLDivElement}
     */
    function _createCardFaceElement(card) {
        const cardFace = document.createElement('div');
        cardFace.className = 'card-face';
        cardFace.style.backgroundImage = `url('images/cards/${Lib.stringifyCard(card)}.png')`;
        cardFace.dataset.card = card.toString();
        return cardFace;
    }

    /**
     * Erzeugt eine verdeckte Karte.
     *
     * @returns {HTMLDivElement}
     */
    function _createCardBackElement() {
        const cardBack = document.createElement('div');
        cardBack.className = 'card-back';
        return cardBack;
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
                const cardFace = _createCardFaceElement(card)
                _hands[relativeIndex].appendChild(cardFace);
            });
        }
        else {
            const cardCount = State.getCountHandCards(playerIndex);
            for (let k = 0; k < cardCount; k++) {
                _hands[relativeIndex].appendChild(_createCardBackElement());
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
        const cardElements = _schupfZones[0].querySelectorAll('.schupf-subzone .card-face');
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
        return _schupfZones[0].querySelectorAll('.schupf-subzone .card-face').length;
    }

    /**
     * Leert die Schupfzone des Spielers.
     *
     * @param {number} playerIndex - Der Index des Spielers.
     */
    function _clearSchupfZone(playerIndex) {
        const relativeIndex = Lib.getRelativePlayerIndex(playerIndex);
        _schupfZones[relativeIndex].querySelectorAll('.schupf-subzone .card-back, .schupf-subzone .card-face').forEach(cardElement => {
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
        if (!_receivedSchupfCardsConfirmed && State.getCountHandCards() > 8) {
            // Noch keine Tauschkarte aufgenommen und mehr als 8 Handkarten aufgenommen (Frage nach großes Tichu ist erfolgt).

            // Handelt es sich um den Benutzer, ausgewählte Karen zurücksetzen, denn beim Schupfen darf nicht mehr als eine Karte selektiert werden.
            if (relativeIndex === 0 && _getSelectedCardsCount() > 1) {
                _clearSelectedCards();
            }

            // Wenn alle Karten noch auf der Hand abgebildet sind, Schupfzone leeren.
            if (_hands[relativeIndex].children.length === 14) {
               _clearSchupfZone(playerIndex);
            }

            // Schupfzone einblenden
            _schupfZones[relativeIndex].classList.remove('hidden');

            // Falls der Spieler nur noch 11 Karten in der Hand hat, müssen die übrigen drei in der Schupfzone liegen.
            if (State.getCountHandCards(playerIndex) === 11 && _schupfZones[relativeIndex].querySelectorAll('.schupf-subzone .card-back').length !== 3) {
                // Drei verdeckte Karten zeigen.
                _clearSchupfZone(playerIndex);
                _schupfZones[relativeIndex].querySelectorAll('.schupf-subzone').forEach(subzoneElement => {
                    subzoneElement.appendChild(_createCardBackElement());
                });
            }
        }
        else {
            // Schupfzone ausblenden
            _schupfZones[relativeIndex].classList.add('hidden');
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
        turnElement.className = 'trick';
        cards.forEach(card => {
            const cardElement = _createCardFaceElement(card);
            turnElement.appendChild(cardElement);
        });
        return turnElement;
    }

    /**
     * Aktualisiert die ausgespielten Karten des angegebenen Spielers im aktuellen Stich.
     *
     * @param {number} playerIndex - Der Index des Spielers.
     */
    function _updatePlayedCards(playerIndex) {
        const relativeIndex = Lib.getRelativePlayerIndex(playerIndex);

        // todo Trick und Turn geht durcheinander. CSS und JS korrigieren.
        // todo der letzte Zug insgesamt größere ziehen, nicht pro Spieler.

        // ausgespielte Karten entfernen
        _playedCardsAreas[relativeIndex].replaceChildren();

        // Spielzüge anzeigen
        State.getTricks().forEach(trick => {
            for (let turn of trick) {
                if (turn[0] === playerIndex && turn[1]) {
                    const turnElement = _createTurnElement(turn[1]);
                    _playedCardsAreas[relativeIndex].appendChild(turnElement);
                }
            }
        });
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
        } else {
            _tichuIcons[relativeIndex].classList.add('hidden');
        }
    }

    /**
     * Bewegt das Turn-Symbol zum aktuellen Spieler.
     */
    function _updateTurnIcon() {
        for (let relativeIndex = 0; relativeIndex <= 3; relativeIndex++) {
            _turnIcon[relativeIndex].classList.add('hidden');
        }
        const relativeIndex = Lib.getRelativePlayerIndex(State.getCurrentTurnIndex());
        if (relativeIndex !== -1) {
            _turnIcon[relativeIndex].classList.remove('hidden');
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
        if (_hasBomb) {
            _bombIcon.classList.remove('hidden');
        }
        else {
            _bombIcon.classList.add('hidden');
        }
        // todo Bomben-Symbol aktivieren / deaktivieren (anklickbar machen bzw. nicht)
    }

    /**
     * Aktualisiert den Pass-Button.
     */
    function _updatePassButton() {
        if (!State.getReceivedSchupfCards() && State.getCountHandCards() === 8) {
            // Der Benutzer kann ein großes Tichu ansagen.
            _passButton.textContent = "Weiter";
            _passButton.disabled = false;
        }
        else if (_receivedSchupfCardsConfirmed && State.isCurrentPlayer()) {
            // Der Benutzer ist am Zug.
            _passButton.textContent = "Passen";
            _passButton.disabled = State.getTrickCombination()[0] === CombinationType.PASS; // true, wenn Anspiel}
        }
        else {
            _passButton.textContent = "Passen";
            _passButton.disabled = true;
        }
    }

    /**
     * Aktualisiert den Tichu-Button.
     */
    function _updateTichuButton() {
        _tichuButton.textContent = !State.getReceivedSchupfCards() && State.getCountHandCards() === 8 ? "Großes Tichu" : "Tichu";
        _tichuButton.disabled = State.getAnnouncement() > 0;
    }

    /**
     * Aktualisiert den Play-Button.
     */
    function _updatePlayButton() {
        if (!State.getReceivedSchupfCards() && State.getCountHandCards() > 8) {
            // Der Benutzer muss drei Tauschkarten abgeben.
            _playButton.textContent = "Schupfen";
            _playButton.disabled = _getSchupfCardsCount() !== 3;
        }
        else if (State.getReceivedSchupfCards() && !_receivedSchupfCardsConfirmed) {
            // Der Benutzer muss die drei Tauschkarten der Mitspieler aufnehmen.
            _playButton.textContent = "Aufnehmen";
            _playButton.disabled = false;
        }
        else if (State.isCurrentPlayer() && !_canPlay) {
            // Der Benutzer ist am Zug, hat aber keine passende Kombination auf der Hand.
            _playButton.textContent = "Kein Zug";
            _playButton.disabled = true;
        }
        else if (State.isCurrentPlayer() && _getSelectedCardsCount() === 0) {
            // Der Benutzer ist am Zug, hat aber noch keine Karte ausgewählt.
            _playButton.textContent = "Auswählen"; // bei Klick wird die längste kleinstmögliche Kombination ausgewählt
            _playButton.disabled = false;
        }
        else if (State.isCurrentPlayer()) {
            // Der Benutzer ist am Zug und hat mindestens eine Karte ausgewählt.
            _playButton.textContent = "Spielen";
            _playButton.disabled = false; // todo true, wenn die ausgewählte Kombination nicht spielbar ist
        }
        else {
            _playButton.textContent = "Spielen";
            _playButton.disabled = true;
        }
    }


    // todo bomb_click()
    // todo Selektierte Karten eingereiht lassen
    // todo Sound

    // Visuelle Effekte & Animationen
    // todo Bombe werfen
    // todo Tich ansagen (ein- oder 2mal Pulse-Effekt)
    // todo Karten ablegen (von der Hand dorthin, wo auch die Schupfzone liegt)
    // todo Karten kassieren (von der aktuellen Position der Karten zum Spieler, der die Karten bekommt)
    // todo Schupfkarten tauschen (von Zone zu Zone)

    // CSS optimieren
    // todo Aufteilung anders lösen (wobei das Aussehen genauso bleiben soll!):
    //  1) Die gesamte player-area drehen. Dann müssen die untergeordneten Elemente (hand und player-info) nicht mehr gedreht werden.
    //  2) Die Schupfzone und Turn-Symbol in die player-area des Spielers verschieben.
    //  3) wish-icon direkt unter table-area ziehen. center-table wird dann nicht mehr benötigt.
    //  4) position nur da aufführen, wo erforderlich.

    // --------------------------------------------------------------------------------------
    // Test-Buttons
    // --------------------------------------------------------------------------------------

    function _handleTestButtonClick(event) {
        if (event.target.tagName !== 'BUTTON') return;
        const testAction = event.target.dataset.test;
        //const testPlayerRelativeIdxInput = document.getElementById('test-player-index');
        //const testPlayerRelativeIdx = testPlayerRelativeIdxInput ? parseInt(testPlayerRelativeIdxInput.value, 10) : 1;

        switch (testAction) {
            case 'show-all-controls': _testShowAllControls(); break;
            case 'reset-round': _testResetRound(); break;
            case 'toggle-wish': _testToggleWish(); break;
            case 'toggle-bomb': _testToggleBomb(); break;
            case 'toggle-tichu': _testToggleTichu(); break;
            case 'move-turn': _testMoveTurn(); break;

            case 'deal-cards': _testDealCards(); break;
            case 'get-selected-cards': _testGetSelectedCards(); break;
            case 'clear-selected-cards': _testClearSelectedCards(); break;

            case 'toggle-schupf-zones': _testToggleSchupfZones(); break;
            case 'fill-schupf-zones': _testFillSchupfZones(); break;
            case 'clear-schupf-zones': _testClearSchupfZones(); break;
            case 'get-schupf-cards': _testGetSchupfCards(); break;

            case 'add-trick': _testAddTrick(); break;
            case 'remove-trick': _testRemoveTrick(); break;

            case 'show-dragon-dialog': _testShowDragonDialog(); break;
            case 'show-wish-dialog': _testShowWishDialog(); break;
            case 'show-round-over-dialog': _testShowRoundOverDialog(); break;
            case 'show-game-over-dialog': _testShowGameOverDialog(); break;
            case 'show-error-toast': _testShowErrorToast(); break;

            // todo
            // case 'select-cards': _testSelectSomeCards(); break;
            // case 'play-selected-cards': _testPlaySelectedCards(); break;
            // case 'opponent-plays-cards': _testOpponentPlaysCards(testPlayerRelativeIdx); break;
            // case 'highlight-trick': _testHighlightTrick(testPlayerRelativeIdx); break;
            // case 'take-trick-self': _testTakeTrick(0); break;
            // case 'take-trick-opponent': _testTakeTrick(testPlayerRelativeIdx); break;
            // case 'give-own-schupf-card': _testGiveOwnSchupfCard(); break;
            // case 'opponent-schupf-cards': _testOpponentSchupfCards(); break;
            // case 'animate-schupf-exchange': _testAnimateSchupfExchange(); break;
            // case 'take-schupf-cards': _testTakeSchupfCards(); break;
            // case 'update-score': _testUpdateScore(); break;
            // case 'update-player-name': _testUpdatePlayerName(testPlayerRelativeIdx); break;
            // case 'throw-bomb-effect': _testThrowBombEffect(); break;
            // case 'reveal-opponent-cards': _testRevealOpponentCards(testPlayerRelativeIdx); break;
        }
    }

    let _testWishValue = 2
    let _testCurrentTurnIndex = 3;

    function _testShowAllControls() {
        State.resetGameScore();
        State.addGameScore([123, 321]);
        State.setStartPlayerIndex(2);
        let cards = /** @type Cards */ [[0,0], [1,0], [2,1], [2,2], [2,3], [2,4], [3,4], [10,1], [11,2], [12,2], [13,3], [14,3], [15,0], [16,0]];
        State.setHandCards(cards);
        const playerNames = ["Anton", "Beathe", "Chris", "Doris"];
        for (let playerIndex = 0; playerIndex <= 3; playerIndex++) {
            State.setPlayerName(playerIndex, playerNames[playerIndex]);
            State.setCountHandCards(playerIndex, 14);
        }
        State.setAnnouncement(0, 1);
        State.setAnnouncement(1, 1);
        State.setAnnouncement(2, 2);
        State.setAnnouncement(3, 2);
        State.setCurrentTurnIndex(_testCurrentTurnIndex);
        State.setWishValue(_testWishValue);
        _hasBomb = true;
        render();
    }

    function _testResetRound() {
        State.resetGameScore();
        State.setStartPlayerIndex(-1);
        State.setHandCards([]);
        State.setGivenSchupfCards(null);
        State.setReceivedSchupfCards(null);
        for (let i= 0; i <= 3; i++) {
            State.setCountHandCards(i, 0);
            State.setAnnouncement(i, 0);
        }
        State.setCurrentTurnIndex(-1);
        State.setWishValue(0);
        _hasBomb = false;
        render();
    }

    function _testToggleWish() {
        if (_wishIcon.classList.contains('hidden')) {
            _testWishValue = _testWishValue < 14 ? _testWishValue + 1 : 2;
            State.setWishValue(_testWishValue);
        }
        else {
            State.setWishValue(0);
        }
        _updateWishIcon();
    }

    function _testToggleBomb() {
        _hasBomb = !_hasBomb;
        _updateBombIcon();
    }

    function _testToggleTichu() {
        for (let i= 0; i <= 3; i++) {
            State.setAnnouncement(i, _tichuIcons[i].classList.contains('hidden') ? 1 : 0);
            _updateTichuIcon(i)
        }
    }

    function _testMoveTurn() {
        _testCurrentTurnIndex = (_testCurrentTurnIndex + 1) % 4;
        State.setCurrentTurnIndex(_testCurrentTurnIndex);
        _canPlay = true;
        _updateTurnIcon();
    }

    function _testDealCards() {
        let cardsCount = State.getCountHandCards();
        cardsCount = cardsCount > 0 ? Math.floor(cardsCount / 2) : 14;
        let cards = /** @type Cards */ [[0,0], [1,0], [2,1], [2,2], [2,3], [2,4], [3,4], [10,1], [11,2], [12,2], [13,3], [14,3], [15,0], [16,0]];
        cards.length = cardsCount;
        State.setHandCards(cards);
        for (let playerIndex = 0; playerIndex <= 3; playerIndex++) {
            State.setCountHandCards(playerIndex, cardsCount);
            _updateHand(playerIndex);
        }
    }

    function _testGetSelectedCards() {
        console.log(_getSelectedCards());
    }

    function _testClearSelectedCards() {
        _clearSelectedCards();
    }

    function _testToggleSchupfZones() {
        if (_schupfZones[0].classList.contains('hidden')) {
            State.setReceivedSchupfCards(null);
            _receivedSchupfCardsConfirmed = false;
            for (let i = 0; i <= 3; i++) {
                State.setCountHandCards(i, 14);
                _updateSchupfZone(i);
            }
        }
        else {
            State.setReceivedSchupfCards(/** @type Cards */ [[3,1], [2,1], [10,3]]);
            _receivedSchupfCardsConfirmed = true;
            for (let i = 0; i <= 3; i++) {
                _updateSchupfZone(i);
            }
        }
        _updatePlayButton();
    }

    function _testFillSchupfZones() {
        State.setReceivedSchupfCards(null);
        let cards = /** @type Cards */ [[0,0], [1,0], [2,1], [2,2], [2,3], [2,4], [3,4], [10,1], [11,2], [12,2], [13,3], [14,3], [15,0], [16,0]];
        cards.length = 11;
        State.setHandCards(cards);
        for (let i = 0; i <= 3; i++) {
            State.setCountHandCards(i, 11);
            _updateHand(i);
            _updateSchupfZone(i);
        }
    }

    function _testClearSchupfZones() {
        State.setReceivedSchupfCards(null);
        let cards = /** @type Cards */ [[0,0], [1,0], [2,1], [2,2], [2,3], [2,4], [3,4], [10,1], [11,2], [12,2], [13,3], [14,3], [15,0], [16,0]];
        State.setHandCards(cards);
        for (let i = 0; i <= 3; i++) {
            State.setCountHandCards(i, 14);
            _updateHand(i);
            _updateSchupfZone(i);
        }
    }

    function _testGetSchupfCards() {
        console.log(_getSchupfCards());
    }

    function _testAddTrick() {
        let trick = /** @type Trick */ []
        for (let i=0; i < 8; i++) {
            let turn = /** @type Turn */ [i % 4, [[i+3,1], [i+3,2]], [CombinationType.PAIR, 2, i+3]];
            trick.push(turn);
        }
        State.setTricks([trick]);
        for (let playerIndex = 0; playerIndex <= 3; playerIndex++) {
            _updatePlayedCards(playerIndex);
        }
    }

    function _testRemoveTrick() {
        State.setTricks([]);
        for (let playerIndex = 0; playerIndex <= 3; playerIndex++) {
            _updatePlayedCards(playerIndex);
        }
    }

    function _testShowDragonDialog() {
        Dialogs.showDragonDialog();
    }

    function _testShowWishDialog() {
        Dialogs.showWishDialog();
    }

    function _testShowRoundOverDialog() {
        Dialogs.showRoundOverDialog("Weiter geht's");
    }

    function _testShowGameOverDialog() {
        Dialogs.showGameOverDialog("Wir : Gegner<br\>1020 : 300<br\>400:200");
    }

    function _testShowErrorToast() {
        Dialogs.showErrorToast("Dies ist eine Fehlermeldung!");
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