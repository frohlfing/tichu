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
        cardDiv.style.backgroundImage = `url('images/cards/${cardData.label}.png')`;
        cardDiv.dataset.label = cardData.label;
        cardDiv.dataset.value = cardData.value;
        cardDiv.dataset.suit = cardData.suit;
        if (isOwnCard) {
            cardDiv.onclick = function() {
                if (_schupfZonesContainer && !_schupfZonesContainer.classList.contains('hidden')) {
                    CardHandler.handleCardClick(this, cardData); // Nutze CardHandler für Schupf-Logik
                } else {
                    this.classList.toggle('selected'); // Normale Selektion
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
        const sampleLabels = ['S2', 'B3', 'G4', 'R5', 'SK', 'SA', 'Ma', 'Hu', 'Dr', 'Ph', 'S7', 'B8', 'G9', 'RZ'];
        sampleLabels.forEach(label => {
            const cardData = Helpers.parseCards([label])[0]; // Parse um value/suit zu bekommen
            if(cardData){
                const cardEl = _createCardElement(cardData, true);
                _ownHandContainer.appendChild(cardEl);
                _testOwnCards.push({...cardData, element: cardEl });
            }
        });
        document.querySelector('#player-area-0 .card-count').textContent = _testOwnCards.length;
    }

    function _testSelectSomeCards() {
        _testOwnCards.forEach((card, index) => {
            if (index < 3 && card.element) card.element.classList.add('selected');
        });
    }

    function _testPlaySelectedCards() {
        const pile = _getTestPlayerPile(0); // Eigene Karten auf eigenen Stapel
        if (!pile) return;
        const tempPlayed = [];
        _ownHandContainer.querySelectorAll('.card.selected').forEach(cardEl => {
            cardEl.classList.remove('selected');
            cardEl.classList.add('playing'); // Für Animation
            pile.appendChild(cardEl); // Verschiebe Element
            tempPlayed.push(cardEl.dataset.label);
            // Entferne aus _testOwnCards
            _testOwnCards = _testOwnCards.filter(c => c.label !== cardEl.dataset.label);
        });
        document.querySelector('#player-area-0 .card-count').textContent = _testOwnCards.length;
        console.log("Gespielt (visuell):", tempPlayed.join(" "));
        setTimeout(() => pile.querySelectorAll('.playing').forEach(c => c.classList.remove('playing')), 500);
    }

    function _testOpponentPlaysCards(relativeIdx) {
        const pile = _getTestPlayerPile(relativeIdx);
        if (!pile) return;
        pile.innerHTML = ''; // Alten Stich des Spielers leeren
        const cardData = Helpers.parseCards(['R K', 'R D', 'R B']); // Beispielkarten
        cardData.forEach(cd => pile.appendChild(_createCardElement(cd)));
        // Kartenanzahl des Gegners reduzieren (visuell)
        const countEl = document.querySelector(`#player-area-${relativeIdx} .card-count`);
        let currentCount = parseInt(countEl.textContent);
        countEl.textContent = Math.max(0, currentCount - cardData.length);
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
            CardHandler.enableSchupfMode('test-schupf-req', _testOwnCards);
        } else {
            CardHandler.disableSchupfMode();
        }
    }
    function _testGiveOwnSchupfCard(){
        // Simuliere Klick auf die erste Handkarte, wenn Schupf-Modus aktiv
        if (_testOwnCards.length > 0 && _testOwnCards[0].element &&
            _schupfZonesContainer && !_schupfZonesContainer.classList.contains('hidden')) {
            CardHandler.handleCardClick(_testOwnCards[0].element, _testOwnCards[0]);
        } else {
            console.log("Keine Karten zum Schupfen oder Schupf-Modus nicht aktiv.");
        }
    }


    function _testOpponentSchupfCards() {
        // Zeige Karten in den Schupfzonen der Gegner (simuliert)
        // Dies ist nur visuell, die echten Karten der Gegner sind unsichtbar
        const schupfZoneRight = document.getElementById('schupf-zone-opponent-right'); // Ziel für Karten von Links (relativ 3)
        const schupfZonePartner = document.getElementById('schupf-zone-partner');   // Ziel für Karten von Rechts (relativ 1)
        const schupfZoneLeft = document.getElementById('schupf-zone-opponent-left'); // Ziel für Karten von Partner (relativ 2)

        if(schupfZoneRight.children.length === 1) schupfZoneRight.innerHTML = 'R';
        else schupfZoneRight.innerHTML = `<div class="card" style="background-image: url('images/cards/S5.png');"></div>`;

        if(schupfZonePartner.children.length === 1) schupfZonePartner.innerHTML = 'P';
        else schupfZonePartner.innerHTML = `<div class="card" style="background-image: url('images/cards/B6.png');"></div>`;

         if(schupfZoneLeft.children.length === 1) schupfZoneLeft.innerHTML = 'L';
        else schupfZoneLeft.innerHTML = `<div class="card" style="background-image: url('images/cards/G7.png');"></div>`;
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
        _scoreDisplay.textContent = `Wir: ${scoreStr.split(':')[0]} | Die: ${scoreStr.split(':')[1]}`;
    }

    function _testUpdatePlayerName(relativeIdx) {
        const newName = document.getElementById('test-player-name').value;
        const nameEl = document.querySelector(`#player-area-${relativeIdx} .player-name`);
        if (nameEl) nameEl.textContent = newName;
    }

    function _testShowWishIndicator(value) {
        const cardLabel = (value === 14 ? 'A' : value === 13 ? 'K' : value === 12 ? 'D' : value === 11 ? 'B' : value === 10 ? 'Z' : String(value));
        _wishIndicator.style.backgroundImage = `url('images/cards/Ma${cardLabel}.png')`; // Annahme: Bilder wie Ma7.png, MaA.png
        // Fallback:
        // _wishIndicator.style.backgroundImage = `url('images/wish-indicator.png')`;
        // _wishIndicator.textContent = cardLabel; // Wenn Text überlagert wird
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
            // Simuliere das Aufdecken
            handContainer.innerHTML = ''; // Alte card-backs entfernen
            const sampleCards = ['S K', 'B D', 'G B', 'R Z']; // Beispielkarten
            if(!_testOpponentHands[relativeIdx] || _testOpponentHands[relativeIdx].length === 0){
                _testOpponentHands[relativeIdx] = Helpers.parseCards(sampleCards);
            }
            _testOpponentHands[relativeIdx].forEach(cardData => {
                const cardFace = _createCardElement(cardData);
                cardFace.classList.add('card-face'); // Für separates Styling falls nötig
                handContainer.appendChild(cardFace);
            });
        } else {
            // Simuliere das Zudecken (Anzahl muss bekannt sein)
            const cardCount = _testOpponentHands[relativeIdx] ? _testOpponentHands[relativeIdx].length : 5; // Fallback
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
        // console.log("GAMETABLEVIEW: Rendere GameTableView (minimal).");
        // const publicState = State.getPublicState();
        // const privateState = State.getPrivateState();
        //
        // if (!publicState || !privateState) {
        //     // Fallback, falls Daten noch nicht geladen sind
        //     _scoreDisplay.textContent = 'Lade Spiel...';
        //     // Ggf. andere Elemente auf einen Ladezustand setzen
        //     return;
        // }
        //
        // // Score anzeigen
        // const myPIdx = State.getPlayerIndex();
        // if (myPIdx !== -1 && publicState.game_score && publicState.game_score.length === 2) {
        //     const team02Score = publicState.game_score[0].reduce((a, b) => a + b, 0);
        //     const team13Score = publicState.game__score[1].reduce((a, b) => a + b, 0);
        //     const myTeamIs02 = myPIdx === 0 || myPIdx === 2;
        //     _scoreDisplay.textContent = `Wir: ${String(myTeamIs02 ? team02Score : team13Score).padStart(4, '0')} | Die: ${String(myTeamIs02 ? team13Score : team02Score).padStart(4, '0')}`;
        // }
        // else {
        //     _scoreDisplay.textContent = 'Punkte: 0:0';
        // }

        if (_ownHandContainer.children.length === 0) {
            _testDealOwnCards(); // Beim ersten Rendern Testkarten austeilen
        }
         // Relative Indizes: 0=unten (ich), 1=rechts, 2=oben (Partner), 3=links
        for(let i=1; i<=3; i++) {
            const handContainer = document.getElementById(`player-${i}-hand`);
            if (handContainer.children.length === 0) { // Nur wenn leer
                const cardCount = 14; // Standardanzahl
                document.querySelector(`#player-area-${i} .card-count`).textContent = cardCount;
                for(let k=0; k<cardCount; k++) {
                    const cardBack = document.createElement('div');
                    cardBack.className = 'card-back';
                    handContainer.appendChild(cardBack);
                }
            }
        }
        document.querySelector(`#player-area-${_currentTurnRelativeIndex} .turn-indicator`).classList.remove('hidden');
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