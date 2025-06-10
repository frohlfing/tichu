
    // Beispielkarten für Tests
    let _testOwnCards = []; // Wird mit Objekten {value, suit, label, element} gefüllt
    let _testOpponentHands = { 1: [], 2: [], 3: [] }; // Für aufgedeckte Karten


	// --------------------------------------------------------------------------------------
    // Test-Buttons
    // --------------------------------------------------------------------------------------


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

        const cardsToPlayElements = _ownHandContainer.querySelectorAll('.card-face.selected');
        const playedCardLabels = [];

        cardsToPlayElements.forEach(cardEl => {
            cardEl.classList.remove('selected');
            cardEl.classList.add('playing');
            pile.appendChild(cardEl); // Verschiebt das DOM-Element
            playedCardLabels.push(cardEl.dataset.cardLabel);

            // Entferne die Karte aus dem _testOwnCards Array
            const cardIndex = _testOwnCards.findIndex(c => c.label === cardEl.dataset.cardLabel);
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
        pile.querySelectorAll('.card-face').forEach(c => c.classList.remove('highlight-trick')); // Alte Highlights entfernen
        const cardsInPile = pile.querySelectorAll('.card-face');
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
                    if (cardEl.tagName === 'DIV' && cardEl.classList.contains('card-face')) {
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
        for (let relativeIdx=0; relativeIdx<4; relativeIdx++) {
            const zones = _schupfZonesContainers[relativeIdx];
            zones.classList.toggle('hidden');
        }
    }

    function _testGiveOwnSchupfCard() {
        if (_testOwnCards.length > 0 && _testOwnCards[0].element &&
            _schupfZones && !_schupfZones.classList.contains('hidden') &&
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

        if(schupfZoneRight.querySelector('.card-face')) schupfZoneRight.innerHTML = 'R';
        else { schupfZoneRight.innerHTML = ''; schupfZoneRight.appendChild(_createCardElement(cardDataS5));}

        if(schupfZonePartner.querySelector('.card-face')) schupfZonePartner.innerHTML = 'P';
        else { schupfZonePartner.innerHTML = ''; schupfZonePartner.appendChild(_createCardElement(cardDataB6));}

        if(schupfZoneLeft.querySelector('.card-face')) schupfZoneLeft.innerHTML = 'L';
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
        _schupfZones.querySelectorAll('.schupf-zone .card-face').forEach(c => c.remove());
        _testDealOwnCards(); // Simuliert neue Hand (vereinfacht)
        _schupfZones.classList.add('hidden');
        CardHandler.disableSchupfMode();
        Dialogs.showErrorToast("Schupfkarten 'aufgenommen' (Hand neu gemischt).");
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
            const cardCount = 14;
            handContainer.innerHTML = '';
            for (let i = 0; i < cardCount; i++) {
                const cardBack = document.createElement('div');
                cardBack.className = 'card-back';
                handContainer.appendChild(cardBack);
            }
        }
    }

    function test_toggleDisabled(isSchupfing) {
        _exitButton.disabled = !_exitButton.disabled;
        _optionsButton.disabled = !_optionsButton.disabled;
        _passButton.disabled = !_passButton.disabled;
        _tichuButton.disabled = !_tichuButton.disabled;
        _playButton.disabled = !_playButton.disabled;
    }


    // ----------------------------------------------------------------------------------------------

    /**
     * Aktiviert/Deaktiviert die Steuerelemente für das Ausspielen von Karten.
     * @param {boolean} enable - True zum Aktivieren, false zum Deaktivieren.
     * @param {string} [requestId] - Die Request-ID für die aktuelle "play"-Aktion, falls aktiviert.
     */
    function enablePlayControls(enable, requestId) {
        _passButton.disabled = !enable;
        _playButton.disabled = !enable;
        // Tichu-Button-Logik ist komplexer (abhängig von Kartenanzahl, Phase, bereits angesagt)
        // _tichuButton.disabled = !enable || ...;

        if (_ownHandContainer) {
            _ownHandContainer.classList.toggle('disabled-hand', !enable);
        }

        if (enable && requestId) {
            _passButton.dataset.requestId = requestId;
            _playButton.dataset.requestId = requestId;
        }
        else {
            delete _passButton.dataset.requestId;
            delete _playButton.dataset.requestId;
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

        if (isSchupfing) {
            _playButton.onclick = () => {
                CardHandler.confirmSchupf();
                SoundManager.playSound('buttonClick');
            };
        }
        else {
            _playButton.onclick = _playButton_click; // Standard-Handler wiederherstellen
        }
        _playButton.disabled = false; // Immer aktivierbar im Schupf-Modus (wenn Karten gewählt)
    }


    /**
     * Der Container für die Handkarten des Benutzers.
     *
     * @type {HTMLDivElement}
     */
    const _ownHandContainer = document.getElementById('hand-bottom');

    function _getTestPlayerPile(relativePlayerIndex) {
        return document.getElementById(`played-cards-pile-player-${relativePlayerIndex}`);
    }


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
            const nameEl = _playerNames[relIdx];
            const tichuEl = _tichuIndicators[relIdx];
            const turnEl = _turnIndicators[relIdx]

            nameEl.textContent = (pubState.player_names && pubState.player_names[canonicalIdx])
                               ? pubState.player_names[canonicalIdx] + (canonicalIdx === ownPIdx ? " (Du)" : "")
                               : `Spieler ${relIdx}`;

            if (tichuEl) tichuEl.classList.toggle('hidden', !(pubState.announcements && pubState.announcements[canonicalIdx] > 0));
            if (turnEl) turnEl.classList.toggle('hidden', pubState.current_turn_index !== canonicalIdx);
        }
        if (pubState.current_turn_index === -1 && ownPIdx !== -1) { // Wenn Spiel beginnt, ist eigener Spieler oft Startspieler
             const ownTurnEl = document.querySelector(`#played-cards-pile-player-0 .turn-indicator`);
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
            const handContainer = _hands[i];
            if (handContainer.children.length === 0 && !handContainer.classList.contains('revealed')) {
                const canonicalIdx = Helpers.getCanonicalPlayerIndex(i);
                const cardCount = 14;
                for (let k = 0; k < cardCount; k++) {
                    const cardBack = document.createElement('div');
                    cardBack.className = 'card-back';
                    handContainer.appendChild(cardBack);
                }
            }
        }

        // Wunsch sichtbar machen
        _testToggleWishIndicator();

        // Tichu sichtbar machen
        _testShowSchupfZones();

        // Bomben-Icon Sichtbarkeit
         _bombIcon.classList.toggle('hidden', !(State.getPrivateState()));

        // Tichu-Indikator
        for (let displayIdx=0; displayIdx < 4; displayIdx++) {
            let tichuIndicator = _tichuIndicators[displayIdx];
            tichuIndicator.classList.toggle('hidden');
        }

        // Turn-Indikator
        for (let _currentTurnRelativeIndex=0; _currentTurnRelativeIndex < 4; _currentTurnRelativeIndex++) {
            _turnIndicators[_currentTurnRelativeIndex].classList.toggle('hidden');
        }

        let cardData = {
            value: 2,
            suit: 1,
            label: "S2"
        };
        let card = _createCardElement(cardData, true);
        _schupfZones[0][0].appendChild(card);
    }