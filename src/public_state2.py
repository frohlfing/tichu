from dataclasses import dataclass, field
from typing import List, Optional, Any


@dataclass
class PublicState:
    """Datenklasse: Für alle Spieler sichtbarer Zustand des Spiels."""
    table_name: str
    player_names: List[Optional[str]] = field(default_factory=lambda: [None] * 4)
    player_scores: List[int] = field(default_factory=lambda: [0] * 4)
    current_turn_index: Optional[int] = None
    last_played_combination: Optional[Any] = None # Details später definieren
    # ... weitere öffentliche Daten (z.B. gespielte Bomben, Grand Tichus)
    is_game_over: bool = False

    def to_dict(self) -> dict:
        # Einfache Konvertierung für JSON-Serialisierung
        return self.__dict__
