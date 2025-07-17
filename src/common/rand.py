"""
Dieses Modul implementiert einen Zufallsgenerator, der speziell auf die Verarbeitung mit Multiprocessing ausgelegt ist.
"""

import random
from typing import Any, Optional

class Random:
    """
    Zufallsgenerator, für Multiprocessing ausgelegt.

    Beim Multiprocessing würde jeder Unterprozess die gleichen Zufallszahlen generieren, wenn bereits vor dem Prozess-Fork der
    Zufallsgenerator initialisiert wird. Die Prozesse hätten alle denselben Seed.

    Daher wird der interne Zufallsgenerator mit dem Seed erst initialisiert, wenn die erste Zufallszahl generiert wird.
    """

    def __init__(self, seed: int = None):
        """
        Konstruktor.

        :param seed: (Optional) Initialwert für den Zufallsgenerator (größer 0 oder None).
        """
        self._seed: Optional[int] = seed
        self._random: Optional[random.Random] = None # wegen Multiprocessing ist ein eigener Zufallsgenerator notwendig

    def float(self, low, high) -> float:
        """
        Gibt eine zufällige Dezimalzahl zwischen low (inklusiv) und high (exklusiv) zurück.

        :param low: Untere Grenze (inklusive).
        :param high: Obere Grenze (exklusive).
        :return: Eine zufällige Dezimalzahl.
        """
        self._ensure_initialized()
        return self._random.random() * (high - low) + low

    def integer(self, low, high) -> int:
        """
        Gibt eine zufällige Ganzzahl zwischen low (inklusiv) und high (exklusiv) zurück.

        :param low: Untere Grenze (inklusive).
        :param high: Obere Grenze (exklusive).
        :return: Eine zufällige Ganzzahl.
        """
        self._ensure_initialized()
        return self._random.randint(low, high - 1)

    def boolean(self, prob_true: float = 0.5) -> bool:
        """
        Gibt zufällig True oder False zurück.

        :param prob_true: (Optional) Wahrscheinlichkeit für True (zwischen 0.0 und 1.0).
        :return: Ein zufälliger Wahrheitswert.
        """
        self._ensure_initialized()
        return self._random.random() < prob_true

    def choice(self, seq: list|tuple, weights: list|tuple = None) -> Any:
        """
        Wählt ein zufälliges Element aus einer Sequenz.

        :param seq: Die Eingabesequenz.
        :param weights: (Optional) Die Gewichtung (für jedes Element ein Wert, z.B. [1, 3, 6] oder normiert [0.1, 0.3, 0.6]).
        :return: Ein zufällig ausgewähltes Element.
        """
        self._ensure_initialized()
        if weights is None:
            return self._random.choice(seq)
        else:
            return self._random.choices(seq, weights)[0]

    def sample(self, seq: list|tuple, k: int) -> list:
        """
        Wählt k zufällige Elemente aus einer Sequenz aus (ohne zurücklegen).

        :param seq: Die Eingabesequenz.
        :param k: Anzahl der zu ziehenden Elemente.
        :return: Eine Liste zufälliger Elemente.
        """
        self._ensure_initialized()
        return self._random.sample(seq, k)

    def shuffle(self, seq: list) -> None:
        """
        Mischt eine Sequenz in-place.

        :param seq: Die zu mischende Sequenz (mutable).
        """
        self._ensure_initialized()
        self._random.shuffle(seq)

    def _ensure_initialized(self):
        """
        Stellt sicher, dass der Zufallsgenerator initialisiert ist.
        """
        if not self._random:
            self._random = random.Random(self._seed)
