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
        // console.log("LobbyView: Rendere LobbyView.");

        _tableName.textContent = State.getTableName();
        _playerList.innerHTML = '';

        const isHost = State.isHost();
        _startButton.classList.toggle('hidden', !isHost);

        // Zeige Spieler in der aktuellen Reihenfolge an
        // Schleife über die relativen Sitzplätze (0=Benutzer, 1=Rechts, 2=Partner, 3=Links)
        for (let relativeIndex= 0; relativeIndex <= 3; relativeIndex++) {
            let canonicalIndex = Lib.getCanonicalPlayerIndex(relativeIndex);
            let name = State.getPlayerName(canonicalIndex);

            const li = document.createElement('li');

            let displayName = name || `Spieler ${canonicalIndex + 1}`;
            if (relativeIndex === 0) {
                displayName += ' (Du)';
            }
            else if (canonicalIndex === State.getHostIndex()) {
                displayName += ' (Host)';
            }
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
        return _viewContainer.classList.contains('active');
    }

    /**
     * Ereignishändler für den StartGame-Button.
     */
    function _handleStartButtonClick() {
        _disableButtons();
        SoundManager.playSound('buttonClick');
        EventBus.emit("lobbyView:start");
    }

    /**
     * Ereignishändler für den Exit-Button.
     */
    function _handleExitButtonClick() {
        _disableButtons();
        SoundManager.playSound('buttonClick');
        EventBus.emit("lobbyView:exit");
    }

    /**
     * Sendet eine Aktion zum Vertauschen zweier Spieler an den Server.
     *
     * @param {number} playerIndex - Der Index des zu tauschenden Spielers.
     * @param {number} direction - +1 um mit dem nächsten zu tauschen, -1 um mit dem vorherigen.
     */
    function _upOrDownButton_click(playerIndex, direction) {
        SoundManager.playSound('buttonClick');
        let playerIndex2 = playerIndex + direction

        // Der erste Spieler kann nicht verschoben werden.
        // Und Spieler können nicht an Position 0 geschoben werden.
        if (playerIndex2 < 1 || playerIndex2 > 3) {
            console.log("LobbyView: Verschieben an diese Position nicht möglich.");
            return;
        }

        _disableButtons();
        console.log("LobbyView: Sende neue Indezies zum Vertauschen", [playerIndex, playerIndex2]);
        EventBus.emit("lobbyView:swap", {playerIndex1: playerIndex, playerIndex2: playerIndex2});
    }

    /**
     * Deaktiviert alle Buttons.
     */
    function _disableButtons() {
        _startButton.disabled = true;
        _exitButton.disabled = true;
        // todo Buttons in .player-order-controls deaktivieren
    }

    return {
        init,
        render,
        show,
        hide,
        isVisible
    };
})();