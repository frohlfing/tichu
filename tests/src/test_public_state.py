import pytest

from src.lib.cards import CardSuit
from src.public_state import PublicState
from src.lib.combinations import CombinationType

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
    assert pub.wish_value == -1
    assert pub.dragon_recipient == -1
    assert pub.trick_owner_index == -1
    assert pub.trick_cards == []  # hängt von der Implementierung ab, ob dies noch genutzt wird
    assert pub.trick_combination == (CombinationType.PASS, 0, 0)
    assert pub.trick_points == 0
    assert pub.tricks == []
    assert pub.points == [0, 0, 0, 0]
    assert pub.winner_index == -1
    assert pub.loser_index == -1
    # Diese Felder könnten Properties sein:
    # assert pub.is_round_over is False
    # assert pub.is_double_victory is False
    assert pub.game_score == ([], [])
    assert pub.round_counter == 0
    assert pub.trick_counter == 0

def test_public_state_to_dict(initial_pub_state):
    """Testet die Umwandlung in ein Dictionary."""
    pub = initial_pub_state
    # Setze einige Werte für einen besseren Test
    pub.current_turn_index = 1
    pub.count_hand_cards = [10, 11, 12, 13]
    pub.played_cards = [(5, CardSuit.SWORD), (5,CardSuit.JADE)]  # S5 G5"
    pub.trick_combination = (CombinationType.PAIR, 2, 5)
    pub.trick_points = 10
    pub.trick_owner_index = 0
    # Füge einen Beispiel-Trick zur History hinzu
    trick1_play1 = (0, [(5,1), (5,3)], (CombinationType.PAIR, 2, 5))
    trick1_play2 = (1, [], (CombinationType.PASS, 0, 0))
    pub.tricks.append([trick1_play1, trick1_play2])

    pub_dict = pub.to_dict()
    assert pub_dict["table_name"] == "TestTable"
    assert pub_dict["player_names"] == ["Alice", "Bob", "Charlie", "David"]
    assert pub_dict["current_turn_index"] == 1
    assert pub_dict["count_hand_cards"] == [10, 11, 12, 13]
    assert pub_dict["played_cards"] == [(5,1), (5,3)]
    assert pub_dict["trick_combination"] == (CombinationType.PAIR, 2, 5) # Enum Name
    assert pub_dict["trick_points"] == 10
    assert pub_dict["trick_owner_index"] == 0
    assert len(pub_dict["tricks"]) == 1
    assert len(pub_dict["tricks"][0]) == 2
    # Prüfe den ersten Spielzug im ersten Trick
    assert pub_dict["tricks"][0][0] == (0, [(5,1), (5,3)], (CombinationType.PAIR, 2, 5))
    # Prüfe den zweiten Spielzug (Passen)
    assert pub_dict["tricks"][0][1] == (1, [], (CombinationType.PASS, 0, 0))

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

def test_public_state_total_score(initial_pub_state):
    """Testet die Berechnung des Gesamtspielstands."""
    pub = initial_pub_state
    pub.game_score = [100, -10], [90, 110]  # Punkte pro Partei für Team 20, Team 31
    # Team 20 = 100 - 10 = 90
    # Team 31 = 90 + 110 = 200
    assert pub.total_score == (90, 200)

def test_public_state_is_game_over(initial_pub_state):
    """Testet die Erkennung des Spielendes."""
    pub = initial_pub_state
    assert pub.is_game_over is False
    pub.game_score = [500], [400]
    assert pub.is_game_over is False
    pub.game_score = [500, 500], [400, 450]  # Team 20 = 1000
    assert pub.is_game_over is True
    pub.game_score = [400], [1000]  # Team 31 = 1000
    assert pub.is_game_over is True

def test_reset_round(initial_pub_state):
    """Testet das Zurücksetzen des PublicState für eine neue Runde."""
    pub = initial_pub_state

    # Zustand "verschmutzen"
    pub.table_name = "Tisch1"
    pub.player_names = ["Anton", "Bea", "Charlie", "Doris"]

    pub.current_phase = "foo"
    pub.current_turn_index = 3
    pub.start_player_index = 3
    pub.count_hand_cards = [1, 2, 3, 4]
    pub.played_cards = [(2, CardSuit.SWORD)]
    pub.announcements = [1, 1, 1, 1]
    pub.wish_value = 4
    pub.dragon_recipient = 3
    pub.trick_owner_index = 2
    pub.trick_cards = [(2, CardSuit.SWORD)]
    pub.trick_combination = (CombinationType.SINGLE, 1, 5)
    pub.trick_points = 10
    pub.tricks = [[(0, [(5, CardSuit.SWORD)], (CombinationType.SINGLE, 1, 5))]]
    pub.points = [10, 0, 0, 0]
    pub.winner_index = 3
    pub.loser_index = 2
    pub.is_round_over = True
    pub.is_double_victory = True

    pub.game_score = [60, 10], [40, 90]
    pub.trick_counter = 3

    # Reset durchführen (reset_public_state_for_round ist static)
    pub.reset_round()

    # Prüfen, ob die Werte korrekt zurückgesetzt wurden
    assert pub.table_name == "Tisch1"  # darf nicht zurückgesetzt werden
    assert pub.player_names == ["Anton", "Bea", "Charlie", "Doris"]  # darf nicht zurückgesetzt werden
    assert pub.current_turn_index == -1
    assert pub.start_player_index == -1
    assert pub.count_hand_cards == [0, 0, 0, 0]
    assert pub.played_cards == []
    assert pub.announcements == [0, 0, 0, 0]
    assert pub.wish_value == -1
    assert pub.dragon_recipient == -1
    assert pub.trick_owner_index == -1
    assert pub.trick_cards == []
    assert pub.trick_combination == (CombinationType.PASS, 0, 0)
    assert pub.trick_points == 0
    assert pub.tricks == []
    assert pub.points == [0, 0, 0, 0]
    assert pub.winner_index == -1
    assert pub.loser_index == -1
    assert pub.is_round_over == False
    assert pub.is_double_victory == False
    assert pub.game_score == ([60, 10], [40, 90])  # darf nicht zurückgesetzt werden
    assert pub.round_counter == 2  # darf nicht zurückgesetzt werden
    assert pub.trick_counter == 3  # darf nicht zurückgesetzt werden

def test_reset_game(initial_pub_state):
    """Testet das Zurücksetzen des PublicState für eine neue Partie."""
    pub = initial_pub_state

    # Zustand "verschmutzen"
    pub.table_name = "Tisch1"
    pub.player_names = ["Anton", "Bea", "Charlie", "Doris"]
    pub.game_score = [60, 10], [40, 90]
    pub.trick_counter = 3

    # Reset durchführen (reset_public_state_for_round ist static)
    pub.reset_game()

    # Prüfen, ob die Werte korrekt zurückgesetzt wurden
    pub.table_name = "Tisch1"  # darf nicht zurückgesetzt werden
    pub.player_names = ["Anton", "Bea", "Charlie", "Doris"]  # darf nicht zurückgesetzt werden
    assert pub.game_score == ([], [])
    assert pub.round_counter == 0
    assert pub.trick_counter == 0

# -------------------------------------------------------
# Alte Tests (ursprünglich mit unittest geschrieben)
# -------------------------------------------------------
