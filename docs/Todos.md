# Offene Punkte und nächste Schritte

*   **Arena-Betrieb:**
    *   Weitere Verfeinerung der Unit-Tests.
    *   Todos im code umsetzten
*   **Server-Betrieb:**
    *   Implementierung des WebSocket-Servers und Handlers.
    *   Implementierung der `Game-Factory`.
    *   Finalisierung und Implementierung des WebSocket-Nachrichtenprotokolls.
    *   Implementierung der `Client`-Klasse für die Spieler-Interaktion.
    *   Robustes Handling von Verbindungsabbrüchen und Reconnects.
    *   Lobby-Funktionalität (Tischerstellung, Sitzplatzzuweisung, Spielstart durch Spieler).
    *   Implementierung des Interrupt-Handlings für Tichu-Ansagen und Bomben im Live-Betrieb (Abbruch von Spieler-Aktionen).
    *   Implementierung des Features, dass ausgeschiedene Spieler die Karten der Mitspieler sehen können.
    *   Sicherheitsaspekte des WebSocket-Servers (Input-Validierung, Schutz vor Missbrauch).
   **Frontend:**
    *   Design und Implementierung der Lobby
    *   Implementierung des Spieltisches (Design von Godot-Projekt übernehmen)
*   **Agenten:**
    *   Implementierung von `RuleAgent`
    *   HeuristicAgent optimieren mit neuer Wahrscheinlichkeitsberechnung 
    *   Forschung und Implementierung von `NNetAgent`.
        *   Implementierung von `BehaviorAgent`.
            *   Brettspielwelt-Logs aufbereiten
        *   Implementierung von `AlphaZeroAgent`.