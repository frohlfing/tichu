# Server für TICHU

## Definitionen
- card = (Kartenwert, Farbe)
- hand = Handkarten = cards = [card, card, ...]
- figure = Figur einer Kombination = (Typ, Länge, Wert)
- combination = combi = Kombination = (cards, figure) (inklusiv Passen)
- combinations = Kombinationsmöglichkeiten = [combi, combi, ...] (inklusiv Passen)
- partition = mögliche Aufteilung der Handkarten = [combi, combi, ...]
- Partitions = mögliche Partitionen = [partition, partition, ...]
- canonical = Spielstatus so transformieren, dass der aktuelle Spieler die Nummer 0 bekommt
- reward = Belohnung (Punkte am Ende des Spiels)
- Anspielen (first lead) = Karten zuerst legen 
- Initiative = Anspiel-Recht erlangen
- Runde = Karten austeilen und spielen, bis Gewinner feststeht
- Episode = Partie = Runden spielen, bis ein Team mindestens 1000 Punkte hat 
- Arena = Spielumgebung = Environment
- PublicState = Public Observation Space = Spielstatus, der für alle Spieler zu sehen ist
- PrivateState = Private Observation Space = Spielstatus, der nur für einen bestimmten Spieler zu sehen ist
- Agent = Wählt aufgrund des Spielstatus die nächste Aktion. In der Arena wird die Aktion dann ausgeführt.
- History = 
  - In der DB für Brettspielwelt: [player,cards,cards_type,cards_value,card_points;...|...] (| == Stich einkassiert). 
  - Im PublicState: Der jeweilige Spieler und die gespielte Kombi.
  - In alpha-zero in der Arena: [ ([(state, probability, action)], reward) ] -> 
- Canonical State = Nummerierung der Spieler sind so gedreht, dass der Spieler, dessen Perspektive beobachtet wird, die Nummer 0 erhält
  <pre>
  # Umrechnung:
  canonical_index = (real_index + 4 - player) % 4
  real_index = (player + canonical_index) % 4
  </pre>
  
**todo** History für Arena aus alpha-zero übernehmen. History in PublicState löschen. 
