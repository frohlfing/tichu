# tests/test_public_state.py
"""
Tests für die PublicState-Datenklasse.

Zusammenfassung der Tests für PublicState:
- Initialisierung:
    - Überprüfung der korrekten Standardwerte aller Felder nach der Instanziierung.
- Serialisierung (`to_dict`):
    - Korrekte Umwandlung des Zustands in ein Dictionary.
    - Korrekte Formatierung von Karten (Strings), Kombinationen (Enum-Namen) und der Stich-Historie (`tricks`).
- Berechnete Properties:
    - Korrekte Berechnung von `count_active_players`.
    - Korrekte Berechnung von `points_per_team`.
    - Korrekte Berechnung von `total_score`.
    - Korrekte Erkennung, ob das Spiel beendet ist (`is_game_over`).
    - (Implizit über Initialisierung/to_dict: Struktur von `tricks` als Liste von Listen von Spielzügen).
"""

import pytest
from typing import List, Tuple
from copy import deepcopy

from src.public_state import PublicState
from src.lib.cards import Card, Cards, parse_cards, stringify_cards
from src.lib.combinations import Combination, CombinationType, PlayInTrick, TrickHistory

# Fixture für einen initialisierten PublicState
@pytest.fixture
def initial_pub_state() -> PublicState:
    return PublicState(
        table_name="TestTable",
        player_names=["Alice", "Bob", "Charlie", "David"]
    )

def test_public_state_initialization(initial_pub_state):
    """Testet die Standardwerte nach der Initialisierung."""
    pub = initial_pub_state
    assert pub.table_name == "TestTable"
    assert pub.player_names == ["Alice", "Bob", "Charlie", "David"]
    assert pub.current_turn_index == -1
    assert pub.start_player_index == -1
    assert pub.count_hand_cards == [0, 0, 0, 0]
    assert pub.played_cards == []
    assert pub.announcements == [0, 0, 0, 0]
    assert pub.wish_value == 0
    assert pub.dragon_recipient == -1
    assert pub.trick_owner_index == -1
    assert pub.trick_cards == [] # Hängt von Implementierung ab, ob dies noch genutzt wird
    assert pub.trick_combination == (CombinationType.PASS, 0, 0)
    assert pub.trick_points == 0
    # assert pub._current_trick_plays_internal == [] # Falls in PublicState belassen
    assert pub.tricks == [] # Vormals round_history
    assert pub.points == [0, 0, 0, 0]
    assert pub.winner_index == -1
    assert pub.loser_index == -1
    # Diese Felder könnten Properties sein:
    # assert pub.is_round_over is False
    # assert pub.double_victory is False
    assert pub.game_score == [[], []]
    assert pub.round_counter == 0
    assert pub.trick_counter == 0
    assert pub.current_phase == "setup" # Oder was auch immer der Default ist

def test_public_state_to_dict(initial_pub_state):
    """Testet die Umwandlung in ein Dictionary."""
    pub = initial_pub_state
    # Setze einige Werte für einen besseren Test
    pub.current_turn_index = 1
    pub.count_hand_cards = [10, 11, 12, 13]
    pub.played_cards = parse_cards("S5 G5")
    pub.trick_combination = (CombinationType.PAIR, 2, 5)
    pub.trick_points = 10
    pub.trick_owner_index = 0
    # Füge einen Beispiel-Trick zur History hinzu
    trick1_play1 = (0, parse_cards("S5 G5"), (CombinationType.PAIR, 2, 5))
    trick1_play2 = (1, [], (CombinationType.PASS, 0, 0))
    pub.tricks.append([trick1_play1, trick1_play2])

    pub_dict = pub.to_dict()

    assert pub_dict["tableName"] == "TestTable"
    assert pub_dict["playerNames"] == ["Alice", "Bob", "Charlie", "David"]
    assert pub_dict["currentTurnIndex"] == 1
    assert pub_dict["countHandCards"] == [10, 11, 12, 13]
    assert pub_dict["playedCards"] == "S5 G5" # Stringified
    assert pub_dict["trickCombination"] == ("PAIR", 2, 5) # Enum Name
    assert pub_dict["trickPoints"] == 10
    assert pub_dict["trickOwnerIndex"] == 0
    assert len(pub_dict["tricks"]) == 1
    assert len(pub_dict["tricks"][0]) == 2
    # Prüfe den ersten Spielzug im ersten Trick
    assert pub_dict["tricks"][0][0] == (0, "S5 G5", ("PAIR", 2, 5))
    # Prüfe den zweiten Spielzug (Passen)
    assert pub_dict["tricks"][0][1] == (1, "", ("PASS", 0, 0))

# --- Tests für Properties (Beispiele) ---

def test_public_state_count_active_players(initial_pub_state):
    """Testet die Zählung aktiver Spieler."""
    pub = initial_pub_state
    assert pub.count_active_players == 0
    pub.count_hand_cards = [5, 0, 8, 1]
    assert pub.count_active_players == 3
    pub.count_hand_cards = [0, 0, 0, 0]
    assert pub.count_active_players == 0
    pub.count_hand_cards = [1, 1, 1, 1]
    assert pub.count_active_players == 4

def test_public_state_points_per_team(initial_pub_state):
    """Testet die Berechnung der Teampunkte."""
    pub = initial_pub_state
    pub.points = [10, 20, 30, 40] # Spieler 0, 1, 2, 3
    # Team 20 = Spieler 2 + Spieler 0 = 30 + 10 = 40
    # Team 31 = Spieler 3 + Spieler 1 = 40 + 20 = 60
    assert pub.points_per_team == (40, 60)

def test_public_state_total_score(initial_pub_state):
    """Testet die Berechnung des Gesamtspielstands."""
    pub = initial_pub_state
    pub.game_score = [[100, -10], [90, 110]] # Rundenpunkte Team 20, Team 31
    # Team 20 = 100 - 10 = 90
    # Team 31 = 90 + 110 = 200
    assert pub.total_score == (90, 200)

def test_public_state_is_game_over(initial_pub_state):
    """Testet die Erkennung des Spielendes."""
    pub = initial_pub_state
    assert pub.is_game_over is False
    pub.game_score = [[500], [400]]
    assert pub.is_game_over is False
    pub.game_score = [[500, 500], [400, 450]] # Team 20 = 1000
    assert pub.is_game_over is True
    pub.game_score = [[400], [1000]] # Team 31 = 1000
    assert pub.is_game_over is True
