from dataclasses import dataclass, field
from typing import List


@dataclass
class PrivateState:
    """Datenklasse: Nur für einen spezifischen Spieler sichtbarer Zustand."""
    player_index: int
    hand_cards: List[str] = field(default_factory=list) # Karten als Strings repräsentieren?
    can_announce_tichu: bool = False
    # ... weitere private Daten (z.B. erhaltene Karten beim Schupfen)

    def to_dict(self) -> dict:
        return self.__dict__
