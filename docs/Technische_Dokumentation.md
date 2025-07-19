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

5. [Daten, Konstanten, Typen](#5-daten-konstanten-typen) TODO zur ersten Ausbaustufe packen
    1.  [Datenklassen](#51-datenklassen)
    2.  [Karte](#52-karte)
    3.  [Kombination](#53-kombination)
    4.  [Spielphasen](#54-spielphasen)

6.  [Arena-Betrieb (erste Ausbaustufe)](#6-arena-betrieb-erste-ausbaustufe)
    1.  [Zweck](#61-zweck)
    2.  [Agenten (KI-gesteuerter Spieler)](#62-agenten-ki-gesteuerter-spieler)
    3.  [Implementierung](#63-implementierung)

7.  [Server-Betrieb (zweite Ausbaustufe)](#7-server-betrieb-zweite-ausbaustufe)
    1.  [Query-Parameter der WebSocket-URL](#71-query-parameter-der-websocket-url)
    2.  [WebSocket-Nachrichten](#72websocket-nachrichten)
    3.  [Verantwortlichkeiten der Komponenten im Live-Betrieb](#73-aufgaben-der-komponenten-im-server-betrieb)
        
8. [Frontend (zweite Ausbaustufe)](#8-frontend-zweite-ausbaustufe)
   1.  [Allgemeine Funktionsbeschreibung](#81-funktionsbeschreibung)
   2.  [Module](#82-module)
   3.  [Verzeichnisstruktur](#83-verzeichnisstruktur)
   4.  [Viewport](#84-viewport)
   5.  [Ressourcen](#85-ressourcen)

**ANHANG**

A1.  [Entwicklungsumgebung](#a1-entwicklungsumgebung)
    1.  [Systemanforderungen](#a11-systemanforderungen)
    2.  [Einrichtung](#a12-einrichtung)
    3.  [Testing](#a13-testing)

A2. [Exceptions](#a2-exceptions)

A3. [Versionsnummer](#a3-versionsnummer)
    1. [Release auf Github erstellen](#a31-release-auf-github-erstellen)
    
A4. [Styleguide](#a4-styleguide)
    1. [Code-Dokumentation](#a41-code-dokumentation)
    2. [Namenskonvention](#a42-namenskonvention)
    3. [Type-Hints](#a43-type-hints)
    
A4. [Glossar](#a5-glossar)

---

## 1. Projektziele

Dieses Dokument beschreibt die technische Implementierung einer Webanwendung für das Kartenspiel "Tichu". Ziel des Projekts ist es, eine Plattform zu schaffen, auf der sowohl KI-gesteuerte Agenten als auch menschliche Spieler gegeneinander Tichu spielen können.

Das Projekt umfasst zwei Hauptbetriebsarten:
*   Eine **Arena** für schnelle Simulationen zwischen Agenten optimiert. Für Forschungs- und Entwicklungszwecke (z.B. Training von KI-Agenten).
*   Ein **Live-Betrieb**, der menschlichen Spielern via WebSockets ermöglicht, gegen Agenten oder andere menschliche Spieler anzutreten.

## 2. Regelwerk

### 2.1 Spielregeln

Die detaillierten Spielregeln für Tichu sind hier zu finden:
[Tichu Regeln und Anleitung](https://cardgames.wiki/de/blog/tichu-spielen-regeln-und-anleitung-einfach-erklaert)

### 2.2 Ablauf einer Partie

1.  **Lobby & Spielstart:** Der erste Client am Tisch darf die Sitzplätze der Mitspieler bestimmen, bevor er das Spiel startet. Normalerweise wird er warten, bis seine Freunde auch am Tisch sitzen, und dann sagen, wer mit wem ein Team bildet. Das findet in der Lobby statt.
2.  **Kartenausgabe (Initial):** Der Server verteilt je 8 Karten an jeden Spieler.
3.  **Großes Tichu ansagen:** Jeder Spieler muss sich dann entscheiden, ob er ein großes Tichu ansagen möchte oder nicht.
4.  **Kartenausgabe (restliche):** Sobald jeder Spieler sich entschieden hat, teilt der Server die restlichen Karten aus (je 6 pro Spieler, insgesamt 14).
5.  **Schupfen:** Die Spieler müssen nun drei Karten zum Tauschen abgeben (verdeckt, je eine pro Mitspieler). Falls während dessen jemand ein Tichu ansagt, nehmen alle Spieler ihre Karten zurück und geben erneut eine Tauschkarte ab. 
6.  **Tauschkarte aufnehmen:** Sobald alle Spieler die Karten zum Tauschen abgegeben haben, werden diese an die adressierten Spieler verteilt.
7.  **Karten ausspielen:**
    *   Ab jetzt kann der Spieler jederzeit ein einfaches Tichu ansagen, solange er noch keine Kombination ausgespielt hat. 
    *   Ab jetzt kann der Spieler jederzeit (auch wenn er nicht am Zug ist) eine Bombe werfen - es sei denn, ein Mitspieler hat das Anspielrecht. Wer eine Bombe wirft, erhält sofort das Zugrecht. 
    *   Der Spieler mit dem MahJong muss als Erstes eine Kartenkombination ablegen.
    *   Wird der MahJong gespielt, muss der Spieler, der den Mahjong ausgelegt hat, einen Kartenwert wünschen. Dieser Wunsch muss erfüllt werden, sobald die Regeln es zulassen.
    *   Wird der Hund gespielt, bekommt der Partner das Zugrecht.
    *   Der nächste Spieler wird aufgefordert, Karten abzulegen oder zu Passen.
    *   Dies wird wiederholt, bis alle Mitspieler hintereinander gepasst haben, sodass der Spieler, der die letzten Karten gespielt hat, wieder an der Reihe ist.
8.  **Stich kassieren:** Dieser Spieler darf die Karten kassieren. Falls der Stich mit dem Drachen gewonnen wurde, muss der Spieler den Stich an einen der Gegner verschenken.
9. **Spieler scheidet aus:** Wenn ein Spieler keine Handkarten mehr hat, kann er in die Karten der (noch aktiven) Mitspieler schauen (die Karten sind für ihn nicht mehr verdeckt).
10. **Runden-Ende:** Die Runde endet, wenn nur noch ein Spieler Karten hat oder ein Doppelsieg erzielt wird. Punkte werden vergeben. Wenn die Partie noch nicht entschieden ist (kein Team hat 1000 Punkte erreicht), startet eine neue Runde ein (beginnend bei Punkt 2: Kartenausgabe).
11. **Partie-Ende:** Wenn die Partie entschieden ist, wird die Punktetabelle angezeigt. Danach geht es zurück in die Lobby (Punkt 1).

Zusatzregeln und Unterschiede zum offiziellen Regelwerk:

* Laut offiziellem Regelwerk kann ein einfaches Tichu schon vor und während des Schupfens angesagt werden. 
  Fairerweise müssen dann aber alle Spieler die Möglichkeit haben, ihre Schupfkarten noch einmal zu wählen. 
  Aber das ist offiziell nicht geregelt und auch lästig für alle. Daher die Regel: Einfaches Tichu erst nach dem Schupfen.    
* Laut offiziellem Regelwerk KANN ein Wunsch geäußert werden, nicht, nicht MUSS. So ist es derzeit aber nicht umgesetzt. 
* Der Hund bleibt liegen und wird erst mit dem nachfolgenden Stich abgeräumt.
* Um auch beim **Phönix als Einzelkarte** ganzzahlige Ränge zu haben, wird gerundet (ist für das Spiel egal):   
    *   Vor dem Ausspielen ist der Rang 15 (schlägt das Ass, aber nicht den Drachen). 
    *   Nach dem Ausspielen ist der Rang wie die gestochene Karte. Im Anspiel (erste Karte im Stich) hat der Phönix den Rang 1.

### 2.3 Sonderfälle

Diese Punkte stammen aus dem offiziellen Regelwerk:

*   **Kein Vierling:** Es gibt keinen Vierling, daher ist ein Drilling mit Phönix nicht möglich.
*   **Full House Restriktion:** Ein Fullhouse darf nicht aus einer 4er-Bombe mit Phönix gebildet werden (Drilling und Pärchen dürfen nicht den gleichen Rang haben).
*   **Wunscherfüllung:** Der Wunsch muss zwar erfüllt werden, wenn man am Zug ist (sofern möglich), aber nicht in dem Moment, wenn man eine Bombe wirft. 
*   **Phönix als Einzelkarte**: 
    *   Vor dem Ausspielen ist der Rang 14.5 (schlägt das Ass, aber nicht den Drachen). 
    *   Nach dem Ausspielen ist der Rang 0.5 höher als die gestochene Karte. Im Anspiel (erste Karte im Stich) hat der Phönix den Rang 1.5.

## 3. Systemarchitektur

### 3.1 Technologie-Stack

*   **Programmiersprache:** Python (Version 3.11 oder höher)
*   **Kernbibliotheken (Python Standard Library):** `asyncio`, `dataclasses`, `multiprocessing`.
*   **Testing:** `pytest`, `coverage`.
*   **Server:** `aiohttp`.
*   **Frontend:** HTML, CSS, Vanilla-JavaScript.

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

# Verzeichnisstruktur

Diese Struktur trennt klar zwischen:

- Skripten zur Ausführung (bin/)
- Generierten Daten (data/)
- Dokumentation (docs/)
- Proof of Concept (poc/)
- Quellcode (src/)
- Tests (tests/)
- Frontend (web/)

<pre>
└── tichu/
    ├── .idea
    ├── .venv
    ├── bin/                        # ausführbare Skripte und Dateien
    │   ├── bw_download.py          # Lädt Tichu-Logdateien von Brettspielwelt herunter
    │   ├── bw_import.py            # Importiert die Logdateien von Brettspielwelt in eine Sqlite-DB
    │   ├── cov.ps1                 # führt eine Code-Coverage-Analyse durch
    │   ├── run_arena.py            # Startet die `Arena` mit 4 Agenten
    │   ├── serve.py                # Startet den Server für den Live-Betrieb
    │   └── wsclient.py             # Startet einen WebSocket-Client für Testzwecke
    ├── data/                       # alle generierten Daten (von Git ignoriert!)
    │   ├── bw/                     # Daten von Brettspielwelt
    │   │   ├── tichulog
    │   │   │   ├── 2007.zip
    │   │   │   └── 2022.zip
    │   │   └── Logs_runterladen.ipynb
    │   ├── cov/                    # Coverage-Daten
    │   │   ├── htmlcov/
    │   │   │   └── index.html
    │   │   ├── .coverage
    │   │   └── coverage.xml
    │   ├── db/                     # Datenbanken
    │   │   └── tichu.sqlite
    │   ├── logs/                   # Logdateien
    │   │   ├── app.log
    │   │   └── app.log.2025-07
    │   ├── models/                 # Trainierte Modelle, Caches, Tabellen
    │   ├── prob                    # Hilfstabellen für das `src/lib/prob`-Pakage
    │   │   └── bomb04_hi.pkl.gz
    │   │   └── triple_lo.pkl.gz
    │   └── reports/
    ├── docs/
    │   ├── assets.py               # statische Assets (z.B. Bilder) für die Dokumentation
    │   │   └── coverage.svg
    │   ├── .gitkeep
    │   ├── benchmark.txt
    │   ├── Technische_Dokumentation.md
    │   ├── Tichu_Pocket_Regeln.md
    │   ├── Todos.md
    │   └── Zustandsänderung bei Ereignis.xlsx
    ├── poc/                        # Enthält Proof-of-Concept-Skripte
    │   ├── arena_sync/
    │   │   └── main.py
    │   ├── benchmark.py
    │   ├── poc_interrupt.py
    │   └── poc_pickling.py
    ├── src/                         # Top-Level Python-Package
    │   ├── common/                  # allgemeine Bibliotheken
    │   │   ├── git_utils.py         # Hilfsfunktionen zur Interaktion mit Git
    │   │   ├── logger.py            # Logger-Klasse
    │   │   └── rand.py              # Zufallsgenerator-Klasse
    │   ├── lib/                     # projektspezifische Bibliotheken
    │   │   ├── prob/                # Bibliothek zum Berechnen von Wahrscheinlichkeiten und Statistiken
    │   │   │   ├── prob_hi.py
    │   │   │   ├── prob_lo.py
    │   │   │   ├── statistic.py
    │   │   │   ├── tables_hi.py
    │   │   │   └── tables_lo.py
    │   │   ├── cards.py             # Definition von Karten, dem Deck, Punktwerten und Hilfsfunktionen zur Kartenmanipulation
    │   │   ├── combinations.py      # Definition von Kombinationstypen, Logik zur Erkennung, Generierung und Validierung von Kartenkombinationen
    │   │   ├── errors.py            # Definition anwendungsspezifischer Exception-Klassen
    │   │   └── partitions.py        # Logik zur Aufteilung von Handkarten in mögliche Sequenzen von Kombinationen
    │   ├── players/                 # Spieler-Typen
    │   │   ├── player.py            # Abstrakte Basisklasse `Player` mit der Grundschnittstelle für alle Spieler
    │   │   ├── agent.py             # Abstrakte Basisklasse `Agent`, erbt von `Player`, für KI-gesteuerte Spieler
    │   │   ├── heuristic_agent.py   # Agent, der auf Heuristiken basiert
    │   │   ├── peer.py              # Klasse, die den serverseitigen Endpunkt der WebSocket-Verbindung zu einem verbundenen Client repräsentiert
    │   │   └── random_agent.py      # Konkrete Implementierung eines Agenten, der zufällige, gültige Züge macht
    │   ├── __init__.py
    │   ├── arena.py                 # `Arena`-Klasse für den Arena-Betrieb (führt mehrere Spiele parallel oder sequenziell aus und sammelt Statistiken)
    │   ├── server.py                # Webserver und WebSocket-Server für den Live-Betrieb 
    │   ├── config.py                # Konfigurationsvariablen für das Projekt (z.B. Loglevel, Arena-Einstellungen).
    │   ├── game_engine.py           # `GameEngine`-Klasse, die die Hauptspiellogik für einen Tisch steuert
    │   ├── game_factory.py
    │   ├── private_state.py         #  öffentlichen Spielzustand
    │   └── public_state.py          # privaten Spielzustand eines Spielers 
    ├── tests/                       # Unit-Tests für die Module in `src/`, geschrieben mit `pytest` 
    │   ├── common/                 
    │   │   ├── test_git_utils.py    
    │   │   ├── test_logger.py       
    │   │   └── test_rand.py         
    │   ├── lib/                     
    │   │   ├── test_cards.py        
    │   │   └── test_combinations.py 
    │   ├── players/
    │   │   ├── test_agent.py
    │   │   ├── test_player.py
    │   │   └── test_random_agent.py
    │   ├── prob/
    │   │   ├── test_prob_hi.py
    │   │   └── test_prob_lo.py
    │   ├── src/
    │   │   ├── test_arena.py
    │   │   ├── test_game_engine.py
    │   │   ├── test_private_state.py
    │   │   └── test_public_state.py
    │   └── conftest.py
    ├── web/                        # Frontend
    │   ├── css/
    │   │   ├── animation.css
    │   │   ├── common.css
    │   │   ├── loading-view.css
    │   │   ├── lobby-view.css
    │   │   ├── login-view.css
    │   │   ├── modal.css
    │   │   ├── table-view.css
    │   │   └── test.css
    │   ├── fonts/
    │   │   └── architect-s-daughter/
    │   │       ├── Architects Daughter SIL OFL Font License.txt
    │   │       ├── ArchitectsDaughter.ttf
    │   │       ├── ArchitectsDaughter.ttf.import
    │   │       └── ArchitectsDaughter32.tres
    │   ├── images/
    │   │   ├── background.png/
    │   │   ├── bomb-icon.png
    │   │   ├── grand-tichu-icon.png
    │   │   ├── icon.png
    │   │   ├── logo.png
    │   │   ├── spinner.png
    │   │   ├── table-texture.png
    │   │   ├── tichu-icon.png
    │   │   └── wish-icon.png
    │   ├── js/
    │   │   └── views/
    │   │   │   ├── loading-view.js
    │   │   │   ├── lobby-view.js
    │   │   │   ├── login-view.js
    │   │   │   └── table-view.js
    │   │   ├── animation.js
    │   │   ├── app-controller.js
    │   │   ├── bot.js
    │   │   ├── config.js
    │   │   ├── event-bus.js
    │   │   ├── lib.js
    │   │   ├── main.js
    │   │   ├── modal.js
    │   │   ├── network.js
    │   │   ├── random.js
    │   │   ├── sound.js
    │   │   ├── state.js
    │   │   ├── test-runner.js
    │   │   ├── tests.js
    │   │   ├── user.js
    │   │   └── view-manager.js
    │   └── sounds/
    │   │   ├── announce.ogg
    │   │   ├── bomb.ogg
    │   │   ├── play0.ogg
    │   │   ├── play1.ogg
    │   │   ├── play2.ogg
    │   │   ├── play3.ogg
    │   │   ├── schupf.ogg
    │   │   ├── score.ogg
    │   │   ├── select.ogg
    │   │   ├── shuffle.ogg
    │   │   └── take.ogg
    │   ├── index.html
    │   └── tests.html
    ├── .env                        # Umgebungsvariablen für sensible  oder serverabhängige Daten. Wird nicht im Git-Repo abgelegt.
    ├── .env.example                # Diese Datei wird im Git-Repo abgelegt und dient als Vorlage für die .env-Datei.
    ├── .gitignore               
    ├── LICENSE
    ├── pyproject.toml              # Projekt-Setup
    ├── pytest.ini
    └── README.md
</pre>

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

Die Phasen dürfen sich nicht überlappen.
Es sollen hier auch die Bedingungen dokumentiert werden, wann welche Phase aktiv ist (in Abhängigkeit des Spielzustandes).

(siehe hierzu [Ablauf einer Partie](#22-ablauf-einer-partie))

Die Spielphasen des Servers unterscheiden sich von den Spielphasen des Clients. Beim Client laufen z.B. Animationen, Dialoge werden angezeigt, usw.

Die Spielphasen des Servers werden nur bei der Validierung im Peer benötigt. 

## 6. Arena-Betrieb (erste Ausbaustufe)

### 6.1 Zweck

Der Arena-Betrieb (`arena.py` gestartet über `bin/run_arena.py`) dient dazu, KI-Agenten in einer großen Anzahl von Spielen gegeneinander antreten zu lassen. Dies ist nützlich für:
*   Testen der Stabilität der `GameEngine`.
*   Evaluierung und Vergleich der Spielstärke verschiedener Agenten.
*   Sammeln von Spieldaten für das Training von Machine-Learning-Agenten.
*   Performance-Benchmarking.

### 6.2 Agenten (KI-gesteuerter Spieler)

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

#### 6.2.3 Zu treffende Entscheidungen

TODO

### 6.3 Implementierung

Die `Arena`-Klasse:
*   Nimmt eine Liste von 4 Agenten und eine maximale Anzahl von Spielen entgegen.
*   Kann Spiele parallel ausführen, indem `multiprocessing.Pool` genutzt wird, um die `GameEngine` für jedes Spiel in einem separaten Prozess zu starten. Dies beschleunigt die Simulation erheblich.
*   Sammelt Statistiken über die gespielten Partien (Siege, Niederlagen, Spieldauer, Anzahl Runden/Stiche).
*   Unterstützt "Early Stopping", um den Wettkampf zu beenden, wenn eine bestimmte Gewinnrate erreicht oder uneinholbar wird.

## 7. Server-Betrieb (zweite Ausbaustufe)

(in Entwicklung)

### 7.1 Query-Parameter der WebSocket-URL

Ein zentraler Server stellt eine WebSocket bereit. Beim initialen Verbindungsaufbau gibt der Spieler den gewünschten Tisch und seinen Namen über die Query-Parameter an:

`?player_name=str&table_name=str`

Nach einem Reconnect teilt der Spieler statt dessen seine letzte Session-ID über die Query-Parameter mit:  

`?session_id=uuid`

#### 7.2.WebSocket-Nachrichten

Alle Nachrichten sind JSON-Objekte mit einem `type`-Feld und optional einem `payload`-Feld.

**Proaktive (d.h. unaufgeforderte) Nachrichten vom Client an den Server:**

Der WebSocket-Handler empfängt diese Nachrichten und leitet sie an deb Peer weiter.

| Type             | Payload                                      | Beschreibung                                                                                                                 | 
|------------------|----------------------------------------------|------------------------------------------------------------------------------------------------------------------------------|
| `"leave"`        |                                              | Der Spieler möchte den Tisch verlassen.                                                                                      |
| `"swap_players"` | `{player_index_1: int, player_index_2: int}` | Der Host möchte die Position zweier Spieler vertauschen (der Host darf nicht verschoben werden; nur vor Spielstart möglich). |
| `"start_game"`   |                                              | Der Host möchte das Spiel starten.                                                                                           |
| `"announce"`     |                                              | Der Spieler möchte ein einfaches Tichu ansagen.                                                                              |
| `"bomb"`         | `{cards: Cards}`                             | Der Spieler möchte außerhalb seines regulären Zuges eine Bombe werfen.                                                       |

**Proaktive Nachrichten vom Server an den Client:**

Die Engine sendet diese Nachrichten über den Peer an den Client. Bei der `request`-Nachricht wartet der Peer auf die `response`-Nachricht des Clients.
Erhält er sie, liefert der Peer die Daten als Antwort an die Engine aus. 

| Type                        | Payload                                              | Beschreibung                                                     | Antwort vom Client (Type) | Antwort vom Client (Payload)         |
|-----------------------------|------------------------------------------------------|------------------------------------------------------------------|---------------------------|--------------------------------------|
| `"request"`  (s. 7.2.1)     | `{action: str, context: dict (optional)}`            | Der Server fordert den Client auf, eine Entscheidung zu treffen. | `"response"`              | `{action: str, response_data: dict}` | 
| `"notification"` (s. 7.2.2) | `{event: str, context: dict (optional)}`             | Broadcast an alle Clients über ein Spielereignis.                | keine Antwort             |                                      |
| `"error"` (s. 7.2.3)        | `{message: str, code: int, context: dict (optional)` | Informiert den Client über einen Fehler.                         | keine Antwort             |                                      |

#### 7.2.1 Request-/Response-Nachrichten

Der Request Context enthält die Daten, die für die Entscheidung benötigt werden. So kann der Client eine Antwort liefern, selbst wenn er keine Daten zwischenspeichern würde.

| Request Action (vom Server) | Request Context (vom Server)                                           | Response Data (vom Client)                   | Beschreibung                                                                                              |
|-----------------------------|------------------------------------------------------------------------|----------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| "announce_grand_tichu"      |                                                                        | `{announced: bool}`                          | Der Spieler wird gefragt, ob er ein großes Tichu ansagen will.                                            |
| "schupf"                    | `{hand_cards: Cards}`                                                  | `{given_schupf_cards: [Card, Card, Card]}`   | Der Spieler muss drei Karten zum Tausch abgeben (für rechten Gegner, Partner, linken Gegner).             |
| "play"                      | `{hand_cards: Cards, trick_combination: Combination, wish_value: int}` | `{cards: Cards}` (`{cards: []}` für passen)  | Der Spieler muss Karten ausspielen oder passen. Diese Aktion kann durch ein Interrupt abgebrochen werden. |
| "wish"                      |                                                                        | `{wish_value: int}`                          | Der Spieler muss sich einen Kartenwert wünschen.                                                          |
| "give_dragon_away"          |                                                                        | `{dragon_recipient: int}`                    | Der Spieler muss den Gegner benennen, der den Drachen bekommen soll.                                      |

Akzeptiert die Engine die Client-Antwort, sendet sie eine entsprechende [Notification-Nachricht](#722-notification-nachrichten) an alle Clients.
Andernfalls sendet die Engine eine Fehlermeldung über den Peer an den Client.

**Anmerkung bzgl. Tichu-Ansage und zur Bombe:**
Die Anfragen des Servers, ob der Spieler ein einfaches Tichu ansagen möchte, oder ob er eine Bombe werfen will, leitet der Peer nicht an den Client weiter, 
denn diese Entscheidungen trifft der Client proaktiv (im Gegensatz zur KI, die immer explizit gefragt wird).

#### 7.2.2 Notification-Nachrichten

Benachrichtigung an alle Spieler.

Der Notification Context enthält die Daten, die sich mit dem Ereignis geändert haben, sofern der Client diese nicht selbst trivial herleiten kann.
 
| Notification Event    | Notification Context (ergänzende Informationen)                                                                                                        | Beschreibung                                                                                                                            |
|-----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------|
| "player_joined"       | `{player_index: int, player_name: str}` (->) `{session_id: uuid, public_state: PublicStateDict, private_state: PrivateStateDict, pending_action: str}` | Der Spieler spielt jetzt mit.                                                                                                           |
| "player_left"         | `{player_index: int, player_name: str, host_index: int}`                                                                                               | Der Spieler hat das Spiel verlassen; eine KI ist eingesprungen.                                                                         |
| "players_swapped"     | `{player_index_1: int, player_index_2: int}`                                                                                                           | Der Index zweier Spieler wurde getauscht.                                                                                               |
| "game_started"        |                                                                                                                                                        | Das Spiel wurde gestartet.                                                                                                              |
| "round_started"       |                                                                                                                                                        | Eine neue Runde beginnt. Die Karten werden gemischt.                                                                                    |
| "hand_cards_dealt"    | `{player_index: int, count: int}` (->) `{hand_cards: Cards}`                                                                                           | Handkarten wurden an die Spieler verteilt.                                                                                              |
| "player_announced"    | `{player_index: int, grand: bool}`                                                                                                                     | Der Spieler hat ein Tichu angesagt.                                                                                                     |
| "player_schupfed"     | `{player_index: int}` (->) `{given_schupf_cards: [Card, Card, Card]}`                                                                                  | Der Spieler hat drei Karten zum Tausch abgegeben (für rechten Gegner, Partner, linken Gegner).                                          |
| "start_playing"       | `{start_player_index: int}` -> `{start_player_index: int, received_schupf_cards: [Card, Card, Card]}}`                                                 | Die Tauschkarten wurden an die Spieler verteilt (vom rechten Gegner, Partner, linken Gegner). Die Karten können nun ausgespielt werden. |
| "player_passed"       | `{player_index: int}`                                                                                                                                  | Der Spieler hat gepasst.                                                                                                                |
| "player_played"       | `{turn: Turn, trick_points: int, winner_index: int}`                                                                                                   | Der Spieler hat Karten ausgespielt. Turn = [player_index, cards, combination]                                                           |
| "wish_made"           | `{wish_value: int}`                                                                                                                                    | Ein Kartenwert wurde sich gewünscht.                                                                                                    |
| "wish_fulfilled"      |                                                                                                                                                        | Der Wunsch wurde erfüllt.                                                                                                               |
| "trick_taken"         | `{player_index: int, points: int, dragon_recipient: int}`                                                                                              | Der Spieler hat den Stich kassiert.                                                                                                     |
| "player_turn_changed" | `{current_turn_index: int}`                                                                                                                            | Der Spieler ist jetzt am Zug.                                                                                                           |
| "round_over"          | `{points: (int, int, int, int), loser_index: int, is_double_victory: bool)}`                                                                           | Die Runde ist vorbei und die Karten werden neu gemischt.                                                                                |
| "game_over"           | `{game_score: (list, list)}`                                                                                                                           | Die Runde ist vorbei und die Partie ist entschieden.                                                                                    |

* "->" bedeutet, dass der Peer den vom Server gesendeten Kontext mit privaten Statusinformationen anreichert, bevor er es an den Client weiterleitet.
* "(->)" bedeutet, dass der Kontext nur angereichert wird, wenn sich das Ereignis auf den eigenen Spieler bezieht. 

### 7.2.3. Fehlermeldungen

#### aiohttp-Fehler

Der Server schließt die Verbindung mit Code 1008 (WSCloseCode.POLICY_VIOLATION) bei ungültiger Session.

#### Inhaltliche Fehler

| Error Code                                  | Error Message                                             | Context (ergänzende Informationen)     |
|---------------------------------------------|-----------------------------------------------------------|----------------------------------------|
| **Allgemeine Fehler (100-199)**             |                                                           |                                        |
| UNKNOWN_ERROR = 100                         | Ein unbekannter Fehler ist aufgetreten.                   | `{exception: ExceptionClassName}`      |
| INVALID_MESSAGE = 101                       | Ungültiges Nachrichtenformat empfangen.                   | `{message: dict}`                      |
| UNKNOWN_CARD = 102                          | Mindestens eine Karte ist unbekannt.                      | `{cards: Cards}`                       |
| NOT_HAND_CARD = 103                         | Mindestens eine Karte ist keine Handkarte.                | `{cards: Cards}`                       |
| UNAUTHORIZED = 104                          | Aktion nicht autorisiert.                                 | `{action: str}`                        |
| SERVER_BUSY = 105                           | Server ist momentan überlastet. Bitte später versuchen.   |                                        |
| SERVER_DOWN = 106                           | Server wurde heruntergefahren.                            |                                        |
| MAINTENANCE_MODE = 107                      | Server befindet sich im Wartungsmodus.                    |                                        |
| **Verbindungs- & Session-Fehler (200-299)** |                                                           |                                        |
| SESSION_EXPIRED = 200                       | Deine Session ist abgelaufen. Bitte neu verbinden.        |                                        |
| SESSION_NOT_FOUND = 201                     | Session nicht gefunden.                                   | `{session_id: uuid}`                   |
| TABLE_NOT_FOUND = 202                       | Tisch nicht gefunden.                                     | `{table_name: str}`                    |
| TABLE_FULL = 203                            | Tisch ist bereits voll.                                   | `{table_name: str}`                    |
| NAME_TAKEN = 204                            | Dieser Spielername ist an diesem Tisch bereits vergeben.  | `{table_name: str, player_name: str}`  |
| ALREADY_ON_TABLE = 205                      | Du bist bereits an diesem Tisch.                          | `{table_name: str, player_index: int}` |
| **Spiellogik-Fehler (300-399)**             |                                                           |                                        |
| INVALID_ACTION = 300                        | Ungültige Aktion.                                         | `{reason: str, action: str}`           |
| INVALID_RESPONSE = 301                      | Keine wartende Anfrage für die Antwort gefunden.          | `{action: str}`                        |
| NOT_UNIQUE_CARDS = 302                      | Mindestens zwei Karten sind identisch.                    | `{cards: Cards}`                       |
| INVALID_COMBINATION = 303                   | Die Karten bilden keine spielbare Kombination.            | `{cards: Cards}`                       |
| NOT_YOUR_TURN = 304                         | Du bist nicht am Zug.                                     | `{action: str}`                        |
| INTERRUPT_DENIED = 305                      | Interrupt-Anfrage abgelehnt.                              | `{reason: str, action: str}`           |
| INVALID_WISH = 306                          | Ungültiger Kartenwunsch.                                  | `{wish_value: int}`                    |
| INVALID_ANNOUNCE = 307                      | Tichu-Ansage nicht möglich.                               |                                        |
| INVALID_DRAGON_RECIPIENT = 308              | Wahl des Spielers, der den Drachen bekommt, ist ungültig. | `{cards: Cards}`                       |
| ACTION_TIMEOUT = 309                        | Zeit für Aktion abgelaufen.                               | `{timeout: seconds, action: str}`      |
| REQUEST_OBSOLETE = 310                      | Anfrage ist veraltet.                                     | `{action: str}`                        |
| **Lobby-Fehler (400-499)**                  |                                                           |                                        |
| GAME_ALREADY_STARTED = 400                  | Das Spiel an diesem Tisch hat bereits begonnen.           | `{table_name: str}`                    |
| NOT_LOBBY_HOST = 401                        | Nur der Host kann diese Aktion ausführen.                 | `{action: str}`                        |

### 7.3 Aufgaben der Komponenten im Server-Betrieb

#### 7.3.1 WebSocket-Handler

*   Nimmt neue WebSocket-Verbindungen an:
    *   Der Client verbindet sich über eine WebSocket und gibt seinen Namen und den Namen eines Tisches an.
    *   Gibt es den Tisch noch nicht, wird dieser Tisch eröffnet (über die `Game-Factory`). 
    *   Ist der Tisch voll besetzt (max. 4 Clients), kann der Spieler sich nicht an den Tisch setzen. 
    *   Ist noch mind. ein Platz frei (d.h. der Platz ist belegt von einer KI), kann der Spieler sich an den Platz setzen (ersetzt die KI) und erhält den aktuellen Spielzustand.
*   Reagiert darauf, wenn der Spieler das Spiel verlassen will: 
    *   Wenn der Client geht, übernimmt automatisch die KI wieder den Platz, damit die übrigen Spieler weiterspielen können. 
    *   Hat der letzte Client den Tisch verlassen, wird der Tisch geschlossen (über die `Game-Factory`).
*   Händelt Verbindungsabbrüche:  
    *   Bei einem Verbindungsabbruch wartet der Server 20 Sekunden, bevor die KI den Platz einnimmt. 
    *   Sollte der Client sich wiederverbinden (er versucht es automatisch jede Sekunde), nimmt er den alten Platz wieder ein (sofern nicht in der Zwischenzeit ein anderer Client den Platz eingenommen hat) und erhält den aktuellen Spielzustand.
*   Empfangt Nachrichten vom Client:
    *   Leitet reguläre Spielaktionen (Antworten auf Requests) an den zugehörigen Peer weiter.
    *   Leitet Interrupt-Anfragen (`"interrupt"`) direkt an die zuständige `GameEngine` weiter.
    *   Verarbeitet Meta-Nachrichten (Join, Leave, Lobby-Aktionen).

#### 7.3.2 Game-Factory

*   Verwaltet eine Sammlung aktiver Spieltische (`GameEngine`-Instanzen).
*   Erstellt eine neue `GameEngine` für einen neuen Tisch.
*   Schließt Tische, wenn kein Client mehr verbunden ist (nach Timeout).

#### 7.3.3 Game-Engine

*   Bildet die Kern-Spiellogik ab.
*   Interagiert mit den Spielern (unterscheidet idealerweise nicht zw. `Agent` und `Peer`).
*   Reagiert auf Interrupt-Anfragen der Spieler.

#### 7.3.4 Peer

*   Serverseitiger WebSocket-Endpunkt des Clients (ein realer Spieler, der z.B. über einen Browser interagiert, könnte aber auch ein Bot sein); erbt von `Player`.
*   Empfängt Aufforderungen von der `GameEngine` (z.B. `play()`, `announce()`).
*   Formatiert diese Aufforderungen als `request`-Nachricht und sendet sie über den WebSocket an den Client.
*   Wartet auf eine `response`-Nachricht vom Client.
*   Validiert die Antwort und gibt die extrahierte Aktion an die `GameEngine` zurück.
*   Empfängt Benachrichtigungen (`notification`) von der `GameEngine` und leitet diese an den Client weiter.

## 8. Frontend (zweite Ausbaustufe)

### 8.1 Funktionsbeschreibung

#### 8.1.1 Allgemeines

*   Das Frontend ist eine reine Webanwendung mit HTML, CSS und JavaScript. Es wird nur Vanilla-JS verwendet (kein ECMAScript/ES6-Modul, kein TypoScript, keine Frameworks).
*   Als Architektur für das Web-Frontend wurde die **Event-Driven Architecture** (EDA) gewählt.
*   Die Module werden durch **Immediately Invoked Function Expression** (IIFE, selbstaufrufende anonyme Funktionen) erzeugt. 
*   Die Kommunikation mit dem Python-Backend erfolgt über eine WebSocket-Verbindung.

#### 8.1.2 Verbindungsaufbau / Reconnect

*   Mit initialem Verbindungsaufbau teilt der Client per Query-Parameter den Tisch-Namen und seinen Namen mit. 
*   Beim Wiederaufbau nach Verbindungsabbruch übermittelt der Spieler per Query-Parameter die letzte Session-Id.
*   Wenn der Client das Spiel verlassen will, kündigt er dies an, damit der Server nicht erst noch 20 Sekunden wartet, bis er durch eine KI ersetzt wird.
   
#### 8.1.3 Lobby

*   Der erste Client am Tisch darf die Sitzplätze der Mitspieler bestimmen, bevor er das Spiel startet. Normalerweise wird er warten, bis seine Freunde auch am Tisch sitzen, und dann sagen, wer mit wem ein Team bildet.
   
#### 8.1.4 Rundenende

*   Wenn die Runde beendet ist, und die Partie noch nicht entschieden ist, leitet der Server automatisch eine neue Runde ein.
*   Wenn die Partie beendet ist, werden die Spiele wieder zur Lobby gebracht.  

#### 8.1.5 Buttons-Controls

*   GrandTichu-Phase - Austeilen 8 Karten:
    *   „Weiter“,
    *   „Großes Tichu“ (Bei Klick: „Lange drücken für Ansage“.) 
    *   „Spielen“ (deaktiviert)

*   Schupf-Phase - Austeilen von 14 Karten:
    - A) Abgeben:
      *   „Passen“ (deaktiviert),
      *   „Tichu“ (deaktiviert, wenn bereits angesagt)
      *   „Schupfen“ (deaktiviert, wenn nicht 3 Karten in der Schupfzone liegen)

      Nur eine Handkarte kann selektiert werden. Danach muss eine Schupfzone gewählt werden. 
      
    - B) Aufnehmen – Nach Klick auf Schupfen:
      *   „Passen“ (deaktiviert),
      *   „Tichu“ (deaktiviert, wenn bereits angesagt)
      *   „Aufnehmen“
  
*   Spielphase
    * A) Nicht am Zug:
      *   „Passen“ (deaktiviert),
      *   „Tichu“ (deaktiviert, wenn nicht möglich)
      *   „Spielen“ (deaktiviert)
      
    * B) Am Zug (aber keine passende Kombination auf der Hand):
      *   „Passen“,
      *   „Tichu“ (deaktiviert, wenn nicht möglich)
      *   „Kein Zug“ (deaktiviert)
    
    * C) Am Zug (passende Kombination auf der Hand, aber keine Karte selektiert):
      *   „Passen“ (deaktiviert, wenn Anspiel),
      *   „Tichu“ (deaktiviert, wenn nicht möglich)
      *   „Auswählen“
    
      Bei Klick auf Auswählen wird der Button deaktiviert, die längste kleinstmögliche Kombination selektiert, nach Ablauf der Animation wird „Auswählen“ in „Spielen“ umbenannt.
    
    * D) Am Zug (passende Kombination auf der Hand, Karte selektiert):
      *   „Passen“ (deaktiviert, wenn Anspiel),
      *   „Tichu“ (deaktiviert, wenn nicht möglich)
      *   „Spielen“ (deaktiviert, wenn selektierte Karten nicht spielbar sind)

#### 8.1.6 Bombe

Mit dem Klick auf die Bombe werden Handkarten für eine Bombe ausgewählt (aber noch nicht geworfen). 

#### 8.1.7 Request-Zyklus 

*   Der Server sendet eine Anfrage oder eine Benachrichtigung an den Client.
*   Diese wird per Ereignisbus an den App-Controller weitergereicht.
*   Der App-Controller aktualisiert den Spielzustand und rendert danach die View.
*   Die Render-Funktion liest den Status aus und aktualisiert die HTML-Elemente.
*   Eine Benutzeraktion wird per Ereignisbus an den App-Controller weitergereicht.
*   Der App-Controller sendet die Aktion an den Server.

### 8.2 Module

*   `Config`: Konfigurationsvariablen (definiert in `config.js`).
*   `Lib`: Enthält allgemeine Hilfsfunktionen.
*   `State`: Datencontainer für den Spielzustand.
*   `User`: Datencontainer für die Benutzerdaten.    
*   `EventBus`: Zentrale Nachrichtenvermittlung zwischen den Komponenten.
*   `Network`: Verantwortlich für die WebSocket-Verbindung und Kommunikation mit dem Server.    
*   `SoundManager`: Verwaltet das Laden und Abspielen von Soundeffekten.
*   `Modals`: Verwaltet die Anzeige, Logik und Interaktion aller Modal-Dialoge der Anwendung.
*   `LoadingView`: Ansicht und Interaktion der Ladeanzeige. 
*   `LoginView`: Ansicht und Interaktion des Login-Bildschirms. 
*   `LobbyView`: Ansicht und Interaktion der Lobby. 
*   `TableView`: Ansicht und Interaktion des Spieltisch-Bildschirms. 
*   `ViewManager`: Schaltet zwischen den Views der Anwendung um.
*   `AppController`: Aktualisiert den Spielzustand und schaltet zwischen den Views um.

`main.js` ist der Haupt-Einstiegspunkt der Tichu-Anwendung.

Der Spielzustand wird über den App-Controller aktualisiert. 

Die Ansichten lesen den Spielzustand und rendern den Bildschirm entsprechend.

### 8.3 Verzeichnisstruktur

```
web/ 
├── fonts/  # Schriftarten 
│   └── architect-s-daughter/
├── images/  # Bilder
│   └── cards/
├── css/  # Stylesheet-Dateien
├── js/  # JavaScript-Dateien
│   └── views/ 
├── sounds/  # Audiodateien
├── vendor  # Drittanbieter-Assets
├── index.html  Startseite
├── tests.html  Unittests
│
```

### 8.4 Viewport
                      
Der Hauptcontainer (`#wrapper`) hat ein Seitenverhältnis von 9:16 (ein gängiges Smartphone-Hochformat), 
der mit einer Ausgangsgröße von 1080x1920 in den Viewport des Browsers skaliert wird.
Die HTML-Elemente werden pixelgenau positioniert.

#### 8.4.1 Umschalten zwischen den Views

Init: 
    Wenn SessionID vorhanden:
        Network versucht automatisch eine Verbindung aufzubauen
        -> Loading
    sonst 
        -> Login

"loginView:login"-Event:
    Network.open()
    -> Loading
        "network:open"-Event: 
            Wenn State.isRunning:
                -> Table
            sonst 
                -> Lobby
        "network:close"-Event:    
            -> Login

"lobbyView:start"-Event:
    Network.send('start_game')
    -> Loading

### 8.5 Ressourcen

#### Images

*  web/images/bomb-icon.png
	https://pixabay.com/de/vectors/bombe-karikatur-ikonisch-2025548/
	Kostenlos, Zusammenfassung der Inhaltslizenz: https://pixabay.com/de/service/license-summary/

*  web/images/cards
	https://github.com/Tichuana-Tichu/tichuana-tichu/tree/develop/src/ch/tichuana/tichu/client/resources/images/cards
	https://github.com/pgaref/Tichu/blob/master/Tichu_CardGame/src/tichu/images/back.jpg
	Auf Anfrage für nicht kommerziellen Gebrauch von [Fata Morgana Spiele, Bern](https://www.fatamorgana.ch) genehmigt.

*  web/images/background.png, web/images/logo.png, web/images/icon.png (web/images/dragon)
	https://pixabay.com/de/vectors/drachen-eidechse-monster-chinesisch-149393/
	Kostenlos, Zusammenfassung der Inhaltslizenz: https://pixabay.com/de/service/license-summary/

*  web/images/table-texture.png
	Vorlage:
	https://github.com/BananaHolograma/Veneno/blob/main/assets/background/poker_table_green.jpg
	LICENSE is MIT so you can use the code from this project for whatever you want, even commercially

*  web/images/tichu-icon.png 
	Vorlage: 
	https://pixabay.com/de/vectors/drachen-eidechse-monster-chinesisch-149393/
	Kostenlos, Zusammenfassung der Inhaltslizenz: https://pixabay.com/de/service/license-summary/
 
*  web/images/wish-icon.png
	Vorlage:
	https://github.com/Tichuana-Tichu/tichuana-tichu/tree/develop/src/ch/tichuana/tichu/client/resources/images/cards/mahjong.png
	Keine Lizenz-Hinweis!

*  web/images/turn-icon.png
	Selbst gemalt

*  web/images/spinner.png
	Vorlage: 
	https://godotengine.org/asset-library/asset/3350
	Kann frei verwendet werden

#### Sounds

*  web/sounds
	https://www.kenney.nl/assets/category:Audio
	License Creative Commons Zero, CC0: http://creativecommons.org/publicdomain/zero/1.0/
	You may use these assets in personal and commercial projects.
	Credit (Kenney or www.kenney.nl) would be nice but is not mandatory (Donate: http://support.kenney.nl)

| Dateiname | Original                                     | Verwendung                  |
|-----------|----------------------------------------------|-----------------------------|
| announce  | music-jingles/jingles_STEEL04                | Tichu ansagen               |
| bomb      | sci-fi-sounds/lowFrequency_explosion_000.ogg | Bombe werfen                |
| play0     | casino-audio/card-place-1                    | Karte ausspielen Spieler 0  |
| play1     | casino-audio/card-place-2                    | Karte ausspielen Spieler 1  |
| play2     | casino-audio/card-place-3                    | Karte ausspielen Spieler 2  |
| play3     | casino-audio/card-place-4                    | Karte ausspielen Spieler 3  |
| schupf    | casino-audio/card-shove-2                    | Tauschkarten verteilen      |
| score     | casino-audio/chips-handle-6.ogg              | Punkteanzeige aktualisieren |
| select    | ui-audio/click1.ogg                          | Handkarte selektieren       |
| shuffle   | casino-audio/card-shuffle                    | Karten mischen              |
| take      | casino-audio/card-shove-1                    | Karten kassieren            |

#### Schriftarten

web/fonts/architect-s-daughter
	https://godotengine.org/asset-library/asset/316
	Die OFL erlaubt die freie Verwendung, Untersuchung, Änderung und Weiterverbreitung der lizenzierten Schriften, solange sie nicht selbst verkauft werden. 
	Die Schriftarten können mit jeder Software gebündelt, eingebettet, weiterverteilt und/oder verkauft werden.

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
    # veraltet:
    # pip pip install -r requirements.txt
     
    # moderner, die Abhängigkeiten stehen jetzt in der `pyproject.toml`-Datei: 
    # -e: Editable, src wird verlinkt, nicht kopiert.
    # .: Das Zielverzeichnis ist das aktuellen Verzeichnis.
    # [dev]: Auch die optionale Abhängigkeitsgruppe namens dev installieren.
    pip install -e .
    # bzw mit alle [dev]-Abhängigkeiten:
    pip install -e ".[dev]"
    ```
    Mit `pip freeze` können die aktuellen Abhängigkeiten ermittelt werden.

5.  **Arena starten:**
    ```bash
    python bin/run_arena.py
    ```
    **Server starten:**
    ```bash
    python bin/serve.py
    ```
    **WebSocket-Client zum Testen starten:**
    ```bash
    python bin/wsclient.py
    ```

### A1.3 Testing

*   Unit-Tests werden mit `pytest` geschrieben und befinden sich im `tests/`-Verzeichnis.
    *   Ausführen der Tests: `python -m pytest`.
    *   Ausführen mit Coverage: `bin/cov.ps1`
*   Die Codeabdeckung der Tests wird mit `coverage` gemessen, Konfiguration in `.coveragerc` (veraltet) bzw. in `pyproject.toml` (neu).
    *   Ausführen: `bin/cov.ps1`

## A2. Exceptions

| Error                   | Beschreibung                                                                                                                      |
|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| PlayerInteractionError  | Basisklasse für Fehler, die während der Interaktion mit einem Spieler auftreten können.                                           |
| ClientDisconnectedError | Wird ausgelöst, wenn versucht wird, eine Aktion mit einem Client auszuführen, der nicht (mehr) verbunden ist.                     |
| PlayerInterruptError    | Wird ausgelöst, wenn eine wartende Spieleraktion durch ein Engine-internes Ereignis (z.B. Tichu-Ansage, Bombe) unterbrochen wird. |
| PlayerTimeoutError      | Wird ausgelöst, wenn ein Spieler nicht innerhalb des vorgegebenen Zeitlimits auf eine Anfrage reagiert hat.                       |
| PlayerResponseError     | Wird ausgelöst, wenn ein Spieler eine ungültige, unerwartete oder nicht zum Kontext passende Antwort auf eine Anfrage sendet.     |

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

Der Code im Backend folgt den offiziellen Python-Styleguide-Essay [PEP 8](https://peps.python.org/pep-0008/).

Der Code im Web-Frontend folgt den [JS Standard Style Guide](https://www.w3schools.com/js/js_conventions.asp), mit folgenden Ausnahmen:
*   Immer geschweifte Klammern für `if`-, `for`- und `while`-Statements
*   Zeilenumbruch bei `else`
*   Max. eine Leerzeile

### A4.1 Code-Dokumentation

#### Backend

Das Format für die [Docstrings](https://peps.python.org/pep-0257/) ist `reStructuredText`.

*   Jedes Modul (py-Datei) hat eine kurze Datei-Header-Beschreibung (ein oder zwei Sätze, die beschreiben, was das Modul definiert).
    *   Öffentliche Variablen und Konstanten des Moduls werden beschrieben.
*   Jede Klasse hat eine kurze Beschreibung (ein oder zwei Sätze, was die Klasse repräsentiert bzw. tut). 
    *   Öffentliche Instanzvariablen werden mit `:ivar <name>: <Beschreibung>` aufgelistet.
    *   Öffentliche Klassenkonstanten werden mit `:cvar <name>: <Beschreibung>` aufgelistet.
*   Jede Funktion/Klassenmethode hat eine Überschrift und optional eine ergänzende Beschreibung. 
    * Die Parameter werden mit `:param <name>: <Beschreibung>` aufgelistet. Optionale Parameter werden mit `:param <name>: (Optional) <Beschreibung>` gekennzeichnet.  
    * Der Rückgabewert wird mit `:result: <Beschreibung>` dokumentiert. Rückgabe `None` wird nicht erwähnt.
    * Mögliche Exceptions werden mit `:raises <ErrorClass> <Beschreibung>` aufgelistet.

#### Web-Frontend

Zur Dokumentation von JavaScript wird [JSDoc](https://jsdoc.app/) angewendet.

*   Jedes Modul (js-Datei) hat eine kurze Datei-Header-Beschreibung (ein oder zwei Sätze, die beschreiben, was das Modul definiert).
*   Jedes öffentliche Objekt (inkl. Variable, Konstante und Namensraum) wird beschrieben und mit `@type` der Typ angegeben.
*   Jede Funktion wird beschrieben und dessen Parameter mit `@param` und Rückgabewert mit `@returns` angegeben
*   Für ein Type-Alias wird `@typedef` und `@property` verwendet.
    todo: weitere Beispiele auflisten

### A4.2 Namenskonvention

#### Backend

| Type                                     | Schreibweise   |
|------------------------------------------|----------------|
| **Package** (Verzeichnis mit py-Dateien) | `snake_case`   |
| **Modul** (py-Datei)                     | `snake_case`   |
| **Klasse**                               | `PascalCase`   |
| **Funktion** / **Klassenmethode**        | `snake_case()` |
| **Variable** / **Parameter**             | `snake_case()` |
| **Konstante**                            | `UPPER_CASE`   |

#### Web-Frontend

| Type                                                  | Schreibweise  |
|-------------------------------------------------------|---------------|
| **Verzeichnis**                                       | `kebab-case`  |
| **Datei**                                             | `kebab-case`  |
| **CSS-Klasse**                                        | `kebab-case`  |
| **URL** / **Query-Parameter**                         | `kebab-case`  |
| **JS-Typen** / **Aufzählung (Enum)** / **Namensraum** | `PascalCase`  |
| **JS-Funktion**                                       | `camelCase()` |
| **Variable** / **Parameter**                          | `camelCase()` |
| **Konstante**                                         | `UPPER_CASE`  |

Interne Funktionen und Variablen werden mit einem führenden Unterstrich gekennzeichnet.

Aufzählungen (Enum) sind singular (`ErrorCode`, nicht `ErrorCodes`) 

### A4.3 Type-Hints

Es werden sowohl im Backend als auch im Web-Frontend ausgiebig Type-Hints verwendet, insbesondere bei der Funktion-Signatur und bei Klassenvariablen.

## A5. Glossar

*   **Spieler und Teams**: Die Spieler werden gegen den Uhrzeigersinn mit 0 beginnend durchnummeriert. Spieler 0 und 2 bildet das Team 20 sowie Spieler 1 und 3 das Team 31. Ein Spieler hat 3 Mitspieler. Der Mitspieler gegenüber ist der Partner, die beiden anderen Mitspieler sind rechter und linker Gegner.
*   **Spielzug (turn)**: Ein Spieler spielt eine Kartenkombination aus oder passt.
*   **Stich (trick)**: Eine Serie von Spielzügen, bis die Karten vom Tisch genommen werden. Jeder Spieler spielt nacheinander Karten aus oder passt. Der Spieler, der zuletzt Karten abgelegt hat, ist der Besitzer des Stichs. Schaut ein Spieler, der am Zug ist, wieder auf seine zuvor ausgespielten Karten (weil alle Mitspieler gepasst haben), hat er den Stich gewonnen. Der Besitzer wird zum Gewinner des Stichs. Der Stich wird geschlossen, indem er vom Tisch abgeräumt wird. Solange kein Gewinner des Stichs feststeht, ist der Stich offen.
*   **Runde (round)**: Karten austeilen und spielen, bis der Gewinner feststeht. Eine Runde besteht aus mehreren Stichen, bis der Gewinner feststeht und Punkte vergeben werden.
*   **Partie (game)**: Runden spielen, bis ein Team mindestens 1000 Punkte hat. Eine Partie besteht aus mehreren Runden und endet, wenn ein Team mindestens 1000 Punkte erreicht hat.
*   **Öffentlicher Spielzustand/Beobachtungsraum (public state)**: Alle Informationen über die Partie, die für alle Spieler sichtbar sind.
*   **Privater Spielzustand (private state)**: Die verborgenen Informationen über die Partie, die nur der jeweilige Spieler kennt.
*   **Beobachtungsraum (Observation Space)**: (Public + Private State), die Sitzplatznummern sind relativ zum Spieler angegeben (0 == dieser Spieler, 1 == rechter Gegner, 2 == Partner, 3 == linker Gegner). Wird primär für KI-Agenten verwendet.
*   **Index in kanonischer Form (Canonical Index)**: Nummerierung der Spieler (0-3) so, wie der Server/die GameEngine die Spielerliste intern pflegt. Wenn nichts weiter erwähnt ist, ist stets der kanonische Index gemeint.
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
 