"""
Dieses Modul definiert das Kartendeck und Eigenschaften der Spielkarten.
"""

__all__ = "CardSuit", "Card", "Cards", \
    "CARD_DOG", "CARD_MAH", "CARD_DRA", "CARD_PHO", \
    "deck", \
    "validate_card", "validate_cards", "parse_card", "parse_cards", "stringify_card", "stringify_cards", \
    "ranks_to_vector", "cards_to_vector", \
    "is_wish_in", "sum_card_points", "other_cards",

import enum
from typing import Tuple, List, Iterable

# -----------------------------------------------------------------------------
# Spielkarten
# -----------------------------------------------------------------------------

class CardSuit(enum.IntEnum):
    """
    Kartenfarben.
    """
    SPECIAL = 0  #  Sonderkarte (Hund, Mahjong, Drache, Phönix)
    SWORD = 1  # Schwarz/Schwert
    PAGODA = 2 # Blau/Pagode
    JADE = 3  # Grün/Jade
    STAR = 4  # Rot/Stern

Card = Tuple[int, CardSuit]  # Wert, Farbe
"""Type-Alias für eine Karte"""

Cards = List[Card]
"""Type-Alias für mehrere Karten"""

# Sonderkarten
CARD_DOG = (0, CardSuit.SPECIAL)   # Dog
CARD_MAH = (1, CardSuit.SPECIAL)   # Mahjong
CARD_DRA = (15, CardSuit.SPECIAL)  # Phoenix
CARD_PHO = (16, CardSuit.SPECIAL)  # Dragon

deck = (  # const
    (0, CardSuit.SPECIAL),  # Hund
    (1, CardSuit.SPECIAL),  # Mahjong
    (2, CardSuit.SWORD), (2, CardSuit.PAGODA), (2, CardSuit.JADE), (2, CardSuit.STAR),  # 2
    (3, CardSuit.SWORD), (3, CardSuit.PAGODA), (3, CardSuit.JADE), (3, CardSuit.STAR),  # 3
    (4, CardSuit.SWORD), (4, CardSuit.PAGODA), (4, CardSuit.JADE), (4, CardSuit.STAR),  # 4
    (5, CardSuit.SWORD), (5, CardSuit.PAGODA), (5, CardSuit.JADE), (5, CardSuit.STAR),  # 5
    (6, CardSuit.SWORD), (6, CardSuit.PAGODA), (6, CardSuit.JADE), (6, CardSuit.STAR),  # 6
    (7, CardSuit.SWORD), (7, CardSuit.PAGODA), (7, CardSuit.JADE), (7, CardSuit.STAR),  # 7
    (8, CardSuit.SWORD), (8, CardSuit.PAGODA), (8, CardSuit.JADE), (8, CardSuit.STAR),  # 8
    (9, CardSuit.SWORD), (9, CardSuit.PAGODA), (9, CardSuit.JADE), (9, CardSuit.STAR),  # 9
    (10, CardSuit.SWORD), (10, CardSuit.PAGODA), (10, CardSuit.JADE), (10, CardSuit.STAR),  # 10
    (11, CardSuit.SWORD), (11, CardSuit.PAGODA), (11, CardSuit.JADE), (11, CardSuit.STAR),  # Bube
    (12, CardSuit.SWORD), (12, CardSuit.PAGODA), (12, CardSuit.JADE), (12, CardSuit.STAR),  # Dame
    (13, CardSuit.SWORD), (13, CardSuit.PAGODA), (13, CardSuit.JADE), (13, CardSuit.STAR),  # König
    (14, CardSuit.SWORD), (14, CardSuit.PAGODA), (14, CardSuit.JADE), (14, CardSuit.STAR),  # As
    (15, CardSuit.SPECIAL),  # Drache
    (16, CardSuit.SPECIAL),                                                                    # Phönix
)
"""
Kartendeck (56 Karten)

- Werte:  0 = Hund, 1 = Mahjong, 2 bis 10, 11 = Bube, 12 = Dame, 13 = König, 14 = As, 15 = Drache, 16 = Phönix
- Farben: 0 = Sonderkarte, 1 = Schwarz/Schwert, 2 = Blau/Pagode, 3 = Grün/Jade, 4 = Rot/Stern
"""

_card_labels = (
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
"""# Kartenlabel"""

_card_points = (
    0,    # Hund
    0,    # MahJong
    0,    # 2
    0,    # 3
    0,    # 4
    5,    # 5 → 5 Punkte
    0,    # 6
    0,    # 7
    0,    # 8
    0,    # 9
    10,   # Zehn → 10 Punkte
    0,    # Bube
    0,    # Dame
    10,   # Könige → 10 Punkte
    0,    # As
    25,   # Drache → 25 Punkte
    -25,  # Phönix → 25 Minuspunkte
)
"""Zuordnung von Kartenwert zu Punkten."""


def validate_card(s: str) -> bool:
    """
    Validiert die Karte im String.

    :param s: z.B. "R6"
    :return: True, wenn die Karte valide ist, sonst False.
    """
    return s in _card_labels


def validate_cards(s: str) -> bool:
    """
    Validiert die Karten im String.

    :param s: z.B. "R6 B5 G4"
    :return: True, wenn alle Karten validiert sind, sonst False.
    """
    return all(c in _card_labels for c in s.split(" ")) if s else True


def parse_card(label: str) -> Card:
   """
   Parst die Karte aus dem String.

   :param label: Das Label der Karte, z.B. "R6".
   :return: Die geparste Karte (mit Wert und Farbe).
   """
   return deck[_card_labels.index(label)]


def parse_cards(labels: str) -> Cards:
    """
    Parst die Karten aus dem String.

    :param labels: Die Labels der Karten mit Leerzeichen getrennt, z.B. "R6 B5 G4".
    :return: Liste der Karten.
    """
    return [deck[_card_labels.index(label)] for label in labels.split(" ")] if labels else []


def stringify_card(card: Card) -> str:
    """
    Formatiert die Karte als lesbaren String.

    :param card: Die Karte (Wert und Farbe), z.B. (8,3).
    :return: Das Label der Karte.
    """
    return _card_labels[deck.index(card)]


def stringify_cards(cards: Iterable[Card]) -> str:
    """
    Formatiert die Karte als lesbaren String.

    :param cards: Die Karten, z.B. [[8,3], [2,4], [0,1]].
    :return: Die Labels der Karte mit Leerzeichen getrennt.
    """
    return " ".join([_card_labels[deck.index(card)] for card in cards])


def ranks_to_vector(cards: Cards) -> list[int]:
    """
    Zählt die Anzahl der Karten je Rang.

    Zurückgegeben wird eine Liste mit 17 Integer, wobei der Index dem Rang entspricht und
    der Wert die Anzahl der Karten mit diesem Rang.

    :param cards: Die Karten, die gezählt werden sollen.
    :return: Liste mit der Anzahl der Karten je Rang.
    """
    # r=Hu Ma  2  3  4  5  6  7  8  9 10 Bu Da Kö As Dr Ph
    # i= 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16
    h = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    for v, _ in cards:
        h[v] += 1
    return h


def cards_to_vector(cards: Cards) -> list[int]:
    """
    Wandelt die Karten in einen Vektor um.

    Zurückgegeben wird eine Liste mit 56 Integer, wobei der Index auf die Karte im sortierten Deck zeigt
    und der Wert angibt, ob die Karte vorhanden ist oder nicht (0 = Karte nicht vorhanden, 1 = Karte vorhanden).

    :param cards: Die Karten, die als Vektor dargestellt werden sollen.
    :return: Liste mit 56 Integer.
    """
    # r=Hu Ma  2  2  2  2  3  3  3  3  4  4  4  4  5  5  5  5  6  6  6  6  7  7  7  7  8  8  8  8  9  9  9  9 10 10 10 10 Bu Bu Bu Bu Da Da Da Da Kö Kö Kö Kö As As As As Dr Ph
    # i= 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55
    h = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    for r, c in cards:
        if c > 0:
            h[(r - 2) * 4 + c + 1] = 1
        else:
            h[r if r < 2 else r + 39] = 1
    return h


def is_wish_in(wish: int, cards: Cards) -> bool:
    """
    Ermittelt, ob der gewünschte Kartenwert unter den Karten ist.

    :param wish: Der gewünschte Kartenwert.
    :param cards: Die zu prüfenden Karten.
    :return: True, wenn der Kartenwert unter den Karten ist.
    """
    assert 2 <= wish <= 14
    for card in cards:
        if card[0] == wish:
            return True
    return False


def sum_card_points(cards: Cards) -> int:
    """
    Zählt die Punkte der übergebenen Karten.

    :param cards: Die zu zählenden Karten.
    :return: Die Punkte der Karten.
    """
    return sum([_card_points[card[0]] for card in cards])


def other_cards(cards: Cards) -> List[Card]:
    """
    Listet die Karten auf, die nicht in der übergebenen Liste vorkommen.

    Die Reihenfolge entspricht dem Kartendeck (also aufsteigend).

    :param cards: Die Karten, aus denen die fehlenden Karten ermittelt werden.
    :return: Die Karten, die nicht in der übergebenen Liste vorkommen.
    """
    return [card for card in deck if card not in cards]
