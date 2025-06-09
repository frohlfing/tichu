/**
 * Verwaltet die Anzeige, Logik und Interaktion aller Modal-Dialoge der Anwendung.
 */
const Dialogs = (() => {

    /**
     * Dialog "Kartenwert wünschen"
     *
     * @type {HTMLElement}
     */
    const _wishDialog = document.getElementById('wish-dialog');
    const _wishOptionsContainer = document.getElementById('wish-options');
    const _wishButton = document.getElementById('wish-button');

    /**
     * Dialog "Wer soll den Drachen bekommen?"
     *
     * @type {HTMLElement}
     */
    const _dragonDialog = document.getElementById('dragon-dialog');
    const _dragonToLeftButton = document.getElementById('dragon-to-left-button');
    const _dragonToRightButton = document.getElementById('dragon-to-right-button');

    /**
     * Anzeige des Punktestands am Ende einer Runde.
     *
     * @type {HTMLElement}
     */
    const _roundOverDialog = document.getElementById('round-over-dialog');
    const _roundOverText = document.getElementById('round-over-text');
    const _roundOverButton = document.getElementById('round-over-button');

    /**
     * Anzeige des Punktestands am Ende der Partie.
     *
     * @type {HTMLElement}
     */
    const _gameOverDialog = document.getElementById('game-over-dialog');
    const _gameOverText = document.getElementById('game-over-text');
    const _gameOverButton = document.getElementById('game-over-button');

    /**
     * Dialog "Wirklich beenden?"
     *
     * @type {HTMLElement}
     */
    const _exitDialog = document.getElementById('exit-dialog');
    const _exitOkButton = document.getElementById('exit-ok-button');
    const _exitCancelButton = document.getElementById('exit-cancel-button');

    /**
     * Fehler-Popup
     *
     * @type {HTMLElement}
     */
    const _errorToast = document.getElementById('error-toast');
    const _errorToastMessage = document.getElementById('error-toast-message');

    /** @let {string|null} _activeDialogRequestId - Speichert die Request-ID des aktuell offenen Dialogs. */
    let _activeDialogRequestId = null;
    /** @let {Timeout|null} _toastTimeoutId - ID für den Timeout des Error-Toasts. */
    let _toastTimeoutId = null;

    /**
     * Initialisiert das Dialogs-Modul.
     * Setzt Event-Listener für die Buttons in den Dialogen.
     */
    function init() {
        console.log("DIALOGS: Initialisiere Dialogs...");

        // Wish Dialog
        _wishButton.addEventListener('click', _handleConfirmWish);
        // Generiere Wish-Options-Buttons
        CardValueLabels.forEach(label => { // CardValueLabels aus constants.js
            const numVal = (label === 'A' ? 14 : (label === 'K' ? 13 : (label === 'D' ? 12 : (label === 'B' ? 11 : (label === 'Z' ? 10 : parseInt(label))))));
            const btn = document.createElement('button');
            btn.textContent = label;
            btn.dataset.value = numVal;
            btn.addEventListener('click', function () {
                // Vorherige Auswahl entfernen
                const currentSelected = _wishOptionsContainer.querySelector('.selected-wish');
                if (currentSelected) {
                    currentSelected.classList.remove('selected-wish');
                }
                // Neue Auswahl markieren
                this.classList.add('selected-wish');
                SoundManager.playSound('buttonClick');
            });
            _wishOptionsContainer.appendChild(btn);
        });

        // Dragon Dialog
        _dragonToLeftButton.addEventListener('click', () => _handleDragonChoice('left'));
        _dragonToRightButton.addEventListener('click', () => _handleDragonChoice('right'));

        // Round End Dialog
        _roundOverButton.addEventListener('click', () => {
            _hideDialog(_roundOverDialog);
            SoundManager.playSound('buttonClick');
            // Server startet nächste Runde automatisch oder sendet Lobby-Update
        });

        // Game End Dialog
        _gameOverButton.addEventListener('click', () => {
            _hideDialog(_gameOverDialog);
            SoundManager.playSound('buttonClick');
            // AppController entscheidet, ob zur Lobby oder zum Login gewechselt wird
            // (basierend auf Server-Nachricht oder einfach Standardverhalten)
            ViewManager.toggleView('lobby'); // Vorerst zur Lobby
        });

        // Leave Confirm Dialog
        _exitOkButton.addEventListener('click', () => {
            _hideDialog(_exitDialog);
            SoundManager.playSound('buttonClick');
            AppController.leaveGame();
        });
        _exitCancelButton.addEventListener('click', () => {
            _hideDialog(_exitDialog);
            SoundManager.playSound('buttonClick');
        });
    }

    /**
     * Zeigt einen Dialog an.
     * @param {HTMLElement} dialogElement - Das DOM-Element des Dialogs.
     * @param {string} [requestId] - Die optionale Request-ID, falls der Dialog eine Server-Anfrage beantwortet.
     */
    function _showDialog(dialogElement, requestId) {
        // Alle anderen Dialoge schließen, um Überlappung zu vermeiden
        _closeAllDialogs();
        if (requestId) {
            _activeDialogRequestId = requestId;
            dialogElement.dataset.requestId = requestId; // Speichere Request-ID am Element
        }
        dialogElement.classList.remove('hidden');
        SoundManager.playSound('dialogOpen'); // Generischer Sound für Dialog öffnen (falls vorhanden)
    }

    /**
     * Versteckt einen Dialog.
     * @param {HTMLElement} dialogElement - Das DOM-Element des Dialogs.
     */
    function _hideDialog(dialogElement) {
        dialogElement.classList.add('hidden');
        if (dialogElement.dataset.requestId) {
            delete dialogElement.dataset.requestId;
        }
        if (_activeDialogRequestId && dialogElement.dataset.requestId === _activeDialogRequestId) {
            _activeDialogRequestId = null;
        }
    }

    /** Versteckt alle Dialoge. */
    function _closeAllDialogs() {
        _hideDialog(_wishDialog);
        _hideDialog(_dragonDialog);
        _hideDialog(_roundOverDialog);
        _hideDialog(_gameOverDialog);
        _hideDialog(_exitDialog);
        _activeDialogRequestId = null; // Sicherheitshalber
    }

    /** Schließt den Dialog, der mit einer bestimmten Request-ID assoziiert ist. */
    function closeDialogByRequestId(requestId) {
        if (_activeDialogRequestId === requestId) {
            // Finde heraus, welcher Dialog offen ist (oder iteriere über alle)
            if (!_wishDialog.classList.contains('hidden') && _wishDialog.dataset.requestId === requestId) {
                _hideDialog(_wishDialog);
            }
            if (!_dragonDialog.classList.contains('hidden') && _dragonDialog.dataset.requestId === requestId) {
                _hideDialog(_dragonDialog);
            }
            // ... für andere Dialoge, die auf Requests reagieren
            _activeDialogRequestId = null;
        }
    }

    // --- Spezifische Dialog-Handler ---

    function showGrandTichuPrompt(requestId) {
        // TODO: Elegantere UI als confirm(), z.B. temporäre Buttons auf dem Spieltisch
        // Fürs Erste: Standard confirm()
        SoundManager.playSound('prompt'); // Sound für eine Frage
        const announced = confirm("Großes Tichu ansagen?");
        AppController.sendResponse(requestId, {announced: announced});
    }

    function showWishDialog(requestId) {
        // Reset previous selection
        const currentSelected = _wishOptionsContainer.querySelector('.selected-wish');
        if (currentSelected) {
            currentSelected.classList.remove('selected-wish');
        }
        _showDialog(_wishDialog, requestId);
    }

    function _handleConfirmWish() {
        SoundManager.playSound('buttonClick');
        const selectedButton = _wishOptionsContainer.querySelector('.selected-wish');
        const requestId = _wishDialog.dataset.requestId || _activeDialogRequestId;
        if (selectedButton && requestId) {
            const wishValue = parseInt(selectedButton.dataset.value);
            AppController.sendResponse(requestId, {wish_value: wishValue});
            _hideDialog(_wishDialog);
        }
        else if (!selectedButton) {
            showErrorToast("Bitte einen Kartenwert auswählen.");
        }
        else {
            console.warn("DIALOGS: Konnte Wunsch nicht senden, RequestID fehlt oder Dialog nicht korrekt initialisiert.");
        }
    }

    function showDragonDialog(requestId) {
        _showDialog(_dragonDialog, requestId);
        // Gegner-Namen auf Buttons setzen (optional, aber nett)
        const ownIdx = State.getPlayerIndex();
        if (ownIdx !== -1) {
            const publicState = State.getPublicState();
            if (publicState && publicState.player_names) {
                const leftOpponentIdx = Helpers.getCanonicalPlayerIndex(3); // Relativ 3 = links
                const rightOpponentIdx = Helpers.getCanonicalPlayerIndex(1); // Relativ 1 = rechts
                _dragonToLeftButton.textContent = publicState.player_names[leftOpponentIdx] || "Gegner Links";
                _dragonToRightButton.textContent = publicState.player_names[rightOpponentIdx] || "Gegner Rechts";
            }
        }
    }

    function _handleDragonChoice(direction) { // 'left' or 'right'
        SoundManager.playSound('buttonClick');
        const requestId = _dragonDialog.dataset.requestId || _activeDialogRequestId;
        if (requestId) {
            const recipientCanonicalIndex = (direction === 'left')
                ? Helpers.getCanonicalPlayerIndex(3) // Relativ 3 = links
                : Helpers.getCanonicalPlayerIndex(1); // Relativ 1 = rechts
            AppController.sendResponse(requestId, {dragon_recipient: recipientCanonicalIndex});
            _hideDialog(_dragonDialog);
        }
        else {
            console.warn("DIALOGS: Konnte Drachenwahl nicht senden, RequestID fehlt.");
        }
    }

    function showLeaveConfirmDialog() {
        _showDialog(_exitDialog);
    }

    /**
     * Verarbeitet Server-Notifications, die für Dialoge relevant sind.
     * @param {string} eventName - Der Name des Server-Events.
     * @param {object} context - Der Kontext des Events.
     */
    function handleNotification(eventName, context) {
        const pubState = State.getPublicState(); // Hole aktuellen State
        if (!pubState) {
            return;
        }

        switch (eventName) {
            case 'round_over':
                _closeAllDialogs(); // Schließe ggf. offene Aktionsdialoge
                _roundOverText.textContent = `Runde: Team ${pubState.player_names[0] || '0'}/${pubState.player_names[2] || '2'}: ${pubState.game_score[0].slice(-1)[0] || 0} | ` +
                    `Team ${pubState.player_names[1] || '1'}/${pubState.player_names[3] || '3'}: ${pubState.game_score[1].slice(-1)[0] || 0}`;
                _showDialog(_roundOverDialog);
                break;
            case 'game_over':
                _closeAllDialogs();
                const totalScoreTeam02 = pubState.game_score[0].reduce((a, b) => a + b, 0);
                const totalScoreTeam13 = pubState.game_score[1].reduce((a, b) => a + b, 0);
                _gameOverText.textContent = `Partie Ende: Team ${pubState.player_names[0] || '0'}/${pubState.player_names[2] || '2'}: ${totalScoreTeam02} | ` +
                    `Team ${pubState.player_names[1] || '1'}/${pubState.player_names[3] || '3'}: ${totalScoreTeam13}`;
                _showDialog(_gameOverDialog);
                break;
        }
    }

    /**
     * Zeigt eine Toast-Benachrichtigung für Fehler an.
     * @param {string} message - Die anzuzeigende Fehlermeldung.
     */
    function showErrorToast(message) {
        if (_toastTimeoutId) {
            clearTimeout(_toastTimeoutId); // Alten Timeout löschen, falls Toast schnell hintereinander kommt
        }
        _errorToastMessage.textContent = message;
        _errorToast.classList.remove('hidden');
        _toastTimeoutId = setTimeout(() => {
            _errorToast.classList.add('hidden');
            _toastTimeoutId = null;
        }, 3500); // Toast nach 3.5 Sekunden ausblenden
    }

    return {
        init,
        showGrandTichuPrompt,
        showWishDialog,
        showDragonDialog,
        showLeaveConfirmDialog,
        handleNotification, // Damit AppController Notifications weiterleiten kann
        showErrorToast,
        closeDialogByRequestId // Um Dialoge bei Interrupts zu schließen
    };
})();