# Offene Punkte und nächste Schritte

# reStructuredText:
lib.prob.*


# Backend

* Todos im code umsetzten
* Offenes Spiel
* Alte Unit-Tests -> PyTest
* Websocket mit SSL
* WSClient mit Bot ausstatten
* CardsAndCombination
* Engine-Loop verkleinern

# Frontend
* z-index planen
* Sounds einbauen
* Sicherheitsaspekte (Input-Validierung).
* Unittest
* Wish- und DragonDialog nach tableView
* pendingRequest ohne ID, nur ein Request, keine Liste
* bomb und play zusammenführen
* loading-view als Pup-up-Fenster (modal)
* Modul User sinnvoll?
* URLSearchParams zentral auslesen (derzeitige Schalter: tisch_name, player_name, bot, sound)
* localStorage sinnvoll einsetzen
* Setup-Dialog

## Bugs:

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