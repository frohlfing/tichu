__all__ = "CARD_DOG", "CARD_MAH", "CARD_DRA", "CARD_PHO", \
    "deck", \
    "parse_cards", "stringify_cards", \
    "ranks_to_vector", "cards_to_vector", \
    "is_wish_in", "sum_card_points", "other_cards",

# -----------------------------------------------------------------------------
# Spielkarten
# -----------------------------------------------------------------------------

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
    #  rot        grün        blau     schwarz
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
    # rt   gr    bl    sw
    "Hu",                    # Hund
    "Ma",                    # MahJong
    "R2", "G2", "B2", "S2",  # 2
    "R3", "G3", "B3", "S3",  # 3
    "R4", "G4", "B4", "S4",  # 4
    "R5", "G5", "B5", "S5",  # 5
    "R6", "G6", "B6", "S6",  # 6
    "R7", "G7", "B7", "S7",  # 7
    "R8", "G8", "B8", "S8",  # 8
    "R9", "G9", "B9", "S9",  # 9
    "RZ", "GZ", "BZ", "SZ",  # 10
    "RB", "GB", "BB", "SB",  # Bube
    "RD", "GD", "BD", "SD",  # Dame
    "RK", "GK", "BK", "SK",  # König
    "RA", "GA", "BA", "SA",  # As
    "Dr",                    # Drache
    "Ph",                    # Phönix
)

# wie cardlabels.index(label), aber 6 mal schneller
_cardlabels_index = {
    # rot      grün     blau      schwarz
    "Hu": 0,                                 # Hund
    "Ma": 1,                                 # MahJong
    "R2": 2, "G2": 3, "B2": 4, "S2": 5,      # 2
    "R3": 6, "G3": 7, "B3": 8, "S3": 9,      # 3
    "R4": 10, "G4": 11, "B4": 12, "S4": 13,  # 4
    "R5": 14, "G5": 15, "B5": 16, "S5": 17,  # 5
    "R6": 18, "G6": 19, "B6": 20, "S6": 21,  # 6
    "R7": 22, "G7": 23, "B7": 24, "S7": 25,  # 7
    "R8": 26, "G8": 27, "B8": 28, "S8": 29,  # 8
    "R9": 30, "G9": 31, "B9": 32, "S9": 33,  # 9
    "RZ": 34, "GZ": 35, "BZ": 36, "SZ": 37,  # 10
    "RB": 38, "GB": 39, "BB": 40, "SB": 41,  # Bube
    "RD": 42, "GD": 43, "BD": 44, "SD": 45,  # Dame
    "RK": 46, "GK": 47, "BK": 48, "SK": 49,  # König
    "RA": 50, "GA": 51, "BA": 52, "SA": 53,  # As
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
def parse_cards(s: str) -> list[tuple]:
    return [deck[_cardlabels_index[c]] for c in s.split(" ")]


# Formatiert Karten als lesbaren String
# cards: Karten, z.B. [(8,3),(2,4),(0,1)]
def stringify_cards(cards: list[tuple]) -> str:
    return " ".join([_cardlabels[_deck_index[c]] for c in cards])


# Zählt die Anzahl der Karten je Rang
#
# Zurückgegeben wird eine Liste mit 17 Integer, wobei der Index den Rang entspricht und
# der Wert die Anzahl der Karten mit diesem Rang.
def ranks_to_vector(cards: list[tuple]) -> list[int]:
    # r=Hu Ma  2  3  4  5  6  7  8  9 10 Bu Da Kö As Dr Ph
    # i= 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16
    h = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    for v, _ in cards:
        h[v] += 1
    return h


# Wandelt die Karten in einen Vektor um
def cards_to_vector(cards: list[tuple]) -> list[int]:
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
def is_wish_in(wish: int, cards: list[tuple]) -> bool:
    assert 2 <= wish <= 14
    for card in cards:
        if card[0] == wish:
            return True
    return False


# Zählt die Punkte der Karten
# cards: Karten, z.B. [(8,3),(2,4),(0,1)]
def sum_card_points(cards: list[tuple]) -> int:
    return sum([_card_points[card[0]] for card in cards])


# Listet die übrigen Karten auf
# Die Reihenfolge entspricht dem Kartendeck (also aufsteigend).
def other_cards(cards: list[tuple]) -> list[tuple]:
    return [card for card in deck if card not in cards]
