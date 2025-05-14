# tests/test_cards.py
"""
Tests für src.lib.cards.

Zusammenfassung der Tests für cards:
- Konvertierung:
    - String-zu-Karte (`parse_cards`) und Karte-zu-String (`stringify_cards`).
    - Umwandlung von Kartenlisten in Vektorrepräsentationen (`ranks_to_vector`, `cards_to_vector`).
- Punktberechnung:
    - Korrekte Berechnung der Summe der Kartenpunkte (`sum_card_points`), inklusive der Sonderkarten Drache und Phönix.
- Kartenlogik:
    - Korrekte Prüfung, ob ein gewünschter Kartenwert in einer Hand enthalten ist (`is_wish_in`).
    - Korrekte Ermittlung der im Deck fehlenden Karten anhand einer Hand (`other_cards`).
- Validierung:
    - Sicherstellung, dass ungültige Kartennamen beim Parsen Fehler auslösen.
    - Testen von Randfällen wie leeren Listen/Strings.
"""

import pytest

# Annahme: src liegt auf gleicher Ebene wie tests
from src.lib.cards import (
    Cards, deck,
    parse_cards, stringify_cards,
    sum_card_points, is_wish_in, other_cards,
    ranks_to_vector, cards_to_vector,
    CARD_DOG, CARD_MAH, CARD_DRA, CARD_PHO
)

# --- Tests für parse_cards ---

def test_parse_cards_valid():
    """Testet das Parsen eines gültigen Strings."""
    input_str = "S2 B3 G4 RA Hu Dr Ph" # Schwarz 2, Blau 3, Grün 4, Rot Ass, Hund, Drache, Phönix
    expected_cards: Cards = [(2, 1), (3, 2), (4, 3), (14, 4), CARD_DOG, CARD_DRA, CARD_PHO]
    # Sortiere beide Listen für einen stabilen Vergleich, da parse_cards keine Sortierung garantiert
    assert sorted(parse_cards(input_str)) == sorted(expected_cards)

# todo
# def test_parse_cards_empty():
#     """Testet das Parsen eines leeren Strings."""
#     assert parse_cards("") == []

# todo
# def test_parse_cards_extra_spaces():
#     """Testet das Parsen mit überflüssigen Leerzeichen."""
#     input_str = " S2  B3  "
#     expected_cards: Cards = [(2, 1), (3, 2)]
#     assert sorted(parse_cards(input_str)) == sorted(expected_cards)

def test_parse_cards_invalid_label():
    """Testet das Parsen eines Strings mit ungültigem Label."""
    with pytest.raises(KeyError): # Erwartet einen Fehler, da das Label nicht existiert
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
    # Muss sortiert werden, da Reihenfolge von 'deck' und 'other_cards' garantiert ist
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
    hand: Cards = [(2, 1), CARD_MAH] # Schwarz 2, MahJong
    # Erwarteter Vektor (Länge 56): Nur an den Indizes für S2 und MahJong ist eine 1
    # Index von S2 in _deck_index: 2
    # Index von Ma in _deck_index: 1
    expected_vector = [0] * 56
    expected_vector[1] = 1 # MahJong
    expected_vector[2] = 1 # Schwarz 2
    assert cards_to_vector(hand) == expected_vector
