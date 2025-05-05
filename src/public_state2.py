# -*- coding: utf-8 -*-
"""
Definiert die Datenstruktur für den öffentlichen Spielzustand (Public State).

Diese Klasse enthält alle Informationen über das Spiel, die für alle Spieler am Tisch sichtbar sind.
Sie dient als reiner Datencontainer.
Die Logik zur Änderung des Zustands befindet sich in der GameEngine oder ausgelagerten Regelfunktionen.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
from src.lib.cards import Card
from src.lib.combinations import Combination


# --- Nicht übernommene Felder aus altem PublicState ---
# _mixed_deck: Das Mischen und Verteilen ist Aufgabe der Engine, nicht des States.
# _random: Zufallsgenerierung gehört nicht in den State.
# _number_of_players (im Sinne von "noch im Rennen"): Abgeleitet aus num_cards_in_hand, gehört in die Engine-Logik.
# _history (im Sinne aller Züge der Runde): Wird implizit durch played_cards_in_round abgedeckt oder muss separat geführt werden, falls detaillierter benötigt.
# _trick_counter (Statistik): Kann von der Arena/Engine extern gezählt werden.
# _points (alte Bedeutung): Ersetzt durch round_points_collected und round_scores_final.
# gift (alte Bedeutung): Ersetzt durch dragon_trick_recipient.
# trick_player_index (alte Bedeutung): Ersetzt durch last_player_index.
# trick_figure (alte Bedeutung): Ersetzt durch last_combination_details.

@dataclass
class PublicState:
    """
    Datencontainer für den öffentlichen Zustand eines Tichu-Spiels.

    Diese Klasse sammelt alle Datenpunkte, die den Spielverlauf und den Zustand beschreiben, soweit sie für alle Teilnehmer sichtbar sind.

    :ivar table_name: Der Name des Tisches.
    :ivar player_names: Die Namen der Spieler an den Slots 0-3.
    :ivar player_connected_status: Gibt an, ob der Client an dem Slot verbunden ist.
    :ivar current_turn_index: Index des Spielers, der am Zug ist (-1 vor Rundenbeginn).
    :ivar round_start_player_index: Index des Spielers, der Mah Jong hatte (-1 vor Rundenbeginn).
    :ivar trick_leader_index: Index des Spielers, der den aktuellen Stich eröffnet hat (-1 bei leerem Stich).
    :ivar total_scores: Gesamtpunktestand der Partie [Team 0 (0+2), Team 1 (1+3)].
    :ivar round_points_collected: Aktuell gesammelte Punkte pro Spieler (0-3) in dieser Runde.
    :ivar round_scores_final: Finale Punktzahl pro Team für die abgeschlossene Runde (inkl. Boni).
    :ivar is_round_over: Gibt an, ob die aktuelle Runde beendet ist.
    :ivar is_game_over: Gibt an, ob das gesamte Spiel (Partie) beendet ist.
    :ivar round_counter: Zähler für abgeschlossene Runden in dieser Partie.
    :ivar round_winner_index: Index des Spielers, der die Runde gewonnen hat (-1 wenn Runde läuft).
    :ivar round_loser_index: Index des Spielers, der die Runde verloren hat (-1 wenn Runde läuft oder Doppelsieg).
    :ivar round_double_victory: Gibt an, ob die Runde durch einen Doppelsieg beendet wurde.
    :ivar round_announcements: Angekündigte Tichus [Spieler 0-3], 0=Nein, 1=Klein, 2=Groß.
    :ivar last_played_cards_internal: Die Karten der letzten gültigen Kombination (interne Darstellung).
    :ivar last_combination_details: Details (Typ, Länge, Rang) der letzten Kombination. None bei leerem Stich.
    :ivar last_player_index: Index des Spielers, der die letzte Kombination gespielt hat. -1 bei leerem Stich.
    :ivar current_trick_history: Verlauf des aktuellen Stichs [(SpielerIdx, Karten | None, KombiDetails | None), ...].
    :ivar current_trick_points: Aktuell im Stich gesammelte Punkte.
    :ivar num_cards_in_hand: Anzahl der Handkarten pro Spieler [Spieler 0-3].
    :ivar played_cards_in_round_internal: Bereits gespielte Karten in dieser Runde (interne Darstellung).
    :ivar wish_active_value: Der vom Mah Jong Spieler gewünschte Kartenwert (2-14). 0 wenn kein Wunsch aktiv.
    :ivar dragon_trick_recipient: Index des Spielers, der den Drachenstich erhalten hat (-1 wenn nicht relevant).
    :ivar current_phase: Aktuelle Phase des Spiels (z.B. "lobby", "schupfing", "playing").
    """
    # --- Tisch- und Spielerinformationen ---
    table_name: str = "Unbekannter Tisch"  # Der Name des Tisches.
    player_names: List[Optional[str]] = field(default_factory=lambda: [None] * 4)  # Die Namen der Spieler an den Slots 0-3.
    player_connected_status: List[bool] = field(default_factory=lambda: [False] * 4)  # Gibt an, ob der Client an dem Slot verbunden ist.
    current_turn_index: int = -1  # Index des Spielers, der am Zug ist (-1 vor Rundenbeginn).
    round_start_player_index: int = -1  # Index des Spielers, der Mah Jong hatte (-1 vor Rundenbeginn).
    trick_leader_index: int = -1  # Index des Spielers, der den aktuellen Stich eröffnet hat (-1 bei leerem Stich).

    # --- Spielstand ---
    total_scores: List[int] = field(default_factory=lambda: [0, 0])  # Gesamtpunktestand der Partie [Team 0 (0+2), Team 1 (1+3)].
    round_points_collected: List[int] = field(default_factory=lambda: [0, 0, 0, 0])  # Aktuell gesammelte Punkte pro Spieler (0-3) in dieser Runde.
    round_scores_final: Optional[List[int]] = None  # Finale Punktzahl pro Team für die abgeschlossene Runde (inkl. Boni).

    # --- Runden- und Spielstatus ---
    is_round_over: bool = False  # Gibt an, ob die aktuelle Runde beendet ist.
    is_game_over: bool = False  # Gibt an, ob das gesamte Spiel (Partie) beendet ist.
    round_counter: int = 0  # Zähler für abgeschlossene Runden in dieser Partie.
    round_winner_index: int = -1  # Index des Spielers, der die Runde gewonnen hat (-1 wenn Runde läuft).
    round_loser_index: int = -1  # Index des Spielers, der die Runde verloren hat (-1 wenn Runde läuft oder Doppelsieg).
    round_double_victory: bool = False  # Gibt an, ob die Runde durch einen Doppelsieg beendet wurde.
    round_announcements: List[int] = field(default_factory=lambda: [0, 0, 0, 0])  # Angekündigte Tichus [Spieler 0-3], 0=Nein, 1=Klein, 2=Groß.

    # --- Aktueller Stich / Letzte Kombination ---
    last_played_cards_internal: Optional[List[Card]] = None  # Die Karten der letzten gültigen Kombination (interne Darstellung).
    last_combination_details: Optional[Combination] = None  # Details (Typ, Länge, Rang) der letzten Kombination. None bei leerem Stich.
    last_player_index: int = -1  # Index des Spielers, der die letzte Kombination gespielt hat. -1 bei leerem Stich.
    current_trick_history: List[Tuple[int, Optional[List[Card]], Optional[Combination]]] = field(default_factory=list)  # Verlauf des aktuellen Stichs [(SpielerIdx, Karten | None, KombiDetails | None), ...].
    current_trick_points: int = 0  # Aktuell im Stich gesammelte Punkte.

    # --- Karteninformationen (aggregiert) ---
    num_cards_in_hand: List[int] = field(default_factory=lambda: [0] * 4)  # Anzahl der Handkarten pro Spieler [Spieler 0-3].
    played_cards_in_round_internal: List[Card] = field(default_factory=list)  # Bereits gespielte Karten in dieser Runde (interne Darstellung).

    # --- Sonderkarten-Status ---
    wish_active_value: int = 0  # Der vom Mah Jong Spieler gewünschte Kartenwert (2-14). 0 wenn kein Wunsch aktiv. (Negativ für erfüllt wurde entfernt).
    dragon_trick_recipient: int = -1  # Index des Spielers, der den Drachenstich erhalten hat (-1 wenn nicht relevant).

    # --- Spielphasen-Information ---
    current_phase: str = "setup"  # Aktuelle Phase des Spiels (z.B. "lobby", "dealing", "schupfing", "playing").


    def to_dict(self, stringify_card_list_func) -> Dict[str, Any]:
        """
        Konvertiert den Zustand in ein Dictionary für JSON-Serialisierung.

        Verwendet eine übergebene Funktion zur Konvertierung interner Karten in ihre String-Label-Repräsentation.

        :param stringify_card_list_func: Funktion wie `stringify_cards` aus `src.lib.cards`, die `List[Card]` in `List[CardLabel]` umwandelt.
        :return: Eine Dictionary-Repräsentation des Zustands mit Karten als Strings.
        """
        # Konvertiere Kartenlisten in String-Labels für die Ausgabe
        last_played_card_labels = stringify_card_list_func(self.last_played_cards_internal) if self.last_played_cards_internal else None
        played_card_labels = stringify_card_list_func(self.played_cards_in_round_internal)

        # Konvertiere Trick History für die Ausgabe
        trick_history_labels = []
        for p_idx, cards_internal, combo_info in self.current_trick_history:
            card_labels = stringify_card_list_func(cards_internal) if cards_internal else None
            # Konvertiere Enum zu seinem Namen (String) für JSON
            combo_info_serializable = (combo_info[0].name, combo_info[1], combo_info[2]) if combo_info else None
            trick_history_labels.append((p_idx, card_labels, combo_info_serializable))

        # Konvertiere finale Rundenergebnisse (Liste von Zahlen)
        round_scores_final_serializable = self.round_scores_final

        return {
            "tableName": self.table_name,
            "playerNames": self.player_names,
            "playerConnectedStatus": self.player_connected_status,
            "currentTurnIndex": self.current_turn_index,
            "roundStartPlayerIndex": self.round_start_player_index,
            "trickLeaderIndex": self.trick_leader_index,
            "totalScores": self.total_scores,
            "roundPointsCollected": self.round_points_collected,
            "roundScoresFinal": round_scores_final_serializable,
            "isRoundOver": self.is_round_over,
            "isGameOver": self.is_game_over,
            "roundCounter": self.round_counter,
            "roundWinnerIndex": self.round_winner_index,
            "roundLoserIndex": self.round_loser_index,
            "roundDoubleVictory": self.round_double_victory,
            "roundAnnouncements": self.round_announcements,
            "lastPlayedCards": last_played_card_labels,
            "lastCombinationDetails": (self.last_combination_details[0].name, self.last_combination_details[1], self.last_combination_details[2]) if self.last_combination_details else None,
            "lastPlayerIndex": self.last_player_index,
            "currentTrickHistory": trick_history_labels,
            "currentTrickPoints": self.current_trick_points,
            "numCardsInHand": self.num_cards_in_hand,
            "playedCardsInRound": played_card_labels,
            "wishActiveValue": self.wish_active_value,
            "dragonTrickRecipient": self.dragon_trick_recipient,
            "currentPhase": self.current_phase,
        }
