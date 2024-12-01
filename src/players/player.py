import numpy as np
from typing import Optional
from src.private_state import PrivateState
from src.public_state import PublicState


class Player:
    # Basisklasse für einen Spieler

    def __init__(self, seed=None):
        self._seed: Optional[int] = seed  # Initialwert für Zufallsgenerator (Integer > 0 oder None)
        #self._random: Optional[np.random.Generator] = None  # wegen Multiprocessing ist ein eigener Zufallsgenerator notwendig
        self._random = None  # wegen Multiprocessing ist ein eigener Zufallsgenerator notwendig

    @property
    def name(self) -> str:
        return type(self).__name__

    def reset(self):  # pragma: no cover
        pass

    # Welche Karten an die Mitspieler abgeben?
    # return: Karte für rechten Gegner, Karte für Partner, Karte für linken Gegner
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

    # Gibt eine zufällige Ganzzahl zwischen low (inklusiv) und high (exklusiv) zurück
    def _rand_int(self, low, high):
        if not self._random:
            self._random = np.random.default_rng(self._seed)
        return self._random.integers(low, high)