// js/views/login-view.js

/**
 * @module LoginView
 * Verwaltet die Anzeige und Interaktion des Login-Bildschirms.
 */
const LoginView = (() => {
    /** @const {HTMLElement} _viewElement - Das DOM-Element des Login-Views. */
    const _viewElement = document.getElementById('login-screen');
    /** @const {HTMLFormElement} _loginForm - Das Login-Formular. */
    const _loginForm = document.getElementById('login-form');
    /** @const {HTMLInputElement} _playerNameInput - Das Eingabefeld für den Spielernamen. */
    const _playerNameInput = document.getElementById('player-name');
    /** @const {HTMLInputElement} _tableNameInput - Das Eingabefeld für den Tischnamen. */
    const _tableNameInput = document.getElementById('table-name');

    /**
     * Initialisiert das LoginView-Modul.
     * Setzt den Event-Listener für das Absenden des Login-Formulars.
     */
    function init() {
        console.log("LOGINVIEW: Initialisiere LoginView...");
        _loginForm.addEventListener('submit', _handleLoginSubmit);
    }

    /**
     * Event-Handler für das Absenden des Login-Formulars.
     * @param {Event} event - Das Submit-Event.
     */
    function _handleLoginSubmit(event) {
        event.preventDefault(); // Standard-Formularabsendung verhindern
        const playerName = _playerNameInput.value.trim();
        const tableName = _tableNameInput.value.trim();

        if (playerName && tableName) {
            SoundManager.playSound('buttonClick'); // Beispiel für UI-Sound
            AppController.attemptLogin(playerName, tableName);
        } else {
            // Einfache Validierungs-UI, z.B. Fokus auf leeres Feld oder Toast
            Dialogs.showErrorToast("Bitte Spielername und Tischname eingeben.");
            if (!playerName) _playerNameInput.focus();
            else if (!tableName) _tableNameInput.focus();
        }
    }

    /**
     * Rendert den Login-View.
     * Füllt die Eingabefelder mit Werten aus dem State (falls vorhanden, z.B. nach Logout).
     */
    function render() {
        // console.log("LOGINVIEW: Rendere LoginView.");
        // Werte aus dem State holen, um Felder vorzubelegen (nützlich nach Logout oder Fehler)
        _playerNameInput.value = State.getPlayerName() || '';
        _tableNameInput.value = State.getTableName() || '';
        // Sicherstellen, dass der Fokus nicht auf einem invaliden Feld von vorher ist
        _playerNameInput.blur();
        _tableNameInput.blur();
    }

    /**
     * Wird aufgerufen, wenn der View angezeigt wird. (Momentan nicht viel spezielle Logik hier)
     */
    function show() {
        // console.log("LOGINVIEW: LoginView wird angezeigt.");
        // Ggf. Fokus auf erstes Feld setzen
        // _playerNameInput.focus(); // Kann nervig sein, wenn es automatisch passiert
    }

    /**
     * Wird aufgerufen, wenn der View ausgeblendet wird. (Momentan keine spezielle Logik)
     */
    function hide() {
        // console.log("LOGINVIEW: LoginView wird ausgeblendet.");
    }

    return {
        init,
        render,
        show,
        hide
    };
})();