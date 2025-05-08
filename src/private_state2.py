"""
Definiert die Datenstruktur für den privaten Spielzustand eines Spielers.
"""

from dataclasses import dataclass, field
from src.lib.cards import Card, stringify_cards
from typing import List, Dict, Any

@dataclass
class PrivateState:
    """
    Datencontainer für den privaten Spielzustand eines Tichu-Spielers.

    Diese Klasse sammelt die Daten, die nur dem jeweiligen Spieler bekannt sind.

    :ivar player_index: Der Index dieses Spielers am Tisch (zwischen 0 und 3).
    :ivar hand_cards: Die aktuellen Handkarten des Spielers (absteigend sortiert, z.B. [(8,3), (2,4), (0,1)].
    :ivar received_schupf_cards: Die drei Karten, die der Spieler beim Schupfen vom rechten Gegner, Partner und linken Gegner erhalten hat.
    :ivar given_schupf_cards: Die drei Karten, die der Spieler zum Schupfen an den rechten Gegner, Partner und linken Gegner abgegeben hat.
    """
    # --- Spielerinformationen ---
    player_index: int = -1

    # --- Information über die aktuelle Runde ---
    hand_cards: List[Card] = field(default_factory=list)
    received_schupf_cards: List[Card] = field(default_factory=list)
    given_schupf_cards: List[Card] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """
        Konvertiert den Zustand in ein Dictionary für JSON-Serialisierung.

        Verwendet eine übergebene Funktion zur Konvertierung interner Karten in ihre String-Label-Repräsentation.

        :return: Eine Dictionary-Repräsentation des Zustands mit Karten als Strings.
        """
        return {
            "playerIndex": self.player_index,
            "handCards": stringify_cards(self.hand_cards),
            "receivedSchupfCards": stringify_cards(self.received_schupf_cards),
            "givenSchupfCards": stringify_cards(self.given_schupf_cards),
        }
