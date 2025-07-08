"""
Dieses Modul definiert die Logik zur Erkennung und Verarbeitung von Kartenkombinationen.
"""

__all__ = "CombinationType", "Combination",  \
    "FIGURE_PASS", "FIGURE_DOG", "FIGURE_MAH", "FIGURE_DRA", "FIGURE_PHO", \
    "validate_combination", "stringify_combination", "stringify_type", "get_combination", \
    "build_combinations", "remove_combinations", \
    "build_action_space",

import enum
from src.lib.cards import CARD_DOG, CARD_PHO, is_wish_in, Cards, CardSuit
from typing import Tuple, List

# -----------------------------------------------------------------------------
# Kartenkombinationen
# -----------------------------------------------------------------------------

class CombinationType(enum.IntEnum):  # todo überall konsequent verwenden
    """
    Enum für Kombinationstypen.
    """
    PASS = 0  # Passen
    SINGLE = 1  # Einzelkarte
    PAIR = 2  # Paar
    TRIPLE = 3  # Drilling
    STAIR = 4  # Treppe
    FULLHOUSE = 5  # Fullhouse
    STREET = 6  # Straße
    BOMB = 7  # Vierer-Bombe oder Farbbombe


Combination = Tuple[CombinationType, int, int]  # (Typ, Länge, Rang)  # todo überall konsequent verwenden
"""
Type-Alias für eine Kombination.
"""


# Sonderkarten einzeln ausgespielt  # todo entfernen
FIGURE_PASS = (CombinationType.PASS, 0, 0)
FIGURE_DOG = (CombinationType.SINGLE, 1, 0)
FIGURE_MAH = (CombinationType.SINGLE, 1, 1)
FIGURE_DRA = (CombinationType.SINGLE, 1, 15)
FIGURE_PHO = (CombinationType.SINGLE, 1, 16)


def validate_combination(combination: Tuple[int, int, int]) -> bool:
    """
    Ermittelt, ob Typ, Länge und Rang eine gültige Kartenkombination angibt.

    :param combination: Die zu prüfende Kombination.
    :return: True, wenn die Kombination gültig ist.
    """
    t, m, r = combination
    if t == CombinationType.PASS:
        return m == 0 and r == 0
    if t == CombinationType.SINGLE:  # Einzelkarte
        return m == 1 and 0 <= r <= 16
    if t in [CombinationType.PAIR, CombinationType.TRIPLE, CombinationType.FULLHOUSE]:  # Paar, Drilling, Fullhouse
        return m == t and 2 <= r <= 14
    if t == CombinationType.STAIR:  # Treppe
        return m % 2 == 0 and 4 <= m <= 14 and int(m / 2) + 1 <= r <= 14
    if t == CombinationType.STREET:  # Straße
        return 5 <= m <= 14 and m <= r <= 14
    if t == CombinationType.BOMB:
        if m == 4:  # 4er-Bombe
            return 2 <= r <= 14
        else:  # Farbbombe
            return 5 <= m <= 14 and m + 1 <= r <= 14
    return False


def stringify_combination(combination: Combination) -> str:
    """
    Wandelt eine Kombination (Typ, Länge und Rang) in ein Label um.

    :param combination: Die Kombination.
    :return: Label der Kombination.
    """
    t, n, v = combination
    if t in (CombinationType.STAIR, CombinationType.STREET, CombinationType.BOMB):
        return f"{t.name:s}{n:02}-{v:02}"
    else:
        return f"{t.name}-{v:02}"


def stringify_type(t: CombinationType, m: int = None) -> str:
    """
    Wandelt den Typ einer Kombination in ein Label um.

    :param t: Typ der Kombination.
    :param m: Länge der Kombination (optional).
    :return:
    """
    assert CombinationType.PASS <= t <= CombinationType.BOMB
    label = ["pass", "single", "pair", "triple", "stair", "fullhouse", "street", "bomb"][t]
    if m is not None and t in (CombinationType.STAIR, CombinationType.STREET, CombinationType.BOMB):
        assert (t == CombinationType.STAIR and m % 2 == 0 and 4 <= m <= 14) or (t == CombinationType.STREET and 5 <= m <= 14) or (t == CombinationType.BOMB and 4 <= m <= 14)
        label += f"{m:02}"
    return label


def get_combination(cards: Cards, trick_value: int, shift_phoenix: bool = False) -> Combination:
    """
    Ermittelt die Kombination der gegebenen Karten.

    Es wird vorausgesetzt, dass `cards` eine gültige Kombination darstellt.

    Wenn `shift_phoenix` gesetzt ist, wird der Phönix der Kombi entsprechend eingereiht.

    :param cards: Karten der Kombination; werden absteigend sortiert (mutable!).
    :param trick_value: Rang des aktuellen Stichs (0, wenn kein Stich ausgelegt ist).
    :param shift_phoenix: Wenn True, wird der Phönix eingereiht (kostet etwas Zeit).
    :return: Die Kombination (Typ, Länge, Rang).
    """
    n = len(cards)
    if n == 0:
        return FIGURE_PASS

    # Karten absteigend sortieren
    cards.sort(reverse=True)  # Der Phönix ist jetzt, falls vorhanden, die erste Karte von rechts!

    # Typ ermitteln
    if n == 1:
        t = CombinationType.SINGLE
    elif n == 2:
        t = CombinationType.PAIR
    elif n == 3:
        t = CombinationType.TRIPLE
    elif n == 4 and cards[1][0] == cards[2][0] == cards[3][0]:  # Treppe ausschließen: 2., 3. und 4. Karte gleichwertig
        t = CombinationType.BOMB  # 4er-Bombe
    elif n == 5 and (cards[1][0] == cards[2][0] or cards[2][0] == cards[3][0]):  # Straße ausschließen
        t = CombinationType.FULLHOUSE  # 22211 22111 *2211 *2221 *2111
    elif cards[1][0] == cards[2][0] or cards[2][0] == cards[3][0]:  # Straße ausschließen
        t = CombinationType.STAIR  # Treppe: 332211 *32211 *33211 *33221
    elif len([card for card in cards if card[1] == cards[0][1]]) == n:  # Einfarbig?
        t = CombinationType.BOMB  # Farbbombe
    else:
        t = CombinationType.STREET

    # Rang ermitteln
    if t == CombinationType.SINGLE:
        if cards[0] == CARD_PHO:
            assert 0 <= trick_value <= 15
            v = trick_value if trick_value else 1  # ist um 0.5 größer als der Stich (wir runden ab, da egal)
        else:
            v = cards[0][0]
    elif t == CombinationType.FULLHOUSE:
        v = cards[2][0]  # die 3. Karte gehört auf jeden Fall zum Drilling
    elif t == CombinationType.STREET or (t == CombinationType.BOMB and n > 4):
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
        if t == CombinationType.PAIR:  # Phönix ans Ende verschieben
            cards[0] = cards[1]; cards[1] = CARD_PHO
        elif t == CombinationType.TRIPLE:  # Phönix ans Ende verschieben
            cards[0] = cards[1]; cards[1] = cards[2]; cards[2] = CARD_PHO
        elif t == CombinationType.STAIR:  # Phönix in die Lücke verschieben *11233
            for i in range(1, n, 2):
                if i + 1 == n or cards[i][0] != cards[i + 1][0]:
                    # Lücke gefunden
                    for j in range(0, i):
                        cards[j] = cards[j + 1]
                    cards[i] = CARD_PHO
                    break
        elif t == CombinationType.FULLHOUSE:  # Phönix ans Ende des Drillings bzw. Pärchens verschieben
            if cards[1][0] == cards[2][0] == cards[3][0]:  # Drilling vorne komplett → Phönix ans Ende verschieben
                cards[0] = cards[1]; cards[1] = cards[2]; cards[2] = cards[3]; cards[3] = cards[4]; cards[4] = CARD_PHO
            elif cards[2][0] == cards[3][0] == cards[4][0]:  # Drilling hinten komplett → Phönix an die 2. Stelle verschieben
                cards[0] = cards[1]; cards[1] = CARD_PHO
            else:  # kein Drilling komplett → Phönix in die Mitte verschieben
                cards[0] = cards[1]; cards[1] = cards[2]; cards[2] = CARD_PHO
        elif t == CombinationType.STREET:  # Phönix in die Lücke verschieben
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


def build_combinations(hand: Cards) -> List[Tuple[Cards, Combination]]:
    """
    Ermittelt die Kombinationsmöglichkeiten der Handkarten (die besten zuerst).

    :param hand: Die Handkarten; werden absteigend sortiert (mutable!).
    :return: Kombinationsmöglichkeiten [(Karten, (Typ, Länge, Rang)), ...].
    """
    # Handkarten absteigend sortieren
    hand.sort(reverse=True)

    has_phoenix = CARD_PHO in hand
    arr = [[], [], [], [], [], [], [], []]  # pro Typ ein Array
    n = len(hand)

    # Einzelkarten, Paare, Drilling, 4er-Bomben
    for i1 in range(0, n):
        card1 = hand[i1]
        arr[CombinationType.SINGLE].append([card1])
        if card1[1] == CardSuit.SPECIAL:
            continue
        if has_phoenix:
            arr[CombinationType.PAIR].append([card1, CARD_PHO])
        # Paare suchen...
        for i2 in range(i1 + 1, n):
            card2 = hand[i2]
            if card1[0] != card2[0]:
                break
            arr[CombinationType.PAIR].append([card1, card2])
            if has_phoenix:
                arr[CombinationType.TRIPLE].append([card1, card2, CARD_PHO])
            # Drillinge suchen...
            for i3 in range(i2 + 1, n):
                card3 = hand[i3]
                if card1[0] != card3[0]:
                    break
                arr[CombinationType.TRIPLE].append([card1, card2, card3])
                # 4er-Bomben suchen...
                #for i4 in range(i3 + 1, n):
                #    card4 = hand[i4]
                #    if card1[0] == card4[0]:
                #        arr[CombinationType.BOMB].append([card1, card2, card3, card4])
                #    break
                if i3 + 1 < n:
                    card4 = hand[i3 + 1]
                    if card1[0] == card4[0]:
                        arr[CombinationType.BOMB].append([card1, card2, card3, card4])

    # Treppen
    temp = arr[CombinationType.PAIR].copy()
    m = len(temp)
    i = 0
    while i < m:
        v = temp[i][-2][0]  # Rang der vorletzten Karte in der Treppe
        for pair in arr[CombinationType.PAIR]:
            if pair[1] == CARD_PHO and CARD_PHO in temp[i]:
                continue
            if v - 1 == pair[0][0]:
                new_stair = temp[i] + pair
                arr[CombinationType.STAIR].append(new_stair)
                temp.append(new_stair)
                m += 1
        i += 1

    # Fullhouse
    for triple in arr[CombinationType.TRIPLE]:
        for pair in arr[CombinationType.PAIR]:
            if triple[0][0] == pair[0][0]:
                # Ausnahmeregel: Der Drilling darf nicht vom gleichen Rang sein wie das Paar (wäre mit Phönix möglich).
                continue
            if triple[2] == CARD_PHO and triple[0][0] < pair[0][0]:
                # Man würde immer den Phönix zum höherwertigen Pärchen sortieren.
                continue
            if not set(triple).intersection(pair):
                # Schnittmenge ist leer
                arr[CombinationType.FULLHOUSE].append(triple + pair)

    # Straßen
    for i1 in range(0, n - 1):
        if hand[i1][1] == CardSuit.SPECIAL or (i1 > 0 and hand[i1 - 1][0] == hand[i1][0]):
            continue  # Sonderkarte oder vorherige Karte gleichwertig
        v1 = hand[i1][0]
        if v1 < (4 if has_phoenix else 5):
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
                    arr[CombinationType.BOMB if is_bomb else CombinationType.STREET].append(cards[0:k])
                    # jede Karte ab der 2. bis zur vorletzten mit dem Phönix ersetzen
                    if available_phoenix:
                        for i in range(1, k - 1):
                            arr[CombinationType.STREET].append(cards[0:i] + [CARD_PHO] + cards[i + 1:k])
                # Straße mit Phönix verlängern
                if k >= 4 and available_phoenix:
                    if cards[0][0] < 14:
                        arr[CombinationType.STREET].append([CARD_PHO] + cards[0:k])
                    elif cards[k - 1][0] > 2:
                        arr[CombinationType.STREET].append(cards[0:k] + [CARD_PHO])

    # Kombinationen auflisten (zuerst die besten)
    result = []
    for t in range(7, 0, -1):  # Typ t = 7 (BOMB) .. 1 (SINGLE)
        for cards in arr[t]:
            # Rang ermitteln
            if t == CombinationType.STREET and cards[0] == CARD_PHO:
                v = cards[1][0] + 1  # Phönix == Rang der zweiten Karte + 1
            else:
                v = cards[0][0]  # Rang der ersten Karte
            # Kombination speichern
            result.append((cards, (CombinationType(t), len(cards), v)))

    return result


def remove_combinations(combis: List[Tuple[Cards, Combination]], cards: Cards):
    """
    Entfernt die Kombinationsmöglichkeiten, die aus mindestens einer der angegebenen Karten bestehen.

    :param combis: Kombinationsmöglichkeiten [(Karten, (Typ, Länge, Rang)), ...].
    :param cards: Karten, die entfernt werden sollen.
    :return: Kombinationsmöglichkeiten ohne die gegebenen Karten.
    """
    return [combi for combi in combis if not set(cards).intersection(combi[0])]


def build_action_space(combis: List[Tuple[Cards, Combination]], trick_combination: tuple, unfulfilled_wish: int) -> List[Tuple[Cards, Combination]]:  # todo unfulfilled_wish umbenennen in wish_value
    """
    Ermittelt spielbare Kartenkombinationen.
    
    :param combis: Kombinationsmöglichkeiten der Hand, ([(Karten, (Typ, Länge, Rang)), ...]).
    :param trick_combination: Typ, Länge, Rang des aktuellen Stichs ((0,0,0) falls kein Stich liegt).
    :param unfulfilled_wish: Unerfüllter Wunsch (0 == kein Wunsch geäußert, negativ == bereits erfüllt).
    :return: ([], (0,0,0)) für Passen sofern möglich + spielbare Kombinationsmöglichkeiten.
    """
    assert 0 <= trick_combination[0] <= 7
    assert 0 <= trick_combination[1] <= 14
    assert 0 <= trick_combination[2] <= 15
    result = []
    if trick_combination not in (FIGURE_PASS, FIGURE_DOG):  # trickCombination[2] > 0  # Rang > 0?
        # Stich liegt und es ist kein Hund
        result.append(([], (CombinationType.PASS, 0, 0)))  # Passen ist eine Option
        t, n, v = trick_combination
        for combi in combis:
            t2, n2, v2 = combi[1]
            if combi[1] == FIGURE_PHO:  # Phönix als Einzelkarte
                if trick_combination == FIGURE_DRA:
                    continue  # Phönix auf Drache ist nicht erlaubt
                v2 = v + 0.5 if v > 0 else 1.5
            if (t == CombinationType.BOMB and t2 == t and (n2 > n or (n2 == n and v2 > v))) or \
               (t != CombinationType.BOMB and (t2 == CombinationType.BOMB or (t2 == t and n2 == n and v2 > v))):
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

if __name__ == "__main__":  # pragma: no cover
    #hand = parse_cards("B2 B3 B4 S5 G5 S6 B6 S7 S8 S9 Dr")
    #combis = build_combinations(hand)
    pass
