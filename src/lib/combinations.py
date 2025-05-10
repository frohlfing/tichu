__all__ = "CombinationType", "Combination", \
    "PASS", "SINGLE", "PAIR", "TRIPLE", "STAIR", "FULLHOUSE", "STREET", "BOMB", \
    "FIGURE_PASS", "FIGURE_DOG", "FIGURE_MAH", "FIGURE_DRA", "FIGURE_PHO", \
    "validate_figure", "parse_figure", "stringify_figure", "stringify_type", "get_figure", \
    "build_combinations", "remove_combinations", \
    "build_action_space",

import enum
from src.lib.cards import CARD_DOG, CARD_PHO, is_wish_in, Card, Cards
from typing import Tuple, List

# todo Dokumentieren (reStructuredText)

# -----------------------------------------------------------------------------
# Kartenkombinationen
# -----------------------------------------------------------------------------

# Enum für Kombinationstypen
class CombinationType(enum.IntEnum):  # todo überall konsequent verwenden
    PASS = 0  # Passen
    SINGLE = 1  # Einzelkarte
    PAIR = 2  # Paar
    TRIPLE = 3  # Drilling
    STAIR = 4  # Treppe
    FULLHOUSE = 5  # Full House
    STREET = 6  # Straße
    BOMB = 7  # Vierer-Bombe oder Farbbombe

# Typ-Alias für eine Kombination
Combination = Tuple[CombinationType, int, int]  # (Typ, Länge, Rang)  # todo überall konsequent verwenden
Combinations = List[Tuple[Cards, Combination]]  # todo missverständlich? Wenn nicht, überall konsequent verwenden

# Figur-Typen  # todo statt dessen CombinationType verwenden
PASS = 0       # Passen
SINGLE = 1     # Einzelkarte
PAIR = 2       # Paar
TRIPLE = 3     # Drilling
STAIR = 4      # Treppe
FULLHOUSE = 5  # Full House
STREET = 6     # Straße
BOMB = 7       # Vierer-Bombe oder Farbbombe

# Sonderkarten einzeln ausgespielt (Typ, Länge, Rang)
FIGURE_PASS = (0, 0, 0)
FIGURE_DOG = (1, 1, 0)
FIGURE_MAH = (1, 1, 1)
FIGURE_DRA = (1, 1, 15)
FIGURE_PHO = (1, 1, 16)

# todo prüfen, ob wir das tatsächlich brauchen
# Alle möglichen Figuren
_figures = (  # Index → figure == (Typ, Länge, Rang)
    # Passen - PASS
    (0, 0, 0),
    # Einzelkarten - SINGLE  (1,1,0) == Hund, (1,1,1) == MahJong, (1,1,15) == Drache, (1,1,16) == Phönix
    (1, 1, 0), (1, 1, 1), (1, 1, 2), (1, 1, 3), (1, 1, 4), (1, 1, 5), (1, 1, 6), (1, 1, 7), (1, 1, 8), (1, 1, 9), (1, 1, 10), (1, 1, 11), (1, 1, 12), (1, 1, 13), (1, 1, 14), (1, 1, 15), (1, 1, 16),
    # Paare - PAIR
    (2, 2, 2), (2, 2, 3), (2, 2, 4), (2, 2, 5), (2, 2, 6), (2, 2, 7), (2, 2, 8), (2, 2, 9), (2, 2, 10), (2, 2, 11), (2, 2, 12), (2, 2, 13), (2, 2, 14),
    # Drillinge - TRIPLE
    (3, 3, 2), (3, 3, 3), (3, 3, 4), (3, 3, 5), (3, 3, 6), (3, 3, 7), (3, 3, 8), (3, 3, 9), (3, 3, 10), (3, 3, 11), (3, 3, 12), (3, 3, 13), (3, 3, 14),
    # Treppen - STAIR
    (4, 4, 3), (4, 4, 4), (4, 4, 5), (4, 4, 6), (4, 4, 7), (4, 4, 8), (4, 4, 9), (4, 4, 10), (4, 4, 11), (4, 4, 12), (4, 4, 13), (4, 4, 14),
    (4, 6, 4), (4, 6, 5), (4, 6, 6), (4, 6, 7), (4, 6, 8), (4, 6, 9), (4, 6, 10), (4, 6, 11), (4, 6, 12), (4, 6, 13), (4, 6, 14),
    (4, 8, 5), (4, 8, 6), (4, 8, 7), (4, 8, 8), (4, 8, 9), (4, 8, 10), (4, 8, 11), (4, 8, 12), (4, 8, 13), (4, 8, 14),
    (4, 10, 6), (4, 10, 7), (4, 10, 8), (4, 10, 9), (4, 10, 10), (4, 10, 11), (4, 10, 12), (4, 10, 13), (4, 10, 14),
    (4, 12, 7), (4, 12, 8), (4, 12, 9), (4, 12, 10), (4, 12, 11), (4, 12, 12), (4, 12, 13), (4, 12, 14),
    (4, 14, 8), (4, 14, 9), (4, 14, 10), (4, 14, 11), (4, 14, 12), (4, 14, 13), (4, 14, 14),
    # FullHouses - FULLHOUSE
    (5, 5, 2), (5, 5, 3), (5, 5, 4), (5, 5, 5), (5, 5, 6), (5, 5, 7), (5, 5, 8), (5, 5, 9), (5, 5, 10), (5, 5, 11), (5, 5, 12), (5, 5, 13), (5, 5, 14),
    # Straßen - STREET
    (6, 5, 5), (6, 5, 6), (6, 5, 7), (6, 5, 8), (6, 5, 9), (6, 5, 10), (6, 5, 11), (6, 5, 12), (6, 5, 13), (6, 5, 14),
    (6, 6, 6), (6, 6, 7), (6, 6, 8), (6, 6, 9), (6, 6, 10), (6, 6, 11), (6, 6, 12), (6, 6, 13), (6, 6, 14),
    (6, 7, 7), (6, 7, 8), (6, 7, 9), (6, 7, 10), (6, 7, 11), (6, 7, 12), (6, 7, 13), (6, 7, 14),
    (6, 8, 8), (6, 8, 9), (6, 8, 10), (6, 8, 11), (6, 8, 12), (6, 8, 13), (6, 8, 14),
    (6, 9, 9), (6, 9, 10), (6, 9, 11), (6, 9, 12), (6, 9, 13), (6, 9, 14),
    (6, 10, 10), (6, 10, 11), (6, 10, 12), (6, 10, 13), (6, 10, 14),
    (6, 11, 11), (6, 11, 12), (6, 11, 13), (6, 11, 14),
    (6, 12, 12), (6, 12, 13), (6, 12, 14),
    (6, 13, 13), (6, 13, 14),
    (6, 14, 14),
    # Bomben - BOMB
    (7, 4, 2), (7, 4, 3), (7, 4, 4), (7, 4, 5), (7, 4, 6), (7, 4, 7), (7, 4, 8), (7, 4, 9), (7, 4, 10), (7, 4, 11), (7, 4, 12), (7, 4, 13), (7, 4, 14),
    (7, 5, 6), (7, 5, 7), (7, 5, 8), (7, 5, 9), (7, 5, 10), (7, 5, 11), (7, 5, 12), (7, 5, 13), (7, 5, 14),
    (7, 6, 7), (7, 6, 8), (7, 6, 9), (7, 6, 10), (7, 6, 11), (7, 6, 12), (7, 6, 13), (7, 6, 14),
    (7, 7, 8), (7, 7, 9), (7, 7, 10), (7, 7, 11), (7, 7, 12), (7, 7, 13), (7, 7, 14),
    (7, 8, 9), (7, 8, 10), (7, 8, 11), (7, 8, 12), (7, 8, 13), (7, 8, 14),
    (7, 9, 10), (7, 9, 11), (7, 9, 12), (7, 9, 13), (7, 9, 14),
    (7, 10, 11), (7, 10, 12), (7, 10, 13), (7, 10, 14),
    (7, 11, 12), (7, 11, 13), (7, 11, 14),
    (7, 12, 13), (7, 12, 14),
    (7, 13, 14),
)

# todo prüfen, ob wir das tatsächlich brauchen
# wie figures.index(figure), aber schneller!
_figures_index = {  # figure == (Typ, Länge, Rang) → Index
    # Passen - PASS
    (0, 0, 0): 0,
    # Einzelkarten - SINGLE  (1,1,0) == Hund, (1,1,1) == MahJong, (1,1,15) == Drache, (1,1,16) == Phönix
    (1, 1, 0): 1, (1, 1, 1): 2, (1, 1, 2): 3, (1, 1, 3): 4, (1, 1, 4): 5, (1, 1, 5): 6, (1, 1, 6): 7, (1, 1, 7): 8, (1, 1, 8): 9, (1, 1, 9): 10, (1, 1, 10): 11, (1, 1, 11): 12, (1, 1, 12): 13, (1, 1, 13): 14, (1, 1, 14): 15, (1, 1, 15): 16, (1, 1, 16): 17,
    # Paare - PAIR
    (2, 2, 2): 18, (2, 2, 3): 19, (2, 2, 4): 20, (2, 2, 5): 21, (2, 2, 6): 22, (2, 2, 7): 23, (2, 2, 8): 24, (2, 2, 9): 25, (2, 2, 10): 26, (2, 2, 11): 27, (2, 2, 12): 28, (2, 2, 13): 29, (2, 2, 14): 30,
    # Drillinge - TRIPLE
    (3, 3, 2): 31, (3, 3, 3): 32, (3, 3, 4): 33, (3, 3, 5): 34, (3, 3, 6): 35, (3, 3, 7): 36, (3, 3, 8): 37, (3, 3, 9): 38, (3, 3, 10): 39, (3, 3, 11): 40, (3, 3, 12): 41, (3, 3, 13): 42, (3, 3, 14): 43,
    # Treppen - STAIR
    (4, 4, 3): 44, (4, 4, 4): 45, (4, 4, 5): 46, (4, 4, 6): 47, (4, 4, 7): 48, (4, 4, 8): 49, (4, 4, 9): 50, (4, 4, 10): 51, (4, 4, 11): 52, (4, 4, 12): 53, (4, 4, 13): 54, (4, 4, 14): 55,
    (4, 6, 4): 56, (4, 6, 5): 57, (4, 6, 6): 58, (4, 6, 7): 59, (4, 6, 8): 60, (4, 6, 9): 61, (4, 6, 10): 62, (4, 6, 11): 63, (4, 6, 12): 64, (4, 6, 13): 65, (4, 6, 14): 66,
    (4, 8, 5): 67, (4, 8, 6): 68, (4, 8, 7): 69, (4, 8, 8): 70, (4, 8, 9): 71, (4, 8, 10): 72, (4, 8, 11): 73, (4, 8, 12): 74, (4, 8, 13): 75, (4, 8, 14): 76,
    (4, 10, 6): 77, (4, 10, 7): 78, (4, 10, 8): 79, (4, 10, 9): 80, (4, 10, 10): 81, (4, 10, 11): 82, (4, 10, 12): 83, (4, 10, 13): 84, (4, 10, 14): 85,
    (4, 12, 7): 86, (4, 12, 8): 87, (4, 12, 9): 88, (4, 12, 10): 89, (4, 12, 11): 90, (4, 12, 12): 91, (4, 12, 13): 92, (4, 12, 14): 93,
    (4, 14, 8): 94, (4, 14, 9): 95, (4, 14, 10): 96, (4, 14, 11): 97, (4, 14, 12): 98, (4, 14, 13): 99, (4, 14, 14): 100,
    # FullHouses - FULLHOUSE
    (5, 5, 2): 101, (5, 5, 3): 102, (5, 5, 4): 103, (5, 5, 5): 104, (5, 5, 6): 105, (5, 5, 7): 106, (5, 5, 8): 107, (5, 5, 9): 108, (5, 5, 10): 109, (5, 5, 11): 110, (5, 5, 12): 111, (5, 5, 13): 112, (5, 5, 14): 113,
    # Straßen - STREET
    (6, 5, 5): 114, (6, 5, 6): 115, (6, 5, 7): 116, (6, 5, 8): 117, (6, 5, 9): 118, (6, 5, 10): 119, (6, 5, 11): 120, (6, 5, 12): 121, (6, 5, 13): 122, (6, 5, 14): 123,
    (6, 6, 6): 124, (6, 6, 7): 125, (6, 6, 8): 126, (6, 6, 9): 127, (6, 6, 10): 128, (6, 6, 11): 129, (6, 6, 12): 130, (6, 6, 13): 131, (6, 6, 14): 132,
    (6, 7, 7): 133, (6, 7, 8): 134, (6, 7, 9): 135, (6, 7, 10): 136, (6, 7, 11): 137, (6, 7, 12): 138, (6, 7, 13): 139, (6, 7, 14): 140,
    (6, 8, 8): 141, (6, 8, 9): 142, (6, 8, 10): 143, (6, 8, 11): 144, (6, 8, 12): 145, (6, 8, 13): 146, (6, 8, 14): 147,
    (6, 9, 9): 148, (6, 9, 10): 149, (6, 9, 11): 150, (6, 9, 12): 151, (6, 9, 13): 152, (6, 9, 14): 153,
    (6, 10, 10): 154, (6, 10, 11): 155, (6, 10, 12): 156, (6, 10, 13): 157, (6, 10, 14): 158,
    (6, 11, 11): 159, (6, 11, 12): 160, (6, 11, 13): 161, (6, 11, 14): 162,
    (6, 12, 12): 163, (6, 12, 13): 164, (6, 12, 14): 165,
    (6, 13, 13): 166, (6, 13, 14): 167,
    (6, 14, 14): 168,
    # Bomben - BOMB
    (7, 4, 2): 169, (7, 4, 3): 170, (7, 4, 4): 171, (7, 4, 5): 172, (7, 4, 6): 173, (7, 4, 7): 174, (7, 4, 8): 175, (7, 4, 9): 176, (7, 4, 10): 177, (7, 4, 11): 178, (7, 4, 12): 179, (7, 4, 13): 180, (7, 4, 14): 181,
    (7, 5, 6): 182, (7, 5, 7): 183, (7, 5, 8): 184, (7, 5, 9): 185, (7, 5, 10): 186, (7, 5, 11): 187, (7, 5, 12): 188, (7, 5, 13): 189, (7, 5, 14): 190,
    (7, 6, 7): 191, (7, 6, 8): 192, (7, 6, 9): 193, (7, 6, 10): 194, (7, 6, 11): 195, (7, 6, 12): 196, (7, 6, 13): 197, (7, 6, 14): 198,
    (7, 7, 8): 199, (7, 7, 9): 200, (7, 7, 10): 201, (7, 7, 11): 202, (7, 7, 12): 203, (7, 7, 13): 204, (7, 7, 14): 205,
    (7, 8, 9): 206, (7, 8, 10): 207, (7, 8, 11): 208, (7, 8, 12): 209, (7, 8, 13): 210, (7, 8, 14): 211,
    (7, 9, 10): 212, (7, 9, 11): 213, (7, 9, 12): 214, (7, 9, 13): 215, (7, 9, 14): 216,
    (7, 10, 11): 217, (7, 10, 12): 218, (7, 10, 13): 219, (7, 10, 14): 220,
    (7, 11, 12): 221, (7, 11, 13): 222, (7, 11, 14): 223,
    (7, 12, 13): 224, (7, 12, 14): 225,
    (7, 13, 14): 226,
}

# todo prüfen, ob wir das tatsächlich brauchen
_figurelabels = (
    # PASS
    "Passen",
    # SINGLE
    "Hund", "MahJong", "Zwei", "Drei", "Vier", "Fünf", "Sechs", "Sieben", "Acht", "Neun", "Zehn", "Bube", "Dame", "König", "As", "Drache", "Phönix",
    # PAIR
    "Paar2", "Paar3", "Paar4", "Paar5", "Paar6", "Paar7", "Paar8", "Paar9", "PaarZ", "PaarB", "PaarD", "PaarK", "PaarA",
    # TRIPLE
    "Drilling2", "Drilling3", "Drilling4", "Drilling5", "Drilling6", "Drilling7", "Drilling8", "Drilling9", "DrillingZ", "DrillingB", "DrillingD", "DrillingK", "DrillingA",
    # STAIR
    "2erTreppe3", "2erTreppe4", "2erTreppe5", "2erTreppe6", "2erTreppe7", "2erTreppe8", "2erTreppe9", "2erTreppeZ", "2erTreppeB", "2erTreppeD", "2erTreppeK", "2erTreppeA",
    "3erTreppe4", "3erTreppe5", "3erTreppe6", "3erTreppe7", "3erTreppe8", "3erTreppe9", "3erTreppeZ", "3erTreppeB", "3erTreppeD", "3erTreppeK", "3erTreppeA",
    "4erTreppe5", "4erTreppe6", "4erTreppe7", "4erTreppe8", "4erTreppe9", "4erTreppeZ", "4erTreppeB", "4erTreppeD", "4erTreppeK", "4erTreppeA",
    "5erTreppe6", "5erTreppe7", "5erTreppe8", "5erTreppe9", "5erTreppeZ", "5erTreppeB", "5erTreppeD", "5erTreppeK", "5erTreppeA",
    "6erTreppe7", "6erTreppe8", "6erTreppe9", "6erTreppeZ", "6erTreppeB", "6erTreppeD", "6erTreppeK", "6erTreppeA",
    "7erTreppe8", "7erTreppe9", "7erTreppeZ", "7erTreppeB", "7erTreppeD", "7erTreppeK", "7erTreppeA",
    # FULLHOUSE
    "FullHouse2", "FullHouse3", "FullHouse4", "FullHouse5", "FullHouse6", "FullHouse7", "FullHouse8", "FullHouse9", "FullHouseZ", "FullHouseB", "FullHouseD", "FullHouseK", "FullHouseA",
    # STREET
    "5erStraße5", "5erStraße6", "5erStraße7", "5erStraße8", "5erStraße9", "5erStraßeZ", "5erStraßeB", "5erStraßeD", "5erStraßeK", "5erStraßeA",
    "6erStraße6", "6erStraße7", "6erStraße8", "6erStraße9", "6erStraßeZ", "6erStraßeB", "6erStraßeD", "6erStraßeK", "6erStraßeA",
    "7erStraße7", "7erStraße8", "7erStraße9", "7erStraßeZ", "7erStraßeB", "7erStraßeD", "7erStraßeK", "7erStraßeA",
    "8erStraße8", "8erStraße9", "8erStraßeZ", "8erStraßeB", "8erStraßeD", "8erStraßeK", "8erStraßeA",
    "9erStraße9", "9erStraßeZ", "9erStraßeB", "9erStraßeD", "9erStraßeK", "9erStraßeA",
    "10erStraßeZ", "10erStraßeB", "10erStraßeD", "10erStraßeK", "10erStraßeA",
    "11erStraßeB", "11erStraßeD", "11erStraßeK", "11erStraßeA",
    "12erStraßeD", "12erStraßeK", "12erStraßeA",
    "13erStraßeK", "13erStraßeA",
    "14erStraßeA",
    # BOMB
    "4erBombe2", "4erBombe3", "4erBombe4", "4erBombe5", "4erBombe6", "4erBombe7", "4erBombe8", "4erBombe9", "4erBombeZ", "4erBombeB", "4erBombeD", "4erBombeK", "4erBombeA",
    "5erBombe6", "5erBombe7", "5erBombe8", "5erBombe9", "5erBombeZ", "5erBombeB", "5erBombeD", "5erBombeK", "5erBombeA",
    "6erBombe7", "6erBombe8", "6erBombe9", "6erBombeZ", "6erBombeB", "6erBombeD", "6erBombeK", "6erBombeA",
    "7erBombe8", "7erBombe9", "7erBombeZ", "7erBombeB", "7erBombeD", "7erBombeK", "7erBombeA",
    "8erBombe9", "8erBombeZ", "8erBombeB", "8erBombeD", "8erBombeK", "8erBombeA",
    "9erBombeZ", "9erBombeB", "9erBombeD", "9erBombeK", "9erBombeA",
    "10erBombeB", "10erBombeD", "10erBombeK", "10erBombeA",
    "11erBombeD", "11erBombeK", "11erBombeA",
    "12erBombeK", "12erBombeA",
    "13erBombeA",
)

# todo prüfen, ob wir das tatsächlich brauchen
# wie figurelabels.index(label), aber schneller
_figurelabels_index = {
    # PASS
    "Passen": 0,
    # SINGLE
    "Hund": 1, "MahJong": 2, "Zwei": 3, "Drei": 4, "Vier": 5, "Fünf": 6, "Sechs": 7, "Sieben": 8, "Acht": 9, "Neun": 10, "Zehn": 11, "Bube": 12, "Dame": 13, "König": 14, "As": 15, "Drache": 16, "Phönix": 17,
    # PAIR
    "Paar2": 18, "Paar3": 19, "Paar4": 20, "Paar5": 21, "Paar6": 22, "Paar7": 23, "Paar8": 24, "Paar9": 25, "PaarZ": 26, "PaarB": 27, "PaarD": 28, "PaarK": 29, "PaarA": 30,
    # TRIPLE
    "Drilling2": 31, "Drilling3": 32, "Drilling4": 33, "Drilling5": 34, "Drilling6": 35, "Drilling7": 36, "Drilling8": 37, "Drilling9": 38, "DrillingZ": 39, "DrillingB": 40, "DrillingD": 41, "DrillingK": 42, "DrillingA": 43,
    # STAIR
    "2erTreppe3": 44, "2erTreppe4": 45, "2erTreppe5": 46, "2erTreppe6": 47, "2erTreppe7": 48, "2erTreppe8": 49, "2erTreppe9": 50, "2erTreppeZ": 51, "2erTreppeB": 52, "2erTreppeD": 53, "2erTreppeK": 54, "2erTreppeA": 55,
    "3erTreppe4": 56, "3erTreppe5": 57, "3erTreppe6": 58, "3erTreppe7": 59, "3erTreppe8": 60, "3erTreppe9": 61, "3erTreppeZ": 62, "3erTreppeB": 63, "3erTreppeD": 64, "3erTreppeK": 65, "3erTreppeA": 66,
    "4erTreppe5": 67, "4erTreppe6": 68, "4erTreppe7": 69, "4erTreppe8": 70, "4erTreppe9": 71, "4erTreppeZ": 72, "4erTreppeB": 73, "4erTreppeD": 74, "4erTreppeK": 75, "4erTreppeA": 76,
    "5erTreppe6": 77, "5erTreppe7": 78, "5erTreppe8": 79, "5erTreppe9": 80, "5erTreppeZ": 81, "5erTreppeB": 82, "5erTreppeD": 83, "5erTreppeK": 84, "5erTreppeA": 85,
    "6erTreppe7": 86, "6erTreppe8": 87, "6erTreppe9": 88, "6erTreppeZ": 89, "6erTreppeB": 90, "6erTreppeD": 91, "6erTreppeK": 92, "6erTreppeA": 93,
    "7erTreppe8": 94, "7erTreppe9": 95, "7erTreppeZ": 96, "7erTreppeB": 97, "7erTreppeD": 98, "7erTreppeK": 99, "7erTreppeA": 100,
    # FULLHOUSE
    "FullHouse2": 101, "FullHouse3": 102, "FullHouse4": 103, "FullHouse5": 104, "FullHouse6": 105, "FullHouse7": 106, "FullHouse8": 107, "FullHouse9": 108, "FullHouseZ": 109, "FullHouseB": 110, "FullHouseD": 111, "FullHouseK": 112, "FullHouseA": 113,
    # STREET
    "5erStraße5": 114, "5erStraße6": 115, "5erStraße7": 116, "5erStraße8": 117, "5erStraße9": 118, "5erStraßeZ": 119, "5erStraßeB": 120, "5erStraßeD": 121, "5erStraßeK": 122, "5erStraßeA": 123,
    "6erStraße6": 124, "6erStraße7": 125, "6erStraße8": 126, "6erStraße9": 127, "6erStraßeZ": 128, "6erStraßeB": 129, "6erStraßeD": 130, "6erStraßeK": 131, "6erStraßeA": 132,
    "7erStraße7": 133, "7erStraße8": 134, "7erStraße9": 135, "7erStraßeZ": 136, "7erStraßeB": 137, "7erStraßeD": 138, "7erStraßeK": 139, "7erStraßeA": 140,
    "8erStraße8": 141, "8erStraße9": 142, "8erStraßeZ": 143, "8erStraßeB": 144, "8erStraßeD": 145, "8erStraßeK": 146, "8erStraßeA": 147,
    "9erStraße9": 148, "9erStraßeZ": 149, "9erStraßeB": 150, "9erStraßeD": 151, "9erStraßeK": 152, "9erStraßeA": 153,
    "10erStraßeZ": 154, "10erStraßeB": 155, "10erStraßeD": 156, "10erStraßeK": 157, "10erStraßeA": 158,
    "11erStraßeB": 159, "11erStraßeD": 160, "11erStraßeK": 161, "11erStraßeA": 162,
    "12erStraßeD": 163, "12erStraßeK": 164, "12erStraßeA": 165,
    "13erStraßeK": 166, "13erStraßeA": 167,
    "14erStraßeA": 168,
    # BOMB
    "4erBombe2": 169, "4erBombe3": 170, "4erBombe4": 171, "4erBombe5": 172, "4erBombe6": 173, "4erBombe7": 174, "4erBombe8": 175, "4erBombe9": 176, "4erBombeZ": 177, "4erBombeB": 178, "4erBombeD": 179, "4erBombeK": 180, "4erBombeA": 181,
    "5erBombe6": 182, "5erBombe7": 183, "5erBombe8": 184, "5erBombe9": 185, "5erBombeZ": 186, "5erBombeB": 187, "5erBombeD": 188, "5erBombeK": 189, "5erBombeA": 190,
    "6erBombe7": 191, "6erBombe8": 192, "6erBombe9": 193, "6erBombeZ": 194, "6erBombeB": 195, "6erBombeD": 196, "6erBombeK": 197, "6erBombeA": 198,
    "7erBombe8": 199, "7erBombe9": 200, "7erBombeZ": 201, "7erBombeB": 202, "7erBombeD": 203, "7erBombeK": 204, "7erBombeA": 205,
    "8erBombe9": 206, "8erBombeZ": 207, "8erBombeB": 208, "8erBombeD": 209, "8erBombeK": 210, "8erBombeA": 211,
    "9erBombeZ": 212, "9erBombeB": 213, "9erBombeD": 214, "9erBombeK": 215, "9erBombeA": 216,
    "10erBombeB": 217, "10erBombeD": 218, "10erBombeK": 219, "10erBombeA": 220,
    "11erBombeD": 221, "11erBombeK": 222, "11erBombeA": 223,
    "12erBombeK": 224, "12erBombeA": 225,
    "13erBombeA": 226,
}


# Ermittelt, ob Typ, Länge und Rang eine gültige Kartenkombination angibt
def validate_figure(figure: tuple) -> bool:
    t, m, r = figure
    if t == PASS:
        return m == 0 and r == 0
    if t == SINGLE:  # Einzelkarte
        return m == 1 and 0 <= r <= 16
    if t in [PAIR, TRIPLE, FULLHOUSE]:  # Paar, Drilling, Fullhouse
        return m == t and 2 <= r <= 14
    if t == STAIR:  # Treppe
        return m % 2 == 0 and 4 <= m <= 14 and int(m / 2) + 1 <= r <= 14
    if t == STREET:  # Straße
        return 5 <= m <= 14 and m <= r <= 14
    if t == BOMB:
        if m == 4:  # 4er-Bombe
            return 2 <= r <= 14
        else:  # Farbbombe
            return 5 <= m <= 14 and m + 1 <= r <= 14
    return False


# Wandelt das Label einer Kartenkombination in Typ, Länge und Rang umw
def parse_figure(lb: str) -> tuple:
    return _figures[_figurelabels_index[lb]]


# Wandelt Typ, Länge und Rang einer Kombination in ein Label um
def stringify_figure(figure: tuple) -> str:
    return _figurelabels[_figures_index[figure]]


# Wandelt den Typ einer Kombination in ein Label um
#
# t: Typ der Kombination
# m: Länge der Kombination (optional)
def stringify_type(t: int, m: int = None) -> str:
    assert 1 <= t <= 7
    label = ["pass", "single", "pair", "triple", "stair", "fullhouse", "street", "bomb"][t]
    if m is not None and t in (STAIR, STREET, BOMB):
        assert (t == STAIR and m % 2 == 0 and 4 <= m <= 14) or (t == STREET and 5 <= m <= 14) or (t == BOMB and 4 <= m <= 14)
        label += f"{m:02}"
    return label


# Ermittelt Typ, Länge und Rang der gegebenen Kartenkombination
#
# Es wird vorausgesetzt, das cards eine gültige Kombination ist.
# Parameter cards wird absteigend sortiert. Wenn shift_phoenix gesetzt ist, wird der Phönix der Kombi entsprechend eingereiht.
#
# cards: Karten der Kombination, z.B. [(8,4),(8,2),(8,1)]
# trick_value: Rang des aktuellen Stichs (0, wenn kein Stich ausgelegt ist)
# shift_phoenix: Wenn True, wird der Phönix eingereiht (kostet etwas Zeit)
# return: (Typ, Länge, Rang);
def get_figure(cards: list, trick_value: int, shift_phoenix: bool = False) -> tuple:
    n = len(cards)
    if n == 0:
        return 0, 0, 0  # Passen

    # Karten absteigend sortieren
    cards.sort(reverse=True)  # Der Phönix ist jetzt, falls vorhanden, die erste Karte!

    # Type
    if n == 1:
        t = SINGLE
    elif n == 2:
        t = PAIR
    elif n == 3:
        t = TRIPLE
    elif n == 4 and cards[1][0] == cards[2][0] == cards[3][0]:  # Treppe ausschließen: 2., 3. und 4. Karte gleichwertig
        t = BOMB  # 4er-Bombe
    elif n == 5 and (cards[1][0] == cards[2][0] or cards[2][0] == cards[3][0]):  # Straße ausschließen
        t = FULLHOUSE  # 22211 22111 *2211 *2221 *2111
    elif cards[1][0] == cards[2][0] or cards[2][0] == cards[3][0]:  # Straße ausschließen
        t = STAIR  # Treppe: 332211 *32211 *33211 *33221
    elif len([card for card in cards if card[1] == cards[0][1]]) == n:  # Einfarbig?
        t = BOMB  # Farbbombe
    else:
        t = STREET

    # Rang
    if t == SINGLE:
        if cards[0] == CARD_PHO:
            assert 0 <= trick_value <= 15
            v = trick_value if trick_value else 1  # ist um 0.5 größer als der Stich (wir runden ab, da egal)
        else:
            v = cards[0][0]
    elif t == FULLHOUSE:
        v = cards[2][0]  # die 3. Karte gehört auf jeden Fall zum Drilling
    elif t == STREET or (t == BOMB and n > 4):
        if cards[0] == CARD_PHO:
            if cards[1][0] == 14:
                v = 14  # Phönix muss irgendwo anders eingereiht werden
            else:
                v = cards[1][0] + 1  # wir nehmen erstmal an, dass der Phönix vorn eingereiht werden kann
                for i in range(2, n):
                    if v > cards[i][0] + i:
                        # der Phönix füllt eine Lücke
                        v -= 1
                        break
        else:
            v = cards[0][0]
    else:
        v = cards[1][0]

    # Phönix einsortieren
    if shift_phoenix and cards[0] == CARD_PHO:
        if t == PAIR:  # Pärchen → Phönix ans Ende verschieben
            cards[0] = cards[1]; cards[1] = CARD_PHO
        elif t == TRIPLE:  # Drilling → Phönix ans Ende verschieben
            cards[0] = cards[1]; cards[1] = cards[2]; cards[2] = CARD_PHO
        elif t == STAIR:  # Treppe → Phönix in die Lücke verschieben *11233
            for i in range(1, n, 2):
                if i + 1 == n or cards[i][0] != cards[i + 1][0]:
                    # Lücke gefunden
                    for j in range(0, i):
                        cards[j] = cards[j + 1]
                    cards[i] = CARD_PHO
                    break
        elif t == FULLHOUSE:  # Straße → Phönix ans Ende des Drillings bzw. Pärchens verschieben
            if cards[1][0] == cards[2][0] == cards[3][0]:  # Drilling vorne komplett → Phönix ans Ende verschieben
                cards[0] = cards[1]; cards[1] = cards[2]; cards[2] = cards[3]; cards[3] = cards[4]; cards[4] = CARD_PHO
            elif cards[2][0] == cards[3][0] == cards[4][0]:  # Drilling hinten komplett → Phönix an die 2. Stelle verschieben
                cards[0] = cards[1]; cards[1] = CARD_PHO
            else:  # kein Drilling komplett → Phönix in die Mitte verschieben
                cards[0] = cards[1]; cards[1] = cards[2]; cards[2] = CARD_PHO
        elif t == STREET:  # Straße → Phönix in die Lücke verschieben
            w = cards[1][0] + 1  # wir nehmen erstmal an, dass der Phönix vorn bleiben kann
            for i in range(2, n):
                if w > cards[i][0] + i:
                    # Lücke gefunden
                    for j in range(0, i - 1):
                        cards[j] = cards[j + 1]
                    cards[i - 1] = CARD_PHO
                    break
            if cards[0] == CARD_PHO and cards[1][0] == 14:  # keine Lücke gefunden - aber wegen Ass muss Phönix ans Ende
                for j in range(0, n - 1):
                    cards[j] = cards[j + 1]
                cards[n - 1] = CARD_PHO

    return t, n, v


# Ermittelt die Kombinationsmöglichkeiten der Handkarten (die besten zu erst)
#
# hand: Handkarten, absteigend sortiert, z.B. [(8,3),(2,4),(0,1)]
# return: [(Karten, (Typ, Länge, Rang)), ...]
def build_combinations(hand: list[tuple]) -> List[Tuple[Cards, Combination]]:
    has_phoenix = CARD_PHO in hand
    arr = [[], [], [], [], [], [], [], []]  # pro Type ein Array
    n = len(hand)

    # Einzelkarten, Paare, Drilling, 4er-Bomben
    for i1 in range(0, n):
        card1 = hand[i1]
        arr[SINGLE].append([card1])
        if card1[1] == 0:  # Sonderkarte?
            continue
        if has_phoenix:
            arr[PAIR].append([card1, CARD_PHO])
        # Paare suchen...
        for i2 in range(i1 + 1, n):
            card2 = hand[i2]
            if card1[0] != card2[0]:
                break
            arr[PAIR].append([card1, card2])
            if has_phoenix:
                arr[TRIPLE].append([card1, card2, CARD_PHO])
            # Drillinge suchen...
            for i3 in range(i2 + 1, n):
                card3 = hand[i3]
                if card1[0] != card3[0]:
                    break
                arr[TRIPLE].append([card1, card2, card3])
                # 4er-Bomben suchen...
                for i4 in range(i3 + 1, n):
                    card4 = hand[i4]
                    if card1[0] == card4[0]:
                        arr[BOMB].append([card1, card2, card3, card4])
                    break

    # Treppen
    temp = arr[PAIR].copy()
    m = len(temp)
    i = 0
    while i < m:
        v = temp[i][-2][0]  # Rang der vorletzten Karte in der Treppe
        for pair in arr[PAIR]:
            if pair[1] == CARD_PHO and CARD_PHO in temp[i]:
                continue
            if v - 1 == pair[0][0]:
                arr[STAIR].append(temp[i] + pair)
                temp.append(temp[i] + pair)
                m += 1
        i += 1

    # FullHouse
    for triple in arr[TRIPLE]:
        for pair in arr[PAIR]:
            if triple[0][0] == pair[0][0]:
                # Ausnahmeregel: Der Drilling darf nicht vom gleichen Rang sein wie das Paar (wäre mit Phönix möglich).
                continue
            if triple[2] == CARD_PHO and triple[0][0] < pair[0][0]:
                # Man würde immer den Phönix zum höherwertigen Pärchen sortieren.
                continue
            if not set(triple).intersection(pair):
                # Schnittmenge ist leer
                arr[FULLHOUSE].append(triple + pair)

    # Straßen
    for i1 in range(0, n - 1):
        if hand[i1][1] == 0 or (i1 > 0 and hand[i1 - 1][0] == hand[i1][0]):
            continue  # Sonderkarte oder vorherigen Karte gleichwertig
        v1 = hand[i1][0]
        if v1 < (4 if has_phoenix else 5):  # if v1 < 5:
            break  # eine Straße hat mindestens den Rang 5
        temp = [[hand[i1]]]
        for i2 in range(i1 + 1, n):
            if hand[i2] == CARD_DOG:
                break  # Hund
            v2 = hand[i2][0]
            if v1 == v2:
                # gleicher Kartenwert; die letzte Karte in der Straße kann ausgetauscht werden
                temp2 = []
                for cards in temp:
                    cards2 = cards[0:-1] + [hand[i2]]
                    if cards2 not in temp2:
                        temp2.append(cards2)
                temp += temp2
            elif v1 == v2 + 1:
                # keine Lücke zwischen den Karten
                for cards in temp:
                    cards.append(hand[i2])
                v1 = v2
            elif v1 == v2 + 2 and has_phoenix and CARD_PHO not in temp[0]:
                # ein Phönix kann die Lücke schließen
                for cards in temp:
                    cards.append(CARD_PHO)
                    cards.append(hand[i2])
                v1 = v2
            else:
                # zu große Lücke zwischen den Karten, um daraus eine Straße zu machen
                break

        m = len(temp[0])
        for cards in temp:
            for k in range(4, m + 1):
                if cards[k - 1] == CARD_PHO:
                    continue
                available_phoenix = has_phoenix and CARD_PHO not in cards[0:k]
                # Straße bzw. Bombe übernehmen
                if k >= 5:
                    is_bomb = True
                    for card in cards[1:k]:
                        if card[1] != cards[0][1]:
                            is_bomb = False
                            break
                    arr[BOMB if is_bomb else STREET].append(cards[0:k])
                    # jede Karte ab der 2. bis zur vorletzten mit dem Phönix ersetzen
                    if available_phoenix:
                        for i in range(1, k - 1):
                            arr[STREET].append(cards[0:i] + [CARD_PHO] + cards[i + 1:k])
                # Straße mit Phönix verlängern
                if k >= 4 and available_phoenix:
                    if cards[0][0] < 14:
                        arr[STREET].append([CARD_PHO] + cards[0:k])
                    elif cards[k - 1][0] > 2:
                        arr[STREET].append(cards[0:k] + [CARD_PHO])

    # Type, Rang und Länge der Kombinationen auflisten (zuerst die besten)
    result = []
    for t in range(7, 0, -1):  # Typ t = 7 (BOMB) .. 1 (SINGLE)
        for cards in arr[t]:
            # Rang ermitteln
            if t == STREET and cards[0] == CARD_PHO:
                v = cards[1][0] + 1  # Phönix == Rang der zweiten Karte + 1
            else:
                v = cards[0][0]  # Rang der ersten Karte
            # Kombination speichern
            result.append((cards, (CombinationType(t), len(cards), v)))

    return result


# Entfernt die Kombinationsmöglichkeiten, die aus mindestens eine der angegebenen Karten bestehen
#
# combis: Kombinationsmöglichkeiten [(Karten, (Typ, Länge, Rang)), ...]
# cards: Karten, die entfernt werden sollen
# return: [(Karten, (Typ, Länge, Rang)), ...]
def remove_combinations(combis: list[tuple], cards: list[tuple]):
    return [combi for combi in combis if not set(cards).intersection(combi[0])]


# Ermittelt spielbare Kartenkombinationen
#
# combis: Kombinationsmöglichkeiten der Hand, also [(Karten, (Typ, Länge, Rang)), ...]
# trick_figure: Typ, Länge, Rang des aktuellen Stichs ((0,0,0), falls kein Stich liegt)
# unfulfilled_wish: Unerfüllter Wunsch (0 == kein Wunsch geäußert, negativ == bereits erfüllt)
# return: ([], (0,0,0)) für Passen sofern möglich + mögliche Kombinationen aus combis
def build_action_space(combis: List[Tuple[List[Card], Combination]], trick_figure: tuple, unfulfilled_wish: int) -> List[Tuple[List[Card], Combination]]:
    assert 0 <= trick_figure[0] <= 7
    assert 0 <= trick_figure[1] <= 14
    assert 0 <= trick_figure[2] <= 15
    result = []
    if trick_figure not in (FIGURE_PASS, FIGURE_DOG):
        # Stich liegt und es ist kein Hund
        result.append(([], (0, 0, 0)))  # Passen ist eine Option
        t, n, v = trick_figure
        for combi in combis:
            t2, n2, v2 = combi[1]
            if combi[1] == FIGURE_PHO:  # Phönix als Einzelkarte
                if trick_figure == FIGURE_DRA:
                    continue  # Phönix auf Drache ist nicht erlaubt
                v2 = v + 0.5 if v > 0 else 1.5
            if (t == BOMB and t2 == t and (n2 > n or (n2 == n and v2 > v))) or \
               (t != BOMB and (t2 == BOMB or (t2 == t and n2 == n and v2 > v))):
                result.append(combi)
    else:
        # Anspiel! Freie Auswahl (bis auf passen).
        # result = combis.copy()  so, wenn combis eine Liste wäre
        result = combis

    # Falls ein Wunsch offen ist, muss der Spieler diesen erfüllen, wenn er kann.
    if unfulfilled_wish > 0:
        assert 2 <= unfulfilled_wish <= 14
        mandatory = []
        for combi in result:
            if is_wish_in(unfulfilled_wish, combi[0]):
                mandatory.append(combi)
        if mandatory:
            # Der Spieler kann und muss den Wunsch erfüllen.
            result = mandatory

    return result


# -----------------------------------------------------------------------------
# Test
# -----------------------------------------------------------------------------

# if __name__ == "__main__":  # pragma: no cover
#     pass
