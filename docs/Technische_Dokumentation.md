# Technische Projektdokumentation: Tichu Webanwendung

**Datum:** 26. Mai 2024
**Version:** 0.2.0 (Entwurfsphase Live-Betrieb)
**Autor:** [Frank Rohlfing]

**Inhaltsverzeichnis**

1.  [Einleitung und Projektziele](#1-einleitung-und-projektziele)
2.  [Systemarchitektur](#2-systemarchitektur)
    1.  [Betriebsarten](#21-betriebsarten)
    2.  [Kernkomponenten](#22-kernkomponenten)
    3.  [Technologie-Stack (aktuell)](#23-technologie-stack-aktuell)
3.  [Spiellogik und Regeln](#3-spiellogik-und-regeln)
    1.  [Regelwerk](#31-regelwerk)
    2.  [Wichtige Spielphasen und Ablauf einer Partie](#32-wichtige-spielphasen-und-ablauf-einer-partie)
    3.  [Ausnahmeregeln und Spezialkarten (Phönix)](#33-ausnahmeregeln-und-spezialkarten-phönix)
4.  [Modulübersicht und Code-Struktur](#4-modulübersicht-und-code-struktur)
    1.  [`src/` Verzeichnis](#41-src-verzeichnis)
        1.  [`src/lib/`](#411-srclib)
        2.  [`src/players/`](#412-srcplayers)
        3.  [`src/common/`](#413-srccommon)
        4.  [Weitere Kernmodule (`game_engine.py`, `public_state.py` etc.)](#414-weitere-kernmodule)
    2.  [`tests/` Verzeichnis](#42-tests-verzeichnis)
    3.  [Startskripte (`main.py`)](#43-startskripte-mainpy)
5.  [Datenstrukturen](#5-datenstrukturen)
    1.  [`PublicState`](#51-publicstate)
    2.  [`PrivateState`](#52-privatestate)
    3.  [Kartenrepräsentation (`Card`, `Cards`)](#53-kartenrepräsentation-card-cards)
    4.  [Kombinationen (`Combination`)](#54-kombinationen-combination)
6.  [Arena-Betrieb](#6-arena-betrieb)
    1.  [Zweck](#61-zweck)
    2.  [Implementierung (`arena.py`)](#62-implementierung-arenapy)
7.  [Live-Betrieb (Spiel mit realen Spielern) - In Entwicklung](#7-live-betrieb-spiel-mit-realen-spielern---in-entwicklung)
    1.  [Grundkonzept](#71-grundkonzept)
    2.  [WebSocket-Kommunikation](#72-websocket-kommunikation)
        1. [Nachrichtenformat](#721-nachrichtenformat)
        2. [Request-/Response-Nachrichten](#722-request-response-nachrichten)
        3. [Notification-Nachrichten](#723-notification-nachrichten)
        4. [Error-Nachrichten](#724-error-nachrichten) 
    3.  [Verantwortlichkeiten der Komponenten im Live-Betrieb](#73-verantwortlichkeiten-der-komponenten-im-live-betrieb)
        1.  [WebSocket-Handler](#731-websocket-handler)
        2.  [Game-Factory](#732-game-factory)
        3.  [Game-Engine (Server-Modus)](#733-game-engine-server-modus)
        4.  [Client (serverseitiger WebSocket-Endpunkt des realen Spielers)](#734-client-serverseitiger-websocket-endpunkt-des-realen-Spielers)
8.  [Agenten (KI-gesteuerter Spieler)](#8-agenten-ki-gesteuerter-spieler)
    1.  [Basisklassen (`Player`, `Agent`)](#81-basisklassen-player-agent)
    2.  [Implementierte und geplante Agenten-Typen](#82-implementierte-und-geplante-agenten-typen)
9.  [Entwicklungsumgebung und Deployment](#9-entwicklungsumgebung-und-deployment)
    1.  [Systemanforderungen](#91-systemanforderungen)
    2.  [Einrichtung](#92-einrichtung)
    3.  [Testing](#93-testing)
10. [Frontend (Geplant)](#10-frontend-geplant)
11. [Versionsnummer](#11-versionsnummer)
12. [Glossar](#12-glossar)

---

## 1. Einleitung und Projektziele

Dieses Dokument beschreibt die technische Implementierung einer Webanwendung für das Kartenspiel "Tichu". Ziel des Projekts ist es, eine Plattform zu schaffen, auf der sowohl KI-gesteuerte Agenten als auch menschliche Spieler gegeneinander Tichu spielen können.

Das Projekt umfasst zwei Hauptbetriebsarten:
*   Eine **Arena** für schnelle Simulationen zwischen Agenten, optimiert für Forschungs- und Entwicklungszwecke (z.B. Training von KI-Agenten).
*   Einen **Live-Betrieb**, der menschlichen Spielern via WebSockets ermöglicht, gegen Agenten oder andere menschliche Spieler anzutreten.

## 2. Systemarchitektur

### 2.1 Betriebsarten

1.  **Arena-Modus:** Dient dem schnellen Durchspielen vieler Partien zwischen KI-Agenten. Der Fokus liegt hier auf Performance und Datenerfassung. Dieser Teil ist weitgehend implementiert.
2.  **Server-/Live-Modus:** Ermöglicht menschlichen Spielern die Teilnahme an Spielen über eine WebSocket-Schnittstelle. KI-Agenten können freie Plätze einnehmen oder als Gegner dienen. Dieser Teil befindet sich aktiv in der Entwicklung.

### 2.2 Kernkomponenten

Die Hauptkomponenten des Systems sind modular aufgebaut, um eine Wiederverwendung der Spiellogik in beiden Betriebsarten zu ermöglichen:

*   **Spiellogik-Kern (`GameEngine`, Karten- und Kombinationsbibliotheken):** Enthält die Regeln des Tichu-Spiels, die Validierung von Zügen und die Verwaltung des Spielzustands.
*   **Spieler-Abstraktion (`Player`, `Agent`, `Client`):** Definiert eine einheitliche Schnittstelle für alle Arten von Spielern (Mensch oder KI).
    *   `Player`: Abstrakte Basisklasse.
    *   `Agent`: Basisklasse für KI-gesteuerte Spieler.
    *   `Client`: Repräsentiert den serverseitigen Endpunkt einer WebSocket-Verbindung zu einem menschlichen Spieler.
*   **Zustandsverwaltung (`PublicState`, `PrivateState`):** Datenklassen zur Kapselung des öffentlichen und privaten Spielzustands.
*   **Arena (`Arena`):** Orchestriert Spiele zwischen Agenten im Arena-Modus.
*   **WebSocket-Server & Handler (für Live-Modus):** Verwalten Verbindungen zu menschlichen Spielern, empfangen deren Aktionen und senden Spiel-Events. (In Entwicklung)
*   **Game-Factory (für Live-Modus):** Verantwortlich für die Erstellung und Verwaltung von `GameEngine`-Instanzen für verschiedene Spieltische. (In Entwicklung)

### 2.3 Technologie-Stack (aktuell)

*   **Programmiersprache:** Python (Version 3.11 oder höher)
*   **Kernbibliotheken (Python Standard Library):** `asyncio`, `dataclasses`, `multiprocessing`.
*   **Testing:** `pytest`, `pytest-mock`, `coverage`.
*   **WebSocket-Server: (im Aufbau)** `aiohttp`.
*   **Frontend (geplant):** HTML, CSS, JavaScript.

## 3. Spiellogik und Regeln

### 3.1 Regelwerk

Die detaillierten Spielregeln für Tichu sind hier zu finden:
[Tichu Regeln und Anleitung](https://cardgames.wiki/de/blog/tichu-spielen-regeln-und-anleitung-einfach-erklaert)

Die Implementierung versucht, diese Regeln so genau wie möglich abzubilden.

### 3.2 Wichtige Spielphasen und Ablauf einer Partie

1.  **Lobby & Spielstart:** Der erste reale Spieler am Tisch darf die Sitzplätze der Mitspieler bestimmen, bevor er das Spiel startet (normalerweise wird er warten, bis seine Freunde auch am Tisch sitzen und dann sagen, wer mit wem ein Team bildet.) Das findet in der Lobby statt.
2.  **Kartenausgabe (Initial):** Der Server verteilt je 8 Karten an jeden Spieler.
3.  **Grand Tichu Ansage:** Jeder Spieler muss sich dann entscheiden, ob er Grand Tichu ansagen möchte oder nicht (passt).
4.  **Kartenausgabe (Restlich):** Sobald jeder Spieler sich entschieden hat, teilt der Server die restlichen Karten aus (je 6 pro Spieler, insgesamt 14).
5.  **Kleines Tichu Ansage (vor Schupfen):** Solange noch kein Spieler Karten zum Tausch (Schupfen) abgegeben hat, kann der Spieler ein Tichu ansagen. Dazu muss er vorab ein Interrupt auslösen.
6.  **Schupfen:** Die Spieler müssen nun 3 Karten zum Tauschen abgeben (verdeckt, je eine pro Mitspieler).
7.  **Kartenaufnahme nach Schupfen:** Sobald alle Spieler die Karten zum Tauschen abgegeben haben, sendet der Server an jeden Spieler jeweils die getauschten Karten, die für ihn bestimmt sind.
8.  **Spielphase (Kombinationen legen):**
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

### 3.3 Ausnahmeregeln und Spezialkarten (Phönix)

*   **Kein Vierling:** Es gibt kein Vierling, daher ist ein Drilling mit Phönix nicht möglich.
*   **Full House Restriktion:** Ein Fullhouse darf nicht aus einer 4er-Bombe mit Phönix gebildet werden (Drilling und Pärchen dürfen nicht den gleichen Rang haben).
*   **Wunscherfüllung:** Der Wunsch muss zwar erfüllt werden, wenn man am Zug ist (sofern möglich), aber nicht in dem Moment, wenn man eine Bombe wirft.
*   **Phönix:**
    *   **Phönix als Karte:** Der Kartenwert des Phönix ist 16 (höchster Wert im Spiel, liegt über dem Drachen).
    *   **Phönix als Einzelkarte (Kombination):** Die Kombination "Phönix als Einzelkarte" hat den Rang 14.5 (schlägt das Ass, aber nicht den Drachen).
    *   **Phönix im Stich:** Sticht der Phönix eine Einzelkarte, so ist sein Rang im Stich 0.5 höher die gestochene Karte. Im Anspiel (erste Karte im Stich) hat der Phönix den Rang 1.5.

## 4. Modulübersicht und Code-Struktur

Das Projekt ist in Hauptverzeichnisse `src/` (Quellcode) und `tests/` (Unit-Tests) unterteilt.

### 4.1 `src/` Verzeichnis

#### 4.1.1 `src/lib/`
Enthält Kernbibliotheken für die Spiellogik, die relativ eigenständig sind:
*   `cards.py`: Definition von Karten, dem Deck, Punktwerten und Hilfsfunktionen zur Kartenmanipulation (Parsen, Stringify, Vektorisierung).
*   `combinations.py`: Definition von Kombinationstypen, Logik zur Erkennung (`get_figure`), Generierung (`build_combinations`) und Validierung von Kartenkombinationen. Enthält auch Logik zur Erstellung des gültigen Aktionsraums (`build_action_space`).
*   `partitions.py`: (Falls vorhanden und relevant für Agenten) Logik zur Aufteilung von Handkarten in mögliche Sequenzen von Kombinationen.

#### 4.1.2 `src/players/`
Definition der verschiedenen Spieler-Typen:
*   `player.py`: Abstrakte Basisklasse `Player` mit der Grundschnittstelle für alle Spieler.
*   `agent.py`: Abstrakte Basisklasse `Agent`, erbt von `Player`, für KI-gesteuerte Spieler.
*   `random_agent.py`: Konkrete Implementierung eines Agenten, der zufällige, gültige Züge macht.
*   `heuristic_agent.py`: (Implementiert oder Geplant) Agent, der auf Heuristiken basiert.
*   `client.py`: (Für Live-Betrieb) Klasse, die einen menschlichen Spieler repräsentiert und die WebSocket-Kommunikation auf Serverseite abwickelt.

#### 4.1.3 `src/common/`
Allgemeine Hilfsmodule:
*   `logger.py`: Konfiguration des Logging-Frameworks, inklusive farbiger Konsolenausgabe.
*   `rand.py`: Benutzerdefinierte Zufallsgenerator-Klasse, optimiert für potenzielle Multiprocessing-Szenarien (verzögerte Initialisierung des Seeds pro Instanz).
*   `config.py`: (Implizit vorhanden) Konfigurationsvariablen für das Projekt (z.B. Loglevel, Arena-Einstellungen).
*   `errors.py`: Definition anwendungsspezifischer Exception-Klassen.
*   `git_utils.py`: Hilfsfunktionen zur Interaktion mit Git (z.B. Ermittlung des aktuellen Tags/Version).

#### 4.1.4 Weitere Kernmodule
*   `public_state.py`: Definition der `PublicState`-Datenklasse, die alle öffentlich sichtbaren Informationen eines Spiels enthält.
*   `private_state.py`: Definition der `PrivateState`-Datenklasse, die die privaten Informationen eines Spielers (Handkarten etc.) enthält.
*   `game_engine.py`: Die `GameEngine`-Klasse, die die Hauptspiellogik für einen Tisch steuert, Runden abwickelt und mit den `Player`-Instanzen interagiert.
*   `arena.py`: Die `Arena`-Klasse für den Arena-Betrieb, führt mehrere Spiele parallel oder sequenziell aus und sammelt Statistiken.

### 4.2 `tests/` Verzeichnis
Enthält Unit-Tests für die Module in `src/`, geschrieben mit `pytest`. Die Struktur spiegelt grob die `src/`-Struktur wider (z.B. `test_cards.py`, `test_game_engine.py`).

### 4.3 Startskripte (`main.py`)
*   `main.py`: Dient als Haupteinstiegspunkt für den Start des Arena-Betriebs. Konfiguriert Agenten und startet die `Arena`.
*   `server.py`: Startet den Server für den Live-Betrieb. 
*   `wsclient.py`: Startet einen interaktiven WebSocket-Client lediglich für Testzwecke. 

## 5. Datenstrukturen

### 5.1 `PublicState`
Eine `dataclass`, die alle Informationen enthält, die allen Spielern an einem Tisch bekannt sind. Dazu gehören u.a.:
*   Namen der Spieler, aktueller Spieler am Zug (`current_turn_index`), Startspieler der Runde (`start_player_index`).
*   Anzahl der Handkarten jedes Spielers (`count_hand_cards`).
*   Alle bereits gespielten Karten der Runde (`played_cards`).
*   Tichu-Ansagen (`announcements`), geäußerte Wünsche (`wish_value`).
*   Informationen über den aktuellen Stich: gelegte Karten (`trick_cards`), Typ der Kombination (`trick_combination`), Besitzer des Stichs (`trick_owner_index`), Punkte im Stich (`trick_points`).
*   Die `tricks`-Historie (eine Liste von Stichen, wobei jeder Stich `Trick` eine Liste von Spielzügen `Turn` ist; `Turn = Tuple[player_index, cards_played, combination_details]`).
*   Aktuelle Punktestände der Runde (`points`) und der gesamten Partie (`game_score`).
*   Statusinformationen (z.B. `is_round_over`, `double_victory`, `current_phase`).

### 5.2 `PrivateState`
Eine `dataclass`, die Informationen enthält, die nur dem jeweiligen Spieler bekannt sind:
*   Der Index des Spielers (`player_index`).
*   Die eigenen Handkarten (`_hand_cards`, zugreifbar über `@property hand_cards`).
*   Die Karten, die man beim Schupfen abgegeben (`given_schupf_cards`) und erhalten (`received_schupf_cards`) hat (Format: `List[Optional[Card]]` der Länge 4).
*   Caches für mögliche Kombinationen (`_combination_cache`) und Partitionen (`_partition_cache`) der Handkarten zur Performanceoptimierung.

### 5.3 Kartenrepräsentation (`Card`, `Cards`)
*   `Card`: Ein Tupel `(value: int, suit: int)`.
    *   `value`: 0 (Dog), 1 (Mah Jong), 2 bis 10, 11 (Jack/Bube), 12 (Queen/Dame), 13 (King/König), 14 (Ace/As), 15 (Dragon/Drache), 16 (Phoenix/Phönix).
    *   `suit`: 0 (Sonderkarte), 1 (Schwert/Schwarz), 2 (Pagode/Blau), 3 (Jade/Grün), 4 (Stern/Rot).
*   `Cards`: Eine Liste von `Card`-Tupeln (`List[Card]`).

### 5.4 Kombinationen (`Combination`)
*   `Combination`: Ein Tupel `(type: CombinationType, length: int, rank: int)`.
    *   `CombinationType`: Ein `IntEnum` für den Typ (z.B. `CombinationType.SINGLE`, `CombinationType.PAIR`, `CombinationType.STREET`, `CombinationType.BOMB`).
    *   `length`: Anzahl der Karten in der Kombination.
    *   `rank`: Der bestimmende Rang der Kombination (z.B. höchster Wert bei einer Straße, der Wert des Drillings bei einem Full House, Wert der Einzelkarte).

## 6. Arena-Betrieb

### 6.1 Zweck
Der Arena-Betrieb (`arena.py` gestartet über `main.py`) dient dazu, KI-Agenten in einer großen Anzahl von Spielen gegeneinander antreten zu lassen. Dies ist nützlich für:
*   Testen der Stabilität der `GameEngine`.
*   Evaluierung und Vergleich der Spielstärke verschiedener Agenten.
*   Sammeln von Spieldaten für das Training von Machine-Learning-Agenten.
*   Performance-Benchmarking.

### 6.2 Implementierung (`arena.py`)
Die `Arena`-Klasse:
*   Nimmt eine Liste von 4 Agenten und eine maximale Anzahl von Spielen entgegen.
*   Kann Spiele parallel ausführen, indem `multiprocessing.Pool` genutzt wird, um die `GameEngine` für jedes Spiel in einem separaten Prozess zu starten. Dies beschleunigt die Simulation erheblich.
*   Sammelt Statistiken über die gespielten Partien (Siege, Niederlagen, Spieldauer, Anzahl Runden/Stiche).
*   Unterstützt "Early Stopping", um den Wettkampf zu beenden, wenn eine bestimmte Gewinnrate erreicht oder uneinholbar wird.

## 7. Live-Betrieb (Spiel mit realen Spielern) - In Entwicklung

### 7.1 Grundkonzept

Ein zentraler Server stellt eine WebSocket bereit. Menschliche Spieler verbinden sich über diese Websocket mit dem Server. 

### 7.2 WebSocket-Kommunikation

1) Grundsätzlich sendet der Client (serverseitigen Endpunkt) jedes Ereignis inkl. Spielzustand über alle aktiven Websocket-Verbindungen, damit der reale Spieler auf dem aktuellen Stand bleiben können. Das ist für Agenten nicht notwendig, da sie bei einer Entscheidung direkt auf den aktuellen Spielzustand zugreifen können.
2) Mit Verbindungsaufbau über die WebSocket sendet der reale Spieler direkt den Tisch-Namen mit. 
3) Wenn der reale Spieler das Spiel verlassen will, kündigt er dies an, damit der Server nicht erst noch 20 Sekunden wartet, bis er durch eine KI ersetzt wird.
4) Der erste reale Spieler am Tisch darf die Sitzplätze der Mitspieler bestimmen, bevor er das Spiel startet (normalerweise wird er warten, bis seine Freunde auch am Tisch sitzen und dann sagen, wer mit wem ein Team bildet.) Das findet in der Lobby statt.
5) Wenn die Runde beendet ist, und die Partie noch nicht entschieden ist, leitet der Server automatisch eine neue Runde ein.
6) Wenn die Partie beendet ist, werden die Spiele wieder zur Lobby gebracht.  

#### 7.2.1 Nachrichtenformat

Alle Nachrichten sind JSON-Objekte mit einem `type`-Feld und optional einem `payload`-Feld.

**Proaktive Nachrichten vom Spieler an den Server:**

| Typ            | Payload                                                                                     | Beschreibung                                                                              | Antwort vom Server                                                                                                         |
|----------------|---------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------|
| `join`         | `{"table_name": "str", "player_name": "str"}` oder `{"session_id": "str"}` (für Reconnect)  | Der Spieler möchte einem Tisch beitreten oder bei Reconnect.                              | `type: "joined_confirmation", payload: {session_id: str, public_state: PublicStateDict, private_state: PrivateStateDict}`  |
| `leave`        | `{}`                                                                                        | Spieler möchte den Tisch verlassen.                                                       | keine Antwort                                                                                                              |
| `ping`         | `{"timestamp": "ISO8601_string"}`                                                           | Verbindungstest.                                                                          | `type: "pong", payload: {timestamp: ISO8601-str (aus der Ping-Anfrage)}`                                                   |
| `interrupt`    | `{"reason": "tichu"` oder `"bomb"}`                                                         | Der Spieler möchte außerhalb seines regulären Zuges Tichu ansagen oder eine Bombe werfen. | Keine Antwort                                                                                                              |
| `lobby_action` | `{"action": "assign_team", "data": [player_new_index,...]}` oder `{"action": "start_game"}` | Spieler führt eine Aktion in der Lobby aus (bildet die Teams oder startet das Spiel).     | Keine Antwort                                                                                                              |

**Proaktive Nachrichten vom Server an den Spieler:**

| Type                      | Payload                                                                                                                                                  | Beschreibung                                                                                                | Antwort vom Spieler                                                                                                             |
|---------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------|
| `request`  (s. 7.2.3)     | `{request_id: uuid_str, action: str, public_state: PublicStateDict, private_state: PrivateStateDict, context: {(aktionsspezifisch, z.B. action_space)}}` | Server fordert den Spieler auf, eine Entscheidung zu treffen. Der volle Spielzustand ist Teil der Anfrage.  | `type: "response", payload: {request_id: uuid_str (aus der Request-Anfrage), data: dict (vom Spieler getroffene Entscheidung)}` | 
| `notification` (s. 7.2.4) | `{event: str, data: { ereignisspezifische Daten }}`                                                                                                      | Broadcast an alle Spieler über ein Spielereignis.                                                           | keine Antwort                                                                                                                   |
| `deal_cards`              | `{hand_cards: str}`                                                                                                                                      | Eine neue Runde hat begonnen und der jeweilige Spieler hat seine Handkarten bekommen (erst 8 dann alle 14). | keine Antwort                                                                                                                   |
| `schupf_cards_received`   | `{from_opponent_right: str, from_partner: str, from_opponent_left: str}`                                                                                 | Die Tauschkarten wurden an den jeweiligen Spieler abgegeben.                                                | keine Antwort                                                                                                                   |
| `error`                   | `{message: str, code: int, details: {} (optional), original_request_id: str (optional)}`                                                                 | Informiert den Spieler über einen Fehler.                                                                   | keine Antwort                                                                                                                   |

#### 7.2.2 Request-/Response-Nachrichten

| Request Action (vom Server) | Response Data (vom Spieler)                                         | Beschreibung                                                         |
|-----------------------------|---------------------------------------------------------------------|----------------------------------------------------------------------|
| "schupf"                    | `{to_opponent_right: str, to_partner: str, to_opponent_left: str}`  | Der Spieler muss 3 Karten zum Tausch abgeben.                        |
| "announce"                  | `{announced: bool}`                                                 | Der Spieler wird gefragt, ob er ein Tichu ansagen will.              |
| "play"                      | `{cards: str}` oder  `{cards: ""}` (für passen)                     | Der Spieler muss Karten ausspielen oder passen.                      |
| "wish"                      | `{wish_value: int}`                                                 | Der Spieler muss sich einen Kartenwert wünschen.                     |
| "give_dragon_away"          | `{player_index: int}`                                               | Der Spieler muss den Gegner benennen, der den Drachen bekommen soll. |

#### 7.2.3 Notification-Nachrichten

Broadcast-Nachricht an alle Spieler

| Event                   | Event Data                                                          | Beschreibung                                                    |
|-------------------------|---------------------------------------------------------------------|-----------------------------------------------------------------|
| "player_joined"         | `{player_index: int, player_index: str}`                            | Der Spieler spielt jetzt mit.                                   |
| "player_left"           | `{player_index: int, replaced_by_name: str}`                        | Der Spieler hat das Spiel verlassen; eine KI ist eingesprungen. |
| "interrupt_processed"   | `{player_index: int, reason: "tichu"` oder `"bomb"}`                | Der Spieler hat Halt gerufen. (Dies wurde akzeptiert.)          |
| "lobby_update"          | `{action: "assign_team", team: list}` oder `{action: "start_game"}` | Der Spieler hat das Team gebildet oder das Spiel gestartet.     |
| "schupfed_by_player"    | `{player_index: int}`                                               | Der Spieler hat 3 Karten zum Tausch abgegeben.                  |
| "tichu_announced"       | `{player_index: int, announced: bool}`                              | Der Spieler hat Tichu angesagt oder abgelehnt.                  |
| "played"                | `{player_index: int, cards: str}`                                   | Der Spieler hat Karten ausgespielt oder hat gepasst.            |
| "wish_made"             | `{player_index: int, wish_value: int}`                              | Der Spieler hat sich einen Kartenwert gewünscht.                |
| "trick_taken"           | `{player_index: int}`                                               | Der Spieler hat den Stich kassiert.                             |
| "player_turn_changed"   | `{current_turn_index: int}`                                         | Der Spieler ist jetzt am Zug.                                   |
| "round_over"            | `{game_score: (list, list), is_double_victory: bool}`               | Die Runde ist vorbei und die Karten werden neu gemischt.        |
| "game_over"             | `{game_score: (list, list), is_double_victory: bool}`               | Die Runde ist vorbei und die Partie ist entschieden.            |

#### 7.2.4 Error-Nachrichten

Entwurf

| Code                                          |                      | Message (Beispiel)                                         | Details (Beispiel)                                                | Wann gesendet?                                                                                          |
|-----------------------------------------------|----------------------|------------------------------------------------------------|-------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **Allgemeine Fehler (1000-1999)**             |                      |                                                            |                                                                   |                                                                                                         |
| 1000                                          | UNKNOWN_ERROR        | "Ein unbekannter Fehler ist aufgetreten."                  | `{ "exception_type": "RuntimeError" }`                            | Serverseitiger Catch-All.                                                                               |
| 1001                                          | INVALID_MESSAGE      | "Ungültiges Nachrichtenformat empfangen."                  | `{ "received_message": "{...}" }`                                 | Client sendet kein valides JSON oder erwartete Struktur fehlt.                                          |
| 1002                                          | UNAUTHORIZED         | "Aktion nicht autorisiert."                                |                                                                   | Client versucht etwas ohne passende Rechte (z.B. Lobby-Aktion ohne Host zu sein).                       |
| 1003                                          | SERVER_BUSY          | "Server ist momentan überlastet. Bitte später versuchen."  |                                                                   | Falls der Server temporär keine neuen Anfragen/Verbindungen annehmen kann.                              |
| 1004                                          | MAINTENANCE_MODE     | "Server befindet sich im Wartungsmodus."                   |                                                                   | Bei geplanten Wartungsarbeiten.                                                                         |
| **Verbindungs- & Session-Fehler (2000-2999)** |                      |                                                            |                                                                   |                                                                                                         |
| 2000                                          | SESSION_EXPIRED      | "Deine Session ist abgelaufen. Bitte neu verbinden."       |                                                                   | Session-ID ist nicht mehr gültig.                                                                       |
| 2001                                          | SESSION_NOT_FOUND    | "Session nicht gefunden."                                  | `{ "session_id": "xyz" }`                                         | Client versucht Reconnect mit ungültiger Session.                                                       |
| 2002                                          | TABLE_NOT_FOUND      | "Tisch nicht gefunden."                                    | `{ "table_name": "Tisch1" }`                                      | Client will Tisch beitreten, der nicht existiert.                                                       |
| 2003                                          | TABLE_FULL           | "Tisch ist bereits voll."                                  | `{ "table_name": "Tisch1" }`                                      | Client will vollem Tisch beitreten.                                                                     |
| 2004                                          | NAME_TAKEN           | "Dieser Spielername ist an diesem Tisch bereits vergeben." | `{ "player_name": "Anton" }`                                      | Client wählt Namen, der schon am Tisch ist.                                                             |
| 2005                                          | ALREADY_ON_TABLE     | "Du bist bereits an diesem Tisch."                         | `{ "player_index": 1 }`                                           | Client versucht, Tisch beizutreten, an dem seine Session schon aktiv ist.                               |
| **Spiellogik-Fehler (3000-3999)**             |                      |                                                            |                                                                   |                                                                                                         |
| 3000                                          | INVALID_ACTION       | "Ungültige Aktion."                                        | `{ "action_attempted": "play_cards", "reason": "Not your turn" }` | Client versucht Aktion, die nicht erlaubt ist (z.B. nicht am Zug, ungültige Karten).                    |
| 3001                                          | INVALID_CARDS        | "Ausgewählte Karten sind ungültig für diese Aktion."       | `{ "cards": ["S2", "S2"], "action": "play_combination" }`         | Client sendet ungültige Kartenauswahl in einer `response`.                                              |
| 3002                                          | NOT_YOUR_TURN        | "Du bist nicht am Zug."                                    |                                                                   | Client sendet `response` oder , obwohl nicht am Zug (oder Interrupt nicht passend). `interrupt_request` |
| 3003                                          | INTERRUPT_DENIED     | "Interrupt-Anfrage abgelehnt."                             | `{ "reason": "tichu", "denial_reason": "Already announced" }`     | wurde vom Server abgelehnt. `interrupt_request`                                                         |
| 3004                                          | INVALID_WISH         | "Ungültiger Kartenwunsch."                                 | `{ "wish_value": 1 }`                                             | Client wünscht sich einen ungültigen Wert.                                                              |
| 3005                                          | INVALID_SCHUPF       | "Ungültige Karten für den Schupf-Vorgang."                 | `{ "schupf_cards": "..." }`                                       | Client sendet ungültige Karten beim Schupfen.                                                           |
| 3006                                          | ACTION_TIMEOUT       | "Zeit für Aktion abgelaufen."                              | `{ "action_requested": "play_combination" }`                      | Falls serverseitige Timeouts für Spieleraktionen implementiert werden.                                  |
| **Lobby-Fehler (4000-4999)**                  |                      |                                                            |                                                                   |                                                                                                         |
| 4000                                          | GAME_ALREADY_STARTED | "Das Spiel an diesem Tisch hat bereits begonnen."          |                                                                   | Client versucht Lobby-Aktion, obwohl Spiel läuft.                                                       |
| 4001                                          | NOT_LOBBY_HOST       | "Nur der Host kann diese Aktion ausführen."                | `{ "action": "start_game" }`                                      | Falls ein Host-Konzept in der Lobby existiert.                                                          |

### 7.3 Verantwortlichkeiten der Komponenten im Live-Betrieb

#### 7.3.1 WebSocket-Handler
*   Nimmt neue WebSocket-Verbindungen an:
    *   Der reale Spieler verbindet sich über eine WebSocket und gibt seinen Namen und den Namen eines Tisches an.
    *   Gibt es den Tisch noch nicht, wird dieser Tisch eröffnet (über die `Game-Factory`). 
    *   Ist der Tisch voll besetzt (max. 4 reale Spieler), kann der Spieler sich nicht an den Tisch setzen. 
    *   Ist noch mind. ein Platz fei (d.h. der Platz ist belegt von einer KI), kann der Spieler sich an den Platz setzen (ersetzt die KI) und erhält den aktuellen Spielzustand.
*   Reagiert darauf, wenn der Spieler das Spiel verlassen will: 
    *   Wenn der reale Spieler geht, übernimmt automatisch die KI wieder den Platz, damit die übrigen Spieler weiterspielen können. 
    *   Ist der letzte reale Spieler vom Tisch aufgestanden, wird der Tisch geschlossen (über die `Game-Factory`).
*   Händelt Verbindungsabbrüche:  
    *   Bei einem Verbindungsabbruch wartet der Server 20 Sekunden, bevor die KI den Platz einnimmt. 
    *   Sollte der Spieler sich wiederverbinden (er versucht es automatisch jede Sekunden), nimmt er den alten Platz wieder ein (sofern nicht in der zwischenzeit ein anderer reale Spieler sich dort hingesetzt hat) und erhält den aktuellen Spielzustand.
*   Empfängt Nachrichten von realen Spielern:
    *   Leitet reguläre Spielaktionen (Antworten auf Requests) an die `Client`-Instanz des Spielers weiter.
    *   Leitet Interrupt-Anfragen (`"interrupt"`) direkt an die zuständige `GameEngine` weiter.
    *   Verarbeitet Meta-Nachrichten (Join, Leave, Ping, Lobby-Aktionen).

#### 7.3.2 Game-Factory
*   Verwaltet eine Sammlung aktiver Spieltische (`GameEngine`-Instanzen).
*   Erstellt eine neue `GameEngine` für einen neuen Tisch.
*   Schließt Tische, wenn keine realen Spieler mehr verbunden sind (nach Timeout).

#### 7.3.3 Game-Engine (Server-Modus)
*   Bildet die Kern-Spiellogik ab.
*   Interagiert über die `Player`-Schnittstelle mit Agenten und realen Spieler (unterscheidet aber nicht zw. `Agent` und `Client`).
*   Muss auf Interrupt-Anfragen der Spieler reagieren können.
*   Übermittelt dem Spieler, der keine Handkarten mehr hat, zusätzlich die Handkarten der Mitspieler.

#### 7.3.4 Client (serverseitiger WebSocket-Endpunkt des realen Spielers)
*   Erbt von `Player`.
*   Kapselt die WebSocket-Verbindung zu einem einzelnen realen Spieler.
*   Empfängt Aufforderungen von der `GameEngine` (z.B. `play()`, `announce()`).
*   Formatiert diese Aufforderungen als `request`-Nachricht und sendet sie über den WebSocket an den realen Spieler.
*   Wartet auf eine `response`-Nachricht vom realen Spieler.
*   Validiert die Antwort und gibt die extrahierte Aktion an die `GameEngine` zurück.
*   Empfängt Benachrichtigungen (`state_update`, `notification` von der Engine) und leitet diese an den realen Spieler weiter.
*   Einzige proaktive Aktion (außerhalb einer direkten Antwort auf eine Engine-Anfrage) ist das Senden eines "Interrupts" an die Engine.

## 8. Agenten (KI-gesteuerter Spieler)

### 8.1 Basisklassen (`Player`, `Agent`)
*   `Player`: Definiert die Schnittstelle, die jeder Spieler (Mensch oder KI) implementieren muss (Methoden `schupf`, `announce`, `play`, `wish`, `choose_dragon_recipient`, `cleanup`).
*   `Agent`: Erbt von `Player` und dient als Basis für alle KI-Implementierungen.

### 8.2 Implementierte und geplante Agenten-Typen
*   **`RandomAgent`**: Wählt zufällige, aber regelkonforme Züge. Dient als Baseline und zum Testen.
*   **`RuleAgent`**: (Geplant/Konzept) Befolgt festgelegte Regeln.
*   **`HeuristicAgent`**: (Geplant/Konzept) Berechnet (exakte oder durch Erfahrungswerte geschätzte) Wahrscheinlichkeiten für die Entscheidungsfindung.
*   **`NNetAgent`**: Überbegriff für Agenten, die Neuronale Netze verwenden.
    *   **`BehaviorAgent`**: (Konzept) Lernt durch überwachtes Lernen aus Log-Daten (von bettspielwelt.de), menschliche Spielweisen zu imitieren.
    *   **`AlphaZeroAgent`**: (Konzept) Verwendet Monte-Carlo Tree Search (MCTS) in Kombination mit neuronalen Netzen, um durch selbständiges Spielen das vortrainierte Netz von `BehaviorAgent` zu optimieren.

Während ein **regelbasierter Agent** feste Regeln befolgt und ein **heuristischer Agent** zusätzlich Wahrscheinlichkeiten 
einbezieht, lernt ein **NNetAgent** die Spielstrategie durch Trainingsdaten.

## 9. Entwicklungsumgebung und Deployment

### 9.1 Systemanforderungen
*   **Entwicklung:** Windows 11, Python >= 3.11.
*   **Produktivbetrieb (geplant):** Raspberry Pi 5 (Bookworm OS), Python >= 3.11.

### 9.2 Einrichtung
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

### 9.3 Testing
*   Unit-Tests werden mit `pytest` geschrieben und befinden sich im `tests/`-Verzeichnis.
    *   Ausführen der Tests: `python -m pytest`.
    *   Ausführen mit Coverage: `cov.ps1`
*   Die Codeabdeckung der Tests wird mit `coverage` gemessen, Konfiguration in `.coveragerc`.
    *   Ausführen: `cov.ps1`

## 10. Frontend (Geplant)

Das Frontend für den Live-Betrieb soll als reine Webanwendung mit HTML, CSS und JavaScript umgesetzt werden. Es kommuniziert über WebSockets mit dem Python-Backend. Eine frühere Godot-basierte UI-Entwicklung wird nicht weiterverfolgt, kann aber als visuelle Vorlage dienen.

## 11. Versionsnummer

Die Versionsnummer wird gemäß dem [Semantic Versioning-Schema](https://semver.org/) vergeben.

Das bedeutet, wir erhöhen bei gegebener Versionsnummer MAJOR.MINOR.PATCH die:
- MAJOR-Version, wenn wir inkompatible API-Änderungen vornehmen
- MINOR-Version, wenn wir Funktionen abwärtskompatibel hinzufügen
- PATCH-Version, wenn wir abwärtskompatible Fehlerbehebungen vornehmen

### 11.1 Release in Github erstellen

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

## 12. Glossar

*   **Spieler und Teams**: Die Spieler werden gegen den Uhrzeigersinn mit 0 beginnend durchnummeriert. Spieler 0 und 2 bildet das Team 20 sowie Spieler 1 und 3 das Team 31. Ein Spieler hat 3 Mitspieler. Der Mitspieler gegenüber ist der Partner, die beiden anderen Mitspieler sind rechter und linker Gegner.
*   **Spielzug (turn)**: Ein Spieler spielt eine Kartenkombination aus oder passt.
*   **Stich (trick)**: Eine Serie von Spielzügen, bis die Karten vom Tisch genommen werden. Jeder Spieler spielt nacheinander Karten aus oder passt. Der Spieler, der zuletzt Karten abgelegt hat, ist der Besitzer des Stichs. Schaut ein Spieler, der am Zug ist, wieder auf seine zuvor ausgespielten Karten (weil alle Mitspieler gepasst haben), hat er den Stich gewonnen. Der Besitzer wird zum Gewinner des Stichs. Der Stich wird geschlossen, indem er vom Tisch abgeräumt wird. Solange kein Gewinner des Stichs feststeht, ist der Stich offen.
*   **Runde (round)**: Karten austeilen und spielen, bis Gewinner feststeht. Eine Runde besteht aus mehreren Stichen, bis der Gewinner feststeht und Punkte vergeben werden.
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
*   **Anspielen (first lead)**: Als Erster Karten in einem neuen Stich legen.
*   **Initiative**: Das Recht zum Anspielen erlangen.
*   **Rating**: Numerische Bewertung der Spielstärke eines Agenten.
*   **Ranking**: Platzierung eines Spielers in einer Rangliste.
*   **Spicken (cheat)**: (Als Feature für ausgeschiedene Spieler) In die Handkarten der Mitspieler schauen. 
 