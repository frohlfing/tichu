document.addEventListener('DOMContentLoaded', () => {
    // Module initialisieren
    UiManager.init(LobbyView, null); // TableView kommt später dazu

    // Initial Lobby-Ansicht anzeigen
    LobbyView.showJoinForm();
    // UiManager.showLobby(); // Ist dasselbe wie oben, da nur Lobby initialisiert

    // WebSocket-Nachrichten-Callback setzen
    WebSocketService.setOnMessageCallback(handleServerMessage);

    // LobbyView Callbacks initialisieren
    LobbyView.init(handleJoinAttempt, handleStartGameAttempt);


    // --- Event Handler und Logik ---
    async function handleJoinAttempt(playerName, tableName) {
        LobbyView.displayMessage("Verbinde mit Server...");
        try {
            // Versuche zuerst mit gespeicherter SessionId, falls vorhanden
            const existingSessionId = GameState.getSessionId();
            if (existingSessionId) {
                 console.log("Versuche Reconnect mit Session ID:", existingSessionId);
                 await WebSocketService.connect(null, null, existingSessionId);
            } else {
                 await WebSocketService.connect(playerName, tableName);
            }
            // Wenn connect() erfolgreich ist (Promise resolved), kommt 'joined_confirmation'
            // ansonsten wird der Promise rejecten und hier ein Fehler geworfen.
            LobbyView.displayMessage("Warte auf Server-Bestätigung...");

        } catch (error) {
            console.error("Fehler beim Verbindungsaufbau:", error);
            LobbyView.displayMessage(`Fehler: ${error.message || 'Verbindung fehlgeschlagen'}`, true);
            // Ggf. gespeicherte SessionId löschen, wenn Reconnect fehlschlägt
            // if (GameState.getSessionId()) {
            //     localStorage.removeItem('tichuSessionId');
            //     GameState.setSessionId(null);
            // }
        }
    }

    function handleStartGameAttempt() {
        if (WebSocketService.isConnected()) {
            WebSocketService.sendMessage("lobby_action", { action: "start_game" });
        } else {
            LobbyView.displayMessage("Nicht mit Server verbunden.", true);
        }
    }

    function handleServerMessage(message) {
        const type = message.type;
        const payload = message.payload || {};

        switch (type) {
            case "joined_confirmation": // snake_case vom Server
                GameState.setSessionId(payload.session_id);
                GameState.updateStates(payload.public_state, payload.private_state);

                // TODO: Bestimme, ob der aktuelle Spieler Host ist.
                // Das muss der Server mitteilen, z.B. im public_state oder einem extra Flag in joined_confirmation
                const isHost = payload.public_state.player_names[payload.private_state.player_index] === payload.public_state.player_names[0]; // Einfache Annahme: Erster Spieler ist Host

                const playersForLobby = payload.public_state.player_names
                    .map((name, index) => ({
                        name: name || "Offen",
                        index: index,
                        isSelf: index === payload.private_state.player_index
                    }))
                    .filter(p => p.name !== "Offen"); // Nur belegte Plätze anzeigen

                LobbyView.showTableInfo(payload.public_state.table_name, playersForLobby, isHost);
                break;

            case "notification":
                handleNotification(payload.event, payload.context || {});
                break;

            case "request":
                // TODO: Hier die Anfrage vom Server an den TableView weiterleiten
                // TableView.handleServerRequest(payload.request_id, payload.action, payload.public_state, payload.private_state, payload.context);
                console.log("Request vom Server erhalten:", payload);
                LobbyView.displayMessage(`Server Anfrage: ${payload.action}`); // Temporär
                break;

            case "error":
                LobbyView.displayMessage(`Server Fehler: ${payload.message} (Code: ${payload.code})`, true);
                // Wenn Session ungültig, evtl. Session löschen und neu joinen lassen
                if (payload.code === 200 || payload.code === 201) { // SESSION_EXPIRED oder SESSION_NOT_FOUND
                    localStorage.removeItem('tichuSessionId'); // Gespeicherte ID entfernen
                    GameState.setSessionId(null);
                    UiManager.showLobby();
                    LobbyView.showJoinForm();
                }
                break;

            case "pong":
                console.log("Pong vom Server:", payload.timestamp);
                break;

            // Weitere Nachrichten-Typen (deal_cards, schupf_cards_received) kommen später dazu
            // und werden eher vom TableView behandelt.

            default:
                console.warn("Unbekannter Nachrichtentyp vom Server:", type, payload);
        }
    }

    function handleNotification(event, context) {
        console.log("Notification Event:", event, "Context:", context);
        switch (event) {
            case "player_joined":
            case "player_left":
            case "lobby_update": // Oder spezifischere Events für Team-Zuweisung
                // Lobby-Ansicht aktualisieren, falls sie aktiv ist
                // Dazu muss GameState.getPublicState() den aktuellen Stand haben
                // Oder die Notification enthält die aktualisierte Spielerliste
                if (document.getElementById('lobby-view').style.display !== 'none' && GameState.getPublicState()) {
                    const currentPubState = GameState.getPublicState();
                     // Erneutes Rendern der Spielerliste in der Lobby
                    const playersForLobby = currentPubState.player_names
                        .map((name, index) => ({
                            name: name || "Offen",
                            index: index,
                            isSelf: index === GameState.getPlayerIndex()
                        }))
                        .filter(p => p.name !== "Offen");
                    // TODO: Host-Status korrekt ermitteln
                    const isHost = currentPubState.player_names[GameState.getPlayerIndex()] === currentPubState.player_names[0];
                    LobbyView.showTableInfo(currentPubState.table_name, playersForLobby, isHost);
                }
                LobbyView.displayMessage(`Event: ${event} - Spieler: ${context.player_name || context.replaced_by_name || 'N/A'}`);
                break;

            case "game_started": // Beispiel, muss vom Server gesendet werden
                 UiManager.showTable();
                 // Initialisiere TableView mit den Startdaten
                 // TableView.initGame(GameState.getPublicState(), GameState.getPrivateState());
                 break;
            // Weitere Spiel-Notifications
        }
    }
});