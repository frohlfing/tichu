# Definitionen Deep Learning

## Was sind kategoriale, diskrete und stetige Variablen?

### Binäre Variable (Boolean)
- haben genau zwei Zustände
- Beispiel: Ja/Nein, An/Aus, Gewonnen/Verloren

### Kategoriale Variable (One-Hot-Kodierung)
- umfassen eine endliche Anzahl von Kategorien oder eindeutigen Gruppen.
- die Daten müssen nicht zwangsläufig eine logische Reihenfolge aufweisen.
- Beispiel: Geschlecht, Materialtyp, Zahlungsmethode, Kartenkombination

### Stetige Variable (Float-Wert)
- sind numerische Variablen, die zwischen zwei beliebigen Werten eine unendliche Anzahl von Werten aufweisen.
- die Daten weisen eine logische Reihenfolge auf (sind logisch sortierbar)
- kann aus numerischen oder Datums-/Uhrzeitwerten bestehen.
- Beispiel: Datum und Uhrzeit eines Zahlungseingangs, Siegespunkte

### Diskrete Variable (Int-Wert)
- zwischen zwei beliebigen Werten gibt es eine zählbare Anzahl von Werten
- ist immer numerisch.
- kann nicht normalisiert werden, daher problematisch und sollte vermieden werden
- kann als stetige Variable behandelt werden, wenn die Daten eine logische Reihenfolge aufweisen, also ein Wert zwischen
  den Größen interpretiert werden können. Ansonsten kann die Variable wie eine kategoriale Variable kodiert werden.
  Bsp. 1: Startposition im Autorennen        -> ein Position 1.5 wäre zwischen dem 1. 2. Wagen -> stetig
  Bsp. 2: Nummerierung der Spieler bei Tichu -> ist Spieler 1.5 mein Gegner oder mein Partner? -> Kategorial
- Beispiele: Anzahl von Kundenbeschwerden, Anzahl Handkarten, Kartenwert, Wert und Länge einer Kombination

## Klassifikationsaufgaben

### Binary-Class
Klassifikationsaufgabe mit genau zwei Klassen.
In den neuronalen Netzen verwenden wir üblicherweise Sigmoid binäre, aber Softmax-mehrklassige als letzte Schicht
des Modells.

### Multi-Class
Mehrklassen-Klassifikation bedeutet eine Klassifikationsaufgabe mit mehr als zwei Klassen.
Klassifizieren Sie beispielsweise eine Reihe von Bildern von Früchten, bei denen es sich um Orangen, Äpfel oder
Birnen handeln kann. Bei der Mehrklassen-Klassifizierung wird davon ausgegangen, dass jede Probe genau einem Etikett
zugeordnet wird: Eine Frucht kann entweder ein Apfel oder eine Birne sein, aber nicht beides gleichzeitig.

### Single-Label
Wenn wir in den neuronalen Netzwerken ein einzelnes Etikett benötigen, verwenden wir eine einzelne SoftmaxSchicht als
letzte Schicht und lernen so eine einzelne Wahrscheinlichkeitsverteilung, die sich über alle Klassen erstreckt.

### Multi-Label
Die Multilabel-Klassifizierung weist jeder Probe einen Satz von Ziellabels zu. Dies kann als Vorhersage von
Eigenschaften eines Datenpunkts angesehen werden, die sich nicht gegenseitig ausschließen , wie z. B. Themen, die für
ein Dokument relevant sind. Ein Text kann gleichzeitig über Religion, Politik, Finanzen oder Bildung handeln oder
nichts davon.

---------------------------
Nachtrag

Numerische Werte in den Bereich [-1, 1] linear skalieren: 
- Min-Max-Skalierung 
  x1_scaled = (2*x1 - max_x1 - min_x1)/(max_x1 - min_x1)
  Problem: Min-Max-Werte sind oft Außreißer. Die eigentlichen Daten werden dann auf einem sehr engen Bereich zusammengequetscht.
- Clipping & Min-Max-Skalierung -> am besten für gleichförmig verteilte Daten
  Es werden nur "vernünftige" Werte genommen. Außreißer werden als -1 und 1 behandelt.
- Z-Wert-Normalisierung -> am besten für normalverteilte Daten
  Über Mittelwert und Standardabweichung skalieren
  x1_scaled = (x1 - mean_x1)/stddev_x1
  Bei Normalverteilung liegen 67% im Bereich [-1, 1]. Werte außerhalb dieses Bereichs werden seltener, je größer der absolute Wert wird. 

Kategoriale Werte in eine One-hot-Encoding (1-aus-n-Kodierung) konvertieren

s.a.
https://artemoppermann.com/de/data-preprocessing-in-machine-learning/


