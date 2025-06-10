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
     * Die Container für die Handkarten.
     *
     * @type {HTMLDivElement}
     */
    const _hands = [
        document.getElementById('hand-bottom'),
        document.getElementById('hand-right'),
        document.getElementById('hand-top'),
        document.getElementById('hand-left'),
    ];

    /**
     * Die Container für die Ablage-Zonen der Tauschkarten.
     *
     * @type {HTMLDivElement}
     */
    const _schupfZonesContainers = [
        document.getElementById('schupf-zones-bottom'),
        document.getElementById('schupf-zones-right'),
        document.getElementById('schupf-zones-top'),
        document.getElementById('schupf-zones-left'),
    ];

    /**
     * Die Ablage-Zonen der Tauschkarten.
     *
     * @type {HTMLDivElement}
     */
    const _schupfZones = [
        [document.getElementById('schupf-zone-bottom-1'), document.getElementById('schupf-zone-bottom-2'), document.getElementById('schupf-zone-bottom-3')],
        [document.getElementById('schupf-zone-right-1'), document.getElementById('schupf-zone-right-2'), document.getElementById('schupf-zone-right-3')],
        [document.getElementById('schupf-zone-top-1'), document.getElementById('schupf-zone-top-2'), document.getElementById('schupf-zone-top-3')],
        [document.getElementById('schupf-zone-left-1'), document.getElementById('schupf-zone-left-2'), document.getElementById('schupf-zone-left-3')],
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
    // Öffentliche Funktionen
    // --------------------------------------------------------------------------------------
    
    /**
     * Initialisiert den Spieltisch-Bildschirm.
     */
    function init() {
        console.log("GAMETABLEVIEW: Initialisiere GameTableView (minimal)...");

        // Event-Listener einrichten
        _exitButton.addEventListener('click', _exitButton_click);
        _optionsButton.addEventListener('click', _optionsButton_click);
        _passButton.addEventListener('click', _passButton_click);
        _tichuButton.addEventListener('click', _tichuButton_click);
        _playButton.addEventListener('click', _playButton_click);
        _bombIcon.addEventListener('click', _bombIcon_click);
        _schupfZonesContainers[0].addEventListener('click', _schupfZone_click);

        // Event-Listener für Test-Buttons todo: nach Testphase entfernen
        document.getElementById('test-controls-container').addEventListener('click', _handleTestButtonClick);
    }

    /**
     * Rendert den Spieltisch-Bildschirm.
     */
    function render() {
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
        //enablePlayControls(false);
        CardHandler.disableSchupfMode();
        _viewContainer.classList.remove('active');
    }

    /**
     * Ermittelt, ob der Spieltisch-Bildschirm gerade angezeigt wird.
     *
     * @returns {boolean}
     */
    function isVisible() {
        return _viewContainer.classList.contains('active')
    }

    // Funktionen speziell für den Spieltisch

    /**
     * Aktualisiert den Punktestand in der Top-Bar.
     *
     * @param {[number, number]} score Punkte des Teams 20 und des Teams 31.
     */
    function updateScore(score) {
        let team20 = score[0].toString().padStart(4, '0');
        let team31 = score[1].toString().padStart(4, '0');
        _scoreDisplay.textContent = `${team20} : ${team31}`;
    }

    /**
     * Aktualisiert den Namen des Spielers
     *
     * @param {number} relativeIndex - Der Index des Spielers (relative zum Benutzer).
     * @param {string} name - Der Name des Spielers.
     */
    function updatePlayerName(relativeIndex, name) {
        _playerNames[relativeIndex].textContent = name.trim()
    }

    /**
     * Teilt die Handkarten aus.
     *
     * @param {Cards} cardsData
     */
    function dealOut(cardsData) {
        // alte Karten entfernen
        clearHandCards()

        // eigene Karten anzeigen
        cardsData.forEach(cardData => {
            const cardFace = _createCardFaceElement(cardData)
            cardFace.addEventListener('click', _hand_card_click);
            _hands[0].appendChild(cardFace);
        });

        // Kartenrückseite der Mitspieler zeigen
        const cardCount = cardsData.length;
        for (let i = 1; i <= 3; i++) {
            for (let k = 0; k < cardCount; k++) {
                _hands[i].appendChild(_createCardBackElement());
            }
        }
    }

    /**
     * Entfernt alle Handkarten.
     */
    function clearHandCards() {
        // todo geht das nicht eleganter?
        for (let i = 0; i <= 3; i++) {
            while (_hands[i].children.length)
                _hands[i].children[0].remove();
        }
    }

    /**
     * Zeigt die Schupf-Zonen an.
     */
    function showSchupfZones() {
        for (let i= 0; i <= 3; i++) {
            _schupfZonesContainers[i].classList.remove('hidden');
        }
    }

    /**
     * Blendet die Schupf-Zonen aus.
     */
    function hideSchupfZones() {
        for (let i= 0; i <= 3; i++) {
            _schupfZonesContainers[i].classList.add('hidden');
        }
    }

    /**
     * Bewegt das Turn-Symbol zum angebenden Spieler.
     *
     * @param {number} relativeIndex - Der Index des Spielers (relative zum Benutzer).
     */
    function moveTurnIcon(relativeIndex) {
        hideTurnIcon()
        _turnIcon[relativeIndex].classList.remove('hidden');
    }

    /**
     * Blendet das Turn-Symbol aus.
     */
    function hideTurnIcon() {
        for (let i = 0; i <= 3; i++) {
            _turnIcon[i].classList.add('hidden');
        }
    }

    /**
     * Zeigt das Tichu-Icon an.
     *
     * @param {number} relativeIndex - Der Index des Spielers (relative zum Benutzer).
     */
    function showTichuIcon(relativeIndex) {
        _tichuIcons[relativeIndex].classList.remove('hidden');
    }

    /**
     * Blendet das Tichu-Icon aus.
     *
     * @param {number} relativeIndex - Der Index des Spielers (relative zum Benutzer).
     */
    function hideTichuIcon(relativeIndex) {
        _tichuIcons[relativeIndex].classList.add('hidden');
    }

    // Bottom-Controls

    /**
     * Aktiviert den Pass-Button.
     */
    function enablePassButton() {
        _passButton.disabled = false;
    }

    /**
     * Deaktiviert den Pass-Button.
     */
    function disablePassButton() {
        _passButton.disabled = true;
    }

    /**
     * Aktiviert den Tichu-Button.
     */
    function enableTichuButton() {
        _tichuButton.disabled = false;
    }

    /**
     * Deaktiviert den Tichu-Button.
     */
    function disableTichuButton() {
        _tichuButton.disabled = true;
    }

    /**
     * Aktiviert den Play-Button.
     */
    function enablePlayButton() {
        _playButton.disabled = false;
    }

    /**
     * Deaktiviert den Options-Button.
     */
    function disablePlayButton() {
        _playButton.disabled = true;
    }

    /**
     * Zeigt das Wunsch-Symbol an.
     *
     * @param {number} wishValue - Kartenwert zw. 2 und 14
     */
    function showWishIcon(wishValue) {
        _wishText.textContent = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "B", "D", "K", "A"][wishValue];
        _wishIcon.classList.remove('hidden');
    }

    /**
     * Blendet das Wunsch-Symbol aus.
     */
    function hideWishIcon() {
        _wishIcon.classList.add('hidden');
    }

    /**
     * Zeigt das Bomben-Symbol.
     */
    function showBombIcon() {
        _bombIcon.classList.remove('hidden');
    }

    /**
     * Blendet das Bomben-Symbol aus.
     */
    function hideBombIcon() {
        _bombIcon.classList.add('hidden');
    }

    // --------------------------------------------------------------------------------------
    // Event-Listener
    // --------------------------------------------------------------------------------------

    /**
     * Event-Handler für den "Beenden"-Button.
     */
    function _exitButton_click() {
        SoundManager.playSound('buttonClick');
        Dialogs.showExitDialog();
    }

    /**
     * Event-Handler für den "Optionen"-Button.
     */
    function _optionsButton_click() {
        SoundManager.playSound('buttonClick');
        console.log("GAMETABLEVIEW: Optionen-Button geklickt (noch keine Funktion).");
        Dialogs.showErrorToast("Optionen sind noch nicht implementiert.");
    }

    /**
     * Event-Handler für den "Passen"-Button.
     */
    function _passButton_click() {
        const requestId = _passButton.dataset.requestId;
        if (requestId) {
            SoundManager.playSound('pass' + State.getPlayerIndex());
            AppController.sendResponse(requestId, {cards: []}); // Leeres Array für Passen (Server erwartet [[v,s]])
            CardHandler.clearSelectedCards();
            //enablePlayControls(false);
        }
    }

    /**
     * Event-Handler für den "Tichu"-Button.
     */
    function _tichuButton_click() {
        // Prüfen, ob Tichu angesagt werden darf (macht der Server, aber kleine Client-Prüfung schadet nicht)
        const privState = State.getPrivateState();
        const pubState = State.getPublicState();
        if (privState && pubState && privState.hand_cards && privState.hand_cards.length === 14 &&
            pubState.announcements && pubState.announcements[State.getPlayerIndex()] === 0) {
            SoundManager.playSound('announce' + State.getPlayerIndex());
            AppController.sendProactiveMessage('announce'); // Proaktive Ansage
            _tichuButton.disabled = true; // Deaktivieren nach Ansage
        }
        else {
            Dialogs.showErrorToast("Tichu kann jetzt nicht angesagt werden.");
        }
    }

    /**
     * Event-Handler für den "Schupfen"-, "Aufnehmen"- und "Spielen"-Button.
     */
    function _playButton_click() {
        const requestId = _playButton.dataset.requestId;
        const selectedCards = CardHandler.getSelectedCards(); // Client-Objekte {value, suit, label}
        if (requestId && selectedCards.length > 0) {
            SoundManager.playSound('play' + State.getPlayerIndex());
            AppController.sendResponse(requestId, {cards: Helpers.formatCardsForServer(selectedCards)});
            // Hand-Update erfolgt durch Server-Notification
            CardHandler.clearSelectedCards();
            //enablePlayControls(false);
        }
        else if (selectedCards.length === 0) {
            Dialogs.showErrorToast("Keine Karten zum Spielen ausgewählt.");
        }
    }

    /**
     * Event-Handler für das Anklicken auf das Bomben-Icon.
     */
    function _bombIcon_click() {
        const selectedCards = CardHandler.getSelectedCards();
        if (selectedCards.length >= 4) { // Minimale Voraussetzung für eine Bombe  todo richtige Prüfung für Bombe einbauen
            SoundManager.playSound('bomb' + State.getPlayerIndex());
            AppController.sendProactiveMessage('bomb', {cards: Helpers.formatCardsForServer(selectedCards)});
            CardHandler.clearSelectedCards();
        }
        else {
            Dialogs.showErrorToast("Ungültige Auswahl für eine Bombe.");
        }
    }

    /**
     * Event-Handler für das Anklicken der Schupf-Zone.
     */
    function _schupfZone_click(event) {
       if (typeof (event.target.dataset.schupfZone) != "undefined") {
            // es wurde auf eine leere Schupf-Zone geklickt
            const schupfZone = parseInt(event.target.dataset.schupfZone);
            console.debug(`Schupf-Zone ${schupfZone}`);
        }
        else if (typeof (event.target.dataset.cardLabel) != "undefined") {
            // es wurde auf eine Karte in der Schupf-Zone geklickt
            const cardLabel = event.target.dataset.cardLabel;
            const cardValue = parseInt(event.target.dataset.cardValue);
            const cardSuit = event.target.dataset.cardSuit;
            console.debug(`Karte ${cardLabel} ([${cardValue}, ${cardSuit}])`);
        }
    }

    /**
     * Event-Handler für das Anklicken einer Handkarte
     */
    function _hand_card_click() {
        // if (CardHandler.isSchupfModeActive && typeof CardHandler.isSchupfModeActive === 'function' && CardHandler.isSchupfModeActive()) {
        //     CardHandler.handleCardClick(this, cardData);
        // }
        // else {
             this.classList.toggle('selected');
             SoundManager.playSound('cardSelect');
        // }
    }

    // --------------------------------------------------------------------------------------
    // Hilfsfunktionen
    // --------------------------------------------------------------------------------------

    /**
     * Erzeugt eine offene Karte.
     *
     * @param {Card} cardData - Wert und Farbe der Karte
     * @returns {HTMLDivElement}
     */
    function _createCardFaceElement(cardData) {
        const cardFace = document.createElement('div');
        cardFace.className = 'card-face';
        cardFace.style.backgroundImage = `url('images/cards/${cardData.label}.png')`;
        cardFace.dataset.cardLabel = cardData.label;
        cardFace.dataset.cardValue = cardData.value;
        cardFace.dataset.cardSuit = cardData.suit;
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

    // todo Kartenattribute: nur cardValue und cardSuit speichern (label brauchen wir nicht)
    // todo top-bar-buttons und button-controls click event
    // todo bomb_click()
    // todo Selektierte Karten eingereiht lassen
    // todo schupfen
    // todo Play-Button: "Spielen" "Schupfen" "Kein Zug" "Aufnehmen" "Auswählen"(?)
    // todo Grand Tichu
    // todo Dialoge
    // todo card-handler.js und helpers.js löschen

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
        const testPlayerRelativeIdxInput = document.getElementById('test-player-index');
        const testPlayerRelativeIdx = testPlayerRelativeIdxInput ? parseInt(testPlayerRelativeIdxInput.value) : 1;

        switch (testAction) {
            case 'show-all-controls': _testShowAllControls(); break;
            case 'reset-round': _testResetRound(); break;
            case 'deal-cards': _testDealCards(); break;
            case 'toggle-wish': _testToggleWish(); break;
            case 'toggle-schupf-zones': _testToggleSchupfZones(); break;
            case 'toggle-bomb': _testToggleBomb(); break;
            case 'toggle-tichu': _testToggleTichu(); break;
            case 'move-turn': _testMoveTurn(); break;
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
            // case 'toggle-dragon-dialog': Dialogs.showDragonDialog('test-dragon-req'); break;
            // case 'toggle-wish-dialog': Dialogs.showWishDialog('test-wish-req'); break;
            // case 'throw-bomb-effect': _testThrowBombEffect(); break;
            // case 'reveal-opponent-cards': _testRevealOpponentCards(testPlayerRelativeIdx); break;
            // case 'toggle-round-over-dialog': Dialogs.handleNotification('round_over', { game_score: [[120],[30]], player_names: ["Ich","Chris","Partner","Alex"] }); break;
            // case 'toggle-game-over-dialog': Dialogs.handleNotification('game_over', { game_score: [[1050],[780]], player_names: ["Ich","Chris","Partner","Alex"] }); break;
            // case 'toggle-exit-dialog': Dialogs.showExitDialog(); break;
            // case 'show-error-toast': Dialogs.showErrorToast("Dies ist ein Test-Fehler!"); break;
            // case 'toggle-disabled': test_toggleDisabled(); break;
        }
    }

    function _testShowAllControls() {
        updateScore([321, 123]);
        enablePassButton();
        enableTichuButton();
        enablePlayButton();
        _testDealCards();
        _testWishValue = _testWishValue < 14 ? _testWishValue + 1 : 2;
        showWishIcon(_testWishValue);
        showSchupfZones();
        showBombIcon();

        const playerNames = ["Anton", "Beathe", "Chris", "Doris"];
        for (let i= 0; i <= 3; i++) {
            showTichuIcon(i);
            _turnIcon[i].classList.remove('hidden');
            updatePlayerName(i, playerNames[i]);
        }

        // Karte in der Schupfzone ablegen
        let cardData = {
            value: 2,
            suit: 1,
            label: "S2"
        };
        let card = _createCardFaceElement(cardData);
        _schupfZones[0][0].appendChild(card);
    }

    function _testResetRound() {
        updateScore([0, 0]);
        disablePassButton();
        disableTichuButton();
        disablePlayButton();
        clearHandCards();
        hideWishIcon();
        hideSchupfZones();
        hideBombIcon();
        for (let i= 0; i <= 3; i++) {
            hideTichuIcon(i);
        }
        hideTurnIcon();
    }

    function _testDealCards() {
        // Farben: 0 = Sonderkarte, 1 = Schwarz, 2 = Blau, 3 = Grün, 4 = Rot
        dealOut([
            {value: 2, suit: 1, label: "S2"},
            {value: 2, suit: 2, label: "B4"},
            {value: 2, suit: 3, label: "G5"},
            {value: 2, suit: 4, label: "R5"},
            {value: 2, suit: 4, label: "R6"},
            {value: 0, suit: 0, label: "Hu"},
            {value: 1, suit: 0, label: "Ma"},
            {value: 15, suit: 0, label: "Dr"},
            {value: 16, suit: 0, label: "Ph"},
            {value: 10, suit: 1, label: "SZ"},
            {value: 11, suit: 2, label: "BB"},
            {value: 12, suit: 2, label: "BD"},
            {value: 13, suit: 3, label: "GK"},
            {value: 14, suit: 3, label: "GA"},
        ]);
    }

    let _testWishValue = 1
    function _testToggleWish() {
        if (_wishIcon.classList.contains('hidden')) {
            _testWishValue = _testWishValue < 14 ? _testWishValue + 1 : 2;
            showWishIcon(_testWishValue);
        }
        else {
            hideWishIcon();
        }
    }

    function _testToggleSchupfZones() {
        if (_schupfZonesContainers[0].classList.contains('hidden')) {
            showSchupfZones();
        }
        else {
            hideSchupfZones();
        }
    }

    function _testToggleBomb() {
        if (_bombIcon.classList.contains('hidden')) {
            showBombIcon();
        }
        else {
            hideBombIcon();
        }
    }

    function _testToggleTichu() {
        for (let i= 0; i <= 3; i++) {
            if (_tichuIcons[i].classList.contains('hidden')) {
                showTichuIcon(i);
            }
            else {
                hideTichuIcon(i);
            }
        }
    }

    let _testCurrentTurnIndex = 3  // relative zum Benutzer
    function _testMoveTurn() {
        _testCurrentTurnIndex = (_testCurrentTurnIndex + 1) % 4;
        moveTurnIcon(_testCurrentTurnIndex);
    }

    return {
        init,
        render,
        show,
        hide,
        isVisible,
        updateScore,
        updatePlayerName,
        dealOut,
        clearHandCards,
        showSchupfZones,
        hideSchupfZones,
        moveTurnIcon,
        hideTurnIcon,
        showTichuIcon,
        hideTichuIcon,
        showWishIcon,
        hideWishIcon,
        showBombIcon,
        hideBombIcon,
        enablePassButton,
        disablePassButton,
        enableTichuButton,
        disableTichuButton,
        enablePlayButton,
        disablePlayButton,
    };
})();