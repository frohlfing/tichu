Glossar
========

- Spieler und Teams

Die Spieler werden gegen den Uhrzeigersinn mit 0 beginnend durchnummeriert. Spieler 0 und 1 bildet das Team 10 sowie
Spieler 2 und 3 das Team 32. Ein Spieler hat 3 Mitspieler. Der Mitspieler gegenüber ist der Partner, die beiden anderen 
Mitspieler sind rechter und linker Gegner.

- Spielzug (turn): Ein Spieler spielt eine Kartenkombination aus oder passt

- Stich (trick): Eine Serie von Spielzügen, bis die Karten vom Tisch genommen werden. 

Jeder Spieler spielt nacheinander Karten aus oder passt. Der Spieler, der zuletzt Karten abgelegt hat, ist der Besitzer 
des Stichs. Schaut ein Spieler, der am Zug ist, wieder auf seine zuvor ausgespielten Karten (weil alle Mitspieler 
gepasst haben), hat er den Stich gewonnen. Der Besitzer wird zum Gewinner des Stichs. Der Stich wird geschlossen, indem
er vom Tisch abgeräumt wird. Solange kein Gewinner des Stichs feststeht, ist der Stich offen. 

- Runde (round): Karten austeilen und spielen, bis Gewinner feststeht

Eine Runde besteht aus mehreren Stichen, bis der Gewinner feststeht und Punkte vergeben werden. 

- Episode, Partie (episode, game): Runden spielen, bis ein Team mindestens 1000 Punkte hat 

Eine Partie besteht aus mehreren Runden und endet, wenn ein Team mindestens 1000 Punkte erreicht hat.

- PublicState = Public Observation Space = der öffentliche Spielstatus (ist für alle Spieler zu sehen)

- PrivateState = Private Observation Space = der verborgene Spielstatus (ist nur für einen bestimmten Spieler zu sehen)
 
- Observation Space: Beobachtungsraum des Spielers (Public + Private State), die Sitzplatznummern sind relativ zum Spieler angegeben:
  0 == dieser Spieler, 1 == rechter Gegner, 2 == Partner, 3 == linker Gegner

- Canonical State = Nummerierung der Spieler sind in der Normalform (kanonische Form)

- Relative State = Nummerierung der Spieler sind relativ zum Spieler 

- card = (Kartenwert, Farbe)
    - value: Kartenwert: (0 (Dog, 1 (Mah Jong), 2 bis 10, 11 (Jack), 12 (Queen), 13 (King), 14 (Ace), 15 (Dragon), 16 (Phoenix)
    - suit: Farbe der Karte: Sonderkarte, sword (a, schwarz), pagode (b, blau), jade (c, grün), star (d, rot).
  
- hand = Handkarten = cards = [card, card, ...]
 
- figure = Merkmale einer Kombination = (Typ, Länge, Rang)
    - type: Typ der Kombination, z.B. SINGLE für Einzelkarte
    - length: Länge der Kombination, z.B. 1 bei Single
    - rank: Der Rang der Kombination bestimmt, ob eine Kombination eine andere stechen kann.
 
- combination = combi = Kombination = (cards, figure) (inklusiv Passen)
  
- combinations = Kombinationsmöglichkeiten = [combi, combi, ...] (inklusiv Passen)
 
- partition = mögliche Aufteilung der Handkarten = [combi, combi, ...]

- partitions = mögliche Partitionen = [partition, partition, ...]

- History = 
  - In der DB für Brettspielwelt: [player,cards,cards_type,cards_value,card_points;...|...] (| == Stich einkassiert). 
  - Im PublicState: Der jeweilige Spieler und die gespielte Kombi.
  - In alpha-zero in der Arena: [([(state, probability, action)], reward)] 

- Arena = lässt Agenten gegeneinander antreten
 
- Game Engine = Spielumgebung = Environment

- Agent = Wählt aufgrund des Spielstatus die nächste Aktion. In der Arena wird die Aktion dann ausgeführt.

- reward = Belohnung (Punkte am Ende des Spiels)

- Anspielen (first lead) = Karten zuerst legen 

- Initiative = Anspiel-Recht erlangen
  

## Phönix

- Phönix als Karte: 
  Der Kartenwert des Phönix ist 16 (höchster Wert, liegt über den Drachen).

- Phönix als Kombination (Einzelkarte):
  Die Kombination "Phönix als Einzelkarte" hat den Rang 14.5 (schlägt das Ass, aber nicht den Drachen).

- Phönix im Stich:
  Sticht der Phönix eine Einzelkarte, so ist sein Rang im Stich 0.5 höher die gestochene Karte. 
  Im Anspiel (erste Karte im Stich) hat der Phönix den Rang 1.5.


## Ausnahmeregeln
 
- Es gibt kein Vierling, daher ist ein Drilling mit Phönix nicht möglich.

- Ein Fullhouse darf nicht aus einer 4er-Bombe mit Phönix gebildet werden (Drilling und Pärchen dürfen nicht den gleichen Rang haben).

- Der Wunsch muss zwar erfüllt werden, wenn man am Zug ist (sofern möglich), aber nicht in dem Moment, wenn man eine Bombe wirft.
