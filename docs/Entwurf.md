Für den nächsten Schritt muss ich dir erst einiges zeigen.  

Use Case 1: Verbindungsaufbau und sich an einem Tisch setzen
1.1) Der WS-Client (Browser eines menschlichen Spielers) verbindet sich und der Spieler kann in einem Textfeld den Namen eines Tisches angeben.
1.2)  GameFactory erstellt und verwaltet die GameEngine basierend auf den Tisch, der vom Spieler angegeben wird.  Gibt es den Tisch noch nicht, wird eine neue GameEngine erzeugt. Ist der Tisch voll besetzt (max. 4 menschliche Spieler), kann der Spieler sich nicht an den Tisch setzen. Ist noch mind. ein Platz fei (d.h. der Platz ist belegt von einer KI), kann der Spieler sich an den Platz setzen (anstelle der KI spielen).

Use Case 2: Verbindungsabbruch
2.1) Wenn der Spieler das Spiel verlässt  (absichtlich oder durch Verbindungsabbruch), übernimmt automatisch eine KI den Platz (nach 20 Sekunden), damit die übrigen Spieler weiterspielen können.
2.2) Bei einem Verbindungsabbruch versucht der Client automatisch jede Sekunden, sich wieder die Verbindung aufzunehmen. Bei Erfolg versucht er sich an den vorherigen Platz zu setzen.
2.3) Ist der letzte menschliche Spieler vom Tisch aufgestanden, wird der Tisch von der GameFactory geschlossen (entfernt).

Use Case 3: Unbehandelter Fehler oder Fehler durch "Mogelversuche/Regelverstöße"
3.1) Der Client kriegt eine entsprechende Nachricht.

Weitere UsesCases folgen später

Klassen:
- "GameFactory" verwaltet eine Liste von GameEngine-Instanzen (pro Tisch eine).
- "GameEngine" ist die Spiellogik und hat eine Liste der 4 Player-Instanzen. Details hierzu brauchen wir noch nicht.
- "Player" ist eine Basisklasse für "Client" (Websocket, Mensch) und für "Agent" (KI gesteuert). 
- "PublicState" ist der öffentliche Spielstatus (ist für alle Spieler zu sehen) 
- "PrivateState" ist der verborgene Spielstatus (ist nur für einen bestimmten Spieler zu sehen)
- Brauchen wir noch nicht, aber sei es erwähnt: "Arena": In der Arena können Agenten gegeneinander antreten. Das läuft ohne Websocket auf der Shell und dient dazu, die Agenten zu trainieren. Hier kommt es auf hohe Ausführungsgeschwindigkeit der Spiele an.
- "Test-Client" (keine Klasse, sondern ein Shell-Skript. Das Skript soll mit aiohttp und/oder asyncio ein WS-Client sein, da automatisiert Nachrichten sendet, je nach Use-Case. 

Kannst du mit diesen Infos ein Grundgerüst für die genannten Klassen bauen?