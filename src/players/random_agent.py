"""
Definiert einen Zufallsagenten.
"""

from src.common.rand import Random
from src.lib.cards import Card, Cards
from src.lib.combinations import Combination
from src.players.agent import Agent
from src.private_state import PrivateState
from src.public_state import PublicState
from typing import Optional, List, Tuple

class RandomAgent(Agent):
    """
    Repräsentiert einen Agenten, der seine Entscheidungen zufällig trifft.

    Erbt von der Basisklasse `Agent`.
    """
    def __init__(self, name: Optional[str] = None, session_id: Optional[str] = None, seed: int = None):
        """
        Initialisiert einen neuen Agenten.

        :param name: (Optional) Name für den Agenten. Wenn None, wird einer generiert.
        :param session_id: (Optional) Aktuelle Session des Agenten. Wenn None, wird eine Session generiert.
        :param seed: (Optional) Seed für den internen Zufallsgenerator (für Tests).
        """
        super().__init__(name, session_id=session_id)
        self._random = Random(seed)  # Zufallsgenerator, geeignet für Multiprocessing

    # ------------------------------------------------------
    # Entscheidungen
    # ------------------------------------------------------

    async def schupf(self, pub: PublicState, priv: PrivateState) -> Tuple[Card, Card, Card]:
        """
        Fordert den Spieler auf, drei Karten zum Schupfen auszuwählen.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :return: Karte für rechten Gegner, Karte für Partner, Karte für linken Gegner.
        """
        hand = list(priv.hand_cards)
        a = hand.pop(self._random.integer(0, 14))
        b = hand.pop(self._random.integer(0, 13))
        c = hand.pop(self._random.integer(0, 12))
        return a, b, c

    async def announce(self, pub: PublicState, priv: PrivateState) -> bool:
        """
        Fragt den Spieler, ob er Tichu (oder Grand Tichu) ansagen möchte.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :return: True, wenn angesagt wird, sonst False.
        """
        grand = pub.current_phase == "dealing" and len(priv.hand_cards) == 8
        return self._random.choice([True, False], [1, 19] if grand else [1, 9])

    async def play(self, pub: PublicState, priv: PrivateState, action_space: List[Tuple[Cards, Combination]]) -> Tuple[Cards, Combination]:
        """
        Fordert den Spieler auf, eine gültige Kartenkombination auszuwählen oder zu passen.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :param action_space: Mögliche Kombinationen (inklusive Passen; wenn Passen erlaubt ist, steht Passen an erster Stelle).
        :return: Die ausgewählte Kombination (Karten, (Typ, Länge, Wert)) oder Passen ([], (0,0,0)).
        """
        return action_space[self._random.integer(0, len(action_space))]

    async def wish(self, pub: PublicState, priv: PrivateState) -> int:
        """
        Fragt den Spieler nach einem Kartenwert-Wunsch (nach Ausspielen des Mah Jong).

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :return: Der gewünschte Kartenwert (2-14).
        """
        return self._random.choice([2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14])

    async def give_dragon_away(self, pub: PublicState, priv: PrivateState) -> int:
        """
        Fragt den Spieler, welchem Gegner der mit dem Drachen gewonnene Stich gegeben werden soll.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :return: Der Index (0-3) des Gegners, der den Stich erhält.
        """
        return self.opponent_right_index if self._random.boolean() else self.opponent_left_index
