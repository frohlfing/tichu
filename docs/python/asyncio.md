# Asyncio, Threading und Multiprocessing

## Coroutine ausführen
```
import asyncio
from asyncio import Future

async def compute() -> int:
    # Eine einfache Coroutine, die eine Sekunde wartet und dann 42 zurückgibt
    await asyncio.sleep(1)
    return 42

# Hier erhält man nur ein Coroutine-Objekt, die Funktion wird nicht ausgeführt 
coro = compute()

# Hier wird ein neuer Task im Hintergrund gestartet und die Coroutine ausgeführt 
task: Future = asyncio.create_task(coro)  # ist gleich: asyncio.create_task(compute())   

# Hier wird gewartet, bis der Task fertig wird und das Ergebnis der Coroutine liefert
result: int = await task

# Hier wird die Coroutine direkt ausgeführt und gewartet, bis diese fertig ist: 
result: int = await coro
``` 

### Coroutine
Eine Coroutine ist eine Funktion, die mit dem Schlüsselwort `async` deklariert ist.  
Diese Funktionen können und sollten `await` verwenden, um auf andere Coroutines oder asynchrone Operationen zu warten. 

Um das kooperative Multitasking zu ermöglichen, sollte jede Coroutine mindestens eine `await`-Anweisung enthalten, damit sie die Kontrolle an den Event-Loop zurückgeben kann.
Wenn das nicht der Fall ist, sollt die Coroutine besser im Thread laufen.

### await
Mit `await` wartest du darauf, dass eine Coroutine oder eine asynchrone Operation abgeschlossen wird. 

### asyncio.create_task
Diese Funktion erstellt ein Task, die eine Coroutine im Hintergrund ausführt. 
Die aktuelle Coroutine wird nicht angehalten und kann sofort fortfahren.

### task vs future
Ein Future-Objekt repräsentiert das (u.U. noch nicht vorliegende) Ergebnis einer Coroutine oder einer blockierenden 
Funktion, die in einem separaten Thread oder Prozess ausgeführt weird. 

Ein Task-Objekt ist eine Unterklasse von `Future` und repräsentiert ausschließlich das Ergebnis einer Coroutine. 


## asyncio.gather

```
import asyncio

async def compute(x: int) -> int:
    # Eine einfache Coroutine, die eine Sekunde wartet und dann das Quadrat von x zurückgibt
    await asyncio.sleep(1)
    return x * x

# Erzeugen mehrerer Coroutines
coros = [compute(i) for i in range(5)]

# Verwenden von asyncio.gather, um alle Coroutines parallel auszuführen und auf ihre Ergebnisse zu warten
results: list[int] = await asyncio.gather(*coros)
```

Diese `asyncio.gather` nimmt mehrere Coroutines und führt sie gleichzeitig aus. Sie gibt eine einzige Coroutine zurück, die 
abgeschlossen wird, wenn alle übergebenen Coroutines abgeschlossen sind.


## Blockierende Funktion im Thread bzw. Prozess ausführen

```
import asyncio
import time
from concurrent.futures import Future, ThreadPoolExecutor, ProcessPoolExecutor

def blocking_function() -> int:
    # Eine blockierende Funktion, die zwei Sekunden wartet und dann 42 zurückgibt
    time.sleep(2)
    return 42

loop = asyncio.get_running_loop()
with ThreadPoolExecutor() as pool:
    # Ausführen der blockierenden Funktion im Thread
    future: Future = loop.run_in_executor(pool, blocking_function)
    result: int = await future
    
with ProcessPoolExecutor() as pool:
    # Ausführen der blockierenden Funktion im Prozess
    future: Future = loop.run_in_executor(pool, blocking_function)
    result: int = await future
```

### Map-Funktion
```
def intensive_computation(n):
    time.sleep(2)  # Simuliert eine rechenintensive Aufgabe
    return n * n

numbers = [1, 2, 3, 4, 5]

# Erstelle einen ProcessPoolExecutor
with concurrent.futures.ProcessPoolExecutor() as executor:
    # Verwende map, um die intensive_computation-Funktion parallel auszuführen
    results: list[int] = list(executor.map(intensive_computation, numbers))
```


## Debug-Modus

```
if __name__ == "__main__":
    asyncio.run(main(), debug=True)
```

### Vorteile des Debug-Modus
- Erweiterte Fehlermeldungen: Der Debug-Modus liefert detailliertere Fehlermeldungen und Tracebacks, die dir helfen können, die genaue Ursache eines Problems zu identifizieren.
- Warnungen bei unsicheren Praktiken: asyncio gibt Warnungen aus, wenn unsichere oder ineffiziente Praktiken erkannt werden, wie z.B. das Erstellen von Tasks ohne sie zu awaiten.
- Erkennung von hängenden Tasks: Der Debug-Modus kann hängende Tasks erkennen, die nicht beendet werden, und entsprechende Warnungen ausgeben.
- Überprüfung von Ressourcen: Der Debug-Modus kann Ressourcenlecks erkennen, wie z.B. nicht geschlossene Sockets oder Dateien.

### Was passiert im Debug-Modus:
- Debug-Logs: Es werden zusätzliche Debug-Logs ausgegeben, die dir helfen können, den Ablauf deines Programms besser zu verstehen.
- Langsame Tasks erkennen: Der Debug-Modus kann erkennen, wenn Tasks länger als erwartet dauern, und entsprechende Warnungen ausgeben.
- Strenge