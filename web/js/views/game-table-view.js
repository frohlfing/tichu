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
    const _schupfZones = [
        document.getElementById('schupf-zones-bottom'),
        document.getElementById('schupf-zones-right'),
        document.getElementById('schupf-zones-top'),
        document.getElementById('schupf-zones-left'),
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
    // Öffentliche Funktionen und Ereignishändler
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
     * Aktualisiert den Namen des Spielers.
     *
     * @param {number} relativeIndex - Der Index des Spielers (relative zum Benutzer).
     * @param {string} name - Der Name des Spielers.
     */
    function updatePlayerName(relativeIndex, name) {
        _playerNames[relativeIndex].textContent = name.trim()
    }

    /**
     * Aktualisiert die Handkarten (zeigt die Vorderseite der Karten).
     *
     * @param {number} relativeIndex - Der Index des Spielers (relative zum Benutzer).
     * @param {Cards} cards - Die Handkarten.
     */
    function updateHandCardFaces(relativeIndex, cards) {
        clearHandCards(relativeIndex);
        cards.forEach(card => {
            const cardFace = _createCardFaceElement(card)
            _hands[relativeIndex].appendChild(cardFace);
        });
    }

    /**
     * Aktualisiert die Anzahl der Handkarten (zeigt die Kartenrückseite).
     *
     * @param {number} relativeIndex - Der Index des Spielers (relative zum Benutzer).
     * @param {number} cardCount - Anzahl der Handkarten.
     */
    function updateHandCardBacks(relativeIndex, cardCount) {
        clearHandCards(relativeIndex);
        for (let k = 0; k < cardCount; k++) {
            _hands[relativeIndex].appendChild(_createCardBackElement());
        }
    }

    /**
     * Entfernt alle Handkarten des angegebenen Spielers.
     *
     * @param {number} relativeIndex - Der Index des Spielers (relative zum Benutzer).
     */
    function clearHandCards(relativeIndex) {
        // todo geht das nicht eleganter?
        while (_hands[relativeIndex].children.length) {
            _hands[relativeIndex].children[0].remove();
        }
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
            const selectedCardCount = _hands[0].querySelectorAll('.card-face.selected').length;
            if (selectedCardCount > 0) {
                return;
            }
        }

        SoundManager.playSound('buttonClick');
        const card = /** @type Card */ cardElement.dataset.card.split(",").map(value => parseInt(value, 10));
        console.debug(`_handClick: Karte ${Lib.stringifyCard(card)} (${card})`);
        cardElement.classList.toggle('selected');
    }

    /**
     * Gibt die aktuell ausgewählten Karten zurück.
     *
     * @returns {Cards}
     */
    function getSelectedCards() {
        let cards = [];
        _hands[0].querySelectorAll('.card-face.selected').forEach(cardElement => {
            cards.push(cardElement.dataset.card.split(",").map(value => parseInt(value, 10)));
        });
        return cards;
    }

    /**
     * Setzt die ausgewählten Karten zurück.
     */
    function clearSelectedCards() {
        _hands[0].querySelectorAll('.card-face.selected').forEach(cardElement => {
            cardElement.classList.remove('selected');
        });
    }

    /**
     * Zeigt die Schupfzonen an.
     */
    function showSchupfZones() {
        // ausgewählte Karen zurücksetzen, denn beim Schupfen darf nicht mehr als eine Karte selektiert werden
        clearSelectedCards();
        // Schupfzonen einblenden
        for (let i= 0; i <= 3; i++) {
            _schupfZones[i].classList.remove('hidden');
        }
    }

    /**
     * Blendet die Schupfzonen aus.
     */
    function hideSchupfZones() {
        for (let i= 0; i <= 3; i++) {
            _schupfZones[i].classList.add('hidden');
        }
    }

    /**
     * Füllt die Schupfzone mit verdeckten Karten.
     *
     * @param {number} relativeIndex - Der Index des Spielers (relative zum Benutzer).
     */
    function fillSchupfZone(relativeIndex) {
        clearSchupfZone(relativeIndex);
        _schupfZones[relativeIndex].querySelectorAll('.schupf-zone').forEach(schupfZoneElement => {
            schupfZoneElement.appendChild(_createCardBackElement());
        });
    }

    /**
     * Entfernt die Karten in der Schupfzone des angegebenen Spielers.
     *
     * @param {number} relativeIndex - Der Index des Spielers (relative zum Benutzer).
     */
    function clearSchupfZone(relativeIndex) {
        _schupfZones[relativeIndex].querySelectorAll('.schupf-zone .card-back, .schupf-zone .card-face').forEach(cardElement => {
            cardElement.remove();
        });
    }

    /**
     * Ereignishändler für das Anklicken der Schupfzone.
     *
     * @param {PointerEvent} event
     */
    function _schupfZoneClick(event) {
        if (event.target.classList.contains('schupf-zone')) {
            // es wurde auf eine leere Schupfzone geklickt
            const schupfZoneElement = event.target;
            const cardElement = _hands[0].querySelector('.card-face.selected');
            if (cardElement) {
                SoundManager.playSound('buttonClick');
                schupfZoneElement.appendChild(cardElement);
                cardElement.classList.remove('selected');
            }
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

            // Karte in die Hand einsortieren
            SoundManager.playSound('buttonClick');
            if (referenceElement) {
                _hands[0].insertBefore(cardElement, referenceElement);
            }
            else {
                _hands[0].appendChild(cardElement);
            }
            console.log("Karte zurückgelegt");
        }
    }

    /**
     * Gibt die Karten zurück, die sich aktuell in der Schupfzone befinden.
     *
     * @returns {Cards}
     */
    function getSchupfCards() {
        let cards = [];
        _schupfZones[0].querySelectorAll('.schupf-zone .card-face').forEach(cardElement => {
            cards.push(cardElement.dataset.card.split(",").map(value => parseInt(value, 10)));
        });
        return cards;
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
     * Ereignishändler für das Anklicken auf den "Passen"-Button.
     */
    function _passButtonClick() {
        SoundManager.playSound('buttonClick');
        console.log("_passButtonClick");
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
     * Ereignishändler für das Anklicken auf den "Tichu"-Button.
     */
    function _tichuButtonClick() {
        SoundManager.playSound('buttonClick');
        console.log("_tichuButtonClick");
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
     * Ereignishändler für das Anklicken auf den "Spielen"-Button.
     */
    function _playButtonClick() {
        SoundManager.playSound('buttonClick');
        console.log("_playButtonClick");
    }

    /**
     * Zeigt das Wunsch-Symbol an.
     *
     * @param {number} wishValue - Kartenwert zw. 2 und 14
     */
    function showWishIcon(wishValue) {
        _wishText.textContent = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"][wishValue];
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

    /**
     * Ereignishändler für das Anklicken auf das Bomben-Icon.
     */
    function _bombIconClick() {
        SoundManager.playSound('buttonClick');
        console.log("_bombIconClick");
    }

    // --------------------------------------------------------------------------------------
    // Hilfsfunktionen
    // --------------------------------------------------------------------------------------

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

    // todo top-bar-buttons und button-controls click event
    // todo bomb_click()
    // todo Selektierte Karten eingereiht lassen
    // todo schupfen
    // todo Play-Button: "Spielen" "Schupfen" "Kein Zug" "Aufnehmen" "Auswählen"
    // todo Grand Tichu
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

    // todo card-handler.js löschen

    // --------------------------------------------------------------------------------------
    // Test-Buttons
    // --------------------------------------------------------------------------------------

    function _handleTestButtonClick(event) {
        if (event.target.tagName !== 'BUTTON') return;
        const testAction = event.target.dataset.test;
        const testPlayerRelativeIdxInput = document.getElementById('test-player-index');
        const testPlayerRelativeIdx = testPlayerRelativeIdxInput ? parseInt(testPlayerRelativeIdxInput.value, 10) : 1;

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

            case 'show-dragon-dialog': _testShowDragonDialog(); break;
            case 'show-wish-dialog': _testShowWishDialog(); break;
            case 'show-round-over-dialog': _testShowRoundOverDialog(); break;
            case 'show-game-over-dialog': _testShowGameOverDialog(); break;
            case 'show-error-toast': _testShowErrorToast(); break;

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
    }

    function _testResetRound() {
        updateScore([0, 0]);
        disablePassButton();
        disableTichuButton();
        disablePlayButton();
        for (let i= 0; i <= 3; i++) {
            clearHandCards(i);
        }
        hideWishIcon();
        hideSchupfZones();
        hideBombIcon();
        for (let i= 0; i <= 3; i++) {
            hideTichuIcon(i);
        }
        hideTurnIcon();
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

    function _testDealCards() {
        let cards = /** @type Cards */ [[0,0], [1,0], [2,1], [2,2], [2,3], [2,4], [3,4], [10,1], [11,2], [12,2], [13,3], [14,3], [15,0], [16,0]];
        clearHandCards(0);
        updateHandCardFaces(0, cards);
        for (let i = 1; i <= 3; i++) {
            clearHandCards(i);
            updateHandCardBacks(i, cards.length);
        }
    }

    function _testGetSelectedCards() {
        console.log(getSelectedCards());
    }

    function _testClearSelectedCards() {
        clearSelectedCards();
    }

    function _testToggleSchupfZones() {
        if (_schupfZones[0].classList.contains('hidden')) {
            showSchupfZones();
        }
        else {
            hideSchupfZones();
        }
    }

    function _testFillSchupfZones() {
        for (let i = 0; i <= 3; i++) {
            fillSchupfZone(i);
        }
    }

    function _testClearSchupfZones() {
        for (let i = 0; i <= 3; i++) {
            clearSchupfZone(i);
        }
    }

    function _testGetSchupfCards() {
        console.log(getSchupfCards());
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

    return {
        init,
        render,
        show,
        hide,
        isVisible,
        updateScore,
        updatePlayerName,
        updateHandCardFaces,
        updateHandCardBacks,
        clearHandCards,
        getSelectedCards,
        clearSelectedCards,
        showSchupfZones,
        hideSchupfZones,
        fillSchupfZone,
        clearSchupfZone,
        getSchupfCards,
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