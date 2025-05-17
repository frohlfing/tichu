"""
Definiert die Datenstruktur für den privaten Spielzustand eines Spielers.
"""

from dataclasses import dataclass, field
from src.lib.cards import Cards, stringify_cards
from src.lib.combinations import build_combinations, Combination
from src.lib.partitions import build_partitions, Partition
from typing import List, Dict, Any, Tuple

@dataclass
class PrivateState:
    """
    Datencontainer für den privaten Spielzustand eines Tichu-Spielers.

    Diese Klasse sammelt die Daten, die nur dem jeweiligen Spieler bekannt sind.

    :ivar player_index: Der Index dieses Spielers am Tisch (zwischen 0 und 3).
    :ivar _hand_cards: (property `hand_cards`) Die aktuellen Handkarten des Spielers (absteigend sortiert, z.B. [(8,3), (2,4), (0,1)].
    :ivar given_schupf_cards: Die drei Karten, die der Spieler zum Schupfen an den rechten Gegner, Partner und linken Gegner abgegeben hat.  todo schupf_cards in kanonischer Form
    :ivar received_schupf_cards: Die drei Karten, die der Spieler beim Schupfen vom rechten Gegner, Partner und linken Gegner erhalten hat.
    """
    # --- Spielerinformationen ---
    player_index: int = -1

    # --- Information über die aktuelle Runde ---
    _hand_cards: Cards = field(default_factory=list)
    given_schupf_cards: Cards = field(default_factory=list)
    received_schupf_cards: Cards = field(default_factory=list)  # todo in test_private_state aufnehmen
    # todo schupf_cards in kanonischer Form definieren ([Spieler 0 bis 3], wobei schupf_cards[player_index] immer None ist):
    #  given_schupf_cards: List[Optional[Card]] = field(default_factory=lambda: [None, None, None, None])
    #  received_schupf_cards: List[Optional[Card]] = field(default_factory=lambda: [None, None, None, None])

    # --- Private Caches (verborgene Variablen) ---
    _combination_cache: List[Tuple[Cards, Combination]] = field(default_factory=list, repr=False)  # Nur intern verwendet, daher repr=False
    _partition_cache: List[Partition] = field(default_factory=list, repr=False)
    _partitions_aborted: bool = field(default=True, repr=False)

    @property
    def hand_cards(self) -> Cards:
        """Die aktuellen Handkarten des Spielers (absteigend sortiert, z.B. [(8,3), (2,4), (0,1)]."""
        return self._hand_cards

    @hand_cards.setter
    def hand_cards(self, value: Cards) -> None:
        """Setzt die Handkarten und leert den Cache."""
        self._hand_cards = value
        self._combination_cache = []
        self._partition_cache = []
        self._partitions_aborted = True

    def to_dict(self) -> Dict[str, Any]:
        """
        Konvertiert den Zustand in ein Dictionary für JSON-Serialisierung.

        :return: Eine Dictionary-Repräsentation des Zustands mit Karten als Strings.
        """
        return {
            "player_index": self.player_index,
            "hand_cards": stringify_cards(self.hand_cards),
            "given_schupf_cards": stringify_cards(self.given_schupf_cards),
            "received_schupf_cards": stringify_cards(self.received_schupf_cards),
            # todo schupf_cards in kanonischer Form
            #  "given_schupf_cards": [stringify_cards([card]) if card else None for card in self.given_schupf_cards],
            #  "received_schupf_cards": [stringify_cards([card]) if card else None for card in self.received_schupf_cards],
        }

    @property
    def partner_index(self) -> int:
        """Der Index des Partners (0-3)."""
        return (self.player_index + 2) % 4

    @property
    def opponent_right_index(self) -> int:
        """Der Index des rechten Gegners (0-3)."""
        return (self.player_index + 1) % 4

    @property
    def opponent_left_index(self) -> int:
        """Der Index des linken Gegners (0-3)."""
        return (self.player_index + 3) % 4

    @property
    def combinations(self) -> List[Tuple[Cards, Combination]]:
        """Kombinationsmöglichkeiten der Hand (zuerst die besten)"""
        if not self._combination_cache and self.hand_cards:
            self._combination_cache = build_combinations(self.hand_cards)
        return self._combination_cache

    @property
    def partitions(self) -> List[Partition]:
        """Mögliche Partitionen der Hand (zuerst die besten)"""
        if not self._partition_cache and self.hand_cards:
            self._partitions_aborted = not build_partitions(self._partition_cache, combis=self.combinations, counter=len(self.hand_cards))
        return self._partition_cache
