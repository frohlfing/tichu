/**
 * Verwaltet die Anzeige, Logik und Interaktion aller Modal-Dialoge der Anwendung.
 */
const Modals = (() => {

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
     * Ergebnistext des RoundOver-Modals
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
     * Ergebnistext des GameOver-Modals
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

    /**
     * Fehlermeldung des Fehler-Pop-ups.
     *
     * @type {HTMLElement}
     */
    const _errorToastMessage = document.getElementById('error-toast-message');

    // --------------------------------------------------------------------------------------
    // Öffentliche Funktionen und Ereignishändler
    // --------------------------------------------------------------------------------------

    /**
     * Initialisiert das Modals-Modul.
     */
    function init() {
        console.log("Modals: Initialisiere modale Fenster...");
        // Ereignishändler einrichten
        _wishDialog.addEventListener('click', _handleWishDialogClick);
        _dragonDialog.addEventListener('click', _handleDragonDialogClick);
        _roundOverDialog.addEventListener('click', _handleRoundOverDialogClick);
        _gameOverDialog.addEventListener('click', _handleGameOverDialogClick);
        _exitDialog.addEventListener('click', _handleExitDialogClick);
        _errorToast.addEventListener('click', _handleErrorToastClick);
    }

    /**
     * Versteckt alle Dialoge.
     */
    function hideDialogs() {
        _hideModal(_wishDialog);
        _hideModal(_dragonDialog);
        _hideModal(_roundOverDialog);
        _hideModal(_gameOverDialog);
        _hideModal(_exitDialog);
    }

    /**
     * Zeigt den Wish-Dialog an.
     */
    function showWishDialog() {
        _showModal(_wishDialog);
    }

    /**
     * Ereignishändler für den Wish-Dialog.
     *
     * @param {PointerEvent} event
     */
    function _handleWishDialogClick(event) {
        if (typeof event.target.dataset.value === "undefined") {
            return;
        }
        SoundManager.playSound('buttonClick');
        _hideModal(_wishDialog);
        const value = parseInt(event.target.dataset.value, 10);
        EventBus.emit("wishDialog:select", value);
        console.log(`Modals: _wishDialog: ${value}`);
    }

    /**
     * Zeigt den Dragon-Dialog an.
     */
    function showDragonDialog() {
        _showModal(_dragonDialog);
    }

    /**
     * Ereignishändler für den Dragon-Dialog.
     *
     * @param {PointerEvent} event
     */
    function _handleDragonDialogClick(event) {
        if (typeof event.target.dataset.value === "undefined") {
            return;
        }
        SoundManager.playSound('buttonClick');
        _hideModal(_dragonDialog);
        const value = parseInt(event.target.dataset.value, 10);
        EventBus.emit("dragonDialog:select", value);
        console.log(`Modals: _dragonDialog: ${value}`);
    }

    /**
     * Zeigt den RoundOver-Dialog an.
     *
     * @param {string} text - Ergebnistext
     */
    function showRoundOverDialog(text) {
        _roundOverText.textContent = text;
        _showModal(_roundOverDialog);
    }

    /**
     * Ereignishändler für den RoundOver-Dialog.
     *
     * @param {PointerEvent} event
     */
    function _handleRoundOverDialogClick(event) {
        if (event.target.tagName !== "BUTTON") {
            return;
        }
        SoundManager.playSound('buttonClick');
        _hideModal(_roundOverDialog);
        EventBus.emit("roundOverDialog:click");
        console.log("Modals: _roundOverDialog");
    }

    /**
     * Zeigt den GameOver-Dialog an.
     *
     * @param {string} text - Ergebnistext
     */
    function showGameOverDialog(text) {
        _gameOverText.textContent = text;
        _showModal(_gameOverDialog);
    }

    /**
     * Ereignishändler für den GameOver-Dialog.
     *
     * @param {PointerEvent} event
     */
    function _handleGameOverDialogClick(event) {
        if (event.target.tagName !== "BUTTON") {
            return;
        }
        SoundManager.playSound('buttonClick');
        _hideModal(_gameOverDialog);
        EventBus.emit("gameOverDialog:click");
        console.log("Modals: _gameOverDialog");
    }

    /**
     * Zeigt den Exit-Dialog an.
     */
    function showExitDialog() {
        _showModal(_exitDialog);
    }

    /**
     * Ereignishändler für den Exit-Dialog.
     *
     * @param {PointerEvent} event
     */
    function _handleExitDialogClick(event) {
        if (typeof event.target.dataset.value === "undefined") {
            return;
        }
        SoundManager.playSound('buttonClick');
        _hideModal(_exitDialog);
        const value = parseInt(event.target.dataset.value, 10);
        EventBus.emit("exitDialog:select", value);
        console.log(`Modals: _exitDialog: ${value}`);
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
        _toastTimeoutId = setTimeout(() => {
            _toastTimeoutId = null;
            _hideModal(_errorToast);
        }, Config.TOAST_TIMEOUT);
        _errorToastMessage.textContent = message;
        _showModal(_errorToast);
    }

    /**
     * Ereignishändler für den Fehler-Popup.
     *
     * @param {PointerEvent} _event
     */
    function _handleErrorToastClick(_event) {
        if (_toastTimeoutId) {
            clearTimeout(_toastTimeoutId);
            _toastTimeoutId = null;
        }
        _hideModal(_errorToast);
        console.log("Modals: _handleErrorToastClick");
    }

    // --------------------------------------------------------------------------------------
    // Hilfsfunktionen
    // --------------------------------------------------------------------------------------

    /**
     * Zeigt ein modales Fenster an.
     *
     * @param {HTMLElement} modalElement - Das DOM-Element des Fensters.
     */
    function _showModal(modalElement) {
        //hideDialogs();
        modalElement.classList.remove('hidden');
    }

    /**
     * Versteckt ein modales Fenster.
     *
     * @param {HTMLElement} modalElement - Das DOM-Element des Fensters.
     */
    function _hideModal(modalElement) {
        modalElement.classList.add('hidden');
    }

    // noinspection JSUnusedGlobalSymbols
    return {
        init,
        hideDialogs,
        showWishDialog,
        showDragonDialog,
        showRoundOverDialog,
        showGameOverDialog,
        showExitDialog,
        showErrorToast,
    };
})();