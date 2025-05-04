Ich entwickle eine Webanwendung "Tichu" mit Python. Tichu ist ein Kartenspiel. Die Regeln stehen hier: https://cardgames.wiki/de/blog/tichu-spielen-regeln-und-anleitung-einfach-erklaert/#:~:text=Wichtige%20Regeln%201%20Ein%20Spieler%20kann%20%E2%80%9ETichu%E2%80%9C%20ansagen%2C,verwendet%20werden%2C%20senkt%20aber%20den%20Gesamtwert%20des%20Stichs.
Das System soll sowohl auf Windows 11 laufen (Entwicklungsumgebung) als auch auf einem Raspberry Pi 5 (bookworm).
Der Server stellt eine Websocket bereit, über die der Spieler seine Aktionen mitteilt und die Evens erhält. Die Websocket hab ich mit asyncio umgesetzt. asyncio möchte ich ersetzen mit aiohttp.
Ich gibt dir im Anschluss den Code. Bitte ändere diesen so um das aiohttp eingebunden wird.

-------------------------------------

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


-----------------------------------

Ich möchte eine klare Hierarchy für die Zugriffsebenen:
websocket_handler -> Factory  -> Engine -> Player  (also websocket hat Zugriff auf Factory, und damit auf Engine und damit auf Player; aber nicht umgedreht; keine Zirkelbezüge)
Verbindungsaufbau: websocket_handler holt über Factory die Engine und darüber den Client. factory.handle_new_connection() sollte besser direkt der websocket_handler machen (kann zum Teil als private Funktion in server definiert werden, damit webocket_handler übersichtlich bleibt).
Bei Verbindungsabbruch teilt websocket_handler der Engine dies mit, bevor der websocket_handler entfernt wird. Die Engine statet einen Timer für diesen Client. Bei Timeout schmeißt die Engine den Client aus der Liste und setzt ein Agent (KI) an den Platz.
Sollte der Client mit derselben player_id sich reconnecten, so erfährt die Engine dies über den (neuen) websocket_handler. Ist der Timer noch nicht abgelaufen, stoppt die Engine lediglich den Timer.

-----------------------------------

Jetzt sieht es sehr gut aus. Womit wollen wir weiter machen? Diese TOODS sehe ich:
- Meinen bisherigen Code gegenlesen, alles nochmal ganz genau prüfen: 1) Dokumentieren (restructedText) 2) Log-Einträge auf Deutsch übersetzen 3) todos im Code bearbeiten. (Wichtig! Alle Kommentare beibehalten)
- Test-Client schreiben: Das Shell-Skript soll mit aiohttp und/oder asyncio ein WS-Client sein, das automatisiert Nachrichten senden kann. Nützlich zum testen, UnitTests.
- Unit-Test schreiben: Fall 1) Connect, Tisch zuordnen, Nachricht austauschen, disconnect (clientseitig gewollt) Fall 2) Verbindungsabbruch, Reconnect, Fall 3) Verbindungsabbruch, kein Reconnect Fall 4) Tisch besetzt Fall 5) disconnect, aber ein Spieler spielt noch, Fall 6 disconnect, kein Spieler mehr am Tisch Fall 7 Connect, Neuer Tisch (1 Client und 3 Agents sitzen am Tisch), Fall 8 ... (siehst du noch sinnvolle Fälle)
- Abgleich mit deprecated Code: PublicState und PrivateState und GameEngine mit inhaltlichen Details erweitern
- Nachrichten / Kommunikation zw. Server und Agent bzw. Client definieren
- Dokumentation für Entwickler schreiben (Klassenhierachie, Aufgaben der Klassen, Glossar, Spielablauf, usw.)
- WebApp für den Spieler schreiben (hierzu hab ich im Ansatz ein Client in Godot angefangen, diesen möchte ich aber nach HTML/JS/CSS portieren

Phase 1: Stabilisieren & Definieren (Grundlage schaffen)

Gegenlesen/Prüfen/Inline-Doku/Logs/TODOs:
Warum zuerst? Bevor du neue Funktionalität hinzufügst oder Tests schreibst, sollte der aktuelle Code so sauber und verständlich wie möglich sein. Das Beheben kleinerer TODOs, das Übersetzen von Logs und das Hinzufügen von Docstrings (RestructuredText ist super!) schafft eine solide Basis und vermeidet, dass du Fehler oder Unklarheiten in neue Bereiche "mitziehst".
Fokus: Gehe jede Klasse und Methode durch. Sind die Namen klar? Funktionieren die Abläufe logisch? Sind die deutschen Log-Einträge präzise? Sind alle deine Kommentare noch aktuell? Füge Docstrings hinzu, die erklären, was eine Funktion/Klasse tut, welche Parameter sie erwartet und was sie zurückgibt.
Nachrichten / Kommunikation zw. Server und Client definieren:
Warum jetzt? Du kannst die Spiellogik in der GameEngine und den Test-Client (oder später die WebApp) nicht sinnvoll implementieren, wenn du nicht genau weißt, welche Daten in welchem Format (JSON-Struktur) ausgetauscht werden.
Fokus: Lege fest, wie z.B. eine "Spielkarte spielen"-Aktion vom Client aussieht ({'action': 'play_cards', 'payload': {'cards': ['H10', 'H1']}}?), wie ein "Spielzustand-Update" vom Server aufgebaut ist ({'type': 'public_state_update', 'payload': {...PublicState...}}), wie Fehler gemeldet werden etc. Dokumentiere diese Strukturen.
Phase 2: Kernlogik & Basis-Tests
Abgleich mit deprecated Code / Implementierung PublicState/PrivateState/GameEngine:
Warum jetzt? Mit den definierten Nachrichtenstrukturen kannst du nun die Platzhalter in der GameEngine mit Leben füllen. Implementiere die Kernmechaniken: Karten austeilen, handle_player_message für die definierten Aktionen (Karten spielen, passen, Tichu ansagen?), Runden-/Stichlogik, Punkte zählen (zumindest grundlegend). Fülle PublicState und PrivateState mit den notwendigen Attributen.
Fokus: Ziel ist ein minimal funktionsfähiger Spielablauf innerhalb der Engine, der auf die definierten Nachrichten reagiert.
Test-Client schreiben:
Warum jetzt? Sobald die Engine auf grundlegende Nachrichten reagieren kann, ist ein Test-Client Gold wert. Du kannst damit viel schneller und gezielter testen als mit einer echten WebApp oder nur mit Unit-Tests. Du kannst damit das Verbinden, Trennen, Senden von Spielzügen etc. automatisieren und die Serverantworten prüfen.
Fokus: Ein einfaches Python-Skript (mit aiohttp als Client) das eine WebSocket-Verbindung aufbaut, sich authentifiziert (Parameter sendet), die definierten Nachrichten senden und empfangene Nachrichten ausgeben oder rudimentär prüfen kann.
Phase 3: Umfassende Tests & Dokumentation
Unit-Tests schreiben:
Warum jetzt? Mit dem Test-Client kannst du die Gesamt-Flows testen. Jetzt ist ein guter Zeitpunkt, detailliertere Unit-Tests (z.B. mit pytest) für spezifische, kritische oder komplexe Teile zu schreiben:
Einzelne Funktionen der GameEngine (z.B. Validierung von Kartenkombinationen).
Die Timer-Logik und Randfälle in der GameFactory.
Die Zustandsübergänge in PublicState/PrivateState.
Deine genannten Fälle sind sehr gut! Ergänzend:
Fall 7b: Connect, Tisch beitreten (wo schon 1 Mensch, 2 KIs sitzen).
Fall 8: Ungültige Aktion senden (z.B. Karten spielen, die man nicht hat; Aktion senden, wenn man nicht dran ist).
Fall 9: Schnelles Verbinden/Trennen/Wiederverbinden (Stresstest für Timer/Reconnect).
Fall 10: Fehler bei der JSON-Serialisierung/Deserialisierung.
Fokus: Teste einzelne Komponenten isoliert und decke Randfälle ab.
Dokumentation für Entwickler schreiben:
Warum jetzt? Der Code ist stabilisiert, die Kernlogik implementiert und getestet. Jetzt kannst du die übergeordnete Dokumentation schreiben, die die Architektur, Klassenaufgaben, den Datenfluss und wichtige Designentscheidungen erklärt. Das Glossar ist hier auch sehr sinnvoll.
Fokus: Eine README.md oder separate Dokumentationsdateien, die neuen Entwicklern (oder deinem zukünftigen Ich) den Einstieg erleichtern.
Phase 4: Frontend
WebApp für den Spieler schreiben:
Warum zuletzt? Die WebApp benötigt ein funktionierendes und stabiles Backend mit einer klar definierten API (den Nachrichten). Jetzt kannst du dich auf die Client-Seite konzentrieren. Die Portierung von Godot nach HTML/JS/CSS ist ein eigenes Projekt.
Fokus: UI-Design, Client-seitige Logik, Kommunikation mit dem WebSocket-Server basierend auf den definierten Nachrichten.
Zusammenfassend die empfohlene Reihenfolge:
Code prüfen/dokumentieren/übersetzen/TODOs bearbeiten
Nachrichten/Kommunikation definieren
Kernlogik GameEngine/States implementieren
Test-Client schreiben (und parallel zu 3 nutzen)
Unit-Tests schreiben (detaillierte Fälle)
Entwickler-Dokumentation schreiben
WebApp schreiben