import numpy as np
from src.private_state import PrivateState
from src.public_state import PublicState


class Player:
    def __init__(self, seed=None):
        self._seed = seed  # Initialwert für Zufallsgenerator (Integer > 0 oder None)
        self._random = None  # wegen Multiprocessing ist ein eigener Zufallsgenerator notwendig

    @property
    def name(self) -> str:
        return type(self).__name__

    def reset(self):  # pragma: no cover
        pass

    # Welche Karten an die Mitspieler abgeben?
    # return: Karte für rechten Gegner, Karte für Partner, Karte für linken Gegner (d.h. kanonische Anordnung)
    def schupf(self, pub: PublicState, priv: PrivateState) -> list[tuple]:  # pragma: no cover
        pass

    # Tichu ansagen?
    def announce(self, pub: PublicState, priv: PrivateState, grand: bool = False) -> bool:  # pragma: no cover
        pass

    # Welche Kombination soll gespielt werden?
    # action_space: Mögliche Kombinationen (inklusiv Passen)
    # return: Ausgewählte Kombination (Karten, (Typ, Länge, Wert))
    def combination(self, pub: PublicState, priv: PrivateState, action_space: list[tuple]) -> tuple:  # pragma: no cover
        pass

    # Welcher Kartenwert wird gewünscht?
    # return: Wert zw. 2 und 14
    def wish(self, pub: PublicState, priv: PrivateState) -> int:  # pragma: no cover
        pass

    # Welcher Gegner soll den Drachen bekommen?
    # return: Nummer des Gegners
    def gift(self, pub: PublicState, priv: PrivateState) -> int:  # pragma: no cover
        pass

    # Return random integers from low (inclusive) to high (exclusive).
    def _rand(self, a, b):
        if not self._random:
            self._random = np.random.RandomState(seed=self._seed)
        return self._random.randint(a, b)
