"""
Definiert einen Zufallsagenten.
"""

from src.common.rand import Random
from src.lib.cards import Card, Cards
from src.lib.combinations import Combination, build_action_space, CombinationType
from src.players.agent import Agent
from typing import Optional, Tuple

class RandomAgent(Agent):
    """
    Repräsentiert einen Agenten, der seine Entscheidungen zufällig trifft.
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

    async def announce(self) -> bool:
        """
        Die Engine fragt den Spieler, ob er ein Tichu (großes oder einfaches) ansagen möchte.

        Die Engine ruft diese Methode nur auf, wenn der Spieler ein Tichu ansagen darf.
        Die Engine verlässt sich darauf, dass die Antwort valide ist.

        :return: True, wenn ein Tichu angesagt wird, sonst False.
        """
        grand = len(self.priv.hand_cards) == 8
        return self._random.choice([True, False], [1, 19 if grand else 9])

    async def schupf(self) -> Tuple[Card, Card, Card]:
        """
        Die Engine fordert den Spieler auf, drei Karten zum Schupfen auszuwählen.

        Die Engine ruft diese Methode nur auf, wenn der Spieler noch Karten abgeben muss.
        Die Engine verlässt sich darauf, dass die Antwort valide ist.

        :return: Karte für rechten Gegner, Karte für Partner, Karte für linken Gegner.
        """
        # hand = list(self.priv.hand_cards)
        # a = hand.pop(self._random.integer(0, 14))
        # b = hand.pop(self._random.integer(0, 13))
        # c = hand.pop(self._random.integer(0, 12))
        a, b, c = self._random.sample(self.priv.hand_cards, 3)
        return a, b, c

    async def play(self, interruptable: bool = False) -> Tuple[Cards, Combination]:
        """
        Die Engine fordert den Spieler auf, eine gültige Kartenkombination auszuwählen oder zu passen.

        Die Engine ruft diese Methode nur auf, wenn der Spieler am Zug ist oder eine Bombe hat.
        Die Engine verlässt sich darauf, dass die Antwort valide ist.

        :param interruptable: (Optional) Wenn True, kann die Anfrage durch ein Interrupt abgebrochen werden.
        :return: Die ausgewählte Kombination (Karten, (Typ, Länge, Rang)) oder Passen ([], (0,0,0)).
        """
        if self.pub.current_turn_index != self.priv.player_index:
            # der Spieler ist nicht am Zug, daher kann er nur eine Bombe werfen
            if not self._random.choice([True, False], [1, 2]):  # einmal Ja, zweimal Nein
                return [], (CombinationType.PASS, 0, 0)
            combinations = [combi for combi in self.priv.combinations if combi[1][0] == CombinationType.BOMB]
            action_space = build_action_space(combinations, self.pub.trick_combination, wish_value=0)
            return self._random.choice(action_space)

        # alle spielbaren Kombinationen (inklusive Passen; wenn Passen erlaubt ist, steht Passen an erster Stelle)
        action_space = build_action_space(self.priv.combinations, self.pub.trick_combination, self.pub.wish_value)
        return self._random.choice(action_space)

    async def wish(self) -> int:
        """
        Die Engine fragt den Spieler nach einem Kartenwert-Wunsch (nach Ausspielen des Mah Jong).

        Die Engine ruft diese Methode nur auf, wenn der Spieler sich einen Kartenwert wünschen muss.
        Die Engine verlässt sich darauf, dass die Antwort valide ist.

        :return: Der gewünschte Kartenwert (2-14).
        """
        #return self._random.choice([2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14])
        return self._random.integer(2, 15)

    async def give_dragon_away(self) -> int:
        """
        Die Engine fragt den Spieler, welcher Gegner den Drachen bekommen soll.

        Die Engine ruft diese Methode nur auf, wenn der Spieler den Drachen verschenken muss.
        Die Engine verlässt sich darauf, dass die Antwort valide ist.

        :return: Der Index (0-3) des Gegners, der den Stich erhält.
        """
        #return self.priv.opponent_right_index if self._random.boolean() else self.priv.opponent_left_index
        return self._random.choice([self.priv.opponent_right_index, self.priv.opponent_left_index])
