# Technische Projektdokumentation: Tichu Webanwendung

**Datum:** 26. Mai 2024
**Version:** 0.2.0 (Entwurfsphase für zweite Ausbaustufe)
**Autor:** [Frank Rohlfing]

**Inhaltsverzeichnis**

1.  [Projektziele](#1-projektziele)

2.  [Regelwerk](#2-regelwerk)
    1.  [Spielregeln](#21-spielregeln)
    2.  [Ablauf einer Partie](#22-ablauf-einer-partie)
    3.  [Sonderfälle](#23-sonderfälle)
    
3.  [Systemarchitektur](#3-systemarchitektur)  
    1.  [Technologie-Stack](#31-technologie-stack)
    2.  [Klassenhierarchie](#32-klassenhierarchie)
    
4.  [Modulübersicht und Verzeichnisse](#4-modulübersicht-und-verzeichnisse) TODO Verzeichnisstruktur zum Anhang packen
    1.  [`src/`-Verzeichnis](#41-src-verzeichnis)
    2.  [`tests/`-Verzeichnis](#42-tests-verzeichnis)
    3.  [Start-Skripte](#43-start-skripte)

5. [Daten, Konstanten, Typen](#5-daten-konstanten-typen) TODO zur ersten Ausbaustufe packen
    1.  [Datenklassen](#51-datenklassen)
    2.  [Karte](#52-karte)
    3.  [Kombination](#53-kombination)
    4.  [Spielphasen](#54-spielphasen)

6.  [Arena-Betrieb (erste Ausbaustufe)](#6-arena-betrieb-erste-ausbaustufe)
    1.  [Zweck](#61-zweck)
    2.  [Agenten (KI-gesteuerter Spieler)](#62-agenten-ki-gesteuerter-spieler)
        1.  [Basisklassen](#621-basisklassen)
        2.  [Agenten-Typen](#622-agenten-typen) 
    3.  [Implementierung](#63-implementierung)

7.  [Server-Betrieb (zweite Ausbaustufe)](#7-server-betrieb-zweite-ausbaustufe)
    1.  [Query-Parameer der Websocket-URL](#71-query-parameer-der-websocket-url)
    2.  [WebSocket-Nachrichten](#72websocket-nachrichten)
        1.  [Request-/Response-Nachrichten](#721-request-response-nachrichten)
        2.  [Notification-Nachrichten](#722-notification-nachrichten)
        3.  [Fehlermeldungen](#723-fehlermeldungen)
    3.  [Verantwortlichkeiten der Komponenten im Live-Betrieb](#73-aufgaben-der-komponenten-im-server-betrieb)
        1.  [WebSocket-Handler](#731-websocket-handler)
        2.  [Game-Factory](#732-game-factory)
        3.  [Game-Engine](#733-game-engine)
        4.  [Peer](#734-peer)
        
8. [Frontend (zweite Ausbaustufe)](#8-frontend-zweite-ausbaustufe)

**ANHANG**

A1.  [Entwicklungsumgebung](#a1-entwicklungsumgebung)
    1.  [Systemanforderungen](#a11-systemanforderungen)
    2.  [Einrichtung](#a12-einrichtung)
    3.  [Testing](#a13-testing)

A2. [Exceptions](#a2-exceptions)

A3. [Versionsnummer](#a3-versionsnummer)
    1. [Release auf Github erstellen](#a31-release-auf-github-erstellen)
    
A4. [Styleguide](#a4-styleguide)
    1. [Docstrings](#a41-docstrings)
    2. [Namenskonvention](#a42-namenskonvention)
    3. [Type-Hints](#a43-type-hints)
    
A4. [Glossar](#a5-glossar)

---

## 1. Projektziele

Dieses Dokument beschreibt die technische Implementierung einer Webanwendung für das Kartenspiel "Tichu". Ziel des Projekts ist es, eine Plattform zu schaffen, auf der sowohl KI-gesteuerte Agenten als auch menschliche Spieler gegeneinander Tichu spielen können.

Das Projekt umfasst zwei Hauptbetriebsarten:
*   Eine **Arena** für schnelle Simulationen zwischen Agenten optimiert. Für Forschungs- und Entwicklungszwecke (z.B. Training von KI-Agenten).
*   Einen **Live-Betrieb**, der menschlichen Spielern via WebSockets ermöglicht, gegen Agenten oder andere menschliche Spieler anzutreten.

## 2. Regelwerk

### 2.1 Spielregeln

Die detaillierten Spielregeln für Tichu sind hier zu finden:
[Tichu Regeln und Anleitung](https://cardgames.wiki/de/blog/tichu-spielen-regeln-und-anleitung-einfach-erklaert)

### 2.2 Ablauf einer Partie

1.  **Lobby & Spielstart:** Der erste reale Spieler am Tisch darf die Sitzplätze der Mitspieler bestimmen, bevor er das Spiel startet. Normalerweise wird er warten, bis seine Freunde auch am Tisch sitzen, und dann sagen, wer mit wem ein Team bildet. Das findet in der Lobby statt.
2.  **Kartenausgabe (Initial):** Der Server verteilt je 8 Karten an jeden Spieler.
3.  **Grand Tichu Ansage:** Jeder Spieler muss sich dann entscheiden, ob er Grand Tichu ansagen möchte oder nicht (passt).
4.  **Kartenausgabe (Restlich):** Sobald jeder Spieler sich entschieden hat, teilt der Server die restlichen Karten aus (je 6 pro Spieler, insgesamt 14).
5.  **Kleines Tichu Ansage (vor Schupfen):** Solange noch kein Spieler Karten zum Tausch (Schupfen) abgegeben hat, kann der Spieler ein Tichu ansagen. Dazu muss er vorab ein Interrupt auslösen.
6.  **Schupfen:** Die Spieler müssen nun 3 Karten zum Tauschen abgeben (verdeckt, je eine pro Mitspieler).
7.  **Kartenaufnahme nach Schupfen:** Sobald alle Spieler die Karten zum Tauschen abgegeben haben, sendet der Server an jeden Spieler jeweils die getauschten Karten, die für ihn bestimmt sind.
8.  **Kombinationen legen:**
    *   Ab jetzt kann der Spieler jederzeit a) Tichu ansagen (solange er noch 14 Karten auf der Hand hat) oder b) eine Bombe werfen (sofern er eine besitzt und den Stich überstechen kann). Dazu muss er ein Interrupt auslösen.
    *   Der Spieler mit dem MahJong muss eine Kartenkombination ablegen.
    *   Der nächste Spieler wird aufgefordert, Karten abzulegen oder zu Passen.
    *   Dies wird wiederholt, bis alle Mitspieler hintereinander gepasst haben, sodass der Spieler, der die letzten Karten gespielt hat, wieder an der Reihe ist.
9.  **Stich kassieren:** Dieser Spieler darf die Karten kassieren.
10. **Sonderkarten-Effekte:** MahJong (Wunsch äußern), Hund (Initiative zum Partner), Drache (Stich verschenken).
11. **Spieler scheidet aus:** Wenn ein Spieler keine Handkarten mehr hat, kann er in die Karten der (noch aktiven) Mitspieler schauen (die Karten sind für ihn nicht mehr verdeckt).
12. **Runden-Ende:** Die Runde endet, wenn nur noch ein Spieler Karten hat oder ein Doppelsieg erzielt wird. Punkte werden vergeben.
13. **Partie-Ende:** Wenn die Runde beendet ist und die Partie noch nicht entschieden ist (kein Team hat 1000 Punkte erreicht), leitet der Server automatisch eine neue Runde ein (beginnend bei Punkt 2: Kartenausgabe).
14. **Neustart:** Wenn die Partie beendet ist, beginnt der Prozess wieder in der Lobby (Punkt 1).

### 2.3 Sonderfälle

Diese Punkte stammen aus dem offiziellen Regelwerk.

*   **Kein Vierling:** Es gibt kein Vierling, daher ist ein Drilling mit Phönix nicht möglich.
*   **Full House Restriktion:** Ein Fullhouse darf nicht aus einer 4er-Bombe mit Phönix gebildet werden (Drilling und Pärchen dürfen nicht den gleichen Rang haben).
*   **Wunscherfüllung:** Der Wunsch muss zwar erfüllt werden, wenn man am Zug ist (sofern möglich), aber nicht in dem Moment, wenn man eine Bombe wirft.
*   **Phönix:**
    *   **Phönix als Karte:** Der Kartenwert des Phönix ist 16 (höchster Wert im Spiel, liegt über dem Drachen).
    *   **Phönix als Einzelkarte (Kombination):** Die Kombination "Phönix als Einzelkarte" hat den Rang 14.5 (schlägt das Ass, aber nicht den Drachen).
    *   **Phönix im Stich:** Sticht der Phönix eine Einzelkarte, so ist sein Rang im Stich 0.5 höher die gestochene Karte. Im Anspiel (erste Karte im Stich) hat der Phönix den Rang 1.5.

* Darüber hinaus werden für dieses Projekt folgende Sonderregeln definiert:
    *   Hat ein Spieler ein großes oder normales Tichu angesagt, kann der Partner kein Tichu mehr ansagen. Das vermeidet Fehlentscheidungen aufgrund Synchronisationsprobleme.

## 3. Systemarchitektur

### 3.1 Technologie-Stack

*   **Programmiersprache:** Python (Version 3.11 oder höher)
*   **Kernbibliotheken (Python Standard Library):** `asyncio`, `dataclasses`, `multiprocessing`.
*   **Testing:** `pytest`, `coverage`.
*   **Server: (im Aufbau)** `aiohttp`.
*   **Frontend (geplant):** HTML, CSS, JavaScript.

### 3.2 Klassenhierarchie

Der Zugriff von einer Komponente auf eine andere erfolgt in eine Richtung (top-down); es gibt keinen Zirkelbezug.
      
*   Arena-Betrieb (erste Ausbaustufe)  

```
Arena  
└─ GameEngine 
  ├─ PublicState
  ├─ PrivateState
  └─ Player --- Agent
  
┴┐ 
```

*   Server-Betrieb (zweite Ausbaustufe)

```
WebsocketHandler  
└─ GameFactory 
   └─ GameEngine 
      ├─ PublicState
      ├─ PrivateState
      |            ┌─ Agent
      └─ Player ---┤
                   └─ Peer
┴┐ 
```

## 4 Modulübersicht und Verzeichnisse

### 4.1 `src/`-Verzeichnis

Quellcode für Packages

*   Datenstrukturen:
    *   `public_state.py`: Datenklasse `PublicState`, die den öffentlichen Spielzustand enthält, also alle Informationen, die jedem Spieler an einem Tisch bekannt sind.
    *   `private_state.py`: Datenklasse `PrivateState`, die den privaten Spielzustand eines Spielers enthält, wie z.B. die Handkarten des Spielers.

*   Weitere Kernmodule:
    *   `game_engine.py`: Die `GameEngine`-Klasse, die die Hauptspiellogik für einen Tisch steuert, Runden abwickelt und mit den `Player`-Instanzen interagiert.
    *   `arena.py`: Die `Arena`-Klasse für den Arena-Betrieb, führt mehrere Spiele parallel oder sequenziell aus und sammelt Statistiken.

*   Allgemeine Bibliotheken: 
    * `src/common/` 
       *   `logger.py`: Konfiguration des Logging-Frameworks, inklusive farbiger Konsolenausgabe.
       *   `rand.py`: Benutzerdefinierte Zufallsgenerator-Klasse, optimiert für potenzielle Multiprocessing-Szenarien (verzögerte Initialisierung des Seeds pro Instanz).
       *   `config.py`: (Implizit vorhanden) Konfigurationsvariablen für das Projekt (z.B. Loglevel, Arena-Einstellungen).
       *   `errors.py`: Definition anwendungsspezifischer Exception-Klassen.
       *   `git_utils.py`: Hilfsfunktionen zur Interaktion mit Git (z.B. Ermittlung des aktuellen Tags/Version).

*   Projektspezifische Bibliotheken
    * `src/lib/`
       *   `cards.py`: Definition von Karten, dem Deck, Punktwerten und Hilfsfunktionen zur Kartenmanipulation.
       *   `combinations.py`: Definition von Kombinationstypen, Logik zur Erkennung, Generierung und Validierung von Kartenkombinationen. Enthält auch Logik zur Erstellung des gültigen Aktionsraums.
       *   `partitions.py`: (Falls vorhanden und relevant für Agenten) Logik zur Aufteilung von Handkarten in mögliche Sequenzen von Kombinationen.

*   Spieler-Typen:
    * `src/players/`
       *   `player.py`: Abstrakte Basisklasse `Player` mit der Grundschnittstelle für alle Spieler.
       *   `agent.py`: Abstrakte Basisklasse `Agent`, erbt von `Player`, für KI-gesteuerte Spieler.
       *   `random_agent.py`: Konkrete Implementierung eines Agenten, der zufällige, gültige Züge macht.
       *   `heuristic_agent.py`: (Implementiert oder Geplant) Agent, der auf Heuristiken basiert.
       *   `peer.py`: (Für Server-Betrieb) Klasse, die den serverseitigen Endpunkt der WebSocket-Verbindung zu einem verbundenen Client repräsentiert.

### 4.2 `tests/`-Verzeichnis

Enthält Unit-Tests für die Module in `src/`, geschrieben mit `pytest`. 

### 4.3 Start-Skripte

*   `main.py`: Dient als Haupteinstiegspunkt für den Start des Arena-Betriebs. Konfiguriert Agenten und startet die `Arena`.
*   `server.py`: Startet den Server für den Live-Betrieb. 
*   `wsclient.py`: Startet einen interaktiven WebSocket-Client lediglich für Testzwecke. 

## 5. Daten, Konstanten, Typen

### 5.1 Datenklassen
  
*   `PublicState`: enthält alle Informationen, die allen Spielern an einem Tisch bekannt sind.
*   `PrivateState`: enthält die Informationen, die nur dem jeweiligen Spieler bekannt sind.

### 5.2 Karte

*   `Card`: Die Spielkarte
    *   `value`: Der Kartenwert: 0 (Dog), 1 (Mah Jong), 2 bis 10, 11 (Jack/Bube), 12 (Queen/Dame), 13 (King/König), 14 (Ace/As), 15 (Dragon/Drache), 16 (Phoenix/Phönix).
    *    `suit`: Die Farbe der Karte: 0 (Sonderkarte), 1 (Schwert/Schwarz), 2 (Pagode/Blau), 3 (Jade/Grün), 4 (Stern/Rot).

### 5.3 Kombination

*   `Combination`: Merkmale einer Kartenkombination
    *   `CombinationType`: Ein `IntEnum` für den Typ (z.B. `CombinationType.SINGLE`, `CombinationType.PAIR`, `CombinationType.STREET`, `CombinationType.BOMB`).
    *   `length`: Anzahl der Karten in der Kombination.
    *   `rank`: Der Rang der Kombination (z.B. höchster Kartenwert bei einer Straße).

### 5.4 Spielphasen

TODO!

(siehe hierzu [Ablauf einer Partie](#22-ablauf-einer-partie))

## 6. Arena-Betrieb (erste Ausbaustufe)

### 6.1 Zweck

Der Arena-Betrieb (`arena.py` gestartet über `main.py`) dient dazu, KI-Agenten in einer großen Anzahl von Spielen gegeneinander antreten zu lassen. Dies ist nützlich für:
*   Testen der Stabilität der `GameEngine`.
*   Evaluierung und Vergleich der Spielstärke verschiedener Agenten.
*   Sammeln von Spieldaten für das Training von Machine-Learning-Agenten.
*   Performance-Benchmarking.

### 62. Agenten (KI-gesteuerter Spieler)

#### 6.2.1 Basisklassen

*   `Player`: Definiert die Schnittstelle, die jeder Spieler (Mensch oder KI) implementieren muss (Methoden `schupf`, `announce`, `play`, `wish`, `choose_dragon_recipient`, `cleanup`).
*   `Agent`: Erbt von `Player` und dient als Basis für alle KI-Implementierungen.

#### 6.2.2 Agenten-Typen

*   **`RandomAgent`**: Wählt zufällige, aber regelkonforme Züge. Dient als Baseline und zum Testen.
*   **`RuleAgent`**: (Geplant/Konzept) Befolgt festgelegte Regeln.
*   **`HeuristicAgent`**: (Geplant/Konzept) Berechnet (exakte oder durch Erfahrungswerte geschätzte) Wahrscheinlichkeiten für die Entscheidungsfindung.
*   **`NNetAgent`**: Überbegriff für Agenten, die neuronale Netze verwenden.
    *   **`BehaviorAgent`**: (Konzept) Lernt durch überwachtes Lernen aus Log-Daten (von bettspielwelt.de), menschliche Spielweisen zu imitieren.
    *   **`AlphaZeroAgent`**: (Konzept) Verwendet Monte-Carlo Tree Search (MCTS) in Kombination mit neuronalen Netzen, um durch selbständiges Spielen das vortrainierte Netz von `BehaviorAgent` zu optimieren.

Während ein **regelbasierter Agent** feste Regeln befolgt und ein **heuristischer Agent** zusätzlich Wahrscheinlichkeiten 
einbezieht, lernt ein **NNetAgent** die Spielstrategie durch Trainingsdaten.

### 6.3 Implementierung

Die `Arena`-Klasse:
*   Nimmt eine Liste von 4 Agenten und eine maximale Anzahl von Spielen entgegen.
*   Kann Spiele parallel ausführen, indem `multiprocessing.Pool` genutzt wird, um die `GameEngine` für jedes Spiel in einem separaten Prozess zu starten. Dies beschleunigt die Simulation erheblich.
*   Sammelt Statistiken über die gespielten Partien (Siege, Niederlagen, Spieldauer, Anzahl Runden/Stiche).
*   Unterstützt "Early Stopping", um den Wettkampf zu beenden, wenn eine bestimmte Gewinnrate erreicht oder uneinholbar wird.

## 7. Server-Betrieb (zweite Ausbaustufe)

(in Entwicklung)

### 7.1 Query-Parameer der Websocket-URL

Ein zentraler Server stellt eine WebSocket bereit. Beim initialen Verbindungsaufbau gibt der Spieler den gewünschten Tisch und seinen Namen über die Query-Parameter an:

`?player_name=str&table_name=str`

Nach einem Reconnect teilt der Spieler statt dessen seine letzte Session-ID über die Query-Parameter mit:  

`?session_id=uuid`

#### 7.2.WebSocket-Nachrichten

Alle Nachrichten sind JSON-Objekte mit einem `type`-Feld und optional einem `payload`-Feld.

**Proaktive (d.h. unaufgeforderte) Nachrichten vom Client an den Server:**

Der WebSocket-Handler empfängt diese Nachrichten und leitet sie an die Game-Engine weiter. 
Ausnahme: Ein `ping` wird direkt vom WebSocket-Handler mit einem `pong` quittiert.

| Type             | Payload                                                                                 | Beschreibung                                                                              | Antwort vom Server (Type) | Antwort vom Server (Payload)                                                         |
|------------------|-----------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|---------------------------|--------------------------------------------------------------------------------------|
| `"leave"`        |                                                                                         | Der Spieler möchte den Tisch verlassen.                                                   | keine Antwort             |                                                                                      |
| `"lobby_action"` | `{action: "assign_team", "data": [player_new_index,...]}` oder `{action: "start_game"}` | Der Spieler führt eine Aktion in der Lobby aus (bildet die Teams oder startet das Spiel). | Keine Antwort             |                                                                                      |
| `"interrupt"`    | `{reason: "tichu"}` oder `{reason: "bomb", cards: str}`                                 | Der Spieler möchte außerhalb seines regulären Zuges Tichu ansagen oder eine Bombe werfen. | Keine Antwort             |                                                                                      |
| `"ping"`         | `{timestamp: "ISO8601_string"}`                                                         | Verbindungstest.                                                                          | `"pong"`                  | `{timestamp: ISO8601-str (aus der Ping-Anfrage)}`                                    |

**Proaktive Nachrichten vom Server an den Client:**

Die Engine sendet diese Nachrichten über den Peer an den Client. Bei der `request`-Nachricht wartet der Peer auf die `response`-Nachricht des Clients.
Erhält er sie, liefert der Peer die Daten als Antwort an die Engine aus. 

| Type                        | Payload                                                                                           | Beschreibung                                                                                                | Antwort vom Spieler (Type) | Antwort vom Spieler (Payload)                                        |
|-----------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|----------------------------|----------------------------------------------------------------------|
| `"request"`  (s. 7.2.1)     | `{request_id: uuid, action: str, public_state: PublicStateDict, private_state: PrivateStateDict}` | Der Server fordert den Spieler auf, eine Entscheidung zu treffen.                                           | `"response"`               | `{request_id: uuid (aus der Request-Nachrich), response_data: dict}` | 
| `"notification"` (s. 7.2.2) | `{event: str, context: dict (optional)}`                                                          | Broadcast an alle Spieler über ein Spielereignis.                                                           | keine Antwort              |                                                                      |
| `"error"` (s. 7.2.3)        | `{message: str, code: int, context: dict (optional)`                                              | Informiert den Spieler über einen Fehler.                                                                   | keine Antwort              |                                                                      |

**Anmerkung zur `request`-Nachricht:**
*   Der aktuelle Spielzustand sollte dem Spieler eigentlich bekannt sein, sofern er keine Nachrichten verpasst und entsprechend den Zustand angepasst hat.
    Sollte dies (warum auch immer) mal nicht der Fall sein, würde der Spieler, der sich auf seinen intern gespeicherten Zustand verlässt, u.U. eine ungültige Antwort liefern. 
    Eine Fehlerroutine müsste dann den intern gespeicherten Spielzustand mit dem aktuellen abgleichen. Wir vermeiden dieses Synchronisationsproblem ganz einfach, indem wir bei 
    jeder Anfrage stets den aktuellen Zustand mitsenden, so dass der Spieler sich abgleichen kann, bevor er antwortet. 
*   Keine der definierten Aktionen erfordert einen Kontext (ergänzende Informationen). Daher fällt `context` aus dem Payload raus. 
  
#### 7.2.1 Request-/Response-Nachrichten

| Request Action (vom Server) | Response Data (vom Client)                                         | Beschreibung                                                                                               |
|-----------------------------|--------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| "announce_grand_tichu"      | `{announced: bool}`                                                | Der Spieler wird gefragt, ob er ein großes Tichu ansagen will.                                             |
| "schupf"                    | `{to_opponent_right: str, to_partner: str, to_opponent_left: str}` | Der Spieler muss drei Karten zum Tausch abgeben. Diese Aktion kann durch ein Interrupt abgebrochen werden. |
| "play"                      | `{cards: str}` oder `{cards: ""}` (für passen)                     | Der Spieler muss Karten ausspielen oder passen. Diese Aktion kann durch ein Interrupt abgebrochen werden.  |
| "wish"                      | `{wish_value: int}`                                                | Der Spieler muss sich einen Kartenwert wünschen.                                                           |
| "give_dragon_away"          | `{player_index: int}`                                              | Der Spieler muss den Gegner benennen, der den Drachen bekommen soll.                                       |

Akzeptiert die Engine die Client-Antwort, sendet sie eine entsprechende [Notification-Nachricht](#722-notification-nachrichten) an alle Spieler.
Andernfalls sendet die Engine eine Fehlermeldung über den Peer an den Client.

**Anmerkung:**
Die Anfragen des Servers, ob der Spieler ein normales Tichu ansagen möchte, oder ob er eine Bombe werfen will, leitet der Peer nicht an den Client weiter, 
denn diese Entscheidungen trifft der Client proaktiv (im Gegensatz zur KI, die immer explizit gefragt wird).

#### 7.2.2 Notification-Nachrichten

Benachrichtigung an alle Spieler

| Notification Event      | Notification Context                                                                                                              | Beschreibung                                                                                |
|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| "player_joined"         | `{player_index: int, player_name: str}` (->) `{session_id: uuid, public_state: PublicStateDict, private_state: PrivateStateDict}` | Der Spieler spielt jetzt mit.                                                               |
| "player_left"           | `{player_index: int, replaced_by_name: str}`                                                                                      | Der Spieler hat das Spiel verlassen; eine KI ist eingesprungen.                             |
| "lobby_update"          | `{action: "assign_team", team: list}` oder `{action: "start_game"}`                                                               | Der Host (der erste reale Spieler am Tisch) hat das Team gebildet oder das Spiel gestartet. |
| "hand_cards_dealt"      | `{count: int}` -> `{hand_cards: str}`                                                                                             | Handkarten wurden an die Spieler verteilt.                                                  |
| "grand_tichu_announced" | `{player_index: int, announced: bool}`                                                                                            | Der Spieler hat ein großes Tichu angesagt oder abgelehnt.                                   |
| "tichu_announced"       | `{player_index: int}`                                                                                                             | Der Spieler hat ein normales Tichu angesagt.                                                |
| "player_schupfed"       | `{player_index: int}`                                                                                                             | Der Spieler hat drei Karten zum Tausch abgegeben.                                           |
| "schupf_cards_dealt"    | `None` -> `{received_schupf_cards: str}`                                                                                          | Die Tauschkarten wurden an die Spieler verteilt.                                            |
| "passed"                | `{player_index: int}`                                                                                                             | Der Spieler hat hat gepasst.                                                                |
| "played"                | `{player_index: int, cards: str}`                                                                                                 | Der Spieler hat Karten ausgespielt.                                                         |
| "bombed"                | `{player_index: int, cards: str}`                                                                                                 | Der Spieler hat eine Bombe geworfen.                                                        |
| "wish_made"             | `{wish_value: int}`                                                                                                               | Ein Kartenwert wurde sich gewünscht.                                                        |
| "wish_fulfilled"        |                                                                                                                                   | Der Wunsch wurde erfüllt.                                                                   |
| "trick_taken"           | `{player_index: int}`                                                                                                             | Der Spieler hat den Stich kassiert.                                                         |
| "player_turn_changed"   | `{current_turn_index: int}`                                                                                                       | Der Spieler ist jetzt am Zug.                                                               |
| "round_over"            | `{game_score: (list, list), is_double_victory: bool}`                                                                             | Die Runde ist vorbei und die Karten werden neu gemischt.                                    |
| "game_over"             | `{game_score: (list, list), is_double_victory: bool}`                                                                             | Die Runde ist vorbei und die Partie ist entschieden.                                        |

"->" bedeutet, dass der Peer den vom Server gesendeten Kontext mit privaten Informationen des Spielers anreichert, bevor er es an den Spieler weiterleitet.
Bei "player_joined" ändert der Peer den Kontext nur, wenn es sich um den eigenen Spieler handelt.

### 7.2.3. Fehlermeldungen

| Error Code                                  | Error Message                                              | Context (ergänzende Informationen)     |
|---------------------------------------------|------------------------------------------------------------|----------------------------------------|
| **Allgemeine Fehler (100-199)**             |                                                            |                                        |
| UNKNOWN_ERROR = 100                         | "Ein unbekannter Fehler ist aufgetreten."                  | `{exception: ExceptionClassName}`      |
| INVALID_MESSAGE = 101                       | "Ungültiges Nachrichtenformat empfangen."                  | `{message: dict}`                      |
| UNAUTHORIZED = 102                          | "Aktion nicht autorisiert."                                | `{action: str}`                        |
| SERVER_BUSY = 103                           | "Server ist momentan überlastet. Bitte später versuchen."  |                                        |
| SERVER_DOWN = 104                           | "Server wurde heruntergefahren."                           |                                        |
| MAINTENANCE_MODE = 105                      | "Server befindet sich im Wartungsmodus."                   |                                        |
| **Verbindungs- & Session-Fehler (200-299)** |                                                            |                                        |
| SESSION_EXPIRED = 200                       | "Deine Session ist abgelaufen. Bitte neu verbinden."       |                                        |
| SESSION_NOT_FOUND = 201                     | "Session nicht gefunden."                                  | `{session_id: uuid}`                   |
| TABLE_NOT_FOUND = 202                       | "Tisch nicht gefunden."                                    | `{table_name: str}`                    |
| TABLE_FULL = 203                            | "Tisch ist bereits voll."                                  | `{table_name: str}`                    |
| NAME_TAKEN = 204                            | "Dieser Spielername ist an diesem Tisch bereits vergeben." | `{table_name: str, player_name: str}`  |
| ALREADY_ON_TABLE = 205                      | "Du bist bereits an diesem Tisch."                         | `{table_name: str, player_index: int}` |
| **Spiellogik-Fehler (300-399)**             |                                                            |                                        |
| INVALID_ACTION = 300                        | "Ungültige Aktion."                                        | `{reason: str, request_id: uuid}`      |
| INVALID_CARDS = 301                         | "Ausgewählte Karten sind ungültig für diese Aktion."       | `{request_id: uuid}`                   |
| NOT_YOUR_TURN = 302                         | "Du bist nicht am Zug."                                    | `{request_id: uuid}`                   |
| INTERRUPT_DENIED = 303                      | "Interrupt-Anfrage abgelehnt."                             | `{reason: str, request_id: uuid}`      |
| INVALID_WISH = 304                          | "Ungültiger Kartenwunsch."                                 | `{request_id: uuid}`                   |
| INVALID_SCHUPF = 305                        | "Ungültige Karten für den Schupf-Vorgang."                 | `{request_id: uuid}`                   |
| ACTION_TIMEOUT = 306                        | "Zeit für Aktion abgelaufen."                              | `{timeout: seconds, request_id: uuid}` |
| **Lobby-Fehler (400-499)**                  |                                                            |                                        |
| GAME_ALREADY_STARTED = 400                  | "Das Spiel an diesem Tisch hat bereits begonnen."          | `{table_name: str}`                    |
| NOT_LOBBY_HOST = 401                        | "Nur der Host kann diese Aktion ausführen."                | `{action: str}`                        |

### 7.3 Aufgaben der Komponenten im Server-Betrieb

#### 7.3.1 WebSocket-Handler

*   Nimmt neue WebSocket-Verbindungen an:
    *   Der reale Spieler verbindet sich über eine WebSocket und gibt seinen Namen und den Namen eines Tisches an.
    *   Gibt es den Tisch noch nicht, wird dieser Tisch eröffnet (über die `Game-Factory`). 
    *   Ist der Tisch voll besetzt (max. 4 reale Spieler), kann der Spieler sich nicht an den Tisch setzen. 
    *   Ist noch mind. ein Platz frei (d.h. der Platz ist belegt von einer KI), kann der Spieler sich an den Platz setzen (ersetzt die KI) und erhält den aktuellen Spielzustand.
*   Reagiert darauf, wenn der Spieler das Spiel verlassen will: 
    *   Wenn der reale Spieler geht, übernimmt automatisch die KI wieder den Platz, damit die übrigen Spieler weiterspielen können. 
    *   Hat der letzte Client den Tisch verlassen, wird der Tisch geschlossen (über die `Game-Factory`).
*   Händelt Verbindungsabbrüche:  
    *   Bei einem Verbindungsabbruch wartet der Server 20 Sekunden, bevor die KI den Platz einnimmt. 
    *   Sollte der Client sich wiederverbinden (er versucht es automatisch jede Sekunde), nimmt er den alten Platz wieder ein (sofern nicht in der Zwischenzeit ein anderer Client den Platz eingenommen hat) und erhält den aktuellen Spielzustand.
*   Empfangt Nachrichten vom Client:
    *   Leitet reguläre Spielaktionen (Antworten auf Requests) an den zugehörigen Peer weiter.
    *   Leitet Interrupt-Anfragen (`"interrupt"`) direkt an die zuständige `GameEngine` weiter.
    *   Verarbeitet Meta-Nachrichten (Join, Leave, Ping, Lobby-Aktionen).

#### 7.3.2 Game-Factory

*   Verwaltet eine Sammlung aktiver Spieltische (`GameEngine`-Instanzen).
*   Erstellt eine neue `GameEngine` für einen neuen Tisch.
*   Schließt Tische, wenn keine realen Spieler mehr verbunden sind (nach Timeout).

#### 7.3.3 Game-Engine

*   Bildet die Kern-Spiellogik ab.
*   Interagiert mit den Spielern (unterscheidet idealerweise nicht zw. `Agent` und `Peer`).
*   Reagiert auf Interrupt-Anfragen der Spieler.

#### 7.3.4 Peer

*   Serverseitiger WebSocket-Endpunkt des Clients (ein realer Spieler, der z.B. über einen Browser interagiert, könnte aber auch ein Bot sein); erbt von `Player`.
*   Empfängt Aufforderungen von der `GameEngine` (z.B. `play()`, `announce()`).
*   Formatiert diese Aufforderungen als `request`-Nachricht und sendet sie über den WebSocket an den realen Spieler.
*   Wartet auf eine `response`-Nachricht vom realen Spieler.
*   Validiert die Antwort und gibt die extrahierte Aktion an die `GameEngine` zurück.
*   Empfängt Benachrichtigungen (`notification`) von der `GameEngine` und leitet diese an den realen Spieler weiter.

## 8. Frontend (zweite Ausbaustufe)

(Geplant)

### 8.1 Allgemeine Funktionsweise
1) Das Frontend für den Server-Betrieb soll als reine Webanwendung mit HTML, CSS und JavaScript umgesetzt werden. Eine frühere Godot-basierte UI-Entwicklung wird nicht weiterverfolgt, kann aber als visuelle Vorlage dienen.
2) Es kommuniziert über WebSockets mit dem Python-Backend. 
3) Mit Verbindungsaufbau über die WebSocket sendet der reale Spieler als Query-Parameter in der URL den Tisch-Namen und seinen Namen mit. 
4) Beim Wiederaufbau nach Verbindungsabbruch sendet der Spieler stattdessen die letzte Session-Id.
5) Wenn der reale Spieler das Spiel verlassen will, kündigt er dies an, damit der Server nicht erst noch 20 Sekunden wartet, bis er durch eine KI ersetzt wird.
6) Der erste reale Spieler am Tisch darf die Sitzplätze der Mitspieler bestimmen, bevor er das Spiel startet. Normalerweise wird er warten, bis seine Freunde auch am Tisch sitzen, und dann sagen, wer mit wem ein Team bildet. Das findet in der Lobby statt.
7) Wenn die Runde beendet ist, und die Partie noch nicht entschieden ist, leitet der Server automatisch eine neue Runde ein.
8) Wenn die Partie beendet ist, werden die Spiele wieder zur Lobby gebracht.  

# Anhang 

## A1. Entwicklungsumgebung

### A1.1 Systemanforderungen

*   **Entwicklung:** Windows 11, Python >= 3.11.
*   **Produktivbetrieb (geplant):** Raspberry Pi 5 (Bookworm OS), Python >= 3.11.

### A1.2 Einrichtung

1.  Python 3.11 (oder neuer) installieren.
2.  **Repository klonen:**
    ```bash
    git clone https://github.com/frohlfing/tichu
    cd tichu
    ```
3.  Virtuelle Umgebung erstellen und aktivieren:
    ```bash
    python -m venv .venv
    # Für Linux/macOS:
    source .venv/bin/activate
    # Für Windows (CMD):
    .venv\Scripts\activate.bat
    # Für Windows (PowerShell):
    .venv\Scripts\Activate.ps1
    ```
4.  Abhängigkeiten installieren:
    ```bash
    pip pip install -r requirements.txt
    ```
5.  **Arena starten:**
    ```bash
    python main.py
    ```
    **Server starten:**
    ```bash
    python server.py
    ```
    **WebSocket-Client zum Testen starten:**
    ```bash
    python wsclient.py
    ```
6.  `requirements.txt` aktualisieren:
    ```bash
    pip freeze
    ```

### A1.3 Testing

*   Unit-Tests werden mit `pytest` geschrieben und befinden sich im `tests/`-Verzeichnis.
    *   Ausführen der Tests: `python -m pytest`.
    *   Ausführen mit Coverage: `cov.ps1`
*   Die Codeabdeckung der Tests wird mit `coverage` gemessen, Konfiguration in `.coveragerc`.
    *   Ausführen: `cov.ps1`

## A2. Exceptions

| Error                    | Beschreibung                                                                                                                      |
|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| PlayerInteractionError-  | Basisklasse für Fehler, die während der Interaktion mit einem Spieler auftreten können.                                           |
| ClientDisconnectedError- | Wird ausgelöst, wenn versucht wird, eine Aktion mit einem Client auszuführen, der nicht (mehr) verbunden ist.                     |
| PlayerInterruptError -   | Wird ausgelöst, wenn eine wartende Spieleraktion durch ein Engine-internes Ereignis (z.B. Tichu-Ansage, Bombe) unterbrochen wird. |
| PlayerTimeoutError -     | Wird ausgelöst, wenn ein Spieler nicht innerhalb des vorgegebenen Zeitlimits auf eine Anfrage reagiert hat.                       |
| PlayerResponseError-     | Wird ausgelöst, wenn ein Spieler eine ungültige, unerwartete oder nicht zum Kontext passende Antwort auf eine Anfrage sendet.     |

## A3. Versionsnummer

Die Versionsnummer wird gemäß dem [Semantic Versioning-Schema](https://semver.org/) vergeben.

Das bedeutet, wir erhöhen bei gegebener Versionsnummer MAJOR.MINOR.PATCH die:
- MAJOR-Version, wenn wir inkompatible API-Änderungen vornehmen
- MINOR-Version, wenn wir Funktionen abwärtskompatibel hinzufügen
- PATCH-Version, wenn wir abwärtskompatible Fehlerbehebungen vornehmen

### A3.1. Release auf Github erstellen

- Schritt 1: Tag erstellen (falls noch nicht geschehen)
```bash
git tag -a v0.3.0 -m "Version 0.3.0 Release"
git push origin v0.3.0
git push --tags
```
- Schritt 2: Offizielles Release auf GitHub anlegen
  - Gehe zu GitHub und öffne dein Repository.
  - Klicke oben auf "Releases" / "Draft a new release" / v0.3.0
  - Beschreibung für das Release eingeben (Änderungen, Features, Bugfixes etc.)
  - Auf "Publish release" klicken.

## A4. Styleguide

Der Code folgt den offiziellen Python-Styleguide-Essay [PEP 8](https://peps.python.org/pep-0008/) und Docstring-Konventionen [PEP 257](https://peps.python.org/pep-0257/).

### A4.1 Docstrings

Das Format für die Docstrings ist `reStructuredText`.

*   Jedes Modul (py-Datei) hat eine kurze Datei-Header-Beschreibung (ein oder zwei Sätze, die beschreiben, was das Modul definiert).
    *   Öffentliche Variablen und Konstanten des Moduls werden mit `:??? <name>: <Beschreibung>` beschrieben.  TODO: Wie ist das Schlüsselwort hierfür? Wird für `config.py` benötigt!
*   Jede Klasse hat eine kurze Beschreibung (ein oder zwei Sätze, was die Klasse repräsentiert bzw. tut). 
    *   Öffentliche Instanzvariablen werden mit `:ivar <name>: <Beschreibung>` aufgelistet.
    *   Öffentliche Klassenkonstanten werden mit `:cvar <name>: <Beschreibung>` aufgelistet.
*   Jede Funktion/Klassenmethode hat eine Überschrift und optional eine ergänzende Beschreibung. 
    * Die Parameter werden mit `:param <name>: <Beschreibung>` aufgelistet. Optionale Parameter werden mit `:param <name>: (Optional) <Beschreibung>` gekennzeichnet.  
    * Der Rückgabewert wird mit `:result: <Beschreibung>` dokumentiert. Rückgabe `None` wird nicht erwähnt.
    * Mögliche Exceptions werden mit `:raises <ErrorClass> <Beschreibung>` aufgelistet.

### A4.2 Namenskonvention

| Type                                     | Schreibweise   |
|------------------------------------------|----------------|
| **Package** (Verzeichnis mit py-Dateien) | `snake_case`   |
| **Modul** (py-Datei)                     | `snake_case`   |
| **Klasse**                               | `PascalCase`   |
| **Funktion** / **Klassenmethode**        | `snake_case()` |
| **Variable** / **Parameter**             | `snake_case()` |
| **Konstante**                            | `UPPER_CASE`   |

Interne Funktionen und Variablen werden mit einem führenden Unterstrich gekennzeichnet.

### A4.3 Type-Hints

Es werden ausgiebig Type-Hints verwendet, insbesondere bei der Funktion-Signatur und bei Klassenvariablen.

## A5. Glossar

*   **Spieler und Teams**: Die Spieler werden gegen den Uhrzeigersinn mit 0 beginnend durchnummeriert. Spieler 0 und 2 bildet das Team 20 sowie Spieler 1 und 3 das Team 31. Ein Spieler hat 3 Mitspieler. Der Mitspieler gegenüber ist der Partner, die beiden anderen Mitspieler sind rechter und linker Gegner.
*   **Spielzug (turn)**: Ein Spieler spielt eine Kartenkombination aus oder passt.
*   **Stich (trick)**: Eine Serie von Spielzügen, bis die Karten vom Tisch genommen werden. Jeder Spieler spielt nacheinander Karten aus oder passt. Der Spieler, der zuletzt Karten abgelegt hat, ist der Besitzer des Stichs. Schaut ein Spieler, der am Zug ist, wieder auf seine zuvor ausgespielten Karten (weil alle Mitspieler gepasst haben), hat er den Stich gewonnen. Der Besitzer wird zum Gewinner des Stichs. Der Stich wird geschlossen, indem er vom Tisch abgeräumt wird. Solange kein Gewinner des Stichs feststeht, ist der Stich offen.
*   **Runde (round)**: Karten austeilen und spielen, bis der Gewinner feststeht. Eine Runde besteht aus mehreren Stichen, bis der Gewinner feststeht und Punkte vergeben werden.
*   **Partie (game)**: Runden spielen, bis ein Team mindestens 1000 Punkte hat. Eine Partie besteht aus mehreren Runden und endet, wenn ein Team mindestens 1000 Punkte erreicht hat.
*   **Öffentlicher Spielzustand/Beobachtungsraum (public state)**: Alle Informationen über die Partie, die für alle Spieler sichtbar sind.
*   **Privater Spielzustand (private state)**: Die verborgenen Informationen über die Partie, die nur der jeweilige Spieler kennt.
*   **Beobachtungsraum (Observation Space)**: (Public + Private State), die Sitzplatznummern sind relativ zum Spieler angegeben (0 == dieser Spieler, 1 == rechter Gegner, 2 == Partner, 3 == linker Gegner). Wird primär für KI-Agenten verwendet.
*   **Index in kanonischer Form (Canonical Index)**: Nummerierung der Spieler (0-3) so, wie der Server/die GameEngine die Spielerliste intern pflegt.
*   **Relativer Index**: Nummerierung der Spieler (0-3) aus der Perspektive eines bestimmten Spielers.
*   **Karte (Card)**: Kombination aus Kartenwert (`value`) und Farbe (`suit`).
*   **Kombination (Combination)**: Die Merkmale Typ (`CombinationType`), Länge und Rang einer Kartenzusammenstellung.
*   **Partition**: Aufteilung der (Hand-)Karten in eine Sequenz von gültigen Kombinationen.
*   **Historie (tricks)**: Beinhaltet alle Infos des Spielverlaufs (Stiche mit ihren Spielzügen) zur Rekonstruktion.
*   **Anspielen (first lead)**: Als Erster Karten in einen neuen Stich legen.
*   **Initiative**: Das Recht zum Anspielen erlangen.
*   **Rating**: Numerische Bewertung der Spielstärke eines Agenten.
*   **Ranking**: Platzierung eines Spielers in einer Rangliste.
*   **Spicken (cheat)**: (Als Feature für ausgeschiedene Spieler) In die Handkarten der Mitspieler schauen. 
 