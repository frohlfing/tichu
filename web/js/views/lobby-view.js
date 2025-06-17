/**
 * Anzeige und Interaktion des Lobby-Bildschirms.
 *
 * @type {View}
 */
const LobbyView = (() => {
    /**
     * Der Container des Lobby-Bildschirms.
     *
     * @type {HTMLElement}
     */
    const _viewContainer = document.getElementById('lobby-screen');

    /**
     * Zeigt den Namen des Tisches an.
     *
     * @type {HTMLElement}
     */
    const _lobbyTableNameElement = document.getElementById('lobby-table-name');

    /**
     * Die Liste der Spieler am Tisch.
     *
     * @type {HTMLUListElement}
     */
    const _playerListElement = document.getElementById('lobby-player-list');

    /**
     * Container für Host-Aktionen.
     *
     * @type {HTMLElement}
     */
    const _teamAssignmentContainer = document.getElementById('lobby-team-assignment-container');

    /**
     * Button zum Starten des Spiels (nur für Host).
     *
     * @type {HTMLButtonElement}
     */
    const _startGameButton = document.getElementById('lobby-start-button');

    /**
     * Button zum Verlassen der Lobby.
     *
     * @type {HTMLButtonElement}
     */
    const _leaveLobbyButton = document.getElementById('lobby-leave-button');

    /**
     * Initialisiert den Lobby-Bildschirm.
     */
    function init() {
        _startGameButton.addEventListener('click', _handleStartGameButton_click);
        _leaveLobbyButton.addEventListener('click', _handleLeaveLobbyButton_click);
    }

    /**
     * Ereignishändler für den "Spiel starten"-Button.
     */
    function _handleStartGameButton_click() {
        SoundManager.playSound('buttonClick');
        AppController.sendProactiveMessage('start_game');
    }

    /**
     * Ereignishändler für den "Beenden"-Button.
     */
    function _handleLeaveLobbyButton_click() {
        SoundManager.playSound('buttonClick');
        AppController.leaveGame();
    }

    /**
     * Sendet eine Aktion zum Vertauschen zweier Spieler an den Server.
     *
     * @param {number} playerIndex - Der Index des zu tauschenden Spielers.
     * @param {number} direction - +1 um mit dem nächsten zu tauschen, -1 um mit dem vorherigen.
     */
    function _upOrDownButton_click(playerIndex, direction) {
        SoundManager.playSound('buttonClick');
        const publicState = State.getPublicState();
        if (!publicState || !publicState.player_names || publicState.player_names.length !== 4) {
            return;
        }

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
     */
    function render() {
        // console.log("LOBBYVIEW: Rendere LobbyView.");
        const publicState = State.getPublicState();
        const localPlayerCanonicalIndex = State.getPlayerIndex();

        if (!publicState) {
            _lobbyTableNameElement.textContent = '...?';
            _playerListElement.innerHTML = '<li>Lade Spieler...</li>';
            _teamAssignmentContainer.classList.add('hidden');
            _startGameButton.classList.add('hidden'); // Sicherstellen, dass Buttons versteckt sind
            return;
        }

        _lobbyTableNameElement.textContent = State.getTableName(); // Nimmt Wert aus State
        _playerListElement.innerHTML = '';

        const isHost = State.isHost();
        _teamAssignmentContainer.classList.toggle('hidden', !isHost);
        _startGameButton.classList.toggle('hidden', !isHost);

        // Zeige Spieler in der aktuellen Reihenfolge an
        if (publicState.player_names && publicState.player_names.length === 4) {
            // Schleife über die relativen Sitzplätze (0=Du, 1=Rechts, 2=Partner, 3=Links)
            for (let relativeIndex=0; relativeIndex <= 3; relativeIndex++) {
                let canonicalIndex = Lib.getCanonicalPlayerIndex(relativeIndex);
                let name = publicState.player_names[canonicalIndex];

                const li = document.createElement('li');

                let displayName = name || `Spieler ${canonicalIndex + 1}`;
                if (canonicalIndex === localPlayerCanonicalIndex) {
                    displayName += ' (Du)';
                }
                else if (canonicalIndex === publicState.host_index) {
                    displayName += ' (Host)';
                }

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
                    upButton.onclick = () => _upOrDownButton_click(canonicalIndex, -1);
                    controlsDiv.appendChild(upButton);

                    const downButton = document.createElement('button');
                    downButton.innerHTML = '▼'; // Pfeil runter
                    downButton.title = 'Nach unten verschieben';
                    downButton.disabled = canonicalIndex === publicState.player_names.length - 1;
                    downButton.onclick = () => _upOrDownButton_click(canonicalIndex, 1);
                    controlsDiv.appendChild(downButton);
                    li.appendChild(controlsDiv);
                }
                _playerListElement.appendChild(li);
            }
        }
        else {
            _playerListElement.innerHTML = '<li>Warte auf Spieler...</li>';
        }
    }

    /**
     * Rendert die Lobby und zeigt sie anschließend an.
     */
    function show() {
        render();
        _viewContainer.classList.add('active');
    }

    /**
     * Blendet die Lobby aus.
     */
    function hide() {
        _viewContainer.classList.remove('active');
    }

    /**
     * Ermittelt, ob die Lobby gerade angezeigt wird.
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