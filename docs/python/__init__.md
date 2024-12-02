# __init__.py

Die Datei __init__.py hat mehrere wichtige Funktionen in Python-Paketen:

- Kennzeichnung eines Verzeichnisses als Paket: 

Wenn du eine Datei `__init__.py` in einem Verzeichnis hast, markiert dies das Verzeichnis als Python-Paket. Das ermöglicht es dir, Module aus diesem Verzeichnis zu importieren.

- Initialisierungscode: 

Du kannst Code in `__init__.py` schreiben, der beim Import des Pakets ausgeführt wird. Das ist nützlich für Initialisierungen, wie das Laden von Konfigurationen oder das Einrichten von Loggern.

- Paketstruktur: 

Du kannst in `__init__.py` bestimmte Funktionen, Klassen oder Module importieren, damit sie beim Import des Pakets automatisch verfügbar sind.


Beispielstruktur:

```
mypackage/
    __init__.py
    modul_a.py
    modul_b.py
```


Inhalt von `__init__.py`:

```
# Initialisierungscode oder Importe
from .modul_a import some_function
from .modul_b import another_function
```

Jetzt kannst du direkt aus dem Paket importieren:
```
from mypackage import some_function, another_function
```