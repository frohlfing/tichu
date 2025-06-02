document.addEventListener('DOMContentLoaded', () => {
    // URL-Parameter auslesen
    const urlParams = new URLSearchParams(window.location.search);
    const paramPlayerName = urlParams.get('player_name');
    const paramTableName = urlParams.get('table_name');
    if (paramPlayerName) {
        GameState.setPlayerName(paramPlayerName);
    }
    if (paramTableName) {
        GameState.setTableName(paramTableName);
    }

    // WebSocket-Service initialisieren
    WebSocketService.setOnMessageCallback(handleServerMessage);

    // UI-Manager initialisieren
    UiManager.init(LobbyView, TableView);

    // Views initialisieren
    LobbyView.init(handleJoinAttempt, handleStartGameAttempt);
    TableView.init(handleTablePlayCards, handleTablePass, handleTableTichu, handleTableBomb);

    // Versuche automatischen Login, wenn Session-ID vorhanden ist
    const autoLoginSessionId = GameState.getSessionId();
    if (autoLoginSessionId) {
        console.log("Gefundene Session-ID, versuche automatischen Reconnect:", autoLoginSessionId);
        handleJoinAttempt();
    }
    else {
        UiManager.showLobby(); // UiManager delegiert an LobbyView.show()
        LobbyView.showJoinForm(); // Oder LobbyView entscheidet selbst, was es beim .show() anzeigt
    }

    // -------------------------------------------
    // WebSocket-Callbacks
    // -------------------------------------------

    function handleServerMessage(message) {
        const type = message.type;
        const payload = message.payload || {};

        switch (type) {
            case "request": // Server fordert eine Entscheidung
                            // TODO: Hier die Anfrage vom Server an den TableView weiterleiten
                            // TableView.handleServerRequest(payload.request_id, payload.action, payload.public_state, payload.private_state, payload.context);
                console.log("Request vom Server erhalten:", payload);
                LobbyView.displayMessage(`Server Anfrage: ${payload.action}`); // Temporär
                break;

            case "notification": // Server informiert über ein Spielereignis
                handleNotification(payload.event, payload.context || {});
                break;

            case "error": // Fehlermeldung vom Server
                LobbyView.displayMessage(`Server Fehler: ${payload.message} (Code: ${payload.code})`, true);
                if (payload.code === ErrorCodes.SESSION_EXPIRED || payload.code === ErrorCodes.SESSION_NOT_FOUND) {
                    localStorage.removeItem('tichuSessionId'); // Gespeicherte ID entfernen
                    GameState.setSessionId(null);
                    UiManager.showLobby();
                    LobbyView.showJoinForm();
                }
                break;

            case "pong": // Antwort vom Server auf eine ping-Nachricht
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
        let currentPubState = GameState.getPublicState();
        let localPlayerIndex = GameState.getPlayerIndex();
        switch (event) {
            case "player_joined":
                // Prüfen, ob ICH der Spieler bin, der gerade beigetreten ist.
                // Der angereicherte Kontext enthält dann session_id, public_state, private_state.
                if (context.session_id && context.public_state && context.private_state) {
                    // Dies ist die "Willkommensnachricht" für den neu beigetretenen Spieler
                    console.log("Spezielle 'player_joined' Notification für mich empfangen (initialer State).");
                    GameState.setSessionId(context.session_id);
                    GameState.updateStates(context.public_state, context.private_state);

                    localPlayerIndex = GameState.getPlayerIndex(); // Sicherstellen, dass wir den frischen Index haben
                    currentPubState = GameState.getPublicState(); // Und den frischen Public State

                    LobbyView.displayMessage("Erfolgreich beigetreten!", false);

                    // Host-Logik und Anzeigen der Tisch-Info wie zuvor
                    if (currentPubState && localPlayerIndex !== -1) {
                        let isHost = false; // TODO: Server muss diese Info klarer liefern
                                            // z.B. im angereicherten context für player_joined
                        if (context.is_host !== undefined) {
                            isHost = context.is_host;
                        }
                        // Sonstige Heuristiken für Host sind fehleranfällig.
                        // Besser: Server sendet "is_host: true/false" im angereicherten Kontext
                        // für den joinenden Spieler.

                        const playersForLobby = currentPubState.player_names
                            .map((name, index) => ({
                                name: name || "Offen",
                                index: index,
                                isSelf: index === localPlayerIndex
                            }))
                            .filter(p => p.name && p.name !== "Offen" && !p.name.startsWith("RandomAgent_"));
                        LobbyView.showTableInfo(currentPubState.table_name, playersForLobby, isHost);
                    }
                }
                else if (currentPubState && context.player_index !== undefined) {
                    // Dies ist eine "player_joined" Notification über einen ANDEREN Spieler
                    // oder eine generische für mich, nachdem ich schon initialisiert bin.
                    LobbyView.displayMessage(`Spieler ${context.player_name || context.replaced_by_name || 'Unbekannt'} ist beigetreten.`);

                    // Aktualisiere die Spielerliste in der Lobby
                    // Annahme: Der 'context' enthält genug Info oder der 'public_state' im GameState wird anderweitig aktuell gehalten
                    // (z.B. durch periodische Updates oder wenn der nächste "request" den State enthält)
                    // Sicherer ist, wenn der Server hier alle Namen mitschickt oder der Client einen Request dafür macht.
                    // Für die Lobby reicht es oft, den neuen Spieler hinzuzufügen/Namen zu aktualisieren.
                    if (context.player_index !== undefined && (context.player_name || context.replaced_by_name)) {
                        if (currentPubState.player_names[context.player_index] !== (context.player_name || context.replaced_by_name)) {
                            currentPubState.player_names[context.player_index] = (context.player_name || context.replaced_by_name);
                        }
                    }
                    const playersForLobby = currentPubState.player_names
                        .map((name, index) => ({
                            name: name || "Offen",
                            index: index,
                            isSelf: index === localPlayerIndex
                        }))
                        .filter(p => p.name && p.name !== "Offen" && !p.name.startsWith("RandomAgent_"));
                    let isHost = false; // TODO
                    LobbyView.showTableInfo(currentPubState.table_name, playersForLobby, isHost);
                }
                break;

            case "player_left":
                break

            case "lobby_update":
                // Lobby-Ansicht aktualisieren, falls sie aktiv ist
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

            case "game_started":
                UiManager.showTable();
                // Initialisiere TableView mit den Startdaten
                // TableView.initGame(GameState.getPublicState(), GameState.getPrivateState());
                break;

            case "round_started":
                break

            case "hand_cards_dealt":
                // context ist hier: {"hand_cards": stringify_cards(self.priv.hand_cards)}
                console.log("Handkarten erhalten:", context.hand_cards);
                if (GameState.getPrivateState()) { // Stelle sicher, dass privateState initialisiert ist
                    GameState.getPrivateState().hand_cards = context.hand_cards; // Oder wie auch immer du Karten speicherst
                    // TODO: TableView.renderPlayerHand(context.hand_cards);
                }
                break;

            case "grand_tichu_announced":
                break

            case "tichu_announced":
                break

            case "player_schupfed":
                break

            case "schupf_cards_dealt":
                // context ist hier: {"received_schupf_cards": stringify_cards(self.priv.received_schupf_cards)}
                console.log("Schupf-Karten erhalten:", context.received_schupf_cards);
                if (GameState.getPrivateState()) {
                    GameState.getPrivateState().received_schupf_cards = context.received_schupf_cards;
                    // TODO: TableView.renderPlayerHand(GameState.getPrivateState().hand_cards); // Hand hat sich geändert
                    // TODO: Ggf. UI-Feedback für erhaltene Schupfkarten
                }
                break;

            case "passed":
                break

            case "played":
                break

            case "bombed":
                break

            case "wish_made":
                break

            case "wish_fulfilled":
                break

            case "trick_taken":
                break

            case "player_turn_changed":
                break

            case "round_over":
                break

            case "game_over":
                break
        }
    }

    // -------------------------------------------
    // LobbyView-Callbacks
    // -------------------------------------------

    async function handleJoinAttempt() {
        LobbyView.displayMessage("Verbinde mit Server...");
        try {
            // Versuche zuerst mit gespeicherter SessionId, falls vorhanden
            const existingSessionId = GameState.getSessionId();
            if (existingSessionId) {
                console.log("Versuche Reconnect mit Session ID:", existingSessionId);
                await WebSocketService.connect(null, null, existingSessionId);
            }
            else {
                const playerName = GameState.getPlayerName();
                const tableName = GameState.getTableName();
                await WebSocketService.connect(playerName, tableName);
            }
            LobbyView.displayMessage("Warte auf Server-Bestätigung...");
        } catch (error) {
            console.error("Fehler beim Verbindungsaufbau:", error);
            LobbyView.displayMessage(`Fehler: ${error.message || 'Verbindung fehlgeschlagen'}`, true);
            if (GameState.getSessionId()) {
                GameState.setSessionId(null);
                UiManager.showLobby();
                LobbyView.showJoinForm(); // Zeige wieder das Formular
            }
        }
    }

    function handleStartGameAttempt() {
        if (WebSocketService.isConnected()) {
            WebSocketService.sendMessage("lobby_action", {action: "start_game"});
        }
        else {
            LobbyView.displayMessage("Nicht mit Server verbunden.", true);
        }
    }

    // -------------------------------------------
    // TableView-Callbacks
    // -------------------------------------------

    async function handleTablePlayCards() {
        // todo
    }

    async function handleTablePass() {
        // todo
    }

    async function handleTableTichu() {
        // todo
    }

    async function handleTableBomb() {
        // todo
    }
});