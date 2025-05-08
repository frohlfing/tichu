from src.common.rand import Random
from src.players.agent import Agent
from src.private_state import PrivateState
from src.public_state import PublicState
from typing import Optional


class RandomAgent(Agent):
    """
    Repräsentiert einen Agenten, der seine Entscheidungen zufällig trifft.

    Erbt von der Basisklasse `Agent`.
    """
    def __init__(self, name: Optional[str] = None, uuid: Optional[str] = None, seed: int = None):
        super().__init__(name, uuid=uuid)
        self._random = Random(seed)  # Zufallsgenerator, geeignet für Multiprocessing

    # ------------------------------------------------------
    # Entscheidungen
    # ------------------------------------------------------

    async def schupf(self, pub: PublicState, priv: PrivateState) -> list[tuple]:
        """
        Fordert den Spieler auf, drei Karten zum Schupfen auszuwählen.

        Muss von Subklassen implementiert werden.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :return: Die Liste der Karten (Karte für rechten Gegner, Karte für Partner, Karte für linken Gegner).
        """
        hand = list(priv.hand)
        return [hand.pop(self._random.integer(0, 14)), hand.pop(self._random.integer(0, 13)), hand.pop(self._random.integer(0, 12))]

    async def announce(self, pub: PublicState, priv: PrivateState, grand: bool = False) -> bool:
        """
        Fragt den Spieler, ob er Tichu (oder Grand Tichu) ansagen möchte.

        Muss von Subklassen implementiert werden.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :param grand: True, wenn nach Grand Tichu gefragt wird, False für kleines Tichu.
        :return: True, wenn angesagt wird, sonst False.
        """
        return self._random.choice([True, False], [1, 19] if grand else [1, 9])

    async def combination(self, pub: PublicState, priv: PrivateState, action_space: list[tuple]) -> tuple:
        """
        Fordert den Spieler auf, eine gültige Kartenkombination auszuwählen oder zu passen.

        Muss von Subklassen implementiert werden.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :param action_space: Mögliche Kombinationen (inklusiv Passen; wenn Passen erlaubt ist, steht Passen an erster Stelle).
        :return: Die ausgewählte Kombination (Karten, (Typ, Länge, Wert)) oder Passen ([], (0,0,0)).
        """
        return action_space[self._random.integer(0, len(action_space))]

    async def wish(self, pub: PublicState, priv: PrivateState) -> int:
        """
        Fragt den Spieler nach einem Kartenwert-Wunsch (nach Ausspielen des Mah Jong).

        Muss von Subklassen implementiert werden.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :return: Der gewünschte Kartenwert (2-14).
        """
        return self._random.choice([2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14])

    async def gift(self, pub: PublicState, priv: PrivateState) -> int:
        """
        Fragt den Spieler, welchem Gegner der mit dem Drachen gewonnene Stich gegeben werden soll.

        Muss von Subklassen implementiert werden.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :return: Der Index (0-3) des Gegners, der den Stich erhält.
        """
        return self.opponent_right_index if self._random.boolean() else self.opponent_left_index
