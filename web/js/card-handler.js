// js/card-handler.js

/**
 * Verantwortlich für die Interaktionslogik mit den Karten des Spielers,
 * wie Kartenauswahl für das Spielen und das Schupfen.
 */
const CardHandler = (() => {
    /** @type {Array<object>} _selectedCards - Array der aktuell ausgewählten Kartenobjekte ({value, suit, label}). */
    let _selectedCards = [];
    /** @type {HTMLElement|null} _ownHandContainer - Referenz zum DOM-Element der eigenen Hand. */
    let _ownHandContainer = null;

    /** @type {boolean} _isSchupfModeActive - Gibt an, ob der Schupf-Modus aktiv ist. */
    let _isSchupfModeActive = false;
    /** @type {string|null} _schupfRequestId - Die Request-ID für die aktuelle Schupf-Aktion. */
    let _schupfRequestId = null;
    /** @type {Array<object|null>} _schupfCards - Array für die 3 zu schupfenden Karten, Indizes 0,1,2 für rechts, partner, links. */
    let _schupfCards = [null, null, null];
    /** @type {Array<HTMLElement|null>} _schupfZones - DOM-Elemente der Schupf-Zonen. */
    let _schupfZones = [];

    /**
     * Initialisiert den CardHandler.
     * Holt Referenzen zu relevanten DOM-Elementen.
     */
    function init() {
        console.log("CARDHANDLER: Initialisiere CardHandler...");
        _ownHandContainer = document.getElementById('player-0-hand');
        _schupfZones = [
            document.getElementById('schupf-zone-opponent-right'),
            document.getElementById('schupf-zone-partner'),
            document.getElementById('schupf-zone-opponent-left')
        ];
        // Event-Listener für Kartenklicks werden dynamisch beim Rendern der Hand gesetzt (in GameTableView)
        // Event-Listener für Schupf-Zonen, falls nötig (z.B. um Karten dorthin zu "legen")
        _schupfZones.forEach((zone, index) => {
            if (zone) {
                zone.addEventListener('click', () => _handleSchupfZoneClick(index));
            }
        });
    }

    /**
     * Wird von GameTableView aufgerufen, wenn eine Karte in der eigenen Hand geklickt wird.
     * @param {HTMLElement} cardElement - Das geklickte Karten-DOM-Element.
     * @param {object} cardData - Das Kartenobjekt ({value, suit, label}).
     */
    function handleCardClick(cardElement, cardData) {
        if (!_ownHandContainer || _ownHandContainer.classList.contains('disabled-hand')) {
            return;
        }

        SoundManager.playSound('cardSelect'); // Beispielhafter Sound für Kartenauswahl

        if (_isSchupfModeActive) {
            _handleSchupfCardSelection(cardElement, cardData);
        }
        else {
            // Normaler Spielmodus: Karte auswählen/abwählen
            cardElement.classList.toggle('selected');
            _updateSelectedCardsArray();
        }
    }

    /**
     * Aktualisiert das `_selectedCards` Array basierend auf den .selected Klassen im DOM.
     */
    function _updateSelectedCardsArray() {
        _selectedCards = [];
        if (_ownHandContainer) {
            const cardElements = _ownHandContainer.querySelectorAll('.card.selected');
            cardElements.forEach(el => {
                _selectedCards.push({
                    value: parseInt(el.dataset.cardValue, 10),
                    suit: parseInt(el.dataset.cardSuit, 10),
                    label: el.dataset.cardLabel
                });
            });
        }
    }



    // --- Schupf-Modus Logik ---

    /**
     * Aktiviert den Schupf-Modus.
     * @param {string} requestId - Die Request-ID der Schupf-Anfrage vom Server.
     * @param {Array<object>} currentHandCards - Die aktuellen Handkarten des Spielers.
     */
    function enableSchupfMode(requestId, currentHandCards) {
        console.log("CARDHANDLER: Aktiviere Schupf-Modus, Request:", requestId);
        _isSchupfModeActive = true;
        _schupfRequestId = requestId;
        _schupfCards = [null, null, null];
        clearSelectedCards(); // Vorherige Auswahl löschen

        // Schupf-Zonen anzeigen
        const schupfZonesContainer = document.querySelector('.schupf-zones');
        if (schupfZonesContainer) {
            schupfZonesContainer.classList.remove('hidden');
        }

        // UI anpassen: z.B. Hinweis anzeigen, andere Buttons deaktivieren
        GameTableView.setPlayControlsForSchupfen(true); // z.B. nur "Schupfen Bestätigen"-Button
        _renderSchupfZones(); // Visuelles Feedback für leere Zonen
    }

    /**
     * Deaktiviert den Schupf-Modus.
     */
    function disableSchupfMode() {
        if (!_isSchupfModeActive) {
            return;
        }
        console.log("CARDHANDLER: Deaktiviere Schupf-Modus.");
        _isSchupfModeActive = false;
        _schupfRequestId = null;
        _schupfCards = [null, null, null];

        const schupfZonesContainer = document.querySelector('.schupf-zones');
        if (schupfZonesContainer) {
            schupfZonesContainer.classList.add('hidden');
        }

        // Ausgewählte Karten in der Hand (falls welche für Schupfen markiert waren) deselektieren
        if (_ownHandContainer) {
            _ownHandContainer.querySelectorAll('.schupf-candidate').forEach(c => c.classList.remove('schupf-candidate', 'in-schupf-zone'));
        }
        _renderSchupfZones(); // Leert die Zonen visuell
        GameTableView.setPlayControlsForSchupfen(false); // Normale Spielbuttons wiederherstellen/deaktivieren
    }

    /**
     * Behandelt die Auswahl einer Karte im Schupf-Modus.
     * @param {HTMLElement} cardElement - Das geklickte Karten-DOM-Element.
     * @param {object} cardData - Das Kartenobjekt.
     */
    function _handleSchupfCardSelection(cardElement, cardData) {
        // Ist die Karte bereits in einer Schupf-Zone? Dann entfernen.
        const existingZoneIndex = _schupfCards.findIndex(c => c && c.label === cardData.label);
        if (existingZoneIndex !== -1) {
            _schupfCards[existingZoneIndex] = null;
            cardElement.classList.remove('in-schupf-zone'); // Visuelle Markierung entfernen
            _renderSchupfZones();
            return;
        }

        // Finde die erste freie Schupf-Zone
        const freeZoneIndex = _schupfCards.indexOf(null);
        if (freeZoneIndex !== -1) {
            // Prüfen, ob diese Karte bereits als Kandidat für eine andere Zone markiert ist
            // (sollte nicht passieren, wenn Logik sauber ist, aber sicher ist sicher)
            if (cardElement.classList.contains('in-schupf-zone')) {
                return;
            }

            _schupfCards[freeZoneIndex] = cardData;
            cardElement.classList.add('in-schupf-zone'); // Markiere Karte in der Hand
            _renderSchupfZones();
        }
        else {
            Dialogs.showErrorToast("Alle 3 Schupf-Plätze sind bereits belegt.");
        }
    }

    /**
     * Behandelt einen Klick auf eine Schupf-Zone.
     * Entfernt die Karte aus dieser Zone, falls eine drin ist.
     * @param {number} zoneIndex - Der Index der geklickten Schupf-Zone (0, 1, oder 2).
     */
    function _handleSchupfZoneClick(zoneIndex) {
        if (!_isSchupfModeActive || !_schupfCards[zoneIndex]) {
            return;
        }

        const cardToRemove = _schupfCards[zoneIndex];
        _schupfCards[zoneIndex] = null;

        // Visuelle Markierung von der Handkarte entfernen
        if (_ownHandContainer) {
            const cardInHandElement = _ownHandContainer.querySelector(`.card[data-label="${cardToRemove.label}"]`);
            if (cardInHandElement) {
                cardInHandElement.classList.remove('in-schupf-zone');
            }
        }
        _renderSchupfZones();
    }

    /** Aktualisiert das Aussehen der Schupf-Zonen basierend auf `_schupfCards`. */
    function _renderSchupfZones() {
        _schupfZones.forEach((zoneElement, index) => {
            if (!zoneElement) {
                return;
            }
            zoneElement.innerHTML = ''; // Alte Karte entfernen
            const targetPlayerRelative = zoneElement.dataset.targetPlayerRelative;
            let targetName = "";
            if (targetPlayerRelative === "1") {
                targetName = "Rechts";
            }
            else if (targetPlayerRelative === "2") {
                targetName = "Partner";
            }
            else if (targetPlayerRelative === "3") {
                targetName = "Links";
            }
            zoneElement.textContent = targetName; // Label wiederherstellen

            if (_schupfCards[index]) {
                const card = _schupfCards[index];
                const cardDiv = document.createElement('div');
                cardDiv.className = 'card'; // Styling für Karte in Schupf-Zone
                cardDiv.style.backgroundImage = `url('images/cards/${card.label}.png')`;
                zoneElement.appendChild(cardDiv);
                zoneElement.textContent = ''; // Label entfernen wenn Karte drin ist
            }
        });
    }

    /**
     * Wird aufgerufen, wenn der Spieler das Schupfen bestätigen will.
     * Sendet die ausgewählten Schupf-Karten an den Server.
     */
    function confirmSchupf() {
        if (!_isSchupfModeActive || !_schupfRequestId) {
            console.warn("CARDHANDLER: Schupfen nicht aktiv oder keine Request-ID.");
            return;
        }
        if (_schupfCards.some(card => card === null)) {
            Dialogs.showErrorToast("Bitte 3 Karten zum Schupfen auswählen.");
            return;
        }

        AppController.sendResponse(_schupfRequestId, {
            to_opponent_right: _schupfCards[0].label, // Annahme: Zone 0 ist rechts
            to_partner: _schupfCards[1].label,        // Zone 1 ist Partner
            to_opponent_left: _schupfCards[2].label   // Zone 2 ist links
        });
        SoundManager.playSound('schupf' + State.getPlayerIndex()); // Schupf-Sound des eigenen Spielers
        disableSchupfMode(); // Schupf-Modus beenden nach Senden
    }

    return {
        init,
        handleCardClick,
        enableSchupfMode,
        disableSchupfMode, // Wird vom AppController bei Interrupts aufgerufen
        confirmSchupf      // Wird vom GameTableView-Button aufgerufen
    };
})();