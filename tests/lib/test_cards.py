import pytest
# noinspection PyProtectedMember
from src.lib.cards import _card_labels
from src.lib.cards import *

# --- Tests für parse_cards ---

def test_parse_cards_valid():
    """Testet das Parsen eines gültigen Strings."""
    input_str = "S2 B3 G4 RA Hu Dr Ph" # Schwarz 2, Blau 3, Grün 4, Rot Ass, Hund, Drache, Phönix
    expected_cards: Cards = [(2, 1), (3, 2), (4, 3), (14, 4), CARD_DOG, CARD_DRA, CARD_PHO]
    # Sortiere beide Listen für einen stabilen Vergleich, da parse_cards keine Sortierung garantiert
    assert sorted(parse_cards(input_str)) == sorted(expected_cards)

def test_parse_cards_empty():
    """Testet das Parsen eines leeren Strings."""
    assert parse_cards("") == []

def test_parse_cards_invalid_label():
    """Testet das Parsen eines Strings mit ungültigem Label."""
    with pytest.raises(ValueError): # Erwartet einen Fehler, da das Label nicht existiert
        parse_cards("S2 XX G4")

# --- Tests für stringify_cards ---

def test_stringify_cards_standard():
    """Testet die Konvertierung einer Liste von Karten in einen String."""
    # Wichtig: stringify_cards erwartet die Reihenfolge, wie sie übergeben wird.
    input_cards: Cards = [(2, 1), (14, 4), CARD_DOG, CARD_DRA]
    expected_str = "S2 RA Hu Dr"
    assert stringify_cards(input_cards) == expected_str

def test_stringify_cards_empty():
    """Testet die Konvertierung einer leeren Liste."""
    assert stringify_cards([]) == ""

def test_stringify_cards_all_special():
    """Testet nur Sonderkarten."""
    input_cards: Cards = [CARD_DOG, CARD_MAH, CARD_DRA, CARD_PHO]
    expected_str = "Hu Ma Dr Ph"
    assert stringify_cards(input_cards) == expected_str

# --- Tests für sum_card_points --- (Wie im Beispiel, hier zusammengefasst)

@pytest.mark.parametrize(
    "hand_input, expected_points, description",
    [
        ([], 0, "Leere Hand"),
        ([(2, 1), (14, 4), CARD_MAH], 0, "Keine Punktkarten"),
        ([(5, 1), (10, 2), (13, 3), (5, 4)], 30, "Punkte von 5, 10, K"),
        ([(5, 1), CARD_DRA], 30, "Drache addiert Punkte"),
        ([(10, 1), (13, 2), CARD_PHO], -5, "Phönix zieht Punkte ab"),
        ([(5, 1), CARD_DRA, CARD_PHO], 5, "Drache und Phönix heben sich auf"),
        ([CARD_DRA, CARD_DRA], 50, "Zwei Drachen (unrealistisch, aber testet Summe)"),
        ([CARD_PHO, CARD_PHO], -50, "Zwei Phönix (unrealistisch, aber testet Summe)"),
    ],
    ids=["empty", "no_points", "5_10_K_5", "5_Dragon", "10_K_Phoenix", "5_Dragon_Phoenix", "double_dragon", "double_phoenix"]
)
def test_sum_card_points(hand_input: Cards, expected_points: int, description: str):
    """Testet die Summe der Kartenpunkte für verschiedene Hände."""
    assert sum_card_points(hand_input) == expected_points

# --- Tests für is_wish_in ---

@pytest.mark.parametrize(
    "wish_value, hand, expected_result",
    [
        (5, [(5, 1), (6, 2)], True),      # Wunsch 5 ist in Hand
        (7, [(5, 1), (6, 2)], False),     # Wunsch 7 ist nicht in Hand
        (14, [(14, 4), CARD_DRA], True), # Wunsch Ass ist in Hand
        (2, [], False),                   # Leere Hand
        (10, [(10,1), (10,2), CARD_PHO], True), # Wunsch 10 ist mehrfach da
        (8, [CARD_MAH, CARD_DRA, CARD_PHO], False) # Wunsch 8 nicht in Sonderkarten
    ]
)
def test_is_wish_in(wish_value: int, hand: Cards, expected_result: bool):
    """Testet, ob der gewünschte Kartenwert in der Hand enthalten ist."""
    assert is_wish_in(wish_value, hand) == expected_result

# --- Tests für other_cards ---

def test_other_cards_empty_hand():
    """Testet, dass bei leerer Hand das gesamte Deck zurückgegeben wird."""
    # Muss sortiert werden, da die Reihenfolge von 'deck' und 'other_cards' garantiert ist
    assert sorted(other_cards([])) == sorted(list(deck))

def test_other_cards_partial_hand():
    """Testet mit einer teilweisen Hand."""
    hand: Cards = [(2, 1), CARD_DRA]
    expected_missing: Cards = [card for card in deck if card not in hand]
    assert sorted(other_cards(hand)) == sorted(expected_missing)

def test_other_cards_full_hand():
    """Testet, dass bei voller Hand eine leere Liste zurückgegeben wird."""
    full_hand = list(deck)
    assert other_cards(full_hand) == []

# --- Tests für Vektor-Konvertierungen (Beispielhaft) ---

def test_ranks_to_vector_simple():
    """Testet die Umwandlung in einen Rang-Vektor."""
    hand: Cards = [(5, 1), (5, 2), (10, 3), CARD_DRA] # Zwei 5er, eine 10, ein Drache
    expected_vector = [0] * 17
    expected_vector[5] = 2  # Zwei 5er
    expected_vector[10] = 1 # Eine 10
    expected_vector[15] = 1 # Ein Drache
    assert ranks_to_vector(hand) == expected_vector

def test_cards_to_vector_simple():
    """Testet die Umwandlung in den vollständigen Karten-Vektor."""
    hand: Cards = [(2, 1), (14, 1), CARD_MAH]
    expected_vector = [0] * 56
    expected_vector[1] = 1 # MahJong
    expected_vector[2] = 1 # Schwarz 2
    expected_vector[50] = 1 # Schwarz As
    assert cards_to_vector(hand) == expected_vector

    h1 = [1, 0,
          0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
          0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0,
          0, 0]
    assert h1 == cards_to_vector([(0, CardSuit.SPECIAL), (14, CardSuit.SWORD), (10, CardSuit.PAGODA), (5, CardSuit.JADE), (2, CardSuit.STAR)])

    h = cards_to_vector([(0, CardSuit.SPECIAL), (14, CardSuit.SWORD), (10, CardSuit.PAGODA), (5, CardSuit.JADE), (2, CardSuit.STAR), (16, CardSuit.SPECIAL)])
    assert h[0]
    assert h[(14-2)*4 + CardSuit.SWORD + 1]
    assert h[(10-2)*4 + CardSuit.PAGODA + 1]
    assert h[(5-2)*4 + CardSuit.JADE + 1]
    assert h[(2-2)*4 + CardSuit.STAR + 1]
    assert h[55]


# -------------------------------------------------------
# Alte Tests (ursprünglich mit unittest geschrieben)
# -------------------------------------------------------

def test_parse_and_stringify_cards():
    assert len(deck) == len(_card_labels) == 56, "es gibt 56 Karten"
    assert list(deck) == parse_cards(stringify_cards(deck)), "Index nicht OK"

def test_ranks_to_vector():
    #   Hu Ma  2  3  4  5  6  7  8  9 10 Bu Da Kö As Dr Ph
    h = [1, 0, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 1, 0]
    assert h == ranks_to_vector([(0, 0), (2, 1), (3, 2), (2, 3), (14, 3), (14, 4), (15, 0)])

    #   Hu Ma  2  3  4  5  6  7  8  9 10 Bu Da Kö As Dr Ph
    h = [0, 1, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 1]
    assert h == ranks_to_vector([(1, 0), (8, 1), (8, 2), (8, 3), (8, 4), (16, 0)])

def test_cards_to_vector():
    h1 = [1, 0,
          0, 0, 0, 1,   0, 0, 0, 0,   0, 0, 0, 0,   0, 0, 1, 0,   0, 0, 0, 0,   0, 0, 0, 0,   0, 0, 0, 0,
          0, 0, 0, 0,   0, 1, 0, 0,   0, 0, 0, 0,   0, 0, 0, 0,   0, 0, 0, 0,   1, 0, 0, 0,
          0, 0]
    assert h1 == cards_to_vector([(0, CardSuit.SPECIAL), (14, CardSuit.SWORD), (10, CardSuit.PAGODA), (5, CardSuit.JADE), (2, CardSuit.STAR)])

    h2 = [0, 1,
          0, 0, 0, 0,   0, 0, 0, 0,   0, 0, 0, 0,   0, 0, 0, 0,   0, 0, 0, 0,   0, 0, 0, 0,   0, 0, 0, 0,
          0, 0, 0, 0,   0, 0, 0, 0,   0, 0, 0, 0,   0, 0, 0, 0,   0, 0, 0, 0,   0, 0, 0, 1,
          0, 1]
    assert h2 == cards_to_vector([(1, CardSuit.SPECIAL), (14, CardSuit.STAR), (16, CardSuit.SPECIAL)])

    h3 = [0, 0,
          1, 0, 0, 0,   0, 0, 0, 0,   0, 0, 0, 0,   0, 0, 0, 0,   0, 0, 0, 0,   0, 0, 0, 0,   0, 0, 0, 0,
          0, 0, 0, 0,   0, 0, 0, 0,   0, 0, 0, 0,   0, 0, 0, 0,   0, 0, 0, 0,   0, 0, 0, 0,
          1, 0]
    assert h3 == cards_to_vector([(2, CardSuit.SWORD), (15, CardSuit.SPECIAL)])

def test_is_wish_in2():
    assert is_wish_in(10, parse_cards("RA Ph BZ BZ RB SB")), "eine 10 ist unter den Karten"
    assert not is_wish_in(13, parse_cards("RA Ph BZ BZ RB SB")), "eine 13 ist nicht unter den Karten"

def test_sum_card_points2():
    assert sum_card_points(parse_cards("Ph GK BD RB RZ R9 R8 R7 R6 B5 G5 G3 B2 Ma")) == 5
    assert sum_card_points(parse_cards("Dr GK BD RB RZ R9 R8 R7 R6 B5 G5 G3 B2 Ma")) == 55
    assert sum_card_points(parse_cards("GK BD RB RZ R9 R8 R7 R6 B5 G5 G3 B2 Ma")) == 30

def test_other_cards():
    assert other_cards([card for card in deck if card[0] != 14]) == [(14, 1), (14, 2), (14, 3), (14, 4)]
