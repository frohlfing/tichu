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
     * Aktiviert oder deaktiviert den Test-Bot.
     *
     * @param {boolean} enabled - True zum Aktivieren, False zum Deaktivieren.
     */
    function setEnabled(enabled) {
        if (enabled === _isEnabled) {
            return;
        }
        _isEnabled = enabled;
        if (_isEnabled) {
            console.log("%c🤖 TEST-BOT AKTIVIERT 🤖", "color: #ff4500; font-size: 1.2em; font-weight: bold;");
            // Lausche auf das Event, das signalisiert, dass der Server eine Anfrage stellt.
            // Wir nutzen hier ein allgemeines "view:rendered"-Event, das vom ViewManager
            // nach jedem Render-Vorgang ausgelöst werden könnte.
            // Alternativ können wir direkt auf die "network:message"-Events lauschen.
            EventBus.on("view:rendered", _onViewRendered);
            _scheduleNextAction(); // Erste Aktion planen
        }
        else {
            console.log("%c🤖 TEST-BOT DEAKTIVIERT 🤖", "color: #777; font-size: 1.2em;");
            EventBus.off("view:rendered", _onViewRendered);
            if (_actionTimeoutId) {
                clearTimeout(_actionTimeoutId);
                _actionTimeoutId = null;
            }
        }
    }

    /**
     * Wird aufgerufen, wann immer eine View gerendert wurde. Hier prüft der Bot, ob er handeln muss.
     * HINWEIS: Du musst dieses `view:rendered`-Event in deinem ViewManager.show... Methoden auslösen!
     * `EventBus.emit("view:rendered");`
     */
    function _onViewRendered() {
        if (!_isEnabled) {
            return;
        }
        _scheduleNextAction();
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

        // 1. Login-Screen-Logik
        if (LoginView.isVisible()) {
            console.log("🤖 Bot: Auf dem Login-Screen. Logge ein...");
            const playerName = `Bot_${Random.integer(100, 999)}`;
            const tableName = `TestTisch_${Random.integer(10, 99)}`;

            // Fülle die Felder und löse den Submit aus (simuliert den Event-Händler)
            document.getElementById('login-player-name').value = playerName;
            document.getElementById('login-table-name').value = tableName;
            document.getElementById('login-submit-button').click();
            return;
        }

        // 2. Lobby-Screen-Logik
        if (LobbyView.isVisible()) {
            if (State.isHost()) {
                // Zufällig Position der Spieler ändern
                // todo: Zufällig auf einen oder zwei up- und down-Button klicken

                // todo: Partien mitzählen. Wenn eine bestimmte Anzahl (in config hinterlegt) erreicht ist, nichts mehr machen.

                // Spiel starten
                console.log("🤖 Bot: In der Lobby als Host. Starte das Spiel...");
                document.getElementById('lobby-start-button').click();
            }
            else {
                console.log("🤖 Bot: In der Lobby. Warte auf andere Spieler oder den Host...");
            }
            return;
        }

        // 3. Table-Screen-Logik
        if (TableView.isVisible()) {
            // Prüfe, ob eine Anfrage vom Server an uns gerichtet ist

            /**
             * Aktuellen Anfrage.
             *
             * @type {object|null}
             * @property {string} id - UUID der Anfrage.
             * @property {string} action - Angefragte Aktion.
             */
            const request = {
                id:  localStorage.getItem("tichuRequestId"),
                action:  localStorage.getItem("tichuRequestAction")
            }
            // const request = State.getRequest();

            if (request) {
                console.log(`🤖 Bot: Anfrage erhalten: ${request.action}`);

                switch (request.action) {
                    case 'announce_grand_tichu':
                        // Zufällig entscheiden (z.B. 5% Chance)
                        const announceGrand = Random.choice([true, false], [1, 19]);
                        console.log(`🤖 Bot: Antworte auf Grand Tichu mit: ${announceGrand}`);
                        // todo: über die View auslösen (Klick auf Tichu- der Pass-Button), nicht per EventBus.
                        EventBus.emit("tableView:grandTichu", announceGrand);
                        break;

                    case 'schupf':
                        // Wähle 3 zufällige Karten zum Schupfen
                        const handForSchupf = State.getHandCards();
                        const cardsToSchupf = Random.sample(handForSchupf, 3);
                        console.log(`🤖 Bot: Schupfe Karten: ${Lib.stringifyCards(cardsToSchupf)}`);
                        // Diese Karten müssen in der UI "platziert" werden, bevor der Button geklickt wird
                        // todo: In der View der Reihe nach erst die Karte und dann auf die Schupfzone klicken (ich möchte den Bot bei seinem Tun beobachten).
                        // Einfacher: Direkt das Event mit den Daten auslösen
                        // todo: über die View auslösen (Klick auf Play-Button), nicht per EventBus.
                        EventBus.emit("tableView:schupf", cardsToSchupf);
                        break;

                    case 'play':
                        // Wähle die beste (oder eine zufällige) spielbare Aktion
                        // todo: Zufällig einen dieser beiden Möglichkeiten wählen:
                        //  a) per Random.choice(action_space) eine Wahl treffen und die Karten in der View anklicken, oder
                        //  b) einmal auf Play-Button-Klicken (AUTOSELECT-Mode der View nutzen)
                        const bestPlay = State.getBestPlayableCombination();
                        console.log(`🤖 Bot: Spiele die "beste" Kombination: ${Lib.stringifyCards(bestPlay[0])}`);
                        // todo: über die View auslösen (Klick auf Play-Button), nicht per EventBus.
                        EventBus.emit("tableView:play", bestPlay[0]);
                        break;

                    case 'wish':
                        const wishValue = Random.integer(2, 15); // Wünsche einen zufälligen Wert 2-A
                        console.log(`🤖 Bot: Wünsche mir eine ${wishValue}`);
                        // todo: Klick auf den Button im Modal-Dialog, nicht per EventBus.
                        EventBus.emit("wishDialog:select", wishValue);
                        break;

                    case 'give_dragon_away':
                        const opponentRelativeIndex = Random.choice([1, 3]); // Rechter oder linker Gegner
                        console.log(`🤖 Bot: Gebe Drachen an Gegner ${opponentRelativeIndex}`);
                        // todo: Klick auf den Button im Dragon-Dialog, nicht per EventBus.
                        EventBus.emit("dragonDialog:select", opponentRelativeIndex);
                        break;
                }
            }
            else if (State.getReceivedSchupfCards() && !State.isConfirmedReceivedSchupfCards()) {
                // Sonderfall: Wir haben geschupfte Karten erhalten und müssen sie bestätigen
                console.log("🤖 Bot: Bestätige erhaltene Schupf-Karten.");
                document.getElementById('play-button').click(); // Der "Aufnehmen"-Button
            }
            else {
                console.log("🤖 Bot: Auf dem Spieltisch. Warte auf meinen Zug oder ein Event...");
            }
        }

        // todo: Wenn eine Runde beendet ist, wird mit Modals.showRoundOverDialog() ein Dialog aufgerufen. Hier muss der Bot auf den Button klicken.
        //  Ebenso bei showGameOverDialog.
    }

    // --- Öffentliche API des Bots ---
    return {
        setEnabled,
    };
})();