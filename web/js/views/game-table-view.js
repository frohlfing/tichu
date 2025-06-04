/**
 * Anzeige und Interaktion des Spieltisches.
 *
 * @type {View}
 */
const GameTableView = (() => {
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
    const _endGameButton = document.getElementById('end-game-button');

    /**
     * Button für Spieloptionen.
     *
     * @type {HTMLButtonElement}
     */
    const _optionsButton = document.getElementById('options-button');

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
     * Button zum Karten ausspielen.
     *
     * @type {HTMLButtonElement}
     */
    const _playCardsButton = document.getElementById('play-cards-button');

    /**
     * Die Anzeige des Punktestandes.
     *
     * @type {HTMLDivElement}
     */
    const _scoreDisplay = document.getElementById('score-display');

    /**
     * Der Container für die Handkarten des Benutzers.
     *
     * @type {HTMLDivElement}
     */
    const _ownHandContainer = document.getElementById('player-0-hand');

    /**
     * Der Container für die Ablage-Zonen der Tauschkarten.
     *
     * @type {HTMLDivElement}
     */
    const _schupfZonesContainer = document.querySelector('.schupf-zones');

    /**
     * Das Bomben-Icon.
     *
     * @type {HTMLImageElement}
     */
    const _bombIcon = document.getElementById('bomb-icon');

    /**
     * Das Icon zur Anzeige einer Tichu-Ansage.
     *
     * @type {HTMLImageElement}
     */
    const _tichuIndicator = document.getElementById('tichu-indicator');

    /**
     * Das Icon zur Anzeige eines offenen Wunsches.
     *
     * @type {HTMLImageElement}
     */
    const _wishIndicator = document.getElementById('wish-indicator');

    /**
     * Das Icon zur Anzeige des Spielers, der am Zug ist.
     *
     * @type {HTMLImageElement}
     */
    const _turnIndicator = document.getElementById('turn-indicator');

    // --------------------------------------------------------
    const _viewElement = _viewContainer

    // Für Test-Buttons
    const _testControlsContainer = document.getElementById('test-controls-container');

    // Beispielkarten für Tests
    let _testOwnCards = []; // Wird mit Objekten {value, suit, label, element} gefüllt
    let _testOpponentHands = { 1: [], 2: [], 3: [] }; // Für aufgedeckte Karten

    // Aktueller Spieler am Zug für Turn-Indikator Test
    let _currentTurnRelativeIndex = 0;
    // --------------------------------------------------------

    /**
     * Initialisiert den Spieltisch-Bildschirm.
     */
    function init() {
        console.log("GAMETABLEVIEW: Initialisiere GameTableView (minimal)...");
        _endGameButton.addEventListener('click', _handleEndGame);
        _optionsButton.addEventListener('click', _handleOptions);

        // Event-Listener für später implementierte Features (vorerst nur Beispiele)
        // _passButton.addEventListener('click', _handlePass);
        // _tichuButton.addEventListener('click', _handleTichuAnnounce);
        // _playCardsButton.addEventListener('click', _handlePlayCards);
        // _bombIcon.addEventListener('click', _handleBomb);

        // -----------------------------------------------------------
        // Die echten Action-Buttons sind vorerst für Tests deaktiviert oder lösen Testfunktionen aus
        _passButton.onclick = () => console.log("Test: Passen geklickt");
        _tichuButton.onclick = () => console.log("Test: Tichu geklickt");
        _playCardsButton.onclick = () => _testPlaySelectedCards(); // Test für Ausspielen

        // Event Listener für Test-Buttons
        if (_testControlsContainer) {
            _testControlsContainer.addEventListener('click', _handleTestButtonClick);
        }
        // -----------------------------------------------------------
    }

    /**
     * Event-Handler für den "Beenden"-Button.
     * Zeigt einen Bestätigungsdialog an.
     */
    function _handleEndGame() {
        SoundManager.playSound('buttonClick');
        Dialogs.showLeaveConfirmDialog();
    }

    /**
     * Event-Handler für den "Optionen"-Button.
     * (Aktuell Platzhalter).
     */
    function _handleOptions() {
        SoundManager.playSound('buttonClick');
        console.log("GAMETABLEVIEW: Optionen-Button geklickt (noch keine Funktion).");
        Dialogs.showErrorToast("Optionen sind noch nicht implementiert.");
        // Hier könnte ein Dialog mit Sound-Einstellungen etc. geöffnet werden.
        // Beispiel: Dialogs.showOptionsDialog(SoundManager.areSoundsEnabled(), SoundManager.getVolume());
    }

    // ---------------------------------------------------------

    // --- Hilfsfunktionen für visuelle Tests ---
    function _createCardElement(cardData, isOwnCard = false) {
        const cardDiv = document.createElement('div');
        cardDiv.className = 'card';
        // Stelle sicher, dass cardData.label existiert (sollte durch Helpers.parseCards der Fall sein)
        cardDiv.style.backgroundImage = `url('images/cards/${cardData.label || 'back'}.png')`;
        cardDiv.dataset.label = cardData.label || 'unbekannt';
        cardDiv.dataset.value = cardData.value;
        cardDiv.dataset.suit = cardData.suit;
        if (isOwnCard) {
            cardDiv.onclick = function() {
                // Die Logik, die entscheidet, ob CardHandler oder normale Selektion,
                // sollte hier oder im CardHandler selbst liegen.
                // Fürs Erste: CardHandler immer nutzen, wenn Schupf-Modus aktiv ist.
                if (CardHandler.isSchupfModeActive && typeof CardHandler.isSchupfModeActive === 'function' && CardHandler.isSchupfModeActive()) {
                    CardHandler.handleCardClick(this, cardData);
                } else {
                    this.classList.toggle('selected');
                    SoundManager.playSound('cardSelect');
                }
            };
        }
        return cardDiv;
    }

    function _getTestPlayerPile(relativePlayerIndex) {
        return document.getElementById(`played-cards-pile-player-${relativePlayerIndex}`);
    }


    // --- Test-Button Handler ---
    function _handleTestButtonClick(event) {
        if (event.target.tagName !== 'BUTTON') return;
        const testAction = event.target.dataset.test;
        const testPlayerRelativeIdxInput = document.getElementById('test-player-index');
        const testPlayerRelativeIdx = testPlayerRelativeIdxInput ? parseInt(testPlayerRelativeIdxInput.value) : 1;

        switch (testAction) {
            case 'deal-own-cards': _testDealOwnCards(); break;
            case 'select-cards': _testSelectSomeCards(); break;
            case 'play-selected-cards': _testPlaySelectedCards(); break;
            case 'opponent-plays-cards': _testOpponentPlaysCards(testPlayerRelativeIdx); break;
            case 'highlight-trick': _testHighlightTrick(testPlayerRelativeIdx); break;
            case 'take-trick-self': _testTakeTrick(0); break;
            case 'take-trick-opponent': _testTakeTrick(testPlayerRelativeIdx); break;
            case 'show-schupf-zones': _testShowSchupfZones(); break;
            case 'give-own-schupf-card': _testGiveOwnSchupfCard(); break;
            case 'opponent-schupf-cards': _testOpponentSchupfCards(); break;
            case 'animate-schupf-exchange': _testAnimateSchupfExchange(); break;
            case 'take-schupf-cards': _testTakeSchupfCards(); break;
            case 'update-score': _testUpdateScore(); break;
            case 'update-player-name': _testUpdatePlayerName(testPlayerRelativeIdx); break;
            case 'toggle-dragon-dialog': Dialogs.showDragonDialog('test-dragon-req'); break;
            case 'toggle-wish-dialog': Dialogs.showWishDialog('test-wish-req'); break;
            case 'show-wish-indicator': _testShowWishIndicator(7); break;
            case 'hide-wish-indicator': _wishIndicator.classList.add('hidden'); break;
            case 'toggle-bomb-icon': _bombIcon.classList.toggle('hidden'); break;
            case 'throw-bomb-effect': _testThrowBombEffect(); break;
            case 'toggle-tichu-player1': _testToggleTichuIndicator(testPlayerRelativeIdx); break;
            case 'next-turn-indicator': _testNextTurnIndicator(); break;
            case 'reveal-opponent-cards': _testRevealOpponentCards(testPlayerRelativeIdx); break;
            case 'toggle-round-end-dialog': Dialogs.handleNotification('round_over', { game_score: [[120],[30]], player_names: ["Ich","Chris","Partner","Alex"] }); break;
            case 'toggle-game-end-dialog': Dialogs.handleNotification('game_over', { game_score: [[1050],[780]], player_names: ["Ich","Chris","Partner","Alex"] }); break;
            case 'toggle-leave-dialog': Dialogs.showLeaveConfirmDialog(); break;
            case 'show-error-toast': Dialogs.showErrorToast("Dies ist ein Test-Fehler!"); break;
        }
    }

    // --- Implementierung der Test-Funktionen ---
    function _testDealOwnCards() {
        _ownHandContainer.innerHTML = '';
        _testOwnCards = [];
        // Testkarten als [value, suit] Tupel/Arrays definieren
        const sampleCardTuples = [
            [2, CardSuits.SWORD], [3, CardSuits.PAGODA], [4, CardSuits.JADE], [5, CardSuits.STAR],
            [13, CardSuits.SWORD], [14, CardSuits.SWORD], // SK, SA
            [SpecialCardValues.MAH, CardSuits.SPECIAL],  // Ma
            [SpecialCardValues.DOG, CardSuits.SPECIAL],  // Hu
            [SpecialCardValues.DRA, CardSuits.SPECIAL],  // Dr
            [SpecialCardValues.PHO, CardSuits.SPECIAL],  // Ph
            [7, CardSuits.SWORD], [8, CardSuits.PAGODA], [9, CardSuits.JADE], [10, CardSuits.STAR] // SZ bei Star = RZ
        ];

        const parsedTestCards = Helpers.parseCards(sampleCardTuples);

        parsedTestCards.forEach(cardData => {
            if (cardData && cardData.label) { // Stelle sicher, dass die Karte valide geparst wurde
                const cardEl = _createCardElement(cardData, true);
                _ownHandContainer.appendChild(cardEl);
                _testOwnCards.push({ ...cardData, element: cardEl }); // Füge DOM-Element Referenz hinzu
            }
        });
    }

    function _testSelectSomeCards() {
        _testOwnCards.forEach((cardData, index) => {
            // Stelle sicher, dass cardData.element existiert und eine DOM-Node ist
            if (index < 3 && cardData.element && typeof cardData.element.classList !== 'undefined') {
                cardData.element.classList.add('selected');
            }
        });
    }

    /**
     * Spielt die aktuell im DOM als '.selected' markierten Karten visuell aus.
     */
    function _testPlaySelectedCards() {
        const pile = _getTestPlayerPile(0);
        if (!pile) return;

        const cardsToPlayElements = _ownHandContainer.querySelectorAll('.card.selected');
        const playedCardLabels = [];

        cardsToPlayElements.forEach(cardEl => {
            cardEl.classList.remove('selected');
            cardEl.classList.add('playing');
            pile.appendChild(cardEl); // Verschiebt das DOM-Element
            playedCardLabels.push(cardEl.dataset.label);

            // Entferne die Karte aus dem _testOwnCards Array
            const cardIndex = _testOwnCards.findIndex(c => c.label === cardEl.dataset.label);
            if (cardIndex > -1) {
                _testOwnCards.splice(cardIndex, 1);
            }
        });

        console.log("Gespielt (visuell):", playedCardLabels.join(" "));
        setTimeout(() => pile.querySelectorAll('.playing').forEach(c => c.classList.remove('playing')), 500);
    }

    /**
     * Simuliert, dass ein Mitspieler Karten ablegt.
     * @param {number} relativeIdx - Der relative Index des Mitspielers (1=R, 2=P, 3=L).
     */
    function _testOpponentPlaysCards(relativeIdx) {
        const pile = _getTestPlayerPile(relativeIdx);
        if (!pile) return;
        pile.innerHTML = '';
        // Beispielkarten als [value, suit]
        const sampleOpponentCardTuples = [[13, CardSuits.STAR], [12, CardSuits.STAR], [11, CardSuits.STAR]]; // RK, RD, RB
        const parsedOpponentCards = Helpers.parseCards(sampleOpponentCardTuples);

        parsedOpponentCards.forEach(cd => {
            if (cd && cd.label) pile.appendChild(_createCardElement(cd));
        });
    }

    function _testHighlightTrick(relativeIdx) {
        const pile = _getTestPlayerPile(relativeIdx);
        if (!pile) return;
        pile.querySelectorAll('.card').forEach(c => c.classList.remove('highlight-trick')); // Alte Highlights entfernen
        const cardsInPile = pile.querySelectorAll('.card');
        if (cardsInPile.length > 0) {
            cardsInPile[cardsInPile.length - 1].classList.add('highlight-trick'); // Letzte Karte hervorheben
        }
    }

    function _testTakeTrick(takerRelativeIdx) {
        console.log(`Stich geht zu Spieler (relativ) ${takerRelativeIdx}`);
        const takerRect = document.getElementById(`player-area-${takerRelativeIdx}`).getBoundingClientRect();
        const targetX = takerRect.left + takerRect.width / 2;
        const targetY = takerRect.top + takerRect.height / 2;

        for (let i = 0; i < 4; i++) {
            const pile = _getTestPlayerPile(i);
            if (pile) {
                Array.from(pile.children).forEach(cardEl => {
                    if (cardEl.tagName === 'DIV' && cardEl.classList.contains('card')) {
                        cardEl.classList.add('flying');
                        const cardRect = cardEl.getBoundingClientRect();
                        // Absolute Position setzen für Animation
                        cardEl.style.position = 'fixed'; // oder absolute, je nach Elter
                        cardEl.style.left = cardRect.left + 'px';
                        cardEl.style.top = cardRect.top + 'px';
                        document.body.appendChild(cardEl); // An Body anhängen für freie Positionierung

                        // Zielposition animieren
                        setTimeout(() => { // Kleiner Timeout, damit CSS-Transition greift
                            cardEl.style.transform = `translate(${targetX - cardRect.left - cardRect.width/2}px, ${targetY - cardRect.top - cardRect.height/2}px) scale(0.3)`;
                            cardEl.style.opacity = '0';
                        }, 20);

                        // Element nach Animation entfernen
                        setTimeout(() => {
                            if (cardEl.parentNode) cardEl.parentNode.removeChild(cardEl);
                        }, 750); // Etwas länger als Transition
                    } else {
                        pile.innerHTML = ''; // Andere Inhalte (PASS Text) einfach löschen
                    }
                });
            }
        }
    }

    function _testShowSchupfZones() {
        _schupfZonesContainer.classList.toggle('hidden');
        if (!_schupfZonesContainer.classList.contains('hidden')) {
            // Übergebe die clientseitigen Kartenobjekte
            CardHandler.enableSchupfMode('test-schupf-req', _testOwnCards.map(c => ({value: c.value, suit: c.suit, label: c.label})));
        } else {
            CardHandler.disableSchupfMode();
        }
    }

    function _testGiveOwnSchupfCard() {
        if (_testOwnCards.length > 0 && _testOwnCards[0].element &&
            _schupfZonesContainer && !_schupfZonesContainer.classList.contains('hidden') &&
            CardHandler.isSchupfModeActive && CardHandler.isSchupfModeActive()) {
            // Übergebe das volle Kartenobjekt an CardHandler
            CardHandler.handleCardClick(_testOwnCards[0].element, {
                value: _testOwnCards[0].value,
                suit: _testOwnCards[0].suit,
                label: _testOwnCards[0].label
            });
        } else {
            console.log("Keine Karten zum Schupfen oder Schupf-Modus nicht aktiv.");
        }
    }

    function _testOpponentSchupfCards() { /* ... (bleibt strukturell gleich, verwendet jetzt korrekte Labels) ... */
        const schupfZoneRight = document.getElementById('schupf-zone-opponent-right');
        const schupfZonePartner = document.getElementById('schupf-zone-partner');
        const schupfZoneLeft = document.getElementById('schupf-zone-opponent-left');
        const cardDataS5 = Helpers.parseCards([[5, CardSuits.SWORD]])[0];
        const cardDataB6 = Helpers.parseCards([[6, CardSuits.PAGODA]])[0];
        const cardDataG7 = Helpers.parseCards([[7, CardSuits.JADE]])[0];

        if(schupfZoneRight.querySelector('.card')) schupfZoneRight.innerHTML = 'R';
        else { schupfZoneRight.innerHTML = ''; schupfZoneRight.appendChild(_createCardElement(cardDataS5));}

        if(schupfZonePartner.querySelector('.card')) schupfZonePartner.innerHTML = 'P';
        else { schupfZonePartner.innerHTML = ''; schupfZonePartner.appendChild(_createCardElement(cardDataB6));}

        if(schupfZoneLeft.querySelector('.card')) schupfZoneLeft.innerHTML = 'L';
        else { schupfZoneLeft.innerHTML = ''; schupfZoneLeft.appendChild(_createCardElement(cardDataG7));}
    }

    function _testAnimateSchupfExchange() {
        // Komplexere Animation, hier nur ein Platzhalter
        // Man bräuchte Startpositionen (Hände der Spieler) und Zielpositionen (Schupf-Zonen des Empfängers)
        // und dann Karten-Elemente zwischen diesen animieren.
        Dialogs.showErrorToast("Schupf-Animation noch nicht implementiert.");
    }
    function _testTakeSchupfCards() {
        // Simuliere Aufnahme: Eigene Schupfzonen leeren, Kartenanzahl erhöhen
        _schupfZonesContainer.querySelectorAll('.schupf-zone .card').forEach(c => c.remove());
        _testDealOwnCards(); // Simuliert neue Hand (vereinfacht)
        _schupfZonesContainer.classList.add('hidden');
        CardHandler.disableSchupfMode();
        Dialogs.showErrorToast("Schupfkarten 'aufgenommen' (Hand neu gemischt).");
    }


    function _testUpdateScore() {
        const scoreStr = document.getElementById('test-score').value;
        _scoreDisplay.textContent = `${scoreStr.split(':')[0]} : ${scoreStr.split(':')[1]}`;
    }

    function _testUpdatePlayerName(relativeIdx) {
        const newName = document.getElementById('test-player-name').value;
        const nameEl = document.querySelector(`#player-area-${relativeIdx} .player-name`);
        if (nameEl) nameEl.textContent = newName;
    }

    function _testShowWishIndicator(value) {
        // Finde das Label für den Wert
        let cardLabelForWish = String(value);
        if (value === 14) cardLabelForWish = "A";
        else if (value === 13) cardLabelForWish = "K";
        else if (value === 12) cardLabelForWish = "D";
        else if (value === 11) cardLabelForWish = "B";
        else if (value === 10) cardLabelForWish = "Z"; // Für Zehn
        // Annahme: Es gibt kein spezifisches Bild für "Mahjong mit Wert X",
        // daher verwenden wir das generische Wunsch-Icon und zeigen den Wert als Text (oder eine andere visuelle Kennung)
        _wishIndicator.style.backgroundImage = `url('images/wish-indicator.png')`; // Generisches Bild
        // Erstelle ein temporäres Element für den Text, um es über das Bild zu legen
        let existingText = _wishIndicator.querySelector('.wish-value-text');
        if (!existingText) {
            existingText = document.createElement('span');
            existingText.className = 'wish-value-text'; // Style für diesen Text in CSS hinzufügen
            _wishIndicator.appendChild(existingText);
        }
        existingText.textContent = cardLabelForWish;
        _wishIndicator.classList.remove('hidden');
    }

    function _testThrowBombEffect() {
        const bombTextEl = document.createElement('div');
        bombTextEl.className = 'bomb-effect-text';
        bombTextEl.textContent = 'BOMBE!';
        document.body.appendChild(bombTextEl);
        SoundManager.playSound('bomb' + _currentTurnRelativeIndex); // Sound des aktuellen Spielers
        setTimeout(() => {
            if (bombTextEl.parentNode) bombTextEl.parentNode.removeChild(bombTextEl);
        }, 800); // Dauer der Animation
    }

    function _testToggleTichuIndicator(relativeIdx) {
        const indicator = document.querySelector(`#player-area-${relativeIdx} .tichu-indicator`);
        if (indicator) indicator.classList.toggle('hidden');
    }

    function _testNextTurnIndicator() {
        document.querySelector(`#player-area-${_currentTurnRelativeIndex} .turn-indicator`).classList.add('hidden');
        _currentTurnRelativeIndex = (_currentTurnRelativeIndex + 1) % 4;
        document.querySelector(`#player-area-${_currentTurnRelativeIndex} .turn-indicator`).classList.remove('hidden');
    }

    function _testRevealOpponentCards(relativeIdx) {
        const handContainer = document.getElementById(`player-${relativeIdx}-hand`);
        if (!handContainer) return;

        handContainer.classList.toggle('revealed');
        if (handContainer.classList.contains('revealed')) {
            handContainer.innerHTML = '';
            // Beispielhafte Karten als [value, suit] Tupel
            const sampleOpponentCardTuples = [[13, CardSuits.SWORD], [12, CardSuits.PAGODA], [11, CardSuits.JADE], [10, CardSuits.STAR]];
            const parsedOpponentCards = Helpers.parseCards(sampleOpponentCardTuples);
            _testOpponentHands[relativeIdx] = parsedOpponentCards; // Speichere für späteres Zudecken

            parsedOpponentCards.forEach(cardData => {
                if(cardData && cardData.label){
                    const cardFace = _createCardElement(cardData);
                    cardFace.classList.add('card-face');
                    handContainer.appendChild(cardFace);
                }
            });
        } else {
            const cardCount = 10;
            handContainer.innerHTML = '';
            for (let i = 0; i < cardCount; i++) {
                const cardBack = document.createElement('div');
                cardBack.className = 'card-back';
                handContainer.appendChild(cardBack);
            }
        }
    }

    // ---------------------------------------------------------

    /**
     * Rendert den Spieltisch-Bildschirm.
     */
    function render() {
        if (State.getPublicState() === null) { // Sicherstellen, dass Daten da sind
             console.log("GAMETABLEVIEW: Warte auf State für Render...");
            _scoreDisplay.textContent = 'Lade...';
            return;
        }
        console.log("GAMETABLEVIEW: Rendere Spieltisch...");

        // Score (Beispiel, wie es mit neuem State aussehen könnte)
        const pubState = State.getPublicState();
        const ownPIdx = State.getPlayerIndex();
        if (ownPIdx !== -1 && pubState && pubState.game_score && pubState.game_score.length === 2) {
            const team02Score = pubState.game_score[0].reduce((a, b) => a + b, 0);
            const team13Score = pubState.game_score[1].reduce((a, b) => a + b, 0);
            const myTeamIs02 = ownPIdx === 0 || ownPIdx === 2;
            _scoreDisplay.textContent = `${String(myTeamIs02 ? team02Score : team13Score).padStart(4, '0')} : ${String(myTeamIs02 ? team13Score : team02Score).padStart(4, '0')}`;
        } else {
            _scoreDisplay.textContent = '0000 : 0000';
        }

        // Spieler-Infos aktualisieren
        for (let relIdx = 0; relIdx < 4; relIdx++) {
            const canonicalIdx = Helpers.getCanonicalPlayerIndex(relIdx);
            const playerArea = document.getElementById(`player-area-${relIdx}`);
            const nameEl = playerArea.querySelector('.player-name');
            const tichuEl = playerArea.querySelector('.tichu-indicator');
            const turnEl = playerArea.querySelector('.turn-indicator');

            nameEl.textContent = (pubState.player_names && pubState.player_names[canonicalIdx])
                               ? pubState.player_names[canonicalIdx] + (canonicalIdx === ownPIdx ? " (Du)" : "")
                               : `Spieler ${relIdx}`;

            if (tichuEl) tichuEl.classList.toggle('hidden', !(pubState.announcements && pubState.announcements[canonicalIdx] > 0));
            if (turnEl) turnEl.classList.toggle('hidden', pubState.current_turn_index !== canonicalIdx);
        }
        if (pubState.current_turn_index === -1 && ownPIdx !== -1) { // Wenn Spiel beginnt, ist eigener Spieler oft Startspieler
             const ownTurnEl = document.querySelector(`#player-area-0 .turn-indicator`);
             if(ownTurnEl && _currentTurnRelativeIndex === 0) ownTurnEl.classList.remove('hidden');
        }


        // Eigene Hand nur einmal initial mit Testkarten füllen, wenn leer
        if (_ownHandContainer.children.length === 0 && _testOwnCards.length === 0) {
            _testDealOwnCards(); // Diese Funktion sollte _testOwnCards füllen
        } else if (_ownHandContainer.children.length === 0 && _testOwnCards.length > 0) {
            // Hand neu aufbauen, falls sie geleert wurde aber _testOwnCards noch existieren
            _testOwnCards.forEach(cardData => {
                if (cardData && cardData.label) {
                    const cardEl = _createCardElement(cardData, true);
                    _ownHandContainer.appendChild(cardEl);
                    cardData.element = cardEl; // DOM-Referenz aktualisieren
                }
            });
        }

        // Gegnerhände mit Kartenrücken füllen (nur initial oder wenn leer)
        for (let i = 1; i <= 3; i++) { // relative Indizes für Gegner
            const handContainer = document.getElementById(`player-${i}-hand`);
            if (handContainer.children.length === 0 && !handContainer.classList.contains('revealed')) {
                const canonicalIdx = Helpers.getCanonicalPlayerIndex(i);
                const cardCount = (pubState.count_hand_cards && pubState.count_hand_cards[canonicalIdx] !== undefined)
                                  ? pubState.count_hand_cards[canonicalIdx] : 14;
                for (let k = 0; k < cardCount; k++) {
                    const cardBack = document.createElement('div');
                    cardBack.className = 'card-back';
                    handContainer.appendChild(cardBack);
                }
            }
        }
        // Bomben-Icon Sichtbarkeit
         _bombIcon.classList.toggle('hidden', !(State.getPrivateState()));


        // Wunsch-Indikator
        if (pubState.wish_value > 0) {
            _testShowWishIndicator(pubState.wish_value); // Wiederverwende Test-Funktion
        } else {
            _wishIndicator.classList.add('hidden');
        }
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
        // console.log("GAMETABLEVIEW: GameTableView wird ausgeblendet.");
        // Ggf. laufende Animationen stoppen oder Zustände zurücksetzen
        enablePlayControls(false); // Steuerelemente deaktivieren, wenn der Tisch verlassen wird
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

    /**
     * Aktiviert/Deaktiviert die Steuerelemente für das Ausspielen von Karten.
     * @param {boolean} enable - True zum Aktivieren, false zum Deaktivieren.
     * @param {string} [requestId] - Die Request-ID für die aktuelle "play"-Aktion, falls aktiviert.
     */
    function enablePlayControls(enable, requestId) {
        _passButton.disabled = !enable;
        _playCardsButton.disabled = !enable;
        // Tichu-Button-Logik ist komplexer (abhängig von Kartenanzahl, Phase, bereits angesagt)
        // _tichuButton.disabled = !enable || ...;

        if (_ownHandContainer) {
            _ownHandContainer.classList.toggle('disabled-hand', !enable);
        }

        if (enable && requestId) {
            _passButton.dataset.requestId = requestId;
            _playCardsButton.dataset.requestId = requestId;
        }
        else {
            delete _passButton.dataset.requestId;
            delete _playCardsButton.dataset.requestId;
        }
    }

    /**
     * Behandelt Server-Notifications, die für den Spieltisch relevant sind.
     * Stößt spezifische UI-Updates an.
     * @param {string} eventName - Der Name des Server-Events.
     * @param {object} context - Der Kontext des Events.
     */
    function handleNotification(eventName, context) {
        // console.log("GAMETABLEVIEW: Notification empfangen:", eventName, context);
        // Diese Funktion wird sehr umfangreich, wenn alle Spielmechaniken implementiert sind.
        // Für den initialen Test (Login/Lobby/Logout) ist sie noch nicht kritisch.
        // Beispiel:
        switch (eventName) {
            case 'hand_cards_dealt':
            case 'player_turn_changed':
            case 'player_played':
            case 'player_passed':
            case 'trick_taken':
                render(); // Einfaches Neu-Rendern bei vielen Events
                break;
            case 'player_announced':
                // Spezifisches Update für Tichu-Indikator
                if (context && typeof context.player_index === 'number') {
                    const displayIdx = Helpers.getRelativePlayerIndex(context.player_index);
                    const tichuIndicator = document.querySelector(`#player-area-${displayIdx} .tichu-indicator`);
                    if (tichuIndicator) {
                        tichuIndicator.classList.toggle('hidden', !context.announced);
                    }
                }
                break;
            // Weitere Events...
        }
    }

    /** Passt Zustand der UI-Elemente für den Schupf-Vorgang an. */
    function setPlayControlsForSchupfen(isSchupfing) {
        _passButton.classList.toggle('hidden', isSchupfing);
        _tichuButton.classList.toggle('hidden', isSchupfing);
        // Der "Spielen"-Button könnte zu einem "Schupfen Bestätigen"-Button werden
        _playCardsButton.textContent = isSchupfing ? "Schupfen Bestätigen" : "Spielen";
        if (isSchupfing) {
            _playCardsButton.onclick = () => {
                CardHandler.confirmSchupf();
                SoundManager.playSound('buttonClick');
            };
        }
        else {
            _playCardsButton.onclick = _handlePlayCards; // Standard-Handler wiederherstellen
        }
        _playCardsButton.disabled = false; // Immer aktivierbar im Schupf-Modus (wenn Karten gewählt)
    }

    // --- Private Handler für Action-Buttons (werden später implementiert) ---
    function _handlePass() {
        const requestId = _passButton.dataset.requestId;
        if (requestId) {
            SoundManager.playSound('pass' + State.getPlayerIndex());
            AppController.sendResponse(requestId, {cards: []}); // Leeres Array für Passen (Server erwartet [[v,s]])
            CardHandler.clearSelectedCards();
            enablePlayControls(false);
        }
    }

    function _handleTichuAnnounce() {
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

    function _handlePlayCards() {
        const requestId = _playCardsButton.dataset.requestId;
        const selectedCards = CardHandler.getSelectedCards(); // Client-Objekte {value, suit, label}
        if (requestId && selectedCards.length > 0) {
            SoundManager.playSound('play' + State.getPlayerIndex());
            AppController.sendResponse(requestId, {cards: Helpers.formatCardsForServer(selectedCards)});
            // Hand-Update erfolgt durch Server-Notification
            CardHandler.clearSelectedCards();
            enablePlayControls(false);
        }
        else if (selectedCards.length === 0) {
            Dialogs.showErrorToast("Keine Karten zum Spielen ausgewählt.");
        }
    }

    function _handleBomb() {
        const selectedCards = CardHandler.getSelectedCards();
        // TODO: Clientseitige Prüfung, ob ausgewählte Karten eine Bombe sind (optional, Server prüft final)
        if (selectedCards.length >= 4) { // Minimale Voraussetzung für eine Bombe
            SoundManager.playSound('bomb' + State.getPlayerIndex());
            AppController.sendProactiveMessage('bomb', {cards: Helpers.formatCardsForServer(selectedCards)});
            // UI-Feedback für Bombe (z.B. Animation oder Text)
            // Hand-Update durch Server-Notification
            CardHandler.clearSelectedCards();
        }
        else {
            Dialogs.showErrorToast("Ungültige Auswahl für eine Bombe.");
        }
    }

    return {
        init,
        render,
        show,
        hide,
        isVisible,
        enablePlayControls, // Damit AppController dies steuern kann
        handleNotification,  // Damit AppController dies aufrufen kann
        setPlayControlsForSchupfen // Für CardHandler/AppController
    };
})();