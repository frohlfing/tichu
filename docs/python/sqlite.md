# SQLite

##  Die 5 Storage Classes

Storage Class	Beschreibung	Typische Verwendung
NULL	Fehltwert, „kein Wert vorhanden“.	Unbekannte oder nicht gesetzte Daten.
INTEGER	Ganze Zahl, intern in 1, 2, 3, 4, 6 oder 8 Bytes gespeichert – je nach Größe des Werts.	Zähler, IDs, Jahr, Mengen.
REAL	Gleitkommazahl (8‑Byte IEEE 754).	Preise, Messwerte mit Nachkommastellen.
TEXT	Zeichenkette in der DB‑Kodierung (UTF‑8, UTF‑16BE/LE). Länge theoretisch unbegrenzt.	Namen, Beschreibungen, JSON.
BLOB	„Binary Large Object“ – beliebige Bytes, unverändert gespeichert.	Bilder, komprimierte Daten, Binärformate.

### Besonderheiten

Manifest Typing: Der tatsächliche Typ wird vom gespeicherten Wert bestimmt, nicht zwingend von der Spaltendeklaration.

Booleans gibt es nicht als eigenen Typ – üblich ist 0/1 (INTEGER) oder 'true'/'false' (TEXT).

Datum/Zeit: kein eigener Typ – Speicherung als TEXT (ISO‑8601), REAL (Julianisches Datum) oder INTEGER (Unix‑Zeitstempel) ist üblich.

### Speicherbedarf von INTEGER in SQLite

SQLite speichert Ganzzahlen (INTEGER) in einer von sechs möglichen Byte-Größen:

Zahlenwertbereich	Speichergröße
-128 bis 127	1 Byte
-32.768 bis 32.767	2 Byte
-8.388.608 bis 8.388.607	3 Byte
-2.147.483.648 bis 2.147.483.647	4 Byte
-140.737.488.355.328 bis 140.737.488.355.327	6 Byte
-9.223.372.036.854.775.808 bis 9.223.372.036.854.775.807	8 Byte

SQLite verwendet also zwischen 1 und 8 Byte, je nachdem, wie groß der gespeicherte Wert ist2.