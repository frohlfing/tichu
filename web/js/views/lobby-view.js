// js/views/lobby-view.js

/**
 * @module LobbyView
 * Verwaltet die Anzeige und Interaktion des Lobby-Bildschirms.
 */
const LobbyView = (() => {
    /** @const {HTMLElement} _viewElement - Das DOM-Element des Lobby-Views. */
    const _viewElement = document.getElementById('lobby-screen');
    /** @const {HTMLElement} _lobbyTableNameElement - Zeigt den Namen des Tisches an. */
    const _lobbyTableNameElement = document.getElementById('lobby-table-name');
    /** @const {HTMLUListElement} _playerListElement - Die Liste der Spieler am Tisch. */
    const _playerListElement = document.getElementById('lobby-player-list');
    /** @const {HTMLElement} _teamAssignmentContainer - Container für Host-Aktionen. */
    const _teamAssignmentContainer = document.getElementById('team-assignment-container');
    /** @const {HTMLButtonElement} _startGameButton - Button zum Starten des Spiels (nur für Host). */
    const _startGameButton = document.getElementById('start-game-button');
    /** @const {HTMLButtonElement} _leaveLobbyButton - Button zum Verlassen der Lobby. */
    const _leaveLobbyButton = document.getElementById('leave-lobby-button');

    /**
     * Initialisiert das LobbyView-Modul.
     * Setzt Event-Listener für die Buttons.
     */
    function init() {
        console.log("LOBBYVIEW: Initialisiere LobbyView...");
        _startGameButton.addEventListener('click', _handleStartGame);
        _leaveLobbyButton.addEventListener('click', _handleLeaveLobby);
    }

    /**
     * Event-Handler für den "Spiel starten"-Button.
     */
    function _handleStartGame() {
        SoundManager.playSound('buttonClick');
        // Sendet eine 'lobby_action' Nachricht an den Server.
        // Der Server validiert, ob der Spieler der Host ist.
        AppController.sendProactiveMessage('lobby_action', { action: 'start_game' });
    }

    /**
     * Event-Handler für den "Tisch verlassen"-Button.
     */
    function _handleLeaveLobby() {
        SoundManager.playSound('buttonClick');
        AppController.leaveGame(); // Ruft die zentrale leaveGame Funktion im AppController auf
    }

    /**
     * Rendert den Lobby-View basierend auf dem aktuellen Spielzustand.
     * Zeigt den Tischnamen, die Spielerliste und Host-spezifische Steuerelemente an.
     */
    function render() {
        // console.log("LOBBYVIEW: Rendere LobbyView.");
        const publicState = State.getPublicState();
        const localPlayerIndex = State.getPlayerIndex();

        if (!publicState) {
            _lobbyTableNameElement.textContent = '...?';
            _playerListElement.innerHTML = '<li>Lade Spieler...</li>';
            _teamAssignmentContainer.classList.add('hidden');
            return;
        }

        _lobbyTableNameElement.textContent = State.getTableName() || publicState.table_name || 'Unbekannter Tisch';
        _playerListElement.innerHTML = ''; // Alte Liste leeren

        if (publicState.player_names && publicState.player_names.length > 0) {
            publicState.player_names.forEach((name, index) => {
                const li = document.createElement('li');
                let displayName = name || `Spieler ${index + 1}`;
                if (index === localPlayerIndex) {
                    displayName += ' (Du)';
                }
                if (index === publicState.host_index) {
                    displayName += ' (Host)';
                }
                li.textContent = displayName;
                _playerListElement.appendChild(li);
            });
        } else {
            _playerListElement.innerHTML = '<li>Noch keine Spieler am Tisch.</li>';
        }

        // Host-spezifische UI anzeigen/verstecken
        if (State.getIsHost()) {
            _teamAssignmentContainer.classList.remove('hidden');
            // TODO: Hier könnte UI für Team-Zuweisung (Drag & Drop o.ä.) implementiert werden.
            // Fürs Erste ist nur der Start-Button relevant.
        } else {
            _teamAssignmentContainer.classList.add('hidden');
        }
    }

    /**
     * Wird aufgerufen, wenn der View angezeigt wird.
     */
    function show() {
        // console.log("LOBBYVIEW: LobbyView wird angezeigt.");
        // Beim Anzeigen immer neu rendern, um aktuelle Daten zu haben
        render();
    }

    /**
     * Wird aufgerufen, wenn der View ausgeblendet wird.
     */
    function hide() {
        // console.log("LOBBYVIEW: LobbyView wird ausgeblendet.");
    }

    return {
        init,
        render,
        show,
        hide
    };
})();