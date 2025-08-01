"""
Definiert die Datenstruktur für den privaten Spielzustand eines Spielers.
"""

from dataclasses import dataclass, field
from src.lib.cards import Card, Cards
from src.lib.combinations import build_combinations, Combination, CombinationType
from src.lib.partitions import build_partitions, Partition
from typing import List, Dict, Any, Tuple, Optional


@dataclass
class PrivateState:
    """
    Datencontainer für den privaten Spielzustand eines Tichu-Spielers.

    Diese Klasse sammelt die Daten, die nur dem jeweiligen Spieler bekannt sind.

    :ivar player_index: Pflichtargument. Der Index dieses Spielers am Tisch (zwischen 0 und 3).
    :ivar hand_cards: Die aktuellen Handkarten des Spielers (absteigend sortiert, z.B. [(8,3), (2,4), (0,1)].
    :ivar given_schupf_cards: Die drei Karten, die der Spieler zum Schupfen an den rechten Gegner, Partner und linken Gegner abgegeben hat (None, falls noch nicht geschupft).
    :ivar received_schupf_cards: Die drei Karten, die der Spieler beim Schupfen vom rechten Gegner, Partner und linken Gegner erhalten hat (None, falls noch nicht geschupft).
    """
    # --- Spielerinformationen ---
    player_index: int  # muss im Konstruktor angegeben werden

    # --- Information über die aktuelle Runde ---
    _hand_cards: Cards = field(default_factory=list)
    given_schupf_cards: Optional[Tuple[Card, Card, Card]] = None
    received_schupf_cards: Optional[Tuple[Card, Card, Card]] = None

    # --- Private Caches (verborgene Variablen) ---
    _combination_cache: List[Tuple[Cards, Combination]] = field(default_factory=list, repr=False)  # Nur intern verwendet, daher repr=False
    _partition_cache: List[Partition] = field(default_factory=list, repr=False)
    _partitions_aborted: bool = field(default=True, repr=False)

    def __post_init__(self):
        if not (0 <= self.player_index <= 3):
            raise ValueError(f"player_index muss zwischen 0 und 3 liegen, nicht {self.player_index}")

    def reset_round(self):
        """Status für eine neue Runde zurücksetzen."""
        self.hand_cards = []
        self.given_schupf_cards = None
        self.received_schupf_cards = None

    def reset_game(self):
        """Status für eine neue Partie zurücksetzen."""
        self.reset_round()

    def to_dict(self) -> Dict[str, Any]:
        """
        Konvertiert den Zustand in ein Dictionary für JSON-Serialisierung.

        :return: Eine Dictionary-Repräsentation des Zustands.
        """
        return {
            "player_index": self.player_index,
            "hand_cards": self._hand_cards,
            "given_schupf_cards": self.given_schupf_cards,
            "received_schupf_cards": self.received_schupf_cards,
        }

    @property
    def hand_cards(self) -> Cards:
        """Die aktuellen Handkarten des Spielers (absteigend sortiert, z.B. [(8,3), (2,4), (0,1)]."""
        return self._hand_cards

    @hand_cards.setter
    def hand_cards(self, value: Cards):
        """Setzt die Handkarten und leert den Combination-Cache."""
        # Karten absteigend sortieren
        self._hand_cards = value
        self._hand_cards.sort(reverse=True)
        self._combination_cache = []
        self._partition_cache = []
        self._partitions_aborted = True

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

    @property
    def has_bomb(self) -> bool:
        """True, wenn der Spieler eine Bombe hat"""
        combis = self.combinations
        return True if combis and combis[0][1][0] == CombinationType.BOMB else False
