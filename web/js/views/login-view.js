/**
 * Anzeige und Interaktion des Login-Bildschirms.
 *
 * @type {View}
 */
const LoginView = (() => {
    /**
     * Der Container des Login-Bildschirms.
     *
     * @type {HTMLElement}
     */
    const _viewContainer = document.getElementById('login-screen');

    /**
     * Das Login-Formular
     *
     * @type {HTMLFormElement}
     */
    const _loginForm = document.getElementById('login-form');

    /**
     * Das Eingabefeld für den Spielernamen.
     *
     * @type {HTMLInputElement}
     */
    const _playerNameInput = document.getElementById('login-player-name');

    /**
     * Das Eingabefeld für den Tischnamen.
     *
     * @type {HTMLInputElement}
     */
    const _tableNameInput = document.getElementById('login-table-name');

    /**
     * Initialisiert den Bildschirm.
     *
     * Setzt den Event-Listener für das Absenden des Login-Formulars.
     */
    function init() {
        _loginForm.addEventListener('submit', _handleLoginFormSubmit);
    }

    /**
     * Dieser Ereignishändler wird aufgerufen, wenn das Login-Formular abgeschickt werden soll.
     *
     * @param {Event} event - Das Submit-Event.
     */
    function _handleLoginFormSubmit(event) {
        event.preventDefault(); // Standard-Formularabsendung verhindern
        const playerName = _playerNameInput.value.trim();
        const tableName = _tableNameInput.value.trim();

        if (playerName && tableName) {
            SoundManager.playSound('buttonClick'); // Beispiel für UI-Sound
            AppController.attemptLogin(playerName, tableName);
        }
        else {
            Modals.showErrorToast("Bitte Spielername und Tischname eingeben.");
            if (!playerName) {
                _playerNameInput.focus();
            }
            else if (!tableName) {
                _tableNameInput.focus();
            }
        }
    }

    /**
     * Rendert den Login-Bildschirm (füllt die Eingabewerte).
     */
    function render() {
        _playerNameInput.value = User.getPlayerName();
        _tableNameInput.value = User.getTableName();
        _playerNameInput.blur();
        _tableNameInput.blur();
    }

    /**
     * Rendert den Login-Bildschirm und zeigt ihn anschließend an.
     */
    function show() {
        render();
        _viewContainer.classList.add('active');
    }

    /**
     * Blendet den Login-Bildschirm aus.
     */
    function hide() {
        _viewContainer.classList.remove('active');
    }

    /**
     * Ermittelt, ob der Login-Bildschirm gerade angezeigt wird.
     *
     * @returns {boolean}
     */
    function isVisible() {
        return _viewContainer.classList.contains('active')
    }

    return {
        init,
        render,
        show,
        hide,
        isVisible
    };
})();