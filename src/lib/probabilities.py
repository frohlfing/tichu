__all__ = "prob_of_hand",

import math
from src.lib.cards import parse_cards, stringify_cards
from src.lib.combinations import SINGLE, PAIR, TRIPLE, STAIR, FULLHOUSE, STREET, BOMB, stringify_figure, possible_hands_hi
from timeit import timeit

# -----------------------------------------------------------------------------
# Wahrscheinlichkeitsberechnung
# -----------------------------------------------------------------------------

# Listet alle Teilmengen aus den verfügbaren Karten auf, die die gegebene Einzelkarte überstechen
#
# h: Verfügbaren Karten als Vektor (Index entspricht den Rang)
# r: Rang der gegebenen Kombination
def _get_subsets_of_single(h: list, r: int) -> list:
    assert 0 <= r <= 16

    subsets = []
    if r == 16:  # Phönix
        for i in range(2, 16):  # Phönix (im Anspiel) zählt 1.5; jede Karte zw. 2 und Drache ist höher
            if h[i] >= 1:
                subsets.append({i: 1})
    elif r <= 14:  # bis Ass
        for i in range(r + 1, 17):  # Drache und Phönix sind höher
            if h[i] >= 1:
                subsets.append({i: 1})
    else:
        assert r == 15  # Drache kann nicht überstochen werden

    return subsets


# Listet alle Teilmengen aus den verfügbaren Karten auf, die das gegebene Pärchen überstechen
#
# h: Verfügbaren Karten als Vektor (Index entspricht den Rang)
# r: Rang der gegebenen Kombination
def _get_subsets_of_pair(h: list, r: int) -> list:
    assert 2 <= r <= 14

    subsets = []
    for i in range(r + 1, 15):
        # ohne Phönix
        if h[i] >= 2:
            subsets.append({i: 2})

        # mit Phönix
        if h[16] and h[i] >= 1:
            subsets.append({i: 1, 16: 1})
            # subset = {i: 1, 16: 1}
            # if subset not in subsets:
            #     subsets.append(subset)

    return subsets


# Listet alle Teilmengen aus den verfügbaren Karten auf, die das gegebene Drilling überstechen
#
# h: Verfügbaren Karten als Vektor (Index entspricht den Rang)
# r: Rang der gegebenen Kombination
def _get_subsets_of_triple(h: list, r: int) -> list:
    assert 2 <= r <= 14

    subsets = []
    for i in range(r + 1, 15):
        # ohne Phönix
        if h[i] >= 3:
            subsets.append({i: 3})

        # mit Phönix
        if h[16] and h[i] >= 2:
            subsets.append({i: 2, 16: 1})
            # subset = {i: 2, 16: 1}
            # if subset not in subsets:
            #     subsets.append(subset)

    return subsets


# Listet alle Teilmengen aus den verfügbaren Karten auf, die die gegebene Treppe überstechen
#
# h: Verfügbaren Karten als Vektor (Index entspricht den Rang)
# m: Länge der gegebenen Kombination
# r: Rang der gegebenen Kombination
def _get_subsets_of_stairs(h: list, m: int, r: int) -> list:
    assert m % 2 == 0
    assert 4 <= m <= 14
    steps = int(m / 2)
    assert steps + 1 <= r <= 14

    subsets = []
    for r_start in range((r + 1) - steps + 1, 15 - steps + 1):
        r_end = r_start + steps  # exklusiv

        # ohne Phönix
        if all(h[i] >= 2 for i in range(r_start, r_end)):
            subsets.append({i: 2 for i in range(r_start, r_end)})

        # mit Phönix
        if h[16]:  # Phönix vorhanden?
            for r_pho in range(r_start, r_end):
                if all(h[i] >= (1 if i == r_pho else 2) for i in range(r_start, r_end)):
                    subset = {i: 1 if i == r_pho else 2 for i in range(r_start, r_end)}
                    subset[16] = 1
                    if subset not in subsets:  # todo notwendig?
                        subsets.append(subset)

    return subsets


# Listet alle Teilmengen aus den verfügbaren Karten auf, die das gegebene Fullhouse überstechen
#
# h: Verfügbaren Karten als Vektor (Index entspricht den Rang)
# r: Rang der gegebenen Kombination
def _get_subsets_of_fullhouse(h: list, r: int) -> list:
    assert 2 <= r <= 14

    subsets = []

    for i in range(r + 1, 15):
        # ohne Phönix
        if h[i] >= 3:
            for j in range(2, 15):
                if i != j and h[j] >= 2:
                    subsets.append({i: 3, j: 2})

        # mit Phönix im Pärchen
        if h[16] and h[i] >= 3:
            for j in range(2, 15):
                if i != j and h[j] >= 1:
                    subsets.append({i: 3, j: 1, 16: 1})


        # mit Phönix im Drilling
        if h[16] and h[i] >= 2:
            for j in range(2, 15):
                if i != j and h[j] >= 2:
                    subsets.append({i: 2, j: 2, 16: 1})

    return subsets


# Listet alle Teilmengen aus den verfügbaren Karten auf, die die gegebene Straße überstechen
#
# h: Verfügbaren Karten als Vektor (Index entspricht den Rang)
# m: Länge der gegebenen Kombination
# r: Rang der gegebenen Kombination
def _get_subsets_of_streets(h: list, m: int, r: int) -> list:
    assert 5 <= m <= 14
    assert m <= r <= 14

    subsets = []
    for r_start in range((r + 1) - m + 1, 15 - m + 1):
        r_end = r_start + m  # exklusiv

        # ohne Phönix
        if all(h[i] >= 1 for i in range(r_start, r_end)):
            subsets.append({i: 1 for i in range(r_start, r_end)})

        # mit Phönix
        if h[16]:  # Phönix vorhanden?
            for r_pho in range(max(r_start, 2), r_end):  # max(r_start, 2) berücksichtigt die Ausnahmeregel, dass der Phönix die 1 nicht ersetzen kann
                if all(h[i] >= 1 for i in range(r_start, r_end) if i != r_pho):
                    subset = {i: 1 for i in range(r_start, r_end) if i != r_pho}
                    subset[16] = 1
                    if subset not in subsets:  # todo notwendig?
                        subsets.append(subset)

    return subsets

# Listet alle Teilmengen aus den verfügbaren Karten auf, die die gegebene Bombe überstechen
#
# todo: Die Regel, dass längere Farbbomben kürzere überstechen, wird hier ignoriert.
#
# h: Liste der verfügbaren Karten als Vektor
# m: Länge der gegebenen Kombination
# r: Rang der gegebenen Kombination
def _get_subsets_of_bomb(h: list, m: int, r: int) -> list:
    subsets = []

    # 4er-Bombe (h listet nur die Ränge der Karten auf)
    if m == 4:
        assert 2 <= r <= 14
        for i in range(r + 1, 15):
            if h[i] == 4:
                subsets.append({i: 4})

    # Farbbombe (h listet alle 56 Karten auf)
    else:
        assert 5 <= m <= 13
        assert m + 1 <= r <= 14
        for r_start in range((r + 1) - m + 1, 15 - m + 1):
            r_end = r_start + m  # exklusiv
            for color in range(4):
                offset = 13 * color
                if all(h[i] >= 1 for i in range(r_start + offset, r_end + offset)):
                    subsets.append({i: 1 for i in range(r_start + offset, r_end + offset)})

    # # längere Farbbombe
    # for m2 in range(m + 1, 14):
    #     for r_start in range(m2 + 1, 15 - m2 + 1):
    #         r_end = r_start + m2  # exklusiv
    #         if all(h[i] >= 1 for i in range(r_start, r_end)):
    #             subsets.append({i: 1 for i in range(r_start, r_end)})

    return subsets



# Listet alle Teilmengen aus den verfügbaren Karten auf, die die gegebene Kombination überstechen
#
# Zurückgegeben wird ein Dictionary, wobei der Key der Rang und der Wert die erforderliche Mindestanzahl
# von Karten mit diesen Rang ist.
#
# h: Verfügbaren Karten als Vektor
# figure: Typ, Länge und Rang der gegebenen Kombination
def get_subsets(h: list, figure: tuple) -> list:
    t, m, r = figure

    if t == SINGLE:  # Einzelkarte
        subsets = _get_subsets_of_single(h, r)

    elif t == PAIR:  # Paar
        subsets = _get_subsets_of_pair(h, r)

    elif t == TRIPLE:  # Drilling
        subsets = _get_subsets_of_triple(h, r)

    elif t == STAIR:  # Treppe
        subsets = _get_subsets_of_stairs(h, m, r)

    elif t == FULLHOUSE:  # Fullhouse
        subsets = _get_subsets_of_fullhouse(h, r)

    elif t == STREET:  # Straße
        subsets = _get_subsets_of_streets(h, m, r)

    elif t == BOMB:  # Bombe
        subsets = _get_subsets_of_bomb(h, m, r)

    else:
        assert False

    return subsets


# Bildet Vereinigungsmengen aus zwei oder mehr Mengen
#
# Der erste Eintrag der zurückgegebenen Liste listet die gegebenen Ursprungsmengen auf.
# Der zweite Eintrag listet die Vereinigungsmengen auf, die aus zwei Ursprungsmengen bestehen.
# Der dritte Eintrag listet die auf, die aus drei Ursprungsmengen bestehen, usw.
#
# sets: Liste von Mengen (Ursprungsmengen)
# minimums: Erforderliche Mindestanzahl der Karten
# k: Maximal erlaubte Länge der Vereinigungsmenge
def union_sets(sets: list, k: int) -> list[list]:
    length = len(sets)
    result = [sets] + [[] for _ in range(length - 1)]

    def _build_unions(s: dict, start: int, c: int):
        # s: Vereinigungsmenge, zu der eine weitere Ursprungsmenge hinzugefügt werden soll
        # start: sets[start] ist die hinzuzufügende Ursprungsmenge
        # c: Anzahl Teilmengen, die bereits in der Vereinigungsmenge sind
        for j in range(start, length):
            keys = set(s.keys()).union(sets[j].keys())
            union = {key: max(s[key] if key in s else 0, sets[j][key] if key in sets[j] else 0) for key in keys}
            if sum(union.values()) <= k:
                result[c - 1].append(union)
                _build_unions(union, j + 1, c + 1)
        return result

    for i in range(length):
        _build_unions(sets[i], i + 1, 2)

    return result


# Zählt die Anzahl jeder eindeutigen Menge
# Zurückgegeben wird eine Liste mit Tupeln, wobei jedes Tupel eine eindeutige Menge und dessen Anzahl enthält
def count_sets(sets: list) -> list:
    unique_sets = []
    counts = []
    for s in sets:
        if s in unique_sets:
            counts[unique_sets.index(s)] += 1
        else:
            unique_sets.append(s)
            counts.append(1)
    return list(zip(unique_sets, counts))


# Hypergeometrische Verteilung
#
# Zurückgegeben wird die Anzahl der möglichen Kombinationen, die die gegebene Teilmenge beinhalten.
#
# subset: Teilmenge
# h: Verfügbaren Karten als Vektor
# k: Anzahl der Handkarten
def hypergeom(subset: dict, h: list, k: int) -> int:
    def _comb(index: int, n_remain, k_remain) -> int:
        r = keys[index]  # der aktuell zu untersuchende Kartenrang
        n_fav = h[r]  # Anzahl der verfügbaren Karten mit diesem Rang
        c_min = subset[r]  # erforderliche Anzahl Karten mit diesem Rang
        result = 0
        for c in range(c_min, n_fav + 1):
            if k_remain < c:
                break
            if index + 1 < length:
                result += math.comb(n_fav, c) * _comb(index + 1, n_remain - n_fav, k_remain - c)
            else:
                result += math.comb(n_fav, c) * math.comb(n_remain - n_fav, k_remain - c)
        return result

    keys = list(subset)
    length = len(subset)
    return _comb(0, sum(h), k)


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


# Berechnet die Wahrscheinlichkeit, dass die Hand die gegebene Kombination überstechen kann
#
# todo: Die Regel, dass längere Bomben kürzere überstechen, wird hier ignoriert.
# todo: Es wird auch ignoriert, das eine Bombe eine "normale" Kombination überstechen kann.
#
# cards: Verfügbare Karten
# k: Anzahl der Handkarten
# figure: Typ, Länge und Rang der gegebenen Kombination
# r: Rang der gegebenen Kombination
def prob_of_hand(cards: list[tuple], k: int, figure: tuple) -> float:
    n = len(cards)  # Gesamtanzahl der verfügbaren Karten
    assert 0 <= n <= 56
    assert 0 <= k <= 14

    # Vorabprüfung: Sind genügend Karten vorhanden, um die gegebene Kombination zu bilden?
    t, m, _r = figure
    if n < m or k < m:
        return 0

    # die verfügbaren Karten in einen Vektor umwandeln
    if t == BOMB and m >= 5:  # Farbbombe
        h = cards_to_vector(cards)
    else:
        h = ranks_to_vector(cards)  # wenn es keine Farbbombe ist, sind nur die Ränge der Karten von Interesse

    # Teilmengen finden, die die gegebene Kombination überstechen
    subsets = get_subsets(h, figure)
    if len(subsets) == 0:
        return 0

    # Vereinigungsmengen aus zwei oder mehr Teilmengen bilden
    favorable_unions = union_sets(subsets, k)

    # für jede Vereinigungsmengen die möglichen Kombinationen zählen
    matches = 0
    for j, unions in enumerate(favorable_unions):
        number_of_subsets_in_union = j + 1  # Anzahl der Teilmengen, die jede der aktuellen Vereinigungsmengen umfassen
        for union, c in count_sets(unions):
            # Hypergeometrische Verteilung
            matches_part = hypergeom(union, h, k) * c
            # Prinzip der Inklusion und Exklusion
            if number_of_subsets_in_union % 2 == 1:
                matches += matches_part  # inklusion bei ungerade Anzahl an Teilmengen
            else:
                matches -= matches_part  # exklusion bei gerade Anzahl an Teilmengen

    # Gesamtanzahl der möglichen Kombinationen
    total = math.comb(n, k)

    # Wahrscheinlichkeit
    return matches / total


# -----------------------------------------------------------------------------
# Test
# -----------------------------------------------------------------------------

def inspect(cards, k, figure):  # pragma: no cover
    print(f"Kartenauswahl: {cards}")
    print(f"Anzahl Handkarten: {k}")
    print(f"Kombination: {stringify_figure(figure)}")

    print("Mögliche Handkarten:")
    matches, hands = possible_hands_hi(parse_cards(cards), k, figure)
    for match, sample in zip(matches, hands):
        print("  ", stringify_cards(sample), match)
    matches_expected = sum(matches)
    total_expected = len(hands)
    p_expected = (matches_expected / total_expected) if total_expected else "nan"
    print(f"Gezählt:   p = {matches_expected}/{total_expected} = {p_expected}")

    p_actual = prob_of_hand(parse_cards(cards), k, figure)
    print(f"Berechnet: p = {(total_expected * p_actual):.0f}/{total_expected} = {p_actual}")


# todo die Test nach test_probabilities verschieben (inspect() aber hier lassen)

def test(cards, k, figure, p_expected, msg):  # pragma: no cover
    p_actual = prob_of_hand(parse_cards(cards), k, figure)
    print(f"{p_actual:<20} {p_expected:<20}  {msg}")
    assert p_actual == p_expected

def test_single():  # pragma: no cover
    # Einzelkarte
    test("Dr RB G6 B5 S4 R3 R2", 4, (1, 1, 11), 0.5714285714285714, "Einzelkarte")
    test("Dr RB SB B5 S4 R3 R2", 5, (1, 1, 11), 0.7142857142857143, "Einzelkarte mit 2 Buben")
    test("Ph RB G6 B5 S4 R3 R2", 5, (1, 1, 11), 0.7142857142857143, "Einzelkarte mit Phönix")

    # Sonderkarten
    test("Dr Hu Ph Ma S4 R3 R2", 1, (1, 1, 0), 0.8571428571428571, "Einzelkarte Hund")
    test("Dr Hu Ph Ma S4 R3 R2", 1, (1, 1, 1), 0.7142857142857143, "Einzelkarte Mahjong")
    test("Dr Hu Ph Ma S4 R3 R2", 1, (1, 1, 15), 0.0, "Einzelkarte Drache")
    test("Dr Hu Ph Ma S4 R3 R2", 1, (1, 1, 16), 0.5714285714285714, "Einzelkarte Phönix")

    # todo
    # Einzelkarte mit Bombe
    # test("SB RZ GZ BZ SZ R9 G9 R8 G8 B4", 3, (1, 1, 9), 0.9166666666666666, "Einzelkarte mit 4er-Bombe")

def test_pair():  # pragma: no cover
    # Pärchen
    test("Dr RK GK BB SB RB R2", 5, (2, 2, 11), 0.47619047619047616, "Pärchen ohne Phönix")
    test("Ph RK GK BD SB RB R2", 5, (2, 2, 11), 0.9047619047619048, "Pärchen mit Phönix")

    # todo
    # Pärchen mit Bombe

def test_triple():  # pragma: no cover
    # Drilling
    test("SK RK GB BB SB R3 R2", 4, (3, 3, 10), 0.11428571428571428, "Drilling ohne Phönix")
    test("Ph RK GB BB SB R3 R2", 4, (3, 3, 10), 0.37142857142857144, "Drilling mit Phönix")

    # todo
    # Drilling mir Bombe

def test_stair():  # pragma: no cover
    # Treppe ohne Phönix
    test("RK GK BD SD SB RB BB", 6, (4, 6, 12), 0.42857142857142855, "3er-Treppe ohne Phönix")
    test("SB RZ R9 G9 R8 G8 B4", 9, (4, 4, 9),  0.0, "2er-Treppe nicht möglich")
    test("RK GK BD SD GD R9 B2", 6, (4, 4, 12), 0.7142857142857143, "2er-Treppe aus Fullhouse")
    test("Dr GA BA GK BK SD BD", 6, (4, 4, 14), 0.0, "2er-Treppe über Ass")

    # Treppe mit Phönix
    test("Ph GK BK SD SB RB BZ R9", 6, (4, 4, 10), 0.5, "2er-Treppe mit Phönix"),
    test("Ph GK BK SD SB RB R9", 6, (4, 4, 10), 0.7142857142857143, "2er-Treppe mit Phönix (vereinfacht)"),
    test("Ph GK BK SD SB R9 S4", 6, (4, 4, 10), 0.42857142857142855, "2er-Treppe mit Phönix (vereinfacht 2)"),
    test("Ph GK BD SD SB RB BB", 6, (4, 6, 12), 0.42857142857142855, "3er-Treppe mit Phönix"),
    test("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 4, (4, 4, 9), 0.06190476190476191, "2er-Treppe, Phönix übrig"),

    # todo
    # Treppe mit Bombe

def test_fullhouse():
    # Fullhouse ohne Phönix
    test("RK GK BD SB RB BB S2", 6, (5, 5, 10), 0.2857142857142857, "Fullhouse ohne Phönix")
    test("BK RK SK BZ RZ R9 S9 RB", 7, (5, 5, 12), 0.625, "Fullhouse und zusätzliches Pärchen")
    test("BK RK SK G9 R9 S9 RB S2", 7, (5, 5, 12), 0.625, "Fullhouse mit 2 Drillinge")

    # Fullhouse mit Phönix
    test("Ph GK BD SB RB BB S2", 6, (5, 5, 10), 0.42857142857142855, "Fullhouse mit Phönix für Paar")
    test("RK GK BD SB RB BZ Ph", 6, (5, 5, 10), 0.2857142857142857, "Fullhouse mit Phönix für Drilling")
    test("SB RZ GZ BZ Ph G9 R8 G8 B4", 5, (5, 5, 9), 0.07142857142857142, "Fullhouse mit 5 Handkarten mit Phönix")
    test("SB RZ GZ BZ Ph G9 R8 G8 B4", 6, (5, 5, 9), 0.2619047619047619, "Fullhouse mit 6 Handkarten mit Phönix")

    # todo
    # Fullhouse mit Bomben
    # test("BK RK SK GK R9 S9 RB S2", 7, (5, 5, 12), 8, 8, 1.0, "Fullhouse mit 4er-Bombe")

def test_street():
    # Straße ohne Phönix
    test("BK SD BD RB BZ B9 R3", 6, (6, 5, 12), 0.42857142857142855, "5er-Straße ohne Phönix")
    test("RA RK GD BB RZ B9 R2", 6, (6, 5, 10), 0.42857142857142855, "6er-Straße bis Ass ohne Phönix")
    test("SK RK GD BB RZ B9 R8 R2", 6, (6, 5, 12), 0.17857142857142858, "6er-Straße mit 2 Könige ohne Phönix")
    test("RK GD BB RZ B9 R8 S6 S2", 6, (6, 5, 10), 0.17857142857142858, "6er-Straße bis König ohne Phönix")
    test("SK RK GD BB RZ B9 R8 S6 S2", 6, (6, 5, 10), 0.10714285714285714, "7er-Straße bis König mit 2 Könige ohne Phönix")
    test("RA RK GD BB RZ B9 R8 S7 S6", 6, (6, 5, 10), 0.15476190476190477, "8er-Straße bis Ass ohne Phönix")
    test("GK BB SB GB RZ BZ GZ R9 S9 B9 R8 S8 G8 R7 S7 G7 R4 R2", 7, (6, 5, 10), 0.22652714932126697, "Straße mit Drillinge ohne Phönix")

    # Straße mit Phönix
    test("GA RK GD RB GZ Ph", 6, (6, 5, 10), 1.0, "5er-Straße mit Phönix (verlängert)")
    test("RA GK BD RZ B9 R3 Ph", 6, (6, 5, 12), 0.42857142857142855, "6er-Straße mit Phönix (Lücke gefüllt)")
    test("SA RK GD BB RZ B9 Ph", 6, (6, 5, 11), 1.0, "7er-Straße mit Phönix (verlängert)")
    test("Ph SK RK GD BB RZ B9 R8", 6, (6, 5, 12), 0.6428571428571429, "7er-Straße mit 2 Könige mit Phönix (verlängert)")
    test("Ph RK GD BB RZ B9 R8 R2", 6, (6, 5, 12), 0.4642857142857143, "8er-Straße mit Phönix (verlängert)")
    test("SA RK GD BB RZ B9 S8 R7 Ph", 6, (6, 5, 10), 0.5595238095238095, "9er-Straße mit Phönix (verlängert)")
    test("GA RK GD RB GZ R9 S8 B7 S6 B5 S4 B3 Ph", 6, (6, 5, 10), 0.07634032634032634, "13er-Straße mit Phönix (verlängert)")

    # todo
    # Straße mit Bomben
    # test("GB GZ G9 G8 G7", 5, (6, 5, 10), 0, 1, 0.0, "5er-Straße ist Farbbombe")
    # test("GD GB GZ G9 G8 G7", 5, (6, 5, 10), 0, 6, 0.0, "6er-Straße ist Farbbombe")
    # test("BK SD BD BB BZ B9 R3", 6, (6, 5, 12), 3, 7, 0.42857142857142855, "5er-Straße mit 2 Damen und mit Farbbombe")
    # test("BK BD BB BZ B9 RK RD RB RZ R9 G2 G3 G4", 11, (6, 5, 12), 73, 78, 0.9358974358974359, "5er-Straße mit 2 Farbbomben")
    # test("GA GK GD GB GZ G9 G8 G7 G6 G5 G4 G3 G2", 5, (6, 5, 10), 0, 1287, 0.0, "13er-Straße mit Farbbombe")
    # test("GA GK GD GB GZ G9 R8 G7 G6 G5 G4 G3 Ph", 5, (6, 5, 10), 22, 1287, 0.017094017094017096, "13er-Straße mit 2 Farbbomben mit Phönix")
    # test("SK GB GZ G9 G8 G7 RB RZ R9 R8 R7 S4 Ph", 6, (6, 5, 10), 516, 1716, 0.3006993006993007, "2 5er-Straßen mit 2 Farbbomben")

def test_bomb():
    # 4er-Bomben
    test("RK GB BB SB RB BZ R2", 5, (7, 4, 10), 0.14285714285714285, "4er-Bombe")

    # Farbbomben
    test("BK BB BZ B9 B8 B7 B2", 5, (7, 5, 10), 0.047619047619047616, "Farbbombe")
    test("BK BD BB BZ B9 RK RD RB RZ R9 S3 S2", 11, (7, 5, 12), 1.0, "2 Farbbomben in 12 Karten")
    test("BK BD BB BZ B9 RK RD RB RZ R9 G7 S3 S2", 11, (7, 5, 12), 0.6794871794871795, "2 Farbbomben in 13 Karten")

    # todo
    # längere Bomben


# noinspection DuplicatedCode
if __name__ == "__main__":  # pragma: no cover
    #inspect("BK BD BB BZ B9 RK RD RB RZ R9 G7 S3 S2", 11, (7, 5, 12))

    number = 1
    print(f"Gesamtzeit: {timeit(lambda: test_single(), number=number) * 1000 / number:.6f} ms")
    print(f"Gesamtzeit: {timeit(lambda: test_pair(), number=number) * 1000 / number:.6f} ms")
    print(f"Gesamtzeit: {timeit(lambda: test_triple(), number=number) * 1000 / number:.6f} ms")
    print(f"Gesamtzeit: {timeit(lambda: test_stair(), number=number) * 1000 / number:.6f} ms")
    print(f"Gesamtzeit: {timeit(lambda: test_fullhouse(), number=number) * 1000 / number:.6f} ms")
    print(f"Gesamtzeit: {timeit(lambda: test_street(), number=number) * 1000 / number:.6f} ms")
    print(f"Gesamtzeit: {timeit(lambda: test_bomb(), number=number) * 1000 / number:.6f} ms")
