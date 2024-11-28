from src.players.agent import Agent
from src.private_state import PrivateState
from src.public_state import PublicState


class RandomAgent(Agent):
    def __init__(self, seed=None):
        super().__init__(seed=seed) 

    # Welche Karten an die Mitspieler abgeben?
    # return: Karte für rechten Gegner, Karte für Partner, Karte für linken Gegner (d.h. kanonische Anordnung)
    def schupf(self, pub: PublicState, priv: PrivateState) -> list[tuple]:
        hand = list(priv.hand)
        return [hand.pop(self._rand(0, 14)), hand.pop(self._rand(0, 13)), hand.pop(self._rand(0, 12))]

    # Tichu ansagen?
    def announce(self, pub: PublicState, priv: PrivateState, grand: bool = False) -> bool:
        return self._rand(0, 20 if grand else 10) == 0

    # Welche Kombination soll gespielt werden?
    # action_space: Mögliche Kombinationen (inklusiv Passen)
    # return: Ausgewählte Kombination (Karten, (Typ, Länge, Wert))
    def combination(self, pub: PublicState, priv: PrivateState, action_space: list[tuple]) -> tuple:
        return action_space[self._rand(0, len(action_space))]

    # Welcher Kartenwert wird gewünscht?
    # return: Wert zw. 2 und 14
    def wish(self, pub: PublicState, priv: PrivateState) -> int:
        return self._rand(2, 15)

    # Welcher Gegner soll den Drachen bekommen?
    # return: Nummer des Gegners
    def gift(self, pub: PublicState, priv: PrivateState) -> int:
        return priv.opponent_right if self._rand(0, 2) == 1 else priv.opponent_left
