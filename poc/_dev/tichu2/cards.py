from typing import List

__all__ = 'CARD_DOG', 'CARD_MAH', 'CARD_DRA', 'CARD_PHO', \
          'deck', 'cardlabels', 'cardlabels_index', 'parse_cards', 'stringify_cards', 'print_cards', 'is_wish_in', \
          'sum_card_points', 'other_cards', 'cards_to_hash', 'hash_to_cards'

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
    # rot    grün    blau    schwarz
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
deck_index = {  # const
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
    (11, 1): 38, (11, 2): 39, (11, 3): 40, (11, 4): 41,  # Bubort
    (12, 1): 42, (12, 2): 43, (12, 3): 44, (12, 4): 45,  # Dame
    (13, 1): 46, (13, 2): 47, (13, 3): 48, (13, 4): 49,  # König
    (14, 1): 50, (14, 2): 51, (14, 3): 52, (14, 4): 53,  # As
    (15, 0): 54,                                         # Drache
    (16, 0): 55,                                         # Phönix
}

# Kartenlabel
cardlabels = (
    # rt   gr    bl    sw
    'Hu',                    # Hund
    'Ma',                    # MahJong
    'R2', 'G2', 'B2', 'S2',  # 2
    'R3', 'G3', 'B3', 'S3',  # 3
    'R4', 'G4', 'B4', 'S4',  # 4
    'R5', 'G5', 'B5', 'S5',  # 5
    'R6', 'G6', 'B6', 'S6',  # 6
    'R7', 'G7', 'B7', 'S7',  # 7
    'R8', 'G8', 'B8', 'S8',  # 8
    'R9', 'G9', 'B9', 'S9',  # 9
    'RZ', 'GZ', 'BZ', 'SZ',  # 10
    'RB', 'GB', 'BB', 'SB',  # Bube
    'RD', 'GD', 'BD', 'SD',  # Dame
    'RK', 'GK', 'BK', 'SK',  # König
    'RA', 'GA', 'BA', 'SA',  # As
    'Dr',                    # Drache
    'Ph',                    # Phönix
)

# wie cardlabels.index(label), aber 6 mal schneller
cardlabels_index = {
    # rot      grün     blau      schwarz
    'Hu': 0,                                 # Hund
    'Ma': 1,                                 # MahJong
    'R2': 2, 'G2': 3, 'B2': 4, 'S2': 5,      # 2
    'R3': 6, 'G3': 7, 'B3': 8, 'S3': 9,      # 3
    'R4': 10, 'G4': 11, 'B4': 12, 'S4': 13,  # 4
    'R5': 14, 'G5': 15, 'B5': 16, 'S5': 17,  # 5
    'R6': 18, 'G6': 19, 'B6': 20, 'S6': 21,  # 6
    'R7': 22, 'G7': 23, 'B7': 24, 'S7': 25,  # 7
    'R8': 26, 'G8': 27, 'B8': 28, 'S8': 29,  # 8
    'R9': 30, 'G9': 31, 'B9': 32, 'S9': 33,  # 9
    'RZ': 34, 'GZ': 35, 'BZ': 36, 'SZ': 37,  # 10
    'RB': 38, 'GB': 39, 'BB': 40, 'SB': 41,  # Bube
    'RD': 42, 'GD': 43, 'BD': 44, 'SD': 45,  # Dame
    'RK': 46, 'GK': 47, 'BK': 48, 'SK': 49,  # König
    'RA': 50, 'GA': 51, 'BA': 52, 'SA': 53,  # As
    'Dr': 54,                                # Drache
    'Ph': 55,                                # Phönix
}

# Kartenwert => Punkte
card_points = (
    0,    # Hund
    0,    # MahJong
    0,    # 2
    0,    # 3
    0,    # 4
    5,    # 5      => 5 Punkte
    0,    # 6
    0,    # 7
    0,    # 8
    0,    # 9
    10,   # Zehn   => 10 Punkte
    0,    # Bube
    0,    # Dame
    10,   # Könige => 10 Punkte
    0,    # As
    25,   # Drache => 25 Punkte
    -25,  # Phönix => 25 Minuspunkte
)


# Karten aus String parsen
# s: z.B. 'R6 B5 G4'
def parse_cards(s: str) -> List[tuple]:  # todo Rückgabe als Tuple
    return [deck[cardlabels_index[c]] for c in s.split(' ')]


# Karten als lesbaren String formatieren
# cards: Karten, z.B. [(8,3),(2,4),(0,1)]
def stringify_cards(cards: List[tuple]) -> str:  # todo Parameter als Tuple
    return ' '.join([cardlabels[deck_index[c]] for c in cards])


# Karten anzeigen
# cards: Karten, z.B. [(8,3),(2,4),(0,1)]
def print_cards(cards: List[tuple]):  # pragma: no cover  # todo Rückgabe als Tuple
    print(stringify_cards(cards))


# Ist der gewünschte Wert unter den Karten?
def is_wish_in(wish: int, cards: List[tuple]) -> bool:  # todo Parameter als Tuple
    assert 2 <= wish <= 14
    for card in cards:
        if card[0] == wish:
            return True
    return False


# Punkte der Karten zählen
# cards: Karten, z.B. [(8,3),(2,4),(0,1)]
def sum_card_points(cards: List[tuple]) -> int:  # todo Parameter als Tuple
    return sum([card_points[card[0]] for card in cards])


# Alle übrigen Karten auflisten. Die Reihenfolge entspricht dem Kartendeck (also aufsteigend).
def other_cards(cards: List[tuple]) -> List[tuple]:  # todo Parameter und Rückgabe als Tuple
    return [card for card in deck if card not in cards]


# -----------------------------------------------------------------------------
# Codierung der Karten als 64Bit-Hashwert
# -----------------------------------------------------------------------------

HASH_ALL = 2 ** 56 - 1  # Hashwert für alle Karten
HASH_DOG = 1 << 0   # Hashwert für den Hund
HASH_MAH = 1 << 1   # Hashwert für den Mahjong
HASH_DRA = 1 << 54  # Hashwert für den Drachen
HASH_PHO = 1 << 55  # Hashwert für den Phönix


# Eindeutigen Hashwert der gegebenen Karten erzeugen. Dabei steht jedes Bit im 64-Bit-Integer für eine Karte.
def cards_to_hash(cards: List[tuple]) -> int:  # todo Parameter als Tuple
    hash_cards = 0
    for card in cards:
        hash_cards |= 1 << deck_index[card]
    return hash_cards


# Hashwert in den einzelnen Karten umwandeln. Die Reihenfolge entspricht dem Kartendeck (also aufsteigend).
def hash_to_cards(hash_cards: int) -> list:  # todo Rückgabe als Tuple
    return [deck[i] for i in range(0, 56) if hash_cards & (1 << i)]


# -----------------------------------------------------------------------------
# Test
# -----------------------------------------------------------------------------

def test():  # pragma: no cover
    pass
