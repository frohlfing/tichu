__all__ = "Card", "Cards", \
    "CARD_DOG", "CARD_MAH", "CARD_DRA", "CARD_PHO", \
    "deck", \
    "parse_cards", "stringify_cards", \
    "ranks_to_vector", "cards_to_vector", \
    "is_wish_in", "sum_card_points", "other_cards",

from typing import Tuple, List

# todo Dokumentieren (reStructuredText)

# -----------------------------------------------------------------------------
# Spielkarten
# -----------------------------------------------------------------------------

# Typ-Alias für eine Karte
Card = Tuple[int, int]  # Wert, Farbe   # todo überall konsequent verwenden

# Typ-Alias für mehrere Karten
Cards = List[Card]  # todo überall konsequent verwenden

# Sonderkarten
#   (Wert, Farbe)
CARD_DOG = (0, 0)   # Dog
CARD_MAH = (1, 0)   # Mahjong
CARD_DRA = (15, 0)  # Phoenix
CARD_PHO = (16, 0)  # Dragon

# Kartendeck (56 Karten)
# Werte:  14 (As), 13 (König), 12 (Dame), 11 (Bube), 10 bis 2
# Farben: 0 (Sonderkarte), 1 (Schwarz/Schwert), 2 (Blau/Pagode), 3 (Grün/Jade), 4 (Rot/Stern)
deck = (  # const
    # schwarz blau  grün    rot
    (0, 0),                              # Hund
    (1, 0),                              # MahJong
    (2, 1), (2, 2), (2, 3), (2, 4),      # 2
    (3, 1), (3, 2), (3, 3), (3, 4),      # 3
    (4, 1), (4, 2), (4, 3), (4, 4),      # 4
    (5, 1), (5, 2), (5, 3), (5, 4),      # 5
    (6, 1), (6, 2), (6, 3), (6, 4),      # 6
    (7, 1), (7, 2), (7, 3), (7, 4),      # 7
    (8, 1), (8, 2), (8, 3), (8, 4),      # 8
    (9, 1), (9, 2), (9, 3), (9, 4),      # 9
    (10, 1), (10, 2), (10, 3), (10, 4),  # 10
    (11, 1), (11, 2), (11, 3), (11, 4),  # Bube
    (12, 1), (12, 2), (12, 3), (12, 4),  # Dame
    (13, 1), (13, 2), (13, 3), (13, 4),  # König
    (14, 1), (14, 2), (14, 3), (14, 4),  # As
    (15, 0),                             # Drache
    (16, 0),                             # Phönix
)

# wie deck.index(card), aber 6 mal schneller!
_deck_index = {  # const
    # schwarz    blau         grün        rot
    (0, 0): 0,                                           # Hund
    (1, 0): 1,                                           # MahJong
    (2, 1): 2, (2, 2): 3, (2, 3): 4, (2, 4): 5,          # 2
    (3, 1): 6, (3, 2): 7, (3, 3): 8, (3, 4): 9,          # 3
    (4, 1): 10, (4, 2): 11, (4, 3): 12, (4, 4): 13,      # 4
    (5, 1): 14, (5, 2): 15, (5, 3): 16, (5, 4): 17,      # 5
    (6, 1): 18, (6, 2): 19, (6, 3): 20, (6, 4): 21,      # 6
    (7, 1): 22, (7, 2): 23, (7, 3): 24, (7, 4): 25,      # 7
    (8, 1): 26, (8, 2): 27, (8, 3): 28, (8, 4): 29,      # 8
    (9, 1): 30, (9, 2): 31, (9, 3): 32, (9, 4): 33,      # 9
    (10, 1): 34, (10, 2): 35, (10, 3): 36, (10, 4): 37,  # Zehn
    (11, 1): 38, (11, 2): 39, (11, 3): 40, (11, 4): 41,  # Bube
    (12, 1): 42, (12, 2): 43, (12, 3): 44, (12, 4): 45,  # Dame
    (13, 1): 46, (13, 2): 47, (13, 3): 48, (13, 4): 49,  # König
    (14, 1): 50, (14, 2): 51, (14, 3): 52, (14, 4): 53,  # As
    (15, 0): 54,                                         # Drache
    (16, 0): 55,                                         # Phönix
}

# Kartenlabel
_cardlabels = (
    # sw   bl    gr    rt
    "Hu",                    # Hund
    "Ma",                    # MahJong
    "S2", "B2", "G2", "R2",  # 2
    "S3", "B3", "G3", "R3",  # 3
    "S4", "B4", "G4", "R4",  # 4
    "S5", "B5", "G5", "R5",  # 5
    "S6", "B6", "G6", "R6",  # 6
    "S7", "B7", "G7", "R7",  # 7
    "S8", "B8", "G8", "R8",  # 8
    "S9", "B9", "G9", "R9",  # 9
    "SZ", "BZ", "GZ", "RZ",  # 10
    "SB", "BB", "GB", "RB",  # Bube
    "SD", "BD", "GD", "RD",  # Dame
    "SK", "BK", "GK", "RK",  # König
    "SA", "BA", "GA", "RA",  # As
    "Dr",                    # Drache
    "Ph",                    # Phönix
)

# wie cardlabels.index(label), aber 6 mal schneller
_cardlabels_index = {
    # schwarz blau      grün      rot
    "Hu": 0,                                 # Hund
    "Ma": 1,                                 # MahJong
    "S2": 2, "B2": 3, "G2": 4, "R2": 5,      # 2
    "S3": 6, "B3": 7, "G3": 8, "R3": 9,      # 3
    "S4": 10, "B4": 11, "G4": 12, "R4": 13,  # 4
    "S5": 14, "B5": 15, "G5": 16, "R5": 17,  # 5
    "S6": 18, "B6": 19, "G6": 20, "R6": 21,  # 6
    "S7": 22, "B7": 23, "G7": 24, "R7": 25,  # 7
    "S8": 26, "B8": 27, "G8": 28, "R8": 29,  # 8
    "S9": 30, "B9": 31, "G9": 32, "R9": 33,  # 9
    "SZ": 34, "BZ": 35, "GZ": 36, "RZ": 37,  # 10
    "SB": 38, "BB": 39, "GB": 40, "RB": 41,  # Bube
    "SD": 42, "BD": 43, "GD": 44, "RD": 45,  # Dame
    "SK": 46, "BK": 47, "GK": 48, "RK": 49,  # König
    "SA": 50, "BA": 51, "GA": 52, "RA": 53,  # As
    "Dr": 54,                                # Drache
    "Ph": 55,                                # Phönix
}

# Kartenwert → Punkte
_card_points = (
    0,    # Hund
    0,    # MahJong
    0,    # 2
    0,    # 3
    0,    # 4
    5,    # 5      → 5 Punkte
    0,    # 6
    0,    # 7
    0,    # 8
    0,    # 9
    10,   # Zehn   → 10 Punkte
    0,    # Bube
    0,    # Dame
    10,   # Könige → 10 Punkte
    0,    # As
    25,   # Drache → 25 Punkte
    -25,  # Phönix → 25 Minuspunkte
)


# Parst die Karten aus dem String
# s: z.B. "R6 B5 G4"
def parse_cards(s: str) -> Cards:
    return [deck[_cardlabels_index[c]] for c in s.split(" ")]


# Formatiert Karten als lesbaren String
# cards: Karten, z.B. [(8,3),(2,4),(0,1)]
def stringify_cards(cards: Cards) -> str:
    return " ".join([_cardlabels[_deck_index[c]] for c in cards])


# Zählt die Anzahl der Karten je Rang
#
# Zurückgegeben wird eine Liste mit 17 Integer, wobei der Index den Rang entspricht und
# der Wert die Anzahl der Karten mit diesem Rang.
def ranks_to_vector(cards: Cards) -> list[int]:
    # r=Hu Ma  2  3  4  5  6  7  8  9 10 Bu Da Kö As Dr Ph
    # i= 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16
    h = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    for v, _ in cards:
        h[v] += 1
    return h


# Wandelt die Karten in einen Vektor um
def cards_to_vector(cards: Cards) -> list[int]:
    # r=Hu Ma  2  3  4  5  6  7  8  9 10 Bu Da Kö As  2  3  4  5  6  7  8  9 10 Bu Da Kö As  2  3  4  5  6  7  8  9 10 Bu Da Kö As  2  3  4  5  6  7  8  9 10 Bu Da Kö As Dr Ph
    # i= 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55
    h = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    for r, c in cards:
        if c > 0:
            h[r + 13 * (c - 1)] = 1
        else:
            h[r if r < 2 else r + 39] = 1
    return h


# Ermittelt, ob der gewünschte Kartenwert unter den Karten ist
def is_wish_in(wish: int, cards: Cards) -> bool:
    assert 2 <= wish <= 14
    for card in cards:
        if card[0] == wish:
            return True
    return False


# Zählt die Punkte der Karten
# cards: Karten, z.B. [(8,3),(2,4),(0,1)]
def sum_card_points(cards: Cards) -> int:
    return sum([_card_points[card[0]] for card in cards])


def other_cards(cards: Cards) -> List[Card]:
    """
    Listet die Karten auf, die nicht in cards vorkommen.

    Die Reihenfolge entspricht dem Kartendeck (also aufsteigend).

    :param cards: Die Karten, aus denen die fehlenden Karten ermittelt werden.
    :return: Die Karten, die nicht in cards vorkommen.
    """
    return [card for card in deck if card not in cards]
