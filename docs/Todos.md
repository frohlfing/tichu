# Offene Punkte und nächste Schritte

# Backend

* Todos im code umsetzten
* Interrupt-Handling für Tichu-Ansagen und Bomben
* Offenes Spiel
* Alte Unit-Tests -> PyTest
* Sicherheitsaspekte (Input-Validierung, Schutz vor Missbrauch).

# Frontend

## Bugs:
* Tichu-Button nicht disable, obwohl Karten gespielt.
* Score-Anzeige bei negativen Punkten

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