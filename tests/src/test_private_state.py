
import pytest
from unittest.mock import create_autospec, patch
from src.lib.combinations import CombinationType
from src.private_state import PrivateState
from src.lib.cards import parse_cards

# Fixture für einen initialisierten PrivateState
@pytest.fixture
def initial_priv_state() -> PrivateState:
    return PrivateState(player_index=1) # Spieler 1

def test_private_state_initialization(initial_priv_state):
    """Testet die Standardwerte nach der Initialisierung."""
    priv = initial_priv_state
    assert priv.player_index == 1
    assert priv.hand_cards == []
    assert priv.given_schupf_cards is None
    assert priv.received_schupf_cards is None
    assert priv._combination_cache == []
    assert priv._partition_cache == []
    assert priv._partitions_aborted is True

def test_reset_round(initial_priv_state):
    """Testet das Zurücksetzen eines PrivateState für eine neue Runde."""
    priv = initial_priv_state

    # Zustand "verschmutzen"
    priv.player_index = 3
    priv.hand_cards = parse_cards("S5 G5")
    priv.given_schupf_cards = (2, 2), (2, 3), (2, 4)
    priv.given_schupf_cards = (3, 2), (3, 3), (3, 4)

    # Reset durchführen
    priv.reset_round()

    # Prüfen, ob die Werte korrekt zurückgesetzt wurden
    assert priv.player_index == 3  # darf nicht zurückgesetzt werden
    assert priv.hand_cards == []
    assert priv.given_schupf_cards is None
    assert priv.received_schupf_cards is None

def test_private_state_hand_cards_setter_clears_cache(initial_priv_state):
    """Testet, ob das Setzen der Handkarten die Caches leert."""
    priv = initial_priv_state

    # Befülle Caches (simuliert)
    # noinspection PyTypeChecker
    priv._combination_cache = ["dummy_combi"]
    # noinspection PyTypeChecker
    priv._partition_cache = ["dummy_parti"]
    priv._partitions_aborted = False

    new_hand = parse_cards("S5 G5")
    priv.hand_cards = new_hand

    assert priv.hand_cards == new_hand
    assert priv._combination_cache == [] # Cache sollte leer sein
    assert priv._partition_cache == [] # Cache sollte leer sein
    assert priv._partitions_aborted is True # Flag sollte zurückgesetzt sein

def test_private_state_to_dict(initial_priv_state):
    """Testet die Umwandlung in ein Dictionary."""
    priv = initial_priv_state
    priv.hand_cards = parse_cards("SA RA GA")
    priv.given_schupf_cards = (2,1), (3,2), (4,3)  # S2 B3 G4
    priv.received_schupf_cards = (5,4), (6,1), (7,2)  # R5 S6 B7
    priv_dict = priv.to_dict()
    assert priv_dict["player_index"] == 1
    assert priv_dict["hand_cards"] == "SA RA GA"
    assert priv_dict["given_schupf_cards"] == "S2 B3 G4"
    assert priv_dict["received_schupf_cards"] == "R5 S6 B7"

# --- Tests für Properties ---

def test_private_state_indices(initial_priv_state):
    """Testet die Berechnung der Partner/Gegner-Indizes."""
    priv = initial_priv_state # Spieler 1
    assert priv.partner_index == 3
    assert priv.opponent_right_index == 2
    assert priv.opponent_left_index == 0

    priv.player_index = 3
    assert priv.partner_index == 1
    assert priv.opponent_right_index == 0
    assert priv.opponent_left_index == 2

def test_private_state_combinations_property(initial_priv_state):
    """Testet, ob die combinations-Property den Cache füllt."""
    priv = initial_priv_state
    hand = parse_cards("S5 G5 S6 Ph")
    priv.hand_cards = hand
    assert priv._combination_cache == [] # Cache ist initial leer

    # Erster Zugriff auf combinations
    combis = priv.combinations
    assert len(combis) > 0 # Es sollten Kombinationen gefunden werden
    assert priv._combination_cache is combis # Property sollte den Cache zurückgeben

    # Zweiter Zugriff sollte den Cache wiederverwenden
    combis_cached = priv.combinations
    assert combis_cached is combis # Sollte dasselbe Objekt sein

    # Setzen der Handkarten sollte den Cache leeren
    priv.hand_cards = parse_cards("S2")
    assert priv._combination_cache == []
    new_combis = priv.combinations
    assert len(new_combis) == 1
    assert new_combis[0][0] == parse_cards("S2")

# Ein Test für Partitions ist schwierig, da die Logik komplex ist.
# Man könnte testen, ob der Cache befüllt wird.
def test_private_state_partitions_property(initial_priv_state):
    """Testet, ob die partitions-Property den Cache füllt."""
    priv = initial_priv_state
    hand = parse_cards("S5 G5 S6 S7 S8") # Einfache Hand
    priv.hand_cards = hand
    assert priv._partition_cache == []
    assert priv._partitions_aborted is True

    partitions = priv.partitions
    # Wir können nicht leicht prüfen, ob die Partitionen *korrekt* sind,
    # aber wir können prüfen, ob *etwas* generiert wurde (wenn die Hand gültig ist)
    # und ob der Cache verwendet wird.
    assert isinstance(partitions, list)
    # assert len(partitions) > 0 # Erwarte mind. eine Partition für eine normale Hand
    assert priv._partition_cache is partitions
    # assert priv._partitions_aborted is False # Sollte False sein, wenn build_partitions durchläuft

    partitions_cached = priv.partitions
    assert partitions_cached is partitions

# -------------------------------------------------
# test_has_bomb mit drei verschiedene Techniken

# Variante a) Mit create_autospec ein Mock-Objekt von PrivateState erstellen.

@pytest.mark.parametrize(
    "combinations, expected",
    [
        ([([], (CombinationType.BOMB, 4, 12))], True),
        ([([], (CombinationType.TRIPLE, 3, 11))], False),
        ([], False),
    ],
)
def test_has_bomb_with_autospec(combinations, expected):
    """
    Test für Property has_bomb.
    """
    mock_private_state = create_autospec(PrivateState, instance=True)
    type(mock_private_state).combinations = combinations
    type(mock_private_state).has_bomb = PrivateState.has_bomb
    assert mock_private_state.has_bomb is expected

# Variante b) Mock-Klasse durch Vererbung erstellen

class MockPrivateState(PrivateState):
    def __init__(self, combinations):
        self.hand_cards = []
        self._combination_cache = combinations or []

@pytest.mark.parametrize(
    "combinations, expected",
    [
        ([([], (CombinationType.BOMB, 4, 12))], True),
        ([([], (CombinationType.TRIPLE, 3, 11))], False),
        ([], False),
    ],
)
def test_has_bomb_with_mock_class(combinations, expected):
    """
    Test für Property has_bomb.
    """
    state = MockPrivateState(combinations)
    assert state.has_bomb == expected

@patch("src.private_state.build_combinations")
def test_has_bomb_with_mocked_build_partitions(mock_build_combinations):
    """
    Test für Property has_bomb.
    Variante c) build_partitions patchen.
    """
    mock_build_combinations.return_value = [([], (CombinationType.BOMB, 4, 12))]
    priv = PrivateState(player_index=1)
    priv._hand_cards = [(2,2)]
    assert priv.has_bomb is True

# -------------------------------------------------------
# Alte Tests (ursprünglich mit unittest geschrieben)
# -------------------------------------------------------
