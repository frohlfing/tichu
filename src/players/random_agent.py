from src.common.rand import Random
from src.players.agent import Agent
from src.private_state import PrivateState
from src.public_state import PublicState
from typing import Optional


class RandomAgent(Agent):
    # Zufallsagent
    #
    # Die Entscheidungen werden zufällig getroffen.

    def __init__(self, player_name: Optional[str] = None, player_id: Optional[str] = None, seed: int = None):
        super().__init__(player_name, player_id=player_id)
        self._random = Random(seed)  # Zufallsgenerator, geeignet für Multiprocessing

    # ------------------------------------------------------
    # Entscheidungen
    # ------------------------------------------------------

    # Welche Karten an die Mitspieler abgeben?
    # return: Karte für rechten Gegner, Karte für Partner, Karte für linken Gegner
    def schupf(self, pub: PublicState, priv: PrivateState) -> list[tuple]:
        hand = list(priv.hand)
        return [hand.pop(self._random.integer(0, 14)), hand.pop(self._random.integer(0, 13)), hand.pop(self._random.integer(0, 12))]

    # Tichu ansagen?
    def announce(self, pub: PublicState, priv: PrivateState, grand: bool = False) -> bool:
        return self._random.choice([True, False], [1, 19] if grand else [1, 9])

    # Welche Kombination soll gespielt werden?
    # action_space: Mögliche Kombinationen (inklusiv Passen)
    # return: Ausgewählte Kombination (Karten, (Typ, Länge, Wert))
    def combination(self, pub: PublicState, priv: PrivateState, action_space: list[tuple]) -> tuple:
        return action_space[self._random.integer(0, len(action_space))]

    # Welcher Kartenwert wird gewünscht?
    # return: Wert zwischen 2 und 14
    def wish(self, pub: PublicState, priv: PrivateState) -> int:
        return self._random.choice([2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14])

    # Welcher Gegner soll den Drachen bekommen?
    # return: Nummer des Gegners
    def gift(self, pub: PublicState, priv: PrivateState) -> int:
        return priv.opponent_right if self._random.boolean() else priv.opponent_left
