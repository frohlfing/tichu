"""
Definiert die Datenstruktur für den öffentlichen Spielzustand.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
from src.lib.cards import Card, stringify_cards
from src.lib.combinations import Combination

# todo: Nicht übernommene Felder aus altem PublicState
# _history (im Sinne aller Züge der Runde): Wird implizit durch played_cards abgedeckt oder muss separat geführt werden, falls detaillierter benötigt.
# _trick_counter (Statistik): Kann von der Arena/Engine extern gezählt werden.



@dataclass
class PublicState:
    """
    Datencontainer für den öffentlichen Spielzustand eines Tichu-Spiels.

    Diese Klasse sammelt alle Daten, die den Spielverlauf und den Zustand beschreiben, soweit sie für alle Teilnehmer sichtbar sind.

    :ivar table_name: Der Name des Tisches.
    :ivar player_names: Die Namen der 4 Spieler [Spieler 0-3].
    :ivar current_turn_index: Index des Spielers, der am Zug ist (-1 == Startspieler steht noch nicht fest).
    :ivar start_player_index: Index des Spielers, der den Mahjong hat oder hatte (-1 == steht noch nicht fest).
    :ivar num_hand_cards: Anzahl der Handkarten pro Spieler [Spieler 0-3].
    :ivar played_cards: Bereits gespielte Karten in der aktuellen Runde [Card, ...].
    :ivar announcements: Angekündigtes Tichu pro Spieler [Spieler 0-3] (0 == keine Ansage, 1 == kleines, 2 == großes Tichu)
    :ivar wish_value: Der gewünschte Kartenwert (2 bis 14, 0 == kein Wunsch geäußert, negativ == bereits erfüllt)
    :ivar dragon_recipient: Index des Spielers, der den Drachen bekommen hat (-1 == noch niemand).
    :ivar trick_owner_index: Index des Spielers, der die letzte Kombination gespielt hat (-1 == leerer Stich).
    :ivar trick_cards: Die Karten der letzten Kombination im Stich [Card, ...].
    :ivar trick_combination: Typ, Länge und Wert der letzten Kombination im aktuellen Stich ((0,0,0) == leerer Stich)
    :ivar trick_points: Punkte des aktuellen Stichs.
    :ivar round_history: Spielverlauf der aktuellen Runde [(player_index, [Card, ...], Combination), ...]. # todo in Stiche unterteilen
    :ivar points: Punktestand der aktuellen Runde pro Spieler [Spieler 0-3].
    :ivar winner_index: Index des Spielers, der zuerst in der aktuellen Runde fertig wurde (-1 == alle Spieler sind noch dabei).
    :ivar loser_index: Index des Spielers, der in der aktuellen Runde als letztes übrig blieb (-1 == Runde läuft noch oder wurde mit Doppelsieg beendet).
    :ivar is_round_over: Gibt an, ob die aktuelle Runde beendet ist.
    :ivar double_victory: Gibt an, ob die Runde durch einen Doppelsieg beendet wurde.
    :ivar game_score: Punktetabelle der Partie [Team 20, Team 31] (pro Team eine Liste von Punkten).
    :ivar round_counter: Anzahl der abgeschlossenen Runden (nur für statistische Zwecke). # todo kann aus game_ccore ermittelt werden
    :ivar trick_counter: Anzahl der abgeräumten Stiche in der aktuellen Runde (nur für statistische Zwecke). # todo kann aus round_history ermittelt werden
    :ivar current_phase: # Aktuelle Spielphase (z.B. "dealing", "schupfing", "playing").
    """
    # --- Tisch- und Spielerinformationen ---
    table_name: str = "Unbekannter Tisch"
    player_names: List[Optional[str]] = field(default_factory=lambda: [None, None, None, None])

    # --- Information über die aktuelle Runde ---
    current_turn_index: int = -1
    start_player_index: int = -1
    num_hand_cards: List[int] = field(default_factory=lambda: [0, 0, 0, 0])
    played_cards: List[Card] = field(default_factory=list)
    announcements: List[int] = field(default_factory=lambda: [0, 0, 0, 0])
    wish_value: int = 0
    dragon_recipient: int = -1
    trick_owner_index: int = -1
    trick_cards: List[Card] = field(default_factory=lambda: [])
    trick_combination: Combination = field(default_factory=lambda: [0, 0, 0])
    trick_points: int = 0
    round_history: List[Tuple[int, Optional[List[Card]], Optional[Combination]]] = field(default_factory=list)  # todo
    points: List[int] = field(default_factory=lambda: [0, 0, 0, 0])
    winner_index: int = -1
    loser_index: int = -1
    is_round_over: bool = False
    double_victory: bool = False

    # --- Information über die Partie ---
    game_score: List[List[int]] = field(default_factory=lambda: [[0], [0]])

    # --- Statistik ---
    round_counter: int = 0
    trick_counter: int = 0

    # --- Spielphase ---
    current_phase: str = "setup"


    def to_dict(self) -> Dict[str, Any]:
        """
        Konvertiert den Zustand in ein Dictionary für JSON-Serialisierung.

        Verwendet eine übergebene Funktion zur Konvertierung interner Karten in ihre String-Label-Repräsentation.

        :return: Eine Dictionary-Repräsentation des Zustands mit Karten als Strings.
        """
        return {
            "tableName": self.table_name,
            "playerNames": self.player_names,
            "currentTurnIndex": self.current_turn_index,
            "startPlayerIndex": self.start_player_index,
            "numHandCards": self.num_hand_cards,
            "playedCards": stringify_cards(self.played_cards),
            "announcements": self.announcements,
            "wishValue": self.wish_value,
            "dragonRecipient": self.dragon_recipient,
            "trickOwnerIndex": self.trick_owner_index,
            "trickCards": stringify_cards(self.trick_cards),
            "trickCombination": (self.trick_combination[0].name, self.trick_combination[1], self.trick_combination[2]),
            "trickPoints": self.trick_points,
            "roundHistory": [(idx, stringify_cards(cards), (combi[0].name, combi[1], combi[2])) for idx, cards, combi in self.round_history],
            "points": self.points,
            "winnerIndex": self.winner_index,
            "loserIndex": self.loser_index,
            "isRoundOver": self.is_round_over,
            "doubleVictory": self.double_victory,
            "gameScore": self.game_score,
            "roundCounter": self.round_counter,
            "trickCounter": self.trick_counter,
            "currentPhase": self.current_phase,
        }
