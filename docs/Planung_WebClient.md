Okay, das ist ein aufregender Schritt – der WebClient! Das Bild gibt eine tolle visuelle Vorstellung. Jetzt geht es darum, das in eine konkrete Frontend-Architektur und einen Entwicklungsplan zu gießen.

Basierend auf deiner Beschreibung und dem Screenshot, lass uns einen Plan für den WebClient mit HTML, CSS und JavaScript entwerfen. Wir gehen davon aus, dass wir keine komplexen Frontend-Frameworks (wie React, Vue, Angular) verwenden, sondern mit Vanilla JavaScript (oder vielleicht einer kleinen Hilfsbibliothek wie jQuery, falls gewünscht, aber nicht zwingend) arbeiten, um es übersichtlich zu halten.

**Technologie-Stack Frontend:**

*   **HTML5:** Für die Grundstruktur der Seite.
*   **CSS3:** Für Styling und Layout.
*   **JavaScript (ES6+):** Für die gesamte Logik, DOM-Manipulation und WebSocket-Kommunikation.

**Grundlegende Frontend-Komponenten/Module (JavaScript-Sicht):**

1.  **`web-socket-service.js`:**
    *   Verantwortlich für das Aufbauen und Verwalten der WebSocket-Verbindung.
    *   Sendet Nachrichten an den Server.
    *   Empfängt Nachrichten vom Server und leitet sie an die entsprechenden Handler weiter (Callbacks oder Event-Dispatcher).
2.  **`uiManager.js` (oder `viewManager.js`):**
    *   Zuständig für das Umsc  halten zwischen verschiedenen Ansichten (Lobby, Spieltisch).
    *   Koordiniert das Rendern von UI-Elementen.
3.  **`lobby-view.js`:**
    *   Rendert die Lobby-Ansicht (Name/Tisch-Eingabe, Spielerliste, Start-Button).
    *   Behandelt Interaktionen in der Lobby.
4.  **`table-View.js`:**
    *   Rendert den Spieltisch (Handkarten, Gegner, Tischmitte, Buttons).
    *   Behandelt Interaktionen am Spieltisch.
5.  **`game-state.js`:**
    *   Hält den clientseitigen Spielzustand (eine Kopie/Interpretation von `public_state` und den `private_state` des aktuellen Spielers).
    *   Wird durch Nachrichten vom Server aktualisiert.
6.  **`cardRenderer.js` (oder Teil von `table-View.js`):**
    *   Funktionen zum Darstellen einzelner Karten und der Hand.
    *   Logik für das Auswählen/Abwählen von Karten.
7.  **`authService.js` (oder Teil von `lobby-view.js`):**
    *   Speichert Spielernamen, Tischnamen.
    *   Verwaltet die `session_id`.

**Entwicklungsphasen und Implementierungsdetails:**

**Phase 1: Grundstruktur und Lobby**

1.  **HTML-Grundgerüst (`index.html`):**
    *   Einen Container für die Lobby-Ansicht (`<div id="lobby-view">`).
    *   Einen Container für die Spieltisch-Ansicht (`<div id="table-view" style="display:none;">`).
    *   Einbindung der CSS- und JS-Dateien.
2.  **CSS (`style.css`):**
    *   Grundlegendes Styling für Hintergrund (Drachenkopf für Lobby), Schriftarten.
    *   Styling für Formularelemente.
3.  **JavaScript (`lobby-view.js`, `web-socket-service.js`, `main.js`):**
    *   **Lobby-UI:**
        *   Input-Felder für Spielername und Tischname.
        *   "Login/Beitreten"-Button.
        *   Bereich zur Anzeige von Spielern am Tisch.
        *   "Spiel starten"-Button (initial ausgeblendet oder deaktiviert).
        *   (Optional für Host): UI-Elemente zum Umsortieren von Spielern.
    *   **`web-socket-service.js`:**
        *   Funktion `connect(playerName, tableName, sessionId)`: Baut die WebSocket-Verbindung mit den korrekten Query-Parametern auf (`ws://tichu.frank-rohlfing.de/ws?player_name=...&table_name=...` oder `?session_id=...`).
        *   `onopen`: Verbindung erfolgreich.
        *   `onmessage`: Empfängt Nachrichten, parst JSON, leitet an einen zentralen Nachrichten-Handler weiter.
        *   `onerror`: Fehlerbehandlung.
        *   `onclose`: Verbindung geschlossen.
        *   Funktion `sendMessage(type, payload)`: Formatiert und sendet JSON-Nachrichten an den Server.
    *   **Login-Button-Logik:**
        *   Liest Spieler- und Tischnamen aus den Inputs.
        *   Ruft `webSocketService.connect()` auf.
    *   **Nachrichtenbehandlung für Lobby:**
        *   Bei Empfang von `"welcome"` (oder wie wir die erste Bestätigung nach Query-Param-Join nennen, z.B. `"joined_confirmation"`):
            *   Speichere `session_id`.
            *   Aktualisiere die Lobby-Ansicht, um den eigenen Spieler und ggf. den Tischstatus anzuzeigen.
            *   Wechsle von der reinen Eingabemaske zur "Am Tisch"-Ansicht der Lobby.
        *   Bei Empfang von `"notification"` mit `event: "player_joined"` oder `event: "lobby_update"`:
            *   Aktualisiere die Liste der Spieler am Tisch.
            *   Wenn der aktuelle Spieler Host ist (z.B. der erste `Peer` am Tisch, diese Info muss vom Server kommen oder abgeleitet werden), aktiviere die Host-Controls (Spieler umsortieren, Spiel starten).
    *   **"Spiel starten"-Button-Logik:**
        *   Sendet `{"type": "lobby_action", "payload": {"action": "start_game"}}` via `webSocketService`.
    *   **Host-Controls (Spieler umsortieren):**
        *   Ermöglicht Drag&Drop oder Pfeil-Buttons zum Ändern der Reihenfolge.
        *   Sendet `{"type": "lobby_action", "payload": {"action": "assign_team", "data": [new_indices_array]}}`.

**Phase 2: Grundlegende Spieltisch-UI**

1.  **HTML-Struktur (innerhalb von `<div id="table-view">`):**
    *   Bereiche für Spieler Oben, Links, Rechts (initial nur Platzhalter oder Kartenrücken).
    *   Bereich für die Handkarten des Spielers (unten).
    *   Bereich für den Stich/gespielte Karten (Mitte).
    *   Bereich für Aktions-Buttons ("Passen", "Tichu", "Spielen").
    *   Bereich für die Bombe (Icon).
    *   Bereiche für "Großes Tichu"-Anzeigen und Punktestand.
    *   Buttons "Beenden", "Optionen".
2.  **CSS:**
    *   Layout des Spieltischs (Positionierung der Spielerbereiche, Handkarten etc.).
    *   Styling für Karten (Größe, Aussehen).
    *   Styling für Buttons.
3.  **JavaScript (`table-View.js`, `cardRenderer.js`):**
    *   **`tableView.show()` / `lobbyView.hide()`:** Umschalten der Ansichten.
    *   **Kartenrendern:**
        *   Funktion `renderHand(cardsArray)`: Erzeugt HTML-Elemente für jede Karte in der Hand des Spielers und zeigt sie an. Jede Karte bekommt eine eindeutige ID oder Datenattribute, um sie zu identifizieren.
        *   Event-Listener für Klicks auf Handkarten:
            *   Toggle eines "selected"-CSS-Klasse.
            *   Speichert ausgewählte Karten in einem Array.
    *   **Aktions-Buttons:**
        *   Initial oft deaktiviert, werden durch Server-Requests (`action: "play"`, etc.) aktiviert.
    *   **Platzhalter für Gegner/Partner:** Zeigt Kartenrücken oder Spielername an.

**Phase 3: Spielinteraktion und WebSocket-Nachrichten für den Spieltisch**

1.  **JavaScript (`web-socket-service.js`, `table-View.js`, `game-state.js`):**
    *   **Nachrichtenbehandlung für Spielstart:**
        *   Bei Empfang einer `notification` (z.B. `event: "game_started"`) oder wenn die erste `deal_cards` kommt: Rufe `tableView.show()` auf.
    *   **`"deal_cards"`-Nachricht vom Server:**
        *   Aktualisiere `gameState.private_state.hand_cards`.
        *   Rufe `cardRenderer.renderHand()` auf, um die neuen Karten anzuzeigen.
    *   **`"schupf_cards_received"`-Nachricht:**
        *   Aktualisiere `gameState.private_state.hand_cards` (mit den erhaltenen Karten).
        *   Rufe `cardRenderer.renderHand()` auf.
    *   **`"request"`-Nachricht vom Server (z.B. `payload: {action: "play", request_id: "...", ...}`):**
        *   Speichere die `request_id`.
        *   Aktualisiere `gameState` mit dem empfangenen `public_state` und `private_state`.
        *   Rendere den Tisch neu, falls nötig (z.B. gespielte Karten der Gegner anzeigen).
        *   **Aktionsbuttons aktivieren/deaktivieren:**
            *   Wenn `action: "play"`: Aktiviere "Spielen" und "Passen". "Tichu"-Button ggf. basierend auf Spielphase/Handkarten.
            *   Wenn `action: "schupf"`: Ändere UI-Modus auf Kartenauswahl für Schupfen.
            *   Wenn `action: "announce_grand_tichu"`: Zeige "Ja/Nein"-Buttons für Grand Tichu.
            *   ... usw. für `wish`, `give_dragon_away`.
        *   **Turn-Indicator:** Aktualisiere den grauen Kreis, um anzuzeigen, wer am Zug ist (basierend auf `public_state.current_turn_index`).
    *   **"Spielen"-Button-Logik:**
        *   Sammelt die aktuell ausgewählten Karten.
        *   Sendet `{"type": "response", "payload": {"request_id": gespeicherte_id, "data": {"cards": stringify_cards(ausgewaehlte_karten)}}}`.
        *   Animation: Karten gleiten auf den Tisch.
    *   **"Passen"-Button-Logik:**
        *   Sendet `{"type": "response", "payload": {"request_id": gespeicherte_id, "data": {"cards": ""}}}`.
    *   **"Tichu"-Button-Logik (für proaktives Tichu):**
        *   Sendet `{"type": "interrupt_request", "payload": {"reason": "tichu"}}`. (Früher: `announce`)
    *   **Bomben-Icon-Klick-Logik:**
        *   Öffnet ggf. ein Interface zur Auswahl der Bombenkarten (oder prüft, ob nur eine Bombe möglich ist).
        *   Sendet `{"type": "interrupt_request", "payload": {"reason": "bomb", "cards": stringify_cards(bomben_karten)}}`. (Früher: `bomb`)
    *   **`"notification"`-Nachrichten vom Server (z.B. `event: "played"`, `event: "bombed"`, `event: "passed"`):**
        *   Aktualisiere `gameState.public_state` (besonders `played_cards`, `trick_cards`, `trick_owner_index`, `count_hand_cards` der Gegner).
        *   Rendere den Tisch neu:
            *   Zeige die von anderen gespielten Karten in der Mitte.
            *   Aktualisiere die Anzahl der Handkarten der Gegner (als Zahl oder durch Ändern der angezeigten Rücken).
            *   Zeige "Großes Tichu"-Ansagen der anderen.
            *   Aktualisiere Punktestände.
        *   Bei `event: "player_turn_changed"`: Aktualisiere den Turn-Indicator.
    *   **`"error"`-Nachricht:** Zeige dem Spieler die Fehlermeldung an (z.B. in einem kleinen Popup oder Textbereich).

**Phase 4: Verfeinerung und zusätzliche Features**

1.  **CSS-Verbesserungen:** Schickeres Aussehen, Animationen für Kartenbewegungen.
2.  **"Beenden"-Button:** Sendet `{"type": "leave"}` und kehrt zur Lobby oder einer Startseite zurück.
3.  **"Optionen"-Button:** (Noch nicht spezifiziert, könnte Sound-Einstellungen etc. enthalten).
4.  **Visuelles Feedback:** Hervorheben des aktuellen Spielers, klarere Anzeige von Ansagen.
5.  **Responsiveness:** Anpassung an verschiedene Bildschirmgrößen (falls relevant).
6.  **Lokale Speicherung der `session_id`:** Verwendung von `localStorage` oder `sessionStorage`, um die `session_id` zu speichern und bei einem erneuten Besuch der Seite für einen Reconnect zu verwenden.

**Wichtige Überlegungen für den Frontend-Code:**

*   **Zustandsverwaltung:** Der Client muss den Spielzustand (seine Hand, was auf dem Tisch liegt, wer dran ist) aktuell halten. `game-state.js` ist hierfür zentral.
*   **DOM-Manipulation:** Effiziente Updates des DOMs sind wichtig, um die Seite flüssig zu halten. Nicht bei jeder kleinen Änderung den gesamten Tisch neu zeichnen, sondern gezielt Elemente aktualisieren.
*   **Fehlerbehandlung:** Was passiert, wenn der Server einen Fehler sendet? Was, wenn die WebSocket-Verbindung abbricht? Der Nutzer sollte informiert werden.
*   **Asynchronität:** WebSocket-Kommunikation ist asynchron. Promises oder async/await in JavaScript helfen hier.
*   **Validierung auf dem Client (optional, aber gut für UX):** Bevor der Client eine Aktion an den Server sendet (z.B. Karten spielen), kann eine clientseitige Vorab-Validierung stattfinden (z.B. "Hast du diese Karten überhaupt auf der Hand?"). Die finale Validierung erfolgt aber immer auf dem Server.

**Beginnend mit der Lobby:**

Ich würde empfehlen, mit Phase 1 zu beginnen: HTML-Grundstruktur, CSS-Basis, und die JavaScript-Logik für die Lobby (Name/Tisch eingeben, Verbindungsaufbau, Empfang der `joined_confirmation` und Anzeige der Spieler in der Lobby). Wenn das steht, ist der Grundstein für die Kommunikation gelegt.

Das ist ein umfangreicher Plan, aber er deckt die meisten deiner Anforderungen ab. Wir können das iterativ angehen. Was sind deine ersten Gedanken dazu? Wo möchtest du anfangen oder Details vertiefen?


    



:ivar host_index: Index des Clients, der Host des Tisches ist (-1 == kein Client am Tisch)

Das als nächstes posten:

notifikation events game_started und round_started hab ich hinzugefügt. in handleNotification hab ich switch case für alle definierten Events vorbereitet:

```
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
                } else if (currentPubState && context.player_index !== undefined) {
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
```
