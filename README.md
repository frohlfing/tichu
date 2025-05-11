# TICHU

Ich entwickle eine Webanwendung "Tichu" mit Python. Tichu ist ein Kartenspiel. 

Die Regeln stehen hier: https://cardgames.wiki/de/blog/tichu-spielen-regeln-und-anleitung-einfach-erklaert

Das System soll sowohl auf Windows 11 laufen (Entwicklungsumgebung) als auch auf einem Raspberry Pi 5 (bookworm).

Es gibt zwei Betriebsarten:
- In der Arena spielen Agenten (KI-gesteuerte Spieler) gegeneinander. Hier kommt es auf hohe Geschwindigkeit an, um möglichst 
viele Partien zu spielen. 
- Im Live-Betrieb spielen die Agenten mit echten Spielern. Dazu stellt ein Server eine Websocket bereit, über die der reale 
Spieler seine Aktionen mitteilt und die Events erhält. 


## Entwicklungsstand

Die Arena ist bereits umgesetzt, die Agenten können miteinander spielen. 

Der Server für den Live-Betrieb befindet sich im Aufbau.

Die Web-App (das Frontend) ist noch gar nicht umgesetzt; soll via HTML/JS/CSS umgesetzt werden. Ich hatte in Godot angefangen, 
eine App zu entwickeln. Aber diesen Ansatz möchte ich nicht weiter verfolgen. Ich kann davon aber einen Screenshot als Vorlage 
liefern.  

**Anmerkung:**

- Mit "Client" ist hier der serverseitige Endpunkt der WebSocket-Verbindung gemeint. 
Der clientseitige Endpunkt ist der "reale Spieler".
- Mit "Agent" ist ein KI-gesteuerter Spieler gemeint.
 

## Aufgabenbereiche

### Aufgaben des WebSocket-Handlers

Er delegiert eine Interrupt-Anfrage an die Engine, sonstige Nachrichten an die Client-Instanz.

1) Spiel beitreten
Der reale Spieler verbindet sich über eine WebSocket und gibt seinen Namen und den Namen eines Tisches an.
Gibt es den Tisch noch nicht, wird dieser Tisch eröffnet. Ist der Tisch voll besetzt (max. 4 reale Spieler), 
kann der Spieler sich nicht an den Tisch setzen. Ist noch mind. ein Platz fei (d.h. der Platz ist belegt von einer KI), 
kann der Spieler sich an den Platz setzen (ersetzt die KI) und erhält den aktuellen Spielzustand.

2) Spiel verlassen
Wenn der reale Spieler geht, übernimmt automatisch die KI wieder den Platz, damit die übrigen Spieler weiterspielen können. 
Ist der letzte reale Spieler vom Tisch aufgestanden, wird der Tisch geschlossen (entfernt).

3) Verbindungsabbruch
Bei einem Verbindungsabbruch wartet der Server 20 Sekunden, bevor die KI den Platz einnimmt. Sollte der Spieler sich 
wiederverbinden (er versucht es automatisch jede Sekunden), nimmt er den alten Platz wieder ein (sofern nicht in der zwischenzeit 
ein anderer reale Spieler sich dort hingesetzt hat) und erhält den aktuellen Spielzustand.

4) Als einzige proaktive Aktion kann der Spieler ein Handzeichen geben und sagen, was er tun möchte (Interrupt anfordern).
Diese Anfrage delegiert der WebSocket-Handler an die Game-Engine weiter. Alle anderen Nachrichten leitet der Handler an den 
Client (serverseitigen Endpunkt) weiter.

### Aufgaben der Game-Faktory

Die Faktory stellt passend zum Tisch eine Game-Engine bereit. 
 
### Aufgaben der Game-Engine

Die Engine steuert das Spiel für einen Tisch. Die Engine interagiert mit den Spielern, unterscheidet dabei nicht zwischen 
KI-gesteuerten SpAgenten und realen Spieler (abgesehen von verzichtbaren Hacks, um die Ausführungsgeschwindigkeit in der Arena 
zu optimieren).
Der Server übermittelt dem Spieler, der keine Handkarten mehr hat (er spielt also nicht mehr in der aktuellen Runde
mit) zusätzlich die Handkarten der Mitspieler. Der von der Runde ausgeschiedene Spieler darf nämlich in die Karten der Mitspieler
schauen, damit er sich nicht langweilen muss.

### Aufgaben eines Spielers

Der Spieler (Agent und Client) reagiert ausschließlich auf eine Anfrage. Die einzige Ausnahme ist das Handzeichen geben 
(Interrupt anfordern). Bei einem Interrupt bricht der Spieler seine aktuelle Entscheidungsfindung, so dass der Server nicht 
länger auf eine Antwort warten muss.
Der Client (serverseitigen Endpunkt) leitet Benachrichtigungen und Anfragen des Servers an den realen Spieler weiter. 
Bei einer Anfrage wartet der Client, das der Spieler darauf antwortet und gibt diese an den Server zurück.


## Ablauf eine Partie

1) Grundsätzlich sendet der Client (serverseitigen Endpunkt) jedes Ereignis inkl. Spielzustand über alle aktiven Websocket-
Verbindungen, damit der reale Spieler auf dem aktuellen Stand bleiben können. Das ist für Agenten nicht notwendig, da sie bei 
einer Entscheidung direkt auf den aktuellen Spielzustand zugreifen können.
2) Mit Verbindungsaufbau über die WebSocket sendet der reale Spieler direkt den Tisch-Namen mit. 
3) Wenn der reale Spieler das Spiel verlassen will, kündigt er dies an, damit der Server nicht erst noch 20 Sekunden wartet,
bis er durch eine KI ersetzt wird.
4) Der erste reale Spieler am Tisch darf die Sitzplätze der Mitspieler bestimmen, bevor er das Spiel startet (normalerweise wird 
er warten, bis seine Freunde auch am Tisch sitzen und dann sagen, wer mit wem ein Team bildet.) Das findet in der Lobby statt.
5) Eine Neue Runde beginnt. Der Server verteilt je 8 Karten an jeden Spieler. 
6) Jeder Spieler muss sich dann entscheiden, ob er Grand Tichu ansagen möchte oder nicht (passt). 
7) Sobald jeder Spieler sich entschieden hat, ob er ein Großes Tichu ansagen möchte oder nicht, teilt er die restlichen Karten 
aus (je 6 pro Spieler).
8) Solange noch kein Spieler Karten zum Tausch (Schupfen) abgegeben hat, kann der Spieler ein Tichu ansagen. Dazu muss er vorab
ein Interrupt auslösen, damit er vom Server gelegenheit bekommt, dies zu tun.
9) Die Spieler müssen nun 3 Karten zum Tauschen abgeben (verdeckt, je eine pro Mitspieler). 
10) Sobald alle Spieler die Karten zum Tauschen abgegeben haben, sendet der Server an jedem Spieler jeweils die getauschten
Karten, die für den jeweiligen Spieler bestimmt sind.
11) Ab jetzt kann der Spieler jederzeit a) so wie vor dem Schupfen jederzeit Tichu ansagen, solange er noch 14 Karten auf der 
Hand hat und b) eine Bombe werfen (sofern er eine besitzt). Dazu muss er ein Interrupt auslösen.
12) Der Spieler mit dem MahJong muss eine Kartenkombination ablegen. 
13) Der nächste Spieler wird aufgefordert, Karten abzulegen oder zu Passen. 
14) Punkt 13 wird wiederholt, bis alle Mitspieler hintereinander gepasst haben, so das der Spieler, der die letzten Karten 
gespielt hat, wieder an der Reihe ist.
15) Dieser Spieler darf die Karten kassieren.
16) Wenn ein Spieler keine Handkarten mehr hat, kann er in die Karten der Mitspieler kucken (die Karten sind für ihn nicht 
mehr verdeckt).
17) Wenn die Runde beendet ist, und die Partie noch nicht entschieden ist (kein Team hat 1000 Punkte erreicht), leitet der 
Server automatisch eine neue Runde ein (wir beginnen wieder bei Punkt 5).
18) Wenn die Partie beendet ist, beginnen wir wieder mit Punkt 4.  


## Definition der Websocket-Nachrichten

### Proaktive Nachrichten vom realen Spieler an den Server

- type: "bye"

- type: "ping", payload: {timestamp:<timestamp>}

Antwort vom Server: type: "pong", payload: {time:<timestamp>“}

- type: "interrupt", payload: {reason:"tichu"|"bomb"}

Keine Antwort vom Server

### Proaktive Nachrichten vom Server an den realen Spieler
  
TODO: action und data spezifizieren

- type: "request", payload: {action:<action> [,data:<action_data>]}

Antwort vom realen Spieler:

type: "response", payload: {action:<action>, data:<action_data>}


## Zusammenfassung der verschiedenen Agenten und ihrer Funktionsweise 

- **`RandomAgent`** – Wählt zufällige Züge. 
- **`RuleAgent`** – Befolgt festgelegte Regeln. 
- **`HeuristikAgent`** – Berechnet (exakte oder durch Erfahrungswerte geschätzte) Wahrscheinlichkeiten für die 
Entscheidungsfindung.
  (Heuristiken sind Näherungsmethoden, um mit begrenzten Informationen oder Rechenkapazitäten effektive Entscheidungen zu treffen.)
- **`NNetAgent`** – Nutzt ein neuronales Netz (Neural Network), um Entscheidungen zu treffen.
  - **`BehaviorAgent`** – Lernt durch überwachtes Lernen aus Log-Daten (von bettspielwelt.de), menschliche Spielweisen zu 
  imitieren. 
  - **`AlphaZeroAgent`** – Verwendet Monte-Carlo Tree Search (MCTS) in Kombination mit neuronalen Netzen, um durch 
  selbständiges Spielen das vortrainierte Netz von `BehaviorAgent` zu optimieren.  

Während ein **regelbasierter Agent** feste Regeln befolgt und ein **heuristischer Agent** zusätzlich Wahrscheinlichkeiten 
einbezieht, lernt ein **NNetAgent** die Spielstrategie durch Trainingsdaten.


## TODOS

- von Gemini dokumentieren lassen: 
  - Projektbeschreibung
  - Allgemeine Funktionsweise
  - Klassenhierarchie, Klassenbeschreibung
  - Vorschläge für Testfälle (nicht coden, nur eine todo-Liste für den Entwickler)
  - Glossar/Definition der Begriffe
- Test bzg Arena schreiben lassen und durchführen
- Test bzg Server schreiben lassen und durchführen
- Todos im code umsetzten
- Webfrontend aus Godot von Gemini programmieren lassen
- Lobby-Bereich (Html)
- Webfrontend testen
- HeuristikAgent optimieren mit neuer Wahrscheinlichkeitsberechnung
- Brettspielwelt-Logs aufbereiten
- NNetAgent bauen


## Quellen

Regeln
https://abacusspiele.de/wp-content/uploads/2021/01/Tichu_Pocket_Regel.pdf
