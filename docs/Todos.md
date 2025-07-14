# Offene Punkte und nächste Schritte

# Backend

* Todos im code umsetzten
* Interrupt-Handling für Tichu-Ansagen und Bomben
* Offenes Spiel
* Alte Unit-Tests -> PyTest
* Sicherheitsaspekte (Input-Validierung, Schutz vor Missbrauch).
* Websocket mit SSL
* Sounds einbauen

# Frontend

## Bugs:
* Wenn Spiel mitten drin beendet wird, bleiben Züge liegen. Wenn dann ein neues Spiel gestartet wird, 
  werden diese Karten kassiert (Animation läuft).

## Features:
* Animationen
* Sound
* Offenes Spiel
* Unit-Test vom Backend übernehmen
* Abhängigkeiten der Module dokumentieren (was greift auf was zu?)

# Agenten
*   Implementierung von `RuleAgent`
*   HeuristicAgent optimieren mit neuer Wahrscheinlichkeitsberechnung 
*   Forschung und Implementierung von `NNetAgent`.
    *   Implementierung von `BehaviorAgent`.
        *   Brettspielwelt-Logs aufbereiten
    *   Implementierung von `AlphaZeroAgent`.

NEU: Decision Transformer, Return-to-go (Anzahl Punkte ab jetzt bis zum Sieg)