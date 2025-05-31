const LobbyView = (() => {
    const lobbyViewDiv = document.getElementById('lobby-view');
    const joinFormDiv = document.getElementById('join-form');
    const playerNameInput = document.getElementById('player-name');
    const tableNameInput = document.getElementById('table-name');
    const joinButton = document.getElementById('join-button');
    const lobbyMessageP = document.getElementById('lobby-message');

    const tableInfoDiv = document.getElementById('table-info');
    const currentTableNameSpan = document.getElementById('current-table-name');
    const playerListUl = document.getElementById('player-list');
    const hostControlsDiv = document.getElementById('host-controls');
    const startGameButton = document.getElementById('start-game-button');

    function init(onJoinCallback, onStartGameCallback) {
        const savedPlayerName = GameState.getPlayerName();
        if (savedPlayerName) {
            playerNameInput.value = savedPlayerName;
        }

        const savedTableName = GameState.getTableName();
        if (savedTableName) {
            tableNameInput.value = savedTableName;
        }

        joinButton.addEventListener('click', () => {
            const playerName = playerNameInput.value.trim();
            const tableName = tableNameInput.value.trim();
            if (playerName && tableName) {
                lobbyMessageP.textContent = '';
                GameState.setPlayerName(playerName);
                GameState.setTableName(tableName);
                onJoinCallback();
            } else {
                lobbyMessageP.textContent = 'Bitte Name und Tischname eingeben.';
            }
        });

        startGameButton.addEventListener('click', () => {
            onStartGameCallback();
        });
    }

    function showJoinForm() {
        joinFormDiv.style.display = 'block';
        tableInfoDiv.style.display = 'none';
        lobbyViewDiv.style.display = 'flex';
    }

    function showTableInfo(tableName, players, isHost) {
        joinFormDiv.style.display = 'none';
        tableInfoDiv.style.display = 'block';
        lobbyViewDiv.style.display = 'flex';

        currentTableNameSpan.textContent = tableName;
        playerListUl.innerHTML = ''; // Spielerliste leeren
        players.forEach(player => {
            const li = document.createElement('li');
            li.textContent = `${player.name} (Index: ${player.index !== undefined ? player.index : 'N/A'}) ${player.isSelf ? '(Du)' : ''}`;
            playerListUl.appendChild(li);
        });

        if (isHost) {
            hostControlsDiv.style.display = 'block';
        } else {
            hostControlsDiv.style.display = 'none';
        }
    }

    function displayMessage(message, isError = false) {
        lobbyMessageP.textContent = message;
        lobbyMessageP.style.color = isError ? '#ff6b6b' : '#ffc107';
    }

    function hide() {
        lobbyViewDiv.style.display = 'none';
    }

    function show() {
        lobbyViewDiv.style.display = 'flex';
    }

    return {
        init,
        showJoinForm,
        showTableInfo,
        displayMessage,
        hide,
        show
    };
})();