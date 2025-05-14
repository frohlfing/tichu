# tests/test_combinations.py
"""
Tests für src.lib.combinations.

Zusammenfassung der Tests für combinations:
- Kombinationen-Ermittlung (`get_figure`):
    - Korrekte Bestimmung von Typ, Länge und Rang für verschiedene gültige Kartenkombinationen (Singles, Paare, Drillinge, Treppen, Full Houses, Straßen, 4er-Bomben).
    - Korrekte Handhabung des Phönix bei der Rangkalkulation (z.B. bei Einzelkarte, Paaren, Straßen).
    - Hinweis: Testet nicht explizit Farbbomben, da `get_figure` die Farbe nicht primär prüft (dies geschieht in `build_combinations`).
- Kombinationen-Generierung (`build_combinations`):
    - Sicherstellung, dass für Beispielhände bekannte, gültige Kombinationen generiert werden.
    - Korrekte Berücksichtigung des Phönix bei der Generierung von Paaren, Drillingen, Treppen etc.
    - Erkennung von Bomben (4er).
- Aktionsraum-Erstellung (`build_action_space`):
    - Korrekte Erstellung des erlaubten Aktionsraums beim Anspiel (alle Handkombinationen, kein Passen).
    - Korrekte Erstellung des Aktionsraums, wenn eine Kombination geschlagen werden muss (nur passende Typen/Längen mit höherem Rang oder Bomben + Passen).
    - Korrekte Filterung des Aktionsraums, wenn ein (erfüllbarer oder unerfüllbarer) Wunsch aktiv ist.
- Validierung (`validate_figure`):
    - Überprüfung, ob Tupel aus (Typ, Länge, Rang) gültigen Tichu-Kombinationen entsprechen.
"""

import pytest
from typing import Tuple

# Annahme: src liegt auf gleicher Ebene wie tests
from src.lib.cards import Cards, parse_cards
from src.lib.combinations import (
    Combination, CombinationType, Combinations,
    FIGURE_PASS, FIGURE_DOG, FIGURE_MAH, FIGURE_DRA,
    get_figure, build_combinations, build_action_space, validate_figure,
)

# Helper zum Vergleichen von Kombinationslisten (ignoriert Kartenreihenfolge innerhalb einer Kombi)
def sort_combinations(combis: Combinations) -> Combinations:
    # Sortiere die Karten innerhalb jeder Kombi und dann die Liste der Kombis selbst
    # basierend auf Typ, Länge, Rang und den sortierten Karten (als String für einfache Vergleichbarkeit)
    sorted_inner = [(sorted(cards), combi_tuple) for cards, combi_tuple in combis]
    return sorted(sorted_inner, key=lambda item: (item[1][0], item[1][1], item[1][2], tuple(item[0])))

def find_combination(target_cards: Cards, combinations_list: Combinations) -> Combination | None:
    """Hilfsfunktion: Findet die Kombination für spezifische Karten in einer Liste."""
    target_sorted = sorted(target_cards)
    for cards, combi in combinations_list:
        if sorted(cards) == target_sorted:
            return combi
    return None


# --- Tests für get_figure ---

@pytest.mark.parametrize("cards_str, trick_value, expected_figure", [
    # Singles
    ("Hu", 0, FIGURE_DOG),
    ("Ma", 0, FIGURE_MAH),
    ("Dr", 0, FIGURE_DRA),
    ("Ph", 0, (CombinationType.SINGLE, 1, 1)), # Phoenix Anspiel -> Wert 1 (wie Mah Jong)
    ("Ph", 5, (CombinationType.SINGLE, 1, 5)), # Phoenix auf 5 -> Wert 5
    ("SA", 0, (CombinationType.SINGLE, 1, 14)), # Ass
    ("S5", 0, (CombinationType.SINGLE, 1, 5)),  # Fünf
    # Pairs
    ("S5 G5", 0, (CombinationType.PAIR, 2, 5)),
    ("SA RA", 0, (CombinationType.PAIR, 2, 14)),
    ("S5 Ph", 0, (CombinationType.PAIR, 2, 5)), # Paar mit Phönix
    # Triples
    ("S5 G5 B5", 0, (CombinationType.TRIPLE, 3, 5)),
    ("SA RA GA", 0, (CombinationType.TRIPLE, 3, 14)),
    ("S5 G5 Ph", 0, (CombinationType.TRIPLE, 3, 5)), # Drilling mit Phönix
    # Stairs (Treppen)
    ("S5 G5 S6 B6", 0, (CombinationType.STAIR, 4, 6)), # 5566 -> Treppe 4 lang, Rang 6
    ("S5 G5 S6 Ph", 0, (CombinationType.STAIR, 4, 6)), # 556Ph -> Treppe 4 lang, Rang 6
    ("SK BK SA Ph", 0, (CombinationType.STAIR, 4, 14)), # KKAPh -> Treppe 4 lang, Rang Ass
    # Full Houses
    ("S5 G5 B5 S6 B6", 0, (CombinationType.FULLHOUSE, 5, 5)), # 55566 -> Full House Rang 5
    ("S5 G5 S6 B6 R6", 0, (CombinationType.FULLHOUSE, 5, 6)), # 55666 -> Full House Rang 6
    ("S5 Ph S6 B6 R6", 0, (CombinationType.FULLHOUSE, 5, 6)), # 5Ph666 -> Full House Rang 6 (Ph zu Drilling)
    ("S5 G5 Ph S6 B6", 0, (CombinationType.FULLHOUSE, 5, 6)), # 55Ph66 -> Full House Rang 5 (Ph zu Drilling)
    # Streets (Straßen)
    ("S5 S6 S7 R8 S9", 0, (CombinationType.STREET, 5, 9)), # 5-9 -> Straße 5 lang, Rang 9
    ("S5 S6 S7 R8 Ph", 0, (CombinationType.STREET, 5, 9)), # 5-8 + Ph -> Straße 5 lang, Rang 9 (Ph = 9)
    ("S5 S6 Ph R8 S9", 0, (CombinationType.STREET, 5, 9)), # 5,6,Ph,8,9 -> Straße 5 lang, Rang 9 (Ph = 7)
    ("SZ RB SD SK Ph", 0, (CombinationType.STREET, 5, 14)), # Z,B,D,K,Ph -> Straße 5 lang, Rang Ass (Ph = Ass)
    ("Ph RB SD SK SA", 0, (CombinationType.STREET, 5, 14)), # Ph,B,D,K,A -> Straße 5 lang, Rang Ass (Ph = 10)
    # Bombs (4er)
    ("S5 G5 B5 R5", 0, (CombinationType.BOMB, 4, 5)),
    ("SA GA BA RA", 0, (CombinationType.BOMB, 4, 14)),
    # Bombs (Farbe/Street)
    ("S5 S6 S7 S8 S9", 0, (CombinationType.BOMB, 5, 9)), # Farbbombe
    ("S5 S6 S7 S8 S9 SZ", 0, (CombinationType.BOMB, 6, 10)),
    # Echte Farbbomben müssen manuell geprüft werden, da get_figure Farbe nicht kennt
])
def test_get_figure(cards_str, trick_value, expected_figure):
    """Testet die Ermittlung der Kombination (Typ, Länge, Rang) für verschiedene Kartensets."""
    cards = parse_cards(cards_str)
    # get_figure sortiert in-place, daher Kopie übergeben, falls Original benötigt wird
    assert get_figure(list(cards), trick_value) == expected_figure

# Spezieller Test für Farbbombe, da get_figure Farbe nicht prüft
def test_get_figure_color_bomb_type():
     """Testet, dass get_figure bei einer potentiellen Farbbombe BOMB zurückgibt (ohne Farbcheck)."""
     cards = parse_cards("S5 S6 S7 S8 S9") # 5 Karten aufsteigend, gleiche Farbe
     assert get_figure(list(cards), 0) == (CombinationType.BOMB, 5, 9)

# --- Tests für build_combinations ---

def test_build_combinations_simple():
    """Testet die Generierung von Kombinationen für eine einfache Hand."""
    hand = parse_cards("S5 G5 S6 B6 S7") # Zwei Paare, eine Single
    combis = build_combinations(hand)

    # Erwartete Kombinationen (Beispiele)
    assert find_combination(parse_cards("S5"), combis) == (CombinationType.SINGLE, 1, 5)
    assert find_combination(parse_cards("S7"), combis) == (CombinationType.SINGLE, 1, 7)
    assert find_combination(parse_cards("S5 G5"), combis) == (CombinationType.PAIR, 2, 5)
    assert find_combination(parse_cards("S6 B6"), combis) == (CombinationType.PAIR, 2, 6)
    # Treppe 5566
    assert find_combination(parse_cards("S5 G5 S6 B6"), combis) == (CombinationType.STAIR, 4, 6)
    # Keine Straßen, Fullhouses, Bomben erwartet
    assert find_combination(parse_cards("S5 G5 S6"), combis) is None # Keine gültige Kombi

    # Prüfe Gesamtzahl (kann fragil sein, besser spezifische Kombis prüfen)
    # Singles: 5, 5, 6, 6, 7 -> 5
    # Pairs: 55, 66 -> 2
    # Stairs: 5566 -> 1
    # Total: 8 (kann je nach Implementierungsdetails variieren, Phönix etc.)
    # Es ist oft besser, das Vorhandensein/Fehlen wichtiger Kombis zu prüfen als die genaue Zahl.
    assert len(combis) >= 8 # Beispielhafte Mindestanzahl

def test_build_combinations_with_phoenix():
    """Testet Kombinationen mit einem Phönix."""
    hand = parse_cards("S5 G5 S6 Ph") # Ein Paar, eine Single, Phönix
    combis = build_combinations(hand)

    # Phönix als Single
    assert find_combination(parse_cards("Ph"), combis) == (CombinationType.SINGLE, 1, 16) # Rang 16 für Phönix selbst
    # Paare mit Phönix
    assert find_combination(parse_cards("S5 Ph"), combis) == (CombinationType.PAIR, 2, 5)
    assert find_combination(parse_cards("S6 Ph"), combis) == (CombinationType.PAIR, 2, 6)
    # Drilling mit Phönix
    assert find_combination(parse_cards("S5 G5 Ph"), combis) == (CombinationType.TRIPLE, 3, 5)
    # Treppe mit Phönix (556Ph)
    assert find_combination(parse_cards("S5 G5 S6 Ph"), combis) == (CombinationType.STAIR, 4, 6)

def test_build_combinations_bomb():
    """Testet die Erkennung von Bomben."""
    hand = parse_cards("S5 G5 B5 R5 S6") # 4er-Bombe 5, Single 6
    combis = build_combinations(hand)
    assert find_combination(parse_cards("S5 G5 B5 R5"), combis) == (CombinationType.BOMB, 4, 5)

# --- Tests für build_action_space ---

# Fixture für eine Beispielhand und daraus resultierende Kombinationen
@pytest.fixture
def sample_hand_and_combis() -> Tuple[Cards, Combinations]:
    hand = parse_cards("B2 B3 B4 S5 G5 S6 B6 S7 S8 S9 Dr")
    hand.sort(reverse=True)
    combis = build_combinations(hand)
    # Enthält u.a.: Paar 5, Paar 6, Single 7, 8, 9, Drache, Treppe 5566, Straße 789
    return hand, combis

# Fixture für leere Kombinationen (Passen)
FIGURE_PASS_TUPLE = ([], FIGURE_PASS)

def test_action_space_anspiel(sample_hand_and_combis):
    """Testet den Action Space beim Anspiel (leerer Stich)."""
    hand, combis = sample_hand_and_combis
    action_space = build_action_space(combis, FIGURE_PASS, 0) # Leerer Stich, kein Wunsch
    # Muss alle Kombinationen aus der Hand enthalten, außer Passen
    assert FIGURE_PASS_TUPLE not in action_space
    # Jede Kombination im action_space muss auch in den ursprünglichen combis sein
    for action in action_space:
        assert action in combis
    # Die Anzahl muss der Anzahl der ursprünglichen Kombinationen entsprechen
    assert len(action_space) == len(combis)

def test_action_space_anspiel_dog(sample_hand_and_combis):
    """Testet den Action Space beim Anspiel nach einem Hund."""
    hand, combis = sample_hand_and_combis
    action_space = build_action_space(combis, FIGURE_DOG, 0) # Hund liegt, kein Wunsch
    # Muss alle Kombinationen aus der Hand enthalten, außer Passen
    assert FIGURE_PASS_TUPLE not in action_space
    assert len(action_space) == len(combis)

def test_action_space_beat_pair(sample_hand_and_combis):
    """Testet Action Space, wenn ein Paar geschlagen werden muss."""
    hand, combis = sample_hand_and_combis
    trick_figure = (CombinationType.PAIR, 2, 4) # Paar 4 liegt
    action_space = build_action_space(combis, trick_figure, 0)

    # Passen muss möglich sein
    assert FIGURE_PASS_TUPLE in action_space
    # Höhere Paare (Paar 5, Paar 6) müssen drin sein
    assert find_combination(parse_cards("S5 G5"), action_space) is not None
    assert find_combination(parse_cards("S6 B6"), action_space) is not None
    # Singles dürfen nicht drin sein (außer Drache/Phönix, wenn als Single erlaubt?)
    assert find_combination(parse_cards("S7"), action_space) is None
    # Drache als Single darf nicht drin sein, um Paar zu schlagen
    assert find_combination(parse_cards("Dr"), action_space) is None
    # Treppen, Straßen, Fullhouses dürfen nicht drin sein
    assert find_combination(parse_cards("S5 G5 S6 B6"), action_space) is None
    # Bomben dürften drin sein (hier haben wir keine)

def test_action_space_beat_street(sample_hand_and_combis):
    """Testet Action Space, wenn eine Straße geschlagen werden muss."""
    hand, combis = sample_hand_and_combis
    trick_figure = (CombinationType.STREET, 5, 6) # Straße 2-3-4-5-6 liegt (angenommen)
    action_space = build_action_space(combis, trick_figure, 0)

    # Passen muss möglich sein
    assert FIGURE_PASS_TUPLE in action_space
    # Nur höhere Straßen *gleicher Länge* oder Bomben sind erlaubt
    # Unsere Straße 5-6-7-8-9 ist auch Länge 5 -> sollte erlaubt sein
    assert find_combination(parse_cards("S9 S8 S7 B6 G5"), action_space) is not None
    # Andere Typen nicht erlaubt
    assert find_combination(parse_cards("G5 S5"), action_space) is None
    assert find_combination(parse_cards("Dr"), action_space) is None

def test_action_space_wish_fulfillable(sample_hand_and_combis):
    """Testet Action Space, wenn ein erfüllbarer Wunsch aktiv ist."""
    hand, combis = sample_hand_and_combis
    trick_figure = FIGURE_PASS # Anspiel
    wish = 8 # Wunsch Acht
    action_space = build_action_space(combis, trick_figure, wish)

    # Nur Kombinationen mit einer 8 sind erlaubt (hier insgesamt 29)
    assert len(action_space) == 29
    assert action_space[0][1] != (CombinationType.PASS, 0, 0)
    # Passen ist beim Anspiel nicht erlaubt, auch nicht mit Wunsch

def test_action_space_wish_unfulfillable(sample_hand_and_combis):
    """Testet Action Space, wenn ein Wunsch nicht erfüllbar ist."""
    hand, combis = sample_hand_and_combis
    trick_figure = FIGURE_PASS # Anspiel
    wish = 10 # Wunsch Zehn (nicht in Hand)
    action_space = build_action_space(combis, trick_figure, wish)

    # Da Wunsch nicht erfüllbar, ist der normale Action Space für Anspiel aktiv
    assert FIGURE_PASS_TUPLE not in action_space
    assert len(action_space) == len(combis) # Alle Kombis der Hand

# --- Tests für validate_figure --- (Beispielhaft)

@pytest.mark.parametrize("figure, expected_valid", [
    (FIGURE_PASS, True),
    ((CombinationType.SINGLE, 1, 5), True),
    ((CombinationType.SINGLE, 2, 5), False), # Falsche Länge
    ((CombinationType.PAIR, 2, 14), True),
    ((CombinationType.PAIR, 2, 1), False), # Falscher Rang (MahJong ist kein Paar)
    ((CombinationType.STAIR, 4, 6), True), # 5566
    ((CombinationType.STAIR, 5, 6), False), # Ungerade Länge
    ((CombinationType.STREET, 5, 9), True), # 5-9
    ((CombinationType.STREET, 4, 9), False), # Zu kurz
    ((CombinationType.BOMB, 4, 5), True),
    ((CombinationType.BOMB, 5, 9), True), # Farbbombe 5-9
    ((CombinationType.BOMB, 5, 4), False), # Farbbombe Rang zu niedrig für Länge
])
def test_validate_figure(figure: Combination, expected_valid: bool):
    assert validate_figure(figure) == expected_valid
