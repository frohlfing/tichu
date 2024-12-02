# Mutable vs. Immutability

In Python gibt es zwei wichtige Konzepte: Mutability (Veränderlichkeit) und Immutability (Unveränderlichkeit). 
Diese Begriffe beziehen sich darauf, ob der Zustand eines Objekts nach seiner Erstellung geändert werden kann oder nicht.

## Mutable (veränderliche) Objekte

Mutable Objekte sind solche, deren Zustand nach der Erstellung geändert werden kann. 
Beispiele für mutable Objekte in Python sind:

- Listen (`list`)
- Dictionaries (`dict`)
- Sets (`set`)
- Klassen, je nach Implementierung

### Besipiel 

Diese Klasse ist mutable, da sowohl das `name`-Attribut als auch die `kinder`-Liste nach der Erstellung des Objekts 
geändert werden können.

```
class Hund:
    def __init__(self, name, kinder=None):
        self.name = name
        self.kinder = kinder if kinder else []

mein_hund = Hund("Bello", ["Charlie"])
print(mein_hund.name)  # Ausgabe: Bello
print(mein_hund.kinder)  # Ausgabe: ['Charlie']

# Ändern der Liste direkt
mein_hund.kinder.append("Lucy")
print(mein_hund.kinder)  # Ausgabe: ['Charlie', 'Lucy']
```

## Immutable (unveränderliche) Objekte

Immutable Objekte sind solche, deren Zustand nach der Erstellung nicht geändert werden kann. Beispiele für immutable 
Objekte in Python sind:

- Zahlen (`int`, `float`, `bool`)
- Strings (`str`)
- Tupel (`tuple`)
- Klassen, je nach Implementierung

In diesem Beispiel wird eine Kopie der Liste zurückgegeben, wenn auf das `kinder`-Attribut zugegriffen wird. 
Dadurch können keine Änderungen direkt an der originalen Liste vorgenommen werden. 
Stattdessen gibt es eine Methode `add_kind`, um neue Elemente hinzuzufügen. So bleibt die interne Liste geschützt.

```
class Hund:
    def __init__(self, name, kinder=None):
        self._name = name
        self._kinder = kinder if kinder else []

    @property
    def name(self):
        return self._name

    @property
    def kinder(self):
        # Rückgabe einer Kopie der Liste, um Mutationsversuche zu verhindern
        return list(self._kinder)

    def add_kind(self, kind):
        self._kinder.append(kind)

mein_hund = Hund("Bello", ["Charlie"])
print(mein_hund.name)  # Ausgabe: Bello
print(mein_hund.kinder)  # Ausgabe: ['Charlie']

# Versuch, die Liste direkt zu ändern
mein_hund.kinder.append("Lucy")  # Dies ändert nicht die originale Liste
print(mein_hund.kinder)  # Ausgabe: ['Charlie']

# Adding a kind properly
mein_hund.add_kind("Lucy")
print(mein_hund.kinder)  # Ausgabe: ['Charlie', 'Lucy']
```

## copy() 
Erstellt eine flache Kopie des Objekts. Das bedeutet, dass nur das Objekt selbst kopiert wird, aber nicht die Objekte, 
auf die es verweist. Wenn das Originalobjekt also Referenzen auf andere Objekte enthält, werden diese Referenzen in der 
Kopie beibehalten. Änderungen an den referenzierten Objekten wirken sich sowohl auf das Original als auch auf die Kopie 
aus.

```
original = [1, [2, 3], 4]
shallow_copy = original.copy()

shallow_copy[1][0] = 'changed'
print(original)  # Ausgabe: [1, ['changed', 3], 4]
print(shallow_copy)  # Ausgabe: [1, ['changed', 3], 4]
```

## deepcopy()
Erstellt eine tiefe Kopie des Objekts. Das bedeutet, dass sowohl das Objekt selbst als auch alle Objekte, auf die es 
verweist, rekursiv kopiert werden. Änderungen an den referenzierten Objekten wirken sich nicht auf das Original aus.

```
from copy import deepcopy

original = [1, [2, 3], 4]
deep_copy = deepcopy(original)

deep_copy[1][0] = 'changed'
print(original)  # Ausgabe: [1, [2, 3], 4]
print(deep_copy)  # Ausgabe: [1, ['changed', 3], 4]
```