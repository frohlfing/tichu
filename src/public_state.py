"""
Definiert die Datenstruktur für den öffentlichen Spielzustand.
"""

from dataclasses import dataclass, field
from src.lib.cards import Card, Cards, other_cards
from src.lib.combinations import Combination, CombinationType
from typing import List, Tuple, Dict, Any

# Type-Alias für einen Spielzug (inkl. Passen)
Turn = Tuple[int, Cards, Combination]  # Index des Spielers, Karten, Kombination (Typ, Länge, Rang)

# Type-Alias für einen Stich (Liste von Spielzügen)
Trick = List[Turn]

# Type-Alias für die Punktetabelle
GameScore = Tuple[List[int], List[int]]

@dataclass
class PublicState:
    """
    Datencontainer für den öffentlichen Spielzustand eines Tichu-Spiels.

    Diese Klasse sammelt alle Daten, die den Spielverlauf und den Zustand beschreiben, soweit sie für alle Teilnehmer sichtbar sind.

    :ivar table_name: Pflichtargument. Der eindeutige Name des Tisches.
    :ivar player_names: Pflichtargument. Die Namen der 4 Spieler.
    :ivar host_index: Index des Clients, der Host des Tisches ist (-1 == kein Client am Tisch).
    :ivar is_running: # Gibt an, ob eine Partie gerade läuft.
    :ivar current_turn_index: Index des Spielers, der am Zug ist (-1 == Startspieler steht noch nicht fest).
    :ivar start_player_index: Index des Spielers, der den Mahjong hat oder hatte (-1 == steht noch nicht fest; es wurde noch nicht geschupft).
    :ivar count_hand_cards: Anzahl der Handkarten pro Spieler.
    :ivar played_cards: Bereits gespielte Karten in der aktuellen Runde [Card, ...].
    :ivar announcements: Angekündigtes Tichu pro Spieler (0 == keine Ansage, 1 == einfaches Tichu, 2 == großes Tichu).
    :ivar wish_value: Der gewünschte Kartenwert (2 bis 14, 0 == kein Wunsch geäußert, negativ == bereits erfüllt).
    :ivar dragon_recipient: Index des Spielers, der den Drachen bekommen hat (-1 == noch niemand).
    :ivar trick_owner_index: Index des Spielers, der die letzte Kombination gespielt hat, also Besitzer des Stichs ist (-1 == leerer Stich).
    :ivar trick_cards: Die letzten Karten im Stich (nicht Passen) [Card, ...].
    :ivar trick_combination: Typ, Länge und Rang des aktuellen Stichs ((0,0,0) == leerer Stich)
    :ivar trick_points: Punkte des aktuellen Stichs.
    :ivar tricks: Liste der Stiche der aktuellen Runde. Der letzte Eintrag ist u.U. noch offen (wenn der Stich noch nicht einkassiert wurde).
    :ivar points: Bisher kassierte Punkte in der aktuellen Runde pro Spieler.
    :ivar winner_index: Index des Spielers, der zuerst in der aktuellen Runde fertig wurde (-1 == alle Spieler sind noch dabei).
    :ivar loser_index: Index des Spielers, der in der aktuellen Runde als letztes übrig blieb (-1 == Runde läuft noch oder wurde mit Doppelsieg beendet).
    :ivar is_round_over: Gibt an, ob die aktuelle Runde beendet ist.
    :ivar is_double_victory: Gibt an, ob die Runde durch einen Doppelsieg beendet wurde.
    :ivar game_score: Punktetabelle der Partie (Team 20, Team 31) (pro Team eine Liste von Punkten).
    :ivar trick_counter: Anzahl der abgeräumten Stiche insgesamt über alle Runden der Partie (nur für statistische Zwecke).
    """
    # --- Tisch- und Spielerinformationen ---
    table_name: str  # muss im Konstruktor angegeben werden
    player_names: List[str]  # muss im Konstruktor angegeben werden
    host_index: int = -1

    # --- Information über die aktuelle Runde ---
    is_running: bool = False
    current_turn_index: int = -1
    start_player_index: int = -1
    count_hand_cards: List[int] = field(default_factory=lambda: [0, 0, 0, 0])
    played_cards: Cards = field(default_factory=list)
    announcements: List[int] = field(default_factory=lambda: [0, 0, 0, 0])
    wish_value: int = 0
    dragon_recipient: int = -1
    trick_owner_index: int = -1
    trick_cards: Cards = field(default_factory=lambda: [])
    trick_combination: Combination = (CombinationType.PASS, 0, 0)
    trick_points: int = 0
    tricks: List[Trick] = field(default_factory=list)
    points: List[int] = field(default_factory=lambda: [0, 0, 0, 0])
    winner_index: int = -1
    loser_index: int = -1
    is_round_over: bool = False
    is_double_victory: bool = False

    # --- Information über die Partie ---
    game_score: GameScore = field(default_factory=lambda: ([], []))
    trick_counter: int = 0  # nur für statistische Zwecke

    # todo Berechnung:
    #  1) is_round_over = count_active_players == 1 or is_double_victory  # nur noch eine Spieler im Spiel oder Doppelsieg
    #  2) is_double_victory = count_active_players == 2 and count_hand_cards[(winner_index + 2) % 4] == 0  # die beiden Spieler eine Teams sind fertig, die anderen 2 Spieler noch nicht
    #  3) trick_points = sum_card_points(cards)  # kann aus allen Karten in tricks berechnet werden
    #  4) trick_owner_index, trick_cards, trick_combination bilden den letzten Eintrag aus tricks, der nicht Passen ist.

    def __post_init__(self):
        if not self.table_name.strip():
            raise ValueError("table_name darf nicht leer sein.")
        if len(self.player_names) != 4 or any(not name.strip() for name in self.player_names):
            raise ValueError(f"`player_names` muss 4 Namen auflisten.")

    def reset_round(self):
        """Status für eine neue Runde zurücksetzen."""
        self.current_turn_index = -1
        self.start_player_index = -1
        self.count_hand_cards = [0, 0, 0, 0]
        self.played_cards = []
        self.announcements = [0, 0, 0, 0]
        self.wish_value = 0
        self.dragon_recipient = -1
        self.trick_owner_index = -1
        self.trick_cards = []
        self.trick_combination = (CombinationType.PASS, 0, 0)
        self.trick_points = 0
        self.tricks = []
        self.points = [0, 0, 0, 0]
        self.winner_index = -1
        self.loser_index = -1
        self.is_round_over = False
        self.is_double_victory = False

    def reset_game(self):
        """Status für eine neue Partie zurücksetzen."""
        self.reset_round()
        self.game_score = [], []
        self.trick_counter = 0

    def to_dict(self) -> Dict[str, Any]:
        """
        Konvertiert den Zustand in ein Dictionary für JSON-Serialisierung.

        :return: Eine Dictionary-Repräsentation des Zustands.
        """
        return {
            "table_name": self.table_name,
            "player_names": self.player_names,
            "host_index": self.host_index,
            "is_running": self.is_running,
            "current_turn_index": self.current_turn_index,
            "start_player_index": self.start_player_index,
            "count_hand_cards": self.count_hand_cards,
            "played_cards": self.played_cards,
            "announcements": self.announcements,
            "wish_value": self.wish_value,
            "dragon_recipient": self.dragon_recipient,
            "trick_owner_index": self.trick_owner_index,
            "trick_cards": self.trick_cards,
            "trick_combination": self.trick_combination,
            "trick_points": self.trick_points,
            "tricks": self.tricks,
            "points": self.points,
            "winner_Index": self.winner_index,
            "loser_index": self.loser_index,
            "is_round_over": self.is_round_over,
            "is_double_victory": self.is_double_victory,
            "game_score": self.game_score,
            "trick_counter": self.trick_counter,
        }

    # ------------------------------------------------------
    # Properties
    # ------------------------------------------------------

    # Properties sehe ich für das Training von neuronalen Netzen als optionale Features.

    @property
    def count_active_players(self) -> int:
        """Anzahl der Spieler, die noch Handkarten haben."""
        #return sum(1 for n in self.count_hand_cards if n > 0)
        return (self.count_hand_cards[0] > 0) + (self.count_hand_cards[1] > 0) + (self.count_hand_cards[2] > 0) + (self.count_hand_cards[3] > 0)

    @property
    def unplayed_cards(self) -> List[Card]:  # pragma: no cover
        """Nicht gespielte Karten (in aufsteigender Reihenfolge)."""
        return other_cards(self.played_cards)

    # @property
    # def is_round_over(self) -> bool:
    #     """
    #     Gibt an, ob die aktuelle Runde beendet ist.
    #
    #     Die Runde ist vorbei, wenn nur noch ein Spieler Karten hat oder ein Doppelsieg erzielt wurde.
    #     """
    #     c = self.count_hand_cards
    #     if ((c[0] > 0 and c[1] == c[2] == c[3] == 0) or
    #             (c[1] > 0 and c[0] == c[2] == c[3] == 0) or
    #             (c[2] > 0 and c[0] == c[1] == c[3] == 0) or
    #             (c[3] > 0 and c[0] == c[1] == c[2] == 0)):
    #         return True
    #     return self.is_double_victory
    #
    # @property
    # def is_double_victory(self) -> bool:
    #     """
    #     Gibt an, ob die Runde durch einen Doppelsieg beendet wurde.
    #
    #     Ein Doppelsieg heißt, beide Spieler eines Teams haben Handkarten, die beiden anderen nicht.
    #     """
    #     c = self.count_hand_cards
    #     return (c[0] > 0 and c[2] > 0 and c[1] == c[3] == 0) or (c[1] > 0 and c[3] > 0 and c[0] == c[2] == 0)

    @property
    def total_score(self) -> Tuple[int, int]:
        """Gesamtpunktestand der Partie für Team 20 und Team 31"""
        return sum(self.game_score[0]), sum(self.game_score[1])

    @property
    def is_game_over(self) -> bool:
        """Gibt an, ob die Partie beendet ist."""
        score20, score31 = self.total_score
        return score20 >= 1000 or score31 >= 1000

    @property
    def round_counter(self) -> int:
        """Anzahl der abgeschlossenen Runden der Partie."""
        return len(self.game_score[0])