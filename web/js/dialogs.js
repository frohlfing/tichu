/**
 * Verwaltet die Anzeige, Logik und Interaktion aller Modal-Dialoge der Anwendung.
 */
const Dialogs = (() => {
    // --------------------------------------------------------------------------------------
    // DOM-Elemente
    // --------------------------------------------------------------------------------------

    /**
     * Wish-Dialog
     *
     * @type {HTMLElement}
     */
    const _wishDialog = document.getElementById('wish-dialog');

    /**
     * Dragon-Dialog
     *
     * @type {HTMLElement}
     */
    const _dragonDialog = document.getElementById('dragon-dialog');

    /**
     * RoundOver-Dialog
     *
     * @type {HTMLElement}
     */
    const _roundOverDialog = document.getElementById('round-over-dialog');

    /**
     * Ergebnistext des RoundOver-Dialogs
     *
     * @type {HTMLElement}
     */
    const _roundOverText = document.getElementById('round-over-text');

    /**
     * GameOver-Dialog
     *
     * @type {HTMLElement}
     */
    const _gameOverDialog = document.getElementById('game-over-dialog');

    /**
     * Ergebnistext des GameOver-Dialogs
     *
     * @type {HTMLElement}
     */
    const _gameOverText = document.getElementById('game-over-text');

    /**
     * Exit-Dialog
     *
     * @type {HTMLElement}
     */
    const _exitDialog = document.getElementById('exit-dialog');

    /**
     * Fehler-Popup.
     *
     * @type {HTMLElement}
     */
    const _errorToast = document.getElementById('error-toast');
    const _errorToastMessage = document.getElementById('error-toast-message');

    // --------------------------------------------------------------------------------------
    // Öffentliche Funktionen
    // --------------------------------------------------------------------------------------

    /**
     * Initialisiert das Dialogs-Modul.
     * Setzt Event-Listener für die Buttons in den Dialogen.
     */
    function init() {
        console.log("DIALOGS: Initialisiere Dialogs...");
        // Event-Listener einrichten
        _wishDialog.addEventListener('click', _wishDialogSubmit);
        _dragonDialog.addEventListener('click', _dragonDialogSubmit);
        _roundOverDialog.addEventListener('click', _roundOverDialogSubmit);
        _gameOverDialog.addEventListener('click', _gameOverDialogSubmit);
        _exitDialog.addEventListener('click', _exitDialogSubmit);
    }

    /**
     * Zeigt den Wish-Dialog an.
     */
    function showWishDialog() {
        _showDialog(_wishDialog);
    }

    /**
     * Event-Handler für den Wish-Dialog.
     */
    function _wishDialogSubmit(event) {
        if (event.target.tagName !== "BUTTON") {
            return;
        }
        SoundManager.playSound('buttonClick');
        _hideDialog(_wishDialog);
        const wishValue = parseInt(event.target.dataset.value);
        console.log(`_wishDialog_submit: ${wishValue}`);
    }

    /**
     * Zeigt den Dragon-Dialog an.
     */
    function showDragonDialog(event) {
        _showDialog(_dragonDialog);
    }

    /**
     * Event-Handler für den Dragon-Dialog.
     */
    function _dragonDialogSubmit(event) {
        if (event.target.tagName !== "BUTTON") {
            return;
        }
        SoundManager.playSound('buttonClick');
        _hideDialog(_dragonDialog);
        const dragonRecipient = parseInt(event.target.dataset.value);
        console.log(`_dragonDialog_submit: ${dragonRecipient}`);
    }

    /**
     * Zeigt den RoundOver-Dialog an.
     *
     * @param {string} text - Ergebnistext
     */
    function showRoundOverDialog(text) {
        _roundOverText.textContent = text;
        _showDialog(_roundOverDialog);
    }

    /**
     * Event-Handler für den RoundOver-Dialog.
     */
    function _roundOverDialogSubmit(event) {
        if (event.target.tagName !== "BUTTON") {
            return;
        }
        SoundManager.playSound('buttonClick');
        _hideDialog(_roundOverDialog);
    }

    /**
     * Zeigt den GameOver-Dialog an.
     *
     * @param {string} text - Ergebnistext
     */
    function showGameOverDialog(text) {
        _gameOverText.textContent = text;
        _showDialog(_gameOverDialog);
    }

    /**
     * Event-Handler für den GameOver-Dialog.
     */
    function _gameOverDialogSubmit(event) {
        if (event.target.tagName !== "BUTTON") {
            return;
        }
        SoundManager.playSound('buttonClick');
        _hideDialog(_gameOverDialog);
    }

    /**
     * Zeigt den Exit-Dialog an.
     */
    function showExitDialog() {
        _showDialog(_exitDialog);
    }

    /**
     * Event-Handler für den Exit-Dialog.
     */
    function _exitDialogSubmit(event) {
        if (event.target.tagName !== "BUTTON") {
            return;
        }
        SoundManager.playSound('buttonClick');
        _hideDialog(_exitDialog);
        const ok = parseInt(event.target.dataset.value) === 1;
        console.log(`_exitDialogSubmit: ${ok ? "ok" : "cancel"}`);
    }

    /**
     * ID für den Timeout des Fehler-Popups.
     *
     * @type {number|null}
     * @private
     */
    let _toastTimeoutId = null;

    /**
     * Zeigt einen Fehler-Popup an.
     *
     * @param {string} message - Die anzuzeigende Fehlermeldung.
     */
    function showErrorToast(message) {
        if (_toastTimeoutId) {
            clearTimeout(_toastTimeoutId); // alten Timeout löschen, falls Toast schnell hintereinander kommt
        }
        _errorToastMessage.textContent = message;
        _errorToast.classList.remove('hidden');
        _toastTimeoutId = setTimeout(() => {
            _errorToast.classList.add('hidden');
            _toastTimeoutId = null;
        }, Config.TOAST_TIMEOUT);
    }

    // --------------------------------------------------------------------------------------
    // Hilfsfunktionen
    // --------------------------------------------------------------------------------------

    /**
     * Zeigt einen Dialog an.
     *
     * @param {HTMLElement} dialogElement - Das DOM-Element des Dialogs.
     */
    function _showDialog(dialogElement) {
        _closeAllDialogs(); // alle anderen Dialoge schließen, um Überlappung zu vermeiden
        // if (requestId) {
        //     _activeDialogRequestId = requestId;
        //     dialogElement.dataset.requestId = requestId; // Speichere Request-ID am Element
        // }
        dialogElement.classList.remove('hidden');
        SoundManager.playSound('dialogOpen'); // Generischer Sound für Dialog öffnen (falls vorhanden)
    }

    /**
     * Versteckt einen Dialog.
     *
     * @param {HTMLElement} dialogElement - Das DOM-Element des Dialogs.
     */
    function _hideDialog(dialogElement) {
        dialogElement.classList.add('hidden');
        // if (dialogElement.dataset.requestId) {
        //     delete dialogElement.dataset.requestId;
        // }
        // if (_activeDialogRequestId && dialogElement.dataset.requestId === _activeDialogRequestId) {
        //     _activeDialogRequestId = null;
        // }
    }

    /**
     * Versteckt alle Dialoge.
     */
    function _closeAllDialogs() {
        _hideDialog(_wishDialog);
        _hideDialog(_dragonDialog);
        _hideDialog(_roundOverDialog);
        _hideDialog(_gameOverDialog);
        _hideDialog(_exitDialog);
    }

    return {
        init,
        showWishDialog,
        showDragonDialog,
        showRoundOverDialog,
        showGameOverDialog,
        showExitDialog,
        showErrorToast,
    };
})();