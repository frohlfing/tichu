# Offene Punkte und nächste Schritte

# Backend

* Todos im code umsetzten
* Interrupt-Handling für Tichu-Ansagen und Bomben
* Offenes Spiel
* Alte Unit-Tests -> PyTest
* Sicherheitsaspekte (Input-Validierung, Schutz vor Missbrauch).

# Frontend

## Bugs:
* Beim Client-Reload geht requestId serverseitig verloren.
* Zurückgenommene Schupfkarten werden nicht richtig einsortiert.
* Stich wird visuell nicht abgeräumt.
* Tichu-Button nicht disable, obwohl Karten gespielt.
* Nach Rundenende wird etwas gewartet, und dann >> Peer Frank: Räume Warte-Tasks für 'play' auf. (peer, line 271)

## Features:
* Animationen
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