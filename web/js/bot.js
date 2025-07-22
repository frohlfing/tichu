/**
 * Steuert die View autonom durch zufällige Aktionen.
 */
const Bot = (() => {

    /**
     * Ist True, wenn der Bot aktiviert ist.
     *
     * @type {boolean}
     */
    let _isEnabled = false;

    /**
     * ID für den Timeout der laufenden Aktion.
     *
     * @type {number|null}
     */
    let _actionTimeoutId = null;

    /**
     * Anzahl der gespielten Partien.
     *
     * @type {number}
     */
    let _gameCounter = 0;

    /**
     * Aktiviert oder deaktiviert den Bot.
     *
     * @param {boolean} enabled - True zum Aktivieren, False zum Deaktivieren.
     */
    function setEnabled(enabled) {
        if (enabled === _isEnabled) {
            return;
        }
        _isEnabled = enabled;
        if (_isEnabled) {
            console.log("%c🤖 BOT AKTIVIERT 🤖", "color: #ff4500; font-size: 1.2em; font-weight: bold;");
            _gameCounter = 0;  // Partien-Zähler zurücksetzen
            EventBus.on("view:rendered", _onViewRendered);
            _scheduleNextAction(); // initiale Aktion planen
        }
        else {
            console.log("%c🤖 BOT DEAKTIVIERT 🤖", "color: #777; font-size: 1.2em;");
            EventBus.off("view:rendered", _onViewRendered);
            if (_actionTimeoutId) {
                clearTimeout(_actionTimeoutId);
                _actionTimeoutId = null;
            }
        }
    }

    /**
     * Wird aufgerufen, wann immer eine View gerendert wurde.
     */
    function _onViewRendered() {
        if (!_isEnabled) {
            return;
        }
        _scheduleNextAction(); // nächte Aktion planen
    }

    /**
     * Plant die nächste Aktion mit einer zufälligen Verzögerung.
     */
    function _scheduleNextAction() {
        if (!_isEnabled) {
            return;
        }

        // Bestehenden Timer abbrechen, falls ein neues Render-Event schneller kam
        if (_actionTimeoutId) {
            clearTimeout(_actionTimeoutId);
        }

        const delay = Random.integer(Config.BOT_DELAY[0], Config.BOT_DELAY[1]); // Zufällige Verzögerung
        _actionTimeoutId = setTimeout(_performAction, delay);
    }

    /**
     * Führt die eigentliche Logik des Bots aus.
     */
    function _performAction() {
        if (!_isEnabled) {
            return;
        }

        // RoundOver-Dialog und GameOver-Dialog zuerst behandeln, da sie Aktionen blockieren.
        const roundOverButton = document.querySelector('#round-over-dialog:not(.hidden) button:not(:disabled)');
        if (roundOverButton) {
            console.log("🤖 Bot: Runde beendet. Schließe RoundOver-Dialog.");
            roundOverButton.click();
        }

        const gameOverButton = document.querySelector('#game-over-dialog:not(.hidden) button:not(:disabled)');
        if (gameOverButton) {
            // Partien mitzählen. Wenn eine bestimmte Anzahl erreicht wurde, nichts mehr machen.
            _gameCounter++; // Partie beendet, Zähler erhöhen
            console.log(`%c🤖 Bot: Partie ${_gameCounter} beendet. Schließe GameOver-Dialog.`, "color: #008000; font-weight: bold;");
            gameOverButton.click();
        }

        if (ViewManager.isVisible('login')) {
            _performLoginAction();
        }
        else if (ViewManager.isVisible('lobby')) {
            _performLobbyAction();
        }
        else if (ViewManager.isVisible('table')) {
            _performTableAction();
        }
    }

    /**
     * Bedient die Login-View.
     */
    function _performLoginAction() {
        _testUILogin();
        // Fülle die Felder und löse den Submit aus
        console.log("🤖 Bot: Auf dem Login-Screen. Logge ein...");
        document.getElementById('login-player-name').value = User.getPlayerName() || `Bot_${Random.integer(100, 999)}`;
        document.getElementById('login-table-name').value = User.getTableName() || `Tisch_${Random.integer(10, 99)}`;
        _clickButton('#login-submit-button');
    }

    /**
     * Bedient die Lobby-View.
     */
    function _performLobbyAction() {
        _testUILobby()

        if (State.isHost()) {
            // Zufällige Position der Spieler ändern
            if (Random.boolean()) {
                const upButtons = document.querySelectorAll('#lobby-player-list .player-order-controls button:first-child:not(:disabled)');
                const downButtons = document.querySelectorAll('#lobby-player-list .player-order-controls button:last-child:not(:disabled)');
                const allButtons = [...upButtons, ...downButtons];
                if (allButtons.length > 0) {
                    console.log("🤖 Bot: Tausche zufällig Spielerposition in der Lobby...");
                    const randomButton = Random.choice(allButtons);
                    randomButton.click();
                    return;
                }
            }
            // Spiel starten
            console.log("🤖 Bot: In der Lobby als Host. Starte das Spiel...");
            _clickButton('#lobby-start-button');
        }
        else {
            console.log("🤖 Bot: In der Lobby. Warte auf andere Spieler oder den Host...");
        }
    }

    /**
     * Bedient die Table-View.
     */
    function _performTableAction() {
        _testUIHand();
        _testUIScoreDisplay();
        _testUIWishIcon();

        if (State.getReceivedSchupfCards() && !State.isConfirmedReceivedSchupfCards()) {
            if (document.querySelectorAll('#schupf-zone-bottom .schupf-subzone .card:not(.back-site)').length) {
                // Wir haben geschupfte Karten erhalten und müssen sie bestätigen
                console.log("🤖 Bot: Bestätige erhaltene Schupf-Karten.");
                _clickButton('#play-button[data-mode="RECEIVE"]');
            }
        }

        _testUITichuIcons();
        const tichuButton = document.getElementById('tichu-button');
        if (!tichuButton.disabled) {
            if (Random.boolean(0.25)) {
                console.log("🤖 Bot: Klicke auf Tichu-Button.");
                tichuButton.click();
            }
        }

        _testUIBombIcon();
        const bombIcon = document.getElementById('bomb-icon');
        if (!bombIcon.classList.contains('hidden') && !bombIcon.classList.contains("disabled")) {
            if (Random.boolean(0.25)) {
                console.log("🤖 Bot: Klicke auf das Bomben-Symbol.");
                if (State.canPlayBomb()) {
                    _clearSelectedCards();
                    bombIcon.click(); // Nach dem Klick werden die Karten für eine Bombe selektiert.
                    console.log("🤖 Bot: Klicke auf Play-Button.");
                    _clickButton('#play-button[data-mode="PLAY"]')
                }
            }
        }

        // Prüfe, ob eine Anfrage vom Server an uns gerichtet ist

        const pendingAction = State.getPendingAction();
        if (pendingAction) {
            console.log(`🤖 Bot: Anfrage erhalten: ${pendingAction}`);
            switch (pendingAction) {
                case 'announce_grand_tichu':
                    if (Random.boolean(1/20)) {
                        console.log("🤖 Bot: Klicke auf GrandTichu-Button.");
                        _clickButton('#tichu-button[data-mode="GRAND_TICHU"]');
                    }
                    else {
                        console.log("🤖 Bot: Klicke auf NoGrandTichu-Button.");
                        _clickButton('#pass-button[data-mode="NO_GRAND_TICHU"]');
                    }
                    break;

                case 'schupf':
                    _testUISchupfZone();
                    // In der View der Reihe nach erst die Karte und dann auf die Schupfzone klicken.
                    const handCardElements = Array.from(document.querySelectorAll('#hand-bottom .card'));
                    const cardElements = Random.sample(handCardElements, 3);
                    const schupfSubZones = document.querySelectorAll('#schupf-zone-bottom .schupf-subzone');
                    console.log(`🤖 Bot: Wähle Schupf-Karten aus.`);
                    cardElements.forEach((cardElement, i) => {
                        cardElement.click();
                        schupfSubZones[i].click();
                    });
                    // Nachdem 3 Karten ausgewählt sind, wird der Play-Button zu "Schupfen"
                    console.log("🤖 Bot: Klicke auf Schupfen-Button.");
                    _clickButton('#play-button[data-mode="SCHUPF"]');
                    break;

                case 'play':
                    _testUIPlay();
                    // Zufällig eine von zwei Strategien wählen
                    if (Random.boolean()) {
                        // a) Zufällige gültige Kombination spielen
                        console.log("🤖 Bot: Selektiere zufällige Kombination...");
                        const actionSpace = State.getActionSpace();
                        const action = Random.choice(actionSpace);
                        _selectCards(action[0]);
                        if (action[1][0] !== CombinationType.PASS) {
                            console.log("🤖 Bot: Klicke auf Play-Button.");
                            _clickButton('#play-button[data-mode="PLAY"]');
                        }
                        else {
                             console.log("🤖 Bot: Klicke auf Passen-Button.");
                            _clickButton('#pass-button');
                        }
                    }
                    else {
                        // b) AUTOSELECT-Button der View nutzen
                        if (State.canPlayCards()) {
                            _clearSelectedCards();
                            // Nach dem ersten Klick werden die Karten selektiert.
                            console.log("🤖 Bot: Klicke auf Autoselect-Button.");
                            _clickButton('#play-button[data-mode="AUTOSELECT"]');
                            // Plane einen zweiten Klick, um sie auszuspielen.
                            //setTimeout(() => {
                                console.log("🤖 Bot: Klicke auf Play-Button.");
                                _clickButton('#play-button[data-mode="PLAY"]')
                            //}, 500);
                        }
                        else { // kein Autoselect möglich (z.B. nur Passen).
                             console.log("🤖 Bot: Klicke auf Passen-Button.");
                            _clickButton('#pass-button');
                        }
                    }
                    break;

                case 'wish':
                    _testUIWishDialog();
                    // Klick auf den Button im Wish-Dialog
                    const wishOptions = document.querySelectorAll('#wish-dialog:not(.hidden) button:not(:disabled)');
                    if (wishOptions.length > 0) {
                        console.log("🤖 Bot: Wähle einen zufälligen Wunsch.");
                        Random.choice(Array.from(wishOptions)).click();
                    }
                    break;

                case 'give_dragon_away':
                    _testUIDragonDialog();
                    // Klick auf den Button im Dragon-Dialog
                    const dragonOptions = document.querySelectorAll('#dragon-dialog:not(.hidden) button:not(:disabled)');
                    if (dragonOptions.length > 0) {
                        console.log("🤖 Bot: Verschenke Drachen zufällig.");
                        Random.choice(Array.from(dragonOptions)).click();
                    }
                    break;
            }
        }
        else {
            console.log("🤖 Bot: Auf dem Spieltisch. Warte auf meinen Zug oder ein Event...");
        }
    }


    // ------------------------------------------------------
    // Hilfsfunktionen
    // ------------------------------------------------------

    /**
     * Klickt auf einen Button, falls er sichtbar und aktiv ist.
     *
     * @param {string} selector - Der CSS-Selektor für einen Button.
     * @returns {boolean} - True, wenn der Klick erfolgreich war.
     */
    function _clickButton(selector) {
        const element = document.querySelector(selector);
        if (!_assertUI(element !== null, `Button "${selector}" nicht gefunden.`)) {
            return false;
        }
        if (!_assertUI(!element.classList.contains('hidden'), `Button "${selector}" sollte sichtbar sein.`)) {
            return false;
        }
        if (!_assertUI(!element.disabled, `Button "${selector}" sollte aktiv sein.`)) {
            return false;
        }
        element.click();
        return true;
    }

    /**
     * Setzt die ausgewählten Karten zurück.
     */
    function _clearSelectedCards() {
        const cardElements = document.querySelectorAll('#hand-bottom .card.selected');
        cardElements.forEach(cardElement => {
            cardElement.click();
        });
    }

    /**
     * Wählt die gegebenen Karten in der Hand aus.
     *
     * @param {Cards} cards - Die Karten, die selektiert werden sollen.
     */
    function _selectCards(cards) {
        const cardElements = document.querySelectorAll('#hand-bottom .card');
        cardElements.forEach(cardElement => {
            const cardToFind = /** @type Card */ cardElement.dataset.card.split(",").map(value => parseInt(value, 10));
            const found = Lib.includesCard(cardToFind, cards);
            const selected = cardElement.classList.contains('selected');
            if ((found && !selected) || (!found && selected)) {
                cardElement.click();
            }
        });
    }

    /**
     * Gibt eine Warnung aus, wenn die Bedingung fehlschlägt.
     *
     * @param {boolean} condition - Die Bedingung, die wahr sein soll.
     * @param {string} errorMessage - Die Fehlermeldung, die bei Fehlschlag ausgegeben wird.
     * @returns {boolean} - Gibt zurück, ob die Assertion erfolgreich war.
     */
    function _assertUI(condition, errorMessage) {
        if (!condition) {
            console.warn(`🤖 BOT-WARNUNG: ${errorMessage}`);
            throw "Halt"; // dadurch werden keine weiteren Aktionen geplant
        }
        return condition;
    }

    // ------------------------------------------------------
    // UI-Tests
    // ------------------------------------------------------

    /**
     * UI-Test für Login-View.
     */
    function _testUILogin() {
        _assertUI(document.querySelector('#login-form'), "Login-Formular nicht gefunden.");
    }

    /**
     * UI-Test für Lobby-View.
     */
    function _testUILobby() {
        const playerCount = document.querySelectorAll('#lobby-player-list li').length;
        _assertUI(playerCount === 4, `UI zeigt ${playerCount} Spieler, es müssen aber 4 sein.`);
        if (State.isHost()) {
            const upButtons = document.querySelectorAll('#lobby-player-list .player-order-controls button:first-child:not(:disabled)');
            const downButtons = document.querySelectorAll('#lobby-player-list .player-order-controls button:last-child:not(:disabled)');
            _assertUI(upButtons.length === 2 && downButtons.length === 2, "In der Lobby sollten zwei Up- und zwei Down-Buttons aktiviert sein.");
        }
    }

    /**
     * UI-Test für Handkarten.
     */
    function _testUIHand() {
        //const isFinished = State.getCountHandCards() === 0; // ist der Benutzer fertig?
        for (let relativeIndex = 0; relativeIndex <= 3; relativeIndex++) {
            const handCardElements = document.querySelectorAll(`#hand-${['bottom', 'right', 'top', 'left'][relativeIndex]} .card`);
            // offene Schupf-Karten zählen noch zur Hand
            const schupfCardElements = document.querySelectorAll(`#schupf-zone-${['bottom', 'right', 'top', 'left'][relativeIndex]}:not(.hidden) .card:not(.back-site)`);
            const countCards = State.getCountHandCards(Lib.getCanonicalPlayerIndex(relativeIndex));
            _assertUI(handCardElements.length + schupfCardElements.length === countCards, `Spieler ${relativeIndex} hat ${countCards} Handkarten, es sind aber ${handCardElements.length + schupfCardElements.length} zu sehen.`)
            if (relativeIndex === 0) {
                _assertUI(Array.from(handCardElements).every(cardElement => !cardElement.classList.contains('back-site')), `Der Benutzer sollte alle Handkarten offen zeigen.`);
            }
            else {
                _assertUI(Array.from(handCardElements).every(cardElement => cardElement.classList.contains('back-site')), `Die Mitspieler sollten alle Handkarten verdeckt zeigen.`);
            }
        }
    }

    /**
     * UI-Test für die Schupf-Aktion.
     */
    function _testUISchupfZone() {
        _assertUI(!document.getElementById('schupf-zone-bottom').classList.contains('hidden'), "Schupfzone sollte für Schupfen sichtbar sein.");
        // Prüfe Schupfzonen der Mitspieler (wenn sichtbar)
        for (let relativeIndex = 1; relativeIndex <= 3; relativeIndex++) {
            const schupfCardElements = document.querySelectorAll(`#schupf-zone-${['bottom', 'right', 'top', 'left'][relativeIndex]}:not(.hidden) .card`);
            _assertUI(Array.from(schupfCardElements).every(cardElement => cardElement.classList.contains('back-site')), `Die Mitspieler sollten alle Schupfkarten verdeckt zeigen.`);
        }
    }

    /**
     * UI-Test für die Play-Aktion.
     */
    function _testUIPlay() {
        _assertUI(State.isCurrentPlayer(), "Bot soll spielen, ist aber laut State nicht am Zug.");
        _assertUI(document.querySelector('#player-name-bottom').classList.contains('current-player'), "UI zeigt nicht an, dass der Bot am Zug ist.");
    }


    /**
     * UI-Test für die Tichu-Symbole (und den Tichu-Button).
     */
    function _testUITichuIcons() {
        for (let relativeIndex = 0; relativeIndex <= 3; relativeIndex++) {
            const tichuIcon = document.getElementById(`tichu-icon-${['bottom', 'right', 'top', 'left'][relativeIndex]}`)
            const announce = State.getAnnouncement(Lib.getCanonicalPlayerIndex(relativeIndex));
            if (announce) {
                _assertUI(!tichuIcon.classList.contains("hidden"), "Das Tichu-Symbol eines Spieler ist zu nicht sehen, obwohl er ein Tichu angesagt hat.");
                if (announce === 2) {
                    _assertUI(tichuIcon.src.includes("grand"), "Das Tichu-Symbol eines Spieler zeigt ein einfaches statt großes Tichu an.");
                }
                else {
                    _assertUI(!tichuIcon.src.includes("grand"), "Das Tichu-Symbol eines Spieler zeigt ein großes statt einfaches Tichu an.");
                }
                if (relativeIndex === 0) {
                    _assertUI(document.getElementById('tichu-button').disabled, "Der Tichu-Button ist aktiviert, obwohl der Benutzer bereits ein Tichu angesagt hat.");
                }
            }
            else {
                _assertUI(tichuIcon.classList.contains("hidden"), "Das Tichu-Symbol eines Spieler ist zu sehen, obwohl er kein Tichu angesagt hat.");
            }
        }
    }

    /**
     * UI-Test für das Bomben-Symbol.
     */
    function _testUIBombIcon() {
        const bombIcon = document.getElementById('bomb-icon');
        if (State.hasBomb()) {
            _assertUI(!bombIcon.classList.contains('hidden'), "Das Bomben-Symbol ist nicht sichtbar, obwohl der Bot eine Bombe hat.");
            if (State.canPlayBomb()) {
                _assertUI(!bombIcon.classList.contains("disabled"), "Das Bomben-Symbol ist deaktiviert, obwohl der Bot eine Bombe werfen darf.");
            }
            else {
                _assertUI(bombIcon.classList.contains("disabled"), "Das Bomben-Symbol ist aktiviert, obwohl der Bot keine Bombe werfen darf.");
            }
        }
        else {
            _assertUI(bombIcon.classList.contains('hidden'), "Das Bomben-Symbol ist sichtbar, obwohl der Bot keine Bombe hat.");
        }
    }

    /**
     * UI-Test für den Wish-Dialog.
     */
    function _testUIWishIcon() {
        const _wishIcon = document.getElementById('wish-icon');
        if (State.getWishValue() > 0) {
            _assertUI(!_wishIcon.classList.contains('hidden'), "Das Wunsch-Symbol ist nicht sichtbar, obwohl ein Wunsch unerfüllt ist.");
        }
        else {
            _assertUI(_wishIcon.classList.contains('hidden'), "Das Wunsch-Symbol ist sichtbar, obwohl kein Wunsch offen ist.");
        }
    }

    /**
     * UI-Test für den Wish-Dialog.
     */
    function _testUIWishDialog() {
        _assertUI(!document.getElementById('wish-dialog').classList.contains('hidden'), "Wunsch-Dialog sollte sichtbar sein, wenn ein Wunsch angefragt wird.");
    }

    /**
     * UI-Test für den Dragon-Dialog.
     */
    function _testUIDragonDialog() {
        _assertUI(!document.getElementById('dragon-dialog').classList.contains('hidden'), "Drachen-Dialog sollte sichtbar sein.");
    }

    /**
     * UI-Test für den Punkteanzeige.
     */
    function _testUIScoreDisplay() {
        let score = State.getTotalScore();
        if (State.getPlayerIndex() === 1 || State.getPlayerIndex() === 3) {
            [score[0], score[1]] = [score[1], score[0]];
        }
        const scoreDisplay = document.getElementById('score-display').textContent.split(":").map(value => parseInt(value.trim()));
        _assertUI(scoreDisplay[0] === score[0] && scoreDisplay[1] === score[1], "Punkteanzeige zeigt einen falschen Wert.");
    }

    return {
        setEnabled,
    };
})();