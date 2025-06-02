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
        AppController.sendProactiveMessage('lobby_action', {action: 'start_game'});
    }

    /**
     * Event-Handler für den "Beenden"-Button.
     */
    function _handleLeaveLobby() {
        SoundManager.playSound('buttonClick');
        AppController.leaveGame();
    }

    /**
     * Sendet eine Aktion zum Verschieben eines Spielers an den Server.
     * @param {number} playerIndex - Der Index des zu verschiebenden Spielers.
     * @param {number} direction - +1 für runter, -1 für hoch.
     */
    function _handleMovePlayer(playerIndex, direction) {
        SoundManager.playSound('buttonClick');
        const publicState = State.getPublicState();
        if (!publicState || !publicState.player_names) return;

        let playerIndex2 = playerIndex + direction

        // Gültigkeitsprüfungen (z.B. nicht aus der Liste schieben, erster Spieler fix)
        // Der erste Spieler kann nicht verschoben werden.
        // Und Spieler können nicht an Position 0 geschoben werden.
        if (playerIndex2 < 1 || playerIndex2 > 3) {
            console.log("LOBBYVIEW: Verschieben nicht möglich an diese Position.");
            return;
        }

        console.log("LOBBYVIEW: Sende neue Indezies zum Vertauschen", [playerIndex, playerIndex2]);
        AppController.sendProactiveMessage('swap_players', {
            player_index_1: playerIndex,
            player_index_2: playerIndex2
        });
    }

    /**
     * Rendert den Lobby-View basierend auf dem aktuellen Spielzustand.
     * Zeigt den Tischnamen, die Spielerliste und Host-spezifische Steuerelemente an.
     */
    function render() {
        // console.log("LOBBYVIEW: Rendere LobbyView.");
        const publicState = State.getPublicState();
        const localPlayerCanonicalIndex = State.getPlayerIndex(); // Kanonischer Index des eigenen Spielers

        if (!publicState) {
            _lobbyTableNameElement.textContent = '...?';
            _playerListElement.innerHTML = '<li>Lade Spieler...</li>';
            _teamAssignmentContainer.classList.add('hidden');
            return;
        }

        _lobbyTableNameElement.textContent = State.getTableName() || publicState.table_name || 'Unbekannter Tisch';
        _playerListElement.innerHTML = '';

        const isHost = State.getIsHost();
        _teamAssignmentContainer.classList.toggle('hidden', !isHost); // Team Assignment nur für Host

        // Zeige Spieler in der aktuellen Reihenfolge an
        if (publicState.player_names && publicState.player_names.length === 4) {
            for (let relativeIndex=0; relativeIndex <= 3; relativeIndex++) {
                let canonicalIndex = Helpers.getCanonicalPlayerIndex(relativeIndex);
                let name = publicState.player_names[canonicalIndex];

                const li = document.createElement('li');

                let displayName = name || `Spieler ${canonicalIndex + 1}`;
                if (canonicalIndex === localPlayerCanonicalIndex) {
                    displayName += ' (Du)';
                }
                else if (canonicalIndex === publicState.host_index) {
                    displayName += ' (Host)';
                }
                // Player Name Span
                const nameSpan = document.createElement('span');
                nameSpan.textContent = displayName;
                li.appendChild(nameSpan);

                // Controls zum Verschieben (nur für Host, nicht für eigenen Namen oder ersten Spieler, wenn fix)
                if (isHost && canonicalIndex !== 0) { // Host kann andere Spieler verschieben (außer Spieler 0)
                    const controlsDiv = document.createElement('div');
                    controlsDiv.className = 'player-order-controls';

                    const upButton = document.createElement('button');
                    upButton.innerHTML = '▲'; // Pfeil hoch
                    upButton.title = 'Nach oben verschieben';
                    upButton.disabled = canonicalIndex === 1; // Kann nicht vor den ersten Nicht-Host geschoben werden
                    upButton.onclick = () => _handleMovePlayer(canonicalIndex, -1);
                    controlsDiv.appendChild(upButton);

                    const downButton = document.createElement('button');
                    downButton.innerHTML = '▼'; // Pfeil runter
                    downButton.title = 'Nach unten verschieben';
                    downButton.disabled = canonicalIndex === publicState.player_names.length - 1;
                    downButton.onclick = () => _handleMovePlayer(canonicalIndex, 1);
                    controlsDiv.appendChild(downButton);
                    li.appendChild(controlsDiv);
                }
                _playerListElement.appendChild(li);
            }
        }
        else {
            _playerListElement.innerHTML = '<li>Noch keine Spieler am Tisch.</li>';
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