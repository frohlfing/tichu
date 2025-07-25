/**
 * Anzeige und Interaktion des Lobby-Bildschirms.
 *
 * @type {View}
 */
const LobbyView = (() => {

    /**
     * Zeigt den Namen des Tisches an.
     *
     * @type {HTMLElement}
     */
    const _tableName = document.getElementById('lobby-table-name');

    /**
     * Die Liste der Spieler am Tisch.
     *
     * @type {HTMLUListElement}
     */
    const _playerList = document.getElementById('lobby-player-list');

    /**
     * Button zum Starten des Spiels (nur für Host).
     *
     * @type {HTMLButtonElement}
     */
    const _startButton = document.getElementById('lobby-start-button');

    /**
     * Button zum Verlassen der Lobby.
     *
     * @type {HTMLButtonElement}
     */
    const _exitButton = document.getElementById('lobby-exit-button');

    /**
     * Initialisiert den Lobby-Bildschirm.
     */
    function init() {
        _startButton.addEventListener('click', _handleStartButtonClick);
        _exitButton.addEventListener('click', _handleExitButtonClick);
    }

    /**
     * Rendert den Lobby-View basierend auf dem aktuellen Spielzustand.
     */
    function render() {
        _tableName.textContent = State.getTableName();
        _playerList.innerHTML = '';

        const isHost = State.isHost();
        _startButton.classList.toggle('hidden', !isHost);

        // Zeige Spieler in der aktuellen Reihenfolge an
        // Schleife über die relativen Sitzplätze (0=Benutzer, 1=Rechts, 2=Partner, 3=Links)
        for (let relativeIndex= 0; relativeIndex <= 3; relativeIndex++) {
            let canonicalIndex = Lib.getCanonicalPlayerIndex(relativeIndex);
            let displayName = State.getPlayerName(canonicalIndex);
            if (relativeIndex === 0) {
                displayName += ' (Du)';
            }
            else if (canonicalIndex === State.getHostIndex()) {
                displayName += ' (Host)';
            }

            const li = document.createElement('li');
            const nameSpan = document.createElement('span');
            nameSpan.textContent = displayName;
            li.appendChild(nameSpan);

            // Controls zum Verschieben (nur für Host, nicht für eigenen Namen oder ersten Spieler, wenn fix)
            if (isHost && relativeIndex > 0) { // Host kann andere Spieler verschieben, aber nicht sich selber
                const controlsDiv = document.createElement('div');
                controlsDiv.className = 'player-order-controls';

                const upButton = document.createElement('button');
                upButton.innerHTML = '▲'; // Pfeil hoch
                upButton.title = 'Nach oben verschieben';
                upButton.disabled = relativeIndex === 1;
                upButton.onclick = () => _upOrDownButton_click(canonicalIndex, -1);
                controlsDiv.appendChild(upButton);

                const downButton = document.createElement('button');
                downButton.innerHTML = '▼'; // Pfeil runter
                downButton.title = 'Nach unten verschieben';
                downButton.disabled = relativeIndex === 3;
                downButton.onclick = () => _upOrDownButton_click(canonicalIndex, 1);
                controlsDiv.appendChild(downButton);
                li.appendChild(controlsDiv);
            }
            _playerList.appendChild(li);
        }

        _startButton.disabled = false;
        _exitButton.disabled = false;
    }

    /**
     * Ereignishändler für den StartGame-Button.
     */
    function _handleStartButtonClick() {
        //Sound.play('click');
        _disableButtons();
        EventBus.emit("lobbyView:start");
    }

    /**
     * Ereignishändler für den Exit-Button.
     */
    function _handleExitButtonClick() {
        //Sound.play('click');
        _disableButtons();
        EventBus.emit("lobbyView:exit");
    }

    /**
     * Sendet eine Aktion zum Vertauschen zweier Spieler an den Server.
     *
     * @param {number} playerIndex - Der Index des zu tauschenden Spielers.
     * @param {number} direction - +1 um mit dem nächsten zu tauschen, -1 um mit dem vorherigen.
     */
    function _upOrDownButton_click(playerIndex, direction) {
        //Sound.play('click');

        let playerIndex2 = playerIndex + direction
        if (playerIndex2 < 1 || playerIndex2 > 3) {
            return;
        }

        _disableButtons();
        EventBus.emit("lobbyView:swap", {playerIndex1: playerIndex, playerIndex2: playerIndex2});
    }

    /**
     * Deaktiviert alle Buttons.
     */
    function _disableButtons() {
        _startButton.disabled = true;
        _exitButton.disabled = true;
        _playerList.querySelectorAll('button').forEach(button => {
            button.disabled = true
        });
    }

    return {
        init,
        render,
    };
})();