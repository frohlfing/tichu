# todo Dokumentieren (reStructuredText)

import random
from typing import Any, Optional

# Random ist für Multiprocessing ausgelegt.
#
# Beim Multiprocessing würde jeder Unterprozess die gleichen Zufallszahlen generieren,
# wenn bereits vor dem Prozess-Fork der Zufallsgenerator initialisiert wird! Die Prozesse hätten alle denselben Seed.
# Daher wird der interne Zufallsgenerator mit dem Seed erst initialisiert, wenn die erste Zufallszahl benötigt wird.

class Random:
    def __init__(self, seed: int = None):
        self._seed: Optional[int] = seed  # Initialwert für Zufallsgenerator (Integer > 0 oder None)
        self._random: Optional[random.Random] = None # wegen Multiprocessing ist ein eigener Zufallsgenerator notwendig

    def integer(self, low, high) -> int:
        # Gibt eine zufällige Ganzzahl zwischen low (inklusiv) und high (exklusiv) zurück
        self._initialize_random()
        return self._random.randint(low, high - 1)

    def boolean(self) -> bool:
        # Wählt zufällig True oder False
        self._initialize_random()
        return self._random.randint(0, 1) == 1

    def choice(self, seq: list|tuple, weights: list|tuple = None) -> Any:
        # Wählt ein zufälliges Element aus einer Sequenz aus
        # Wenn weights angegeben ist, erfolgt die Auswahl nach dieser Gewichtung.
        # Beispiel 1: decision = self._rand_choice([False, True])
        # Beispiel 2: action = self._rand_choice([Action.PASS, Action.PLAY], [1, len(combinations)])
        self._initialize_random()
        if weights is None:
            return self._random.choice(seq)
        else:
            return self._random.choices(seq, weights)[0]

    def sample(self, seq: list|tuple, k: int) -> list:
        # Wählt k zufällige Elemente aus einer Sequenz aus (ohne zurücklegen)
        # Beispiel: cards = self._rand_sample(self._hand.items, 3)
        self._initialize_random()
        return self._random.sample(seq, k)

    def shuffle(self, seq: list) -> None:
        # Mischt die Sequenz (mutable)
        self._initialize_random()
        self._random.shuffle(seq)

    def _initialize_random(self):
        if not self._random:
            self._random = random.Random(self._seed)
