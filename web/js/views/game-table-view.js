// js/views/game-table-view.js

/**
 * @module GameTableView
 * Verwaltet die Anzeige und Interaktion des Spieltisches.
 * (Aktuell nur mit minimaler Funktionalität für den Beenden-Button).
 */
const GameTableView = (() => {
    /** @const {HTMLElement} _viewElement - Das DOM-Element des Spieltisch-Views. */
    const _viewElement = document.getElementById('game-table-screen');
    /** @const {HTMLButtonElement} _endGameButton - Button zum Beenden des Spiels/Verlassen des Tisches. */
    const _endGameButton = document.getElementById('end-game-button');
    /** @const {HTMLButtonElement} _optionsButton - Button für Spieloptionen. */
    const _optionsButton = document.getElementById('options-button');


    // Platzhalter für DOM-Elemente, die später relevant werden
    const _scoreDisplay = document.getElementById('score-display');
    const _ownHandContainer = document.getElementById('player-0-hand');
    const _passButton = document.getElementById('pass-button');
    const _tichuButton = document.getElementById('tichu-button');
    const _playCardsButton = document.getElementById('play-cards-button');
    const _bombIcon = document.getElementById('bomb-icon');
    const _wishIndicator = document.getElementById('wish-indicator');
    const _schupfZonesContainer = document.querySelector('.schupf-zones');


    /**
     * Initialisiert das GameTableView-Modul.
     * Setzt Event-Listener für die initialen Buttons.
     */
    function init() {
        console.log("GAMETABLEVIEW: Initialisiere GameTableView (minimal)...");
        _endGameButton.addEventListener('click', _handleEndGame);
        _optionsButton.addEventListener('click', _handleOptions);

        // Event-Listener für später implementierte Features (vorerst nur Beispiele)
        _passButton.addEventListener('click', _handlePass);
        _tichuButton.addEventListener('click', _handleTichuAnnounce);
        _playCardsButton.addEventListener('click', _handlePlayCards);
        _bombIcon.addEventListener('click', _handleBomb);

        // Kartenklicks werden über CardHandler und dynamisch erstellte Elemente gehandhabt
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

    /**
     * Rendert den Spieltisch-View.
     * (Aktuell minimal, wird später erweitert, um den gesamten Spielzustand darzustellen).
     */
    function render() {
        // console.log("GAMETABLEVIEW: Rendere GameTableView (minimal).");
        const publicState = State.getPublicState();
        const privateState = State.getPrivateState();

        if (!publicState || !privateState) {
            // Fallback, falls Daten noch nicht geladen sind
            _scoreDisplay.textContent = 'Lade Spiel...';
            // Ggf. andere Elemente auf einen Ladezustand setzen
            return;
        }

        // Score anzeigen
        const myPIdx = State.getPlayerIndex();
        if (myPIdx !== -1 && publicState.game_score && publicState.game_score.length === 2) {
            const team02Score = publicState.game_score[0].reduce((a, b) => a + b, 0);
            const team13Score = publicState.game__score[1].reduce((a, b) => a + b, 0);
            const myTeamIs02 = myPIdx === 0 || myPIdx === 2;
            _scoreDisplay.textContent = `Wir: ${String(myTeamIs02 ? team02Score : team13Score).padStart(4, '0')} | Die: ${String(myTeamIs02 ? team13Score : team02Score).padStart(4, '0')}`;
        } else {
            _scoreDisplay.textContent = 'Punkte: 0:0';
        }

        // TODO: Hier kommt die umfangreiche Logik zum Rendern von:
        // - Spieler-Infos (Namen, Kartenanzahl, Tichu-Anzeigen, Am-Zug-Marker) für alle 4 Spieler
        // - Eigene Handkarten (über CardHandler/Helpers.parseCards und DOM-Erstellung)
        // - Karten der Gegner (Rückseiten)
        // - Gespielte Karten in der Mitte des Tisches
        // - Wunsch-Anzeige
        // - Zustand der Action-Buttons (Passen, Tichu, Spielen) basierend auf _activeServerRequest und Spielphase
        // - Sichtbarkeit des Bomben-Icons
        // - Sichtbarkeit/Zustand der Schupf-Zonen
    }

    /**
     * Wird aufgerufen, wenn der View angezeigt wird.
     */
    function show() {
        // console.log("GAMETABLEVIEW: GameTableView wird angezeigt.");
        render(); // Beim Anzeigen immer den aktuellen Zustand rendern
    }

    /**
     * Wird aufgerufen, wenn der View ausgeblendet wird.
     */
    function hide() {
        // console.log("GAMETABLEVIEW: GameTableView wird ausgeblendet.");
        // Ggf. laufende Animationen stoppen oder Zustände zurücksetzen
        enablePlayControls(false); // Steuerelemente deaktivieren, wenn der Tisch verlassen wird
        CardHandler.disableSchupfMode();
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
        } else {
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
            case 'played':
            case 'passed':
            case 'trick_taken':
                render(); // Einfaches Neu-Rendern bei vielen Events
                break;
            case 'tichu_announced':
                // Spezifisches Update für Tichu-Indikator
                if (context && typeof context.player_index === 'number') {
                    const displayIdx = Helpers.getRelativePlayerIndex(context.player_index);
                    const tichuIndicator = document.querySelector(`#player-area-${displayIdx} .tichu-indicator`);
                    if (tichuIndicator) tichuIndicator.classList.toggle('hidden', !context.announced);
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
            _playCardsButton.onclick = () => { CardHandler.confirmSchupf(); SoundManager.playSound('buttonClick'); };
        } else {
            _playCardsButton.onclick = _handlePlayCards; // Standard-Handler wiederherstellen
        }
        _playCardsButton.disabled = false; // Immer aktivierbar im Schupf-Modus (wenn Karten gewählt)
    }


    // --- Private Handler für Action-Buttons (werden später implementiert) ---
    function _handlePass() {
        const requestId = _passButton.dataset.requestId;
        if (requestId) {
            SoundManager.playSound('pass' + State.getPlayerIndex());
            AppController.sendResponse(requestId, { cards: [] }); // Leeres Array für Passen (Server erwartet [[v,s]])
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
            SoundManager.playSound('announce');
            AppController.sendProactiveMessage('announce'); // Proaktive Ansage
            _tichuButton.disabled = true; // Deaktivieren nach Ansage
        } else {
            Dialogs.showErrorToast("Tichu kann jetzt nicht angesagt werden.");
        }
    }

    function _handlePlayCards() {
        const requestId = _playCardsButton.dataset.requestId;
        const selectedCards = CardHandler.getSelectedCards(); // Client-Objekte {value, suit, label}
        if (requestId && selectedCards.length > 0) {
            SoundManager.playSound('play' + State.getPlayerIndex());
            AppController.sendResponse(requestId, { cards: Helpers.formatCardsForServer(selectedCards) });
            // Hand-Update erfolgt durch Server-Notification
            CardHandler.clearSelectedCards();
            enablePlayControls(false);
        } else if (selectedCards.length === 0) {
            Dialogs.showErrorToast("Keine Karten zum Spielen ausgewählt.");
        }
    }
    function _handleBomb() {
        const selectedCards = CardHandler.getSelectedCards();
        // TODO: Clientseitige Prüfung, ob ausgewählte Karten eine Bombe sind (optional, Server prüft final)
        if (selectedCards.length >= 4) { // Minimale Voraussetzung für eine Bombe
             SoundManager.playSound('bomb' + State.getPlayerIndex());
            AppController.sendProactiveMessage('bomb', { cards: Helpers.formatCardsForServer(selectedCards) });
            // UI-Feedback für Bombe (z.B. Animation oder Text)
            // Hand-Update durch Server-Notification
            CardHandler.clearSelectedCards();
        } else {
            Dialogs.showErrorToast("Ungültige Auswahl für eine Bombe.");
        }
    }

    return {
        init,
        render,
        show,
        hide,
        enablePlayControls, // Damit AppController dies steuern kann
        handleNotification,  // Damit AppController dies aufrufen kann
        setPlayControlsForSchupfen // Für CardHandler/AppController
    };
})();