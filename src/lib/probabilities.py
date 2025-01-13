__all__ = "prob_of_hand"

import math
from src.lib.combinations import SINGLE, PAIR, TRIPLE, STAIR, FULLHOUSE, STREET, BOMB
from timeit import timeit

# -----------------------------------------------------------------------------
# Wahrscheinlichkeitsberechnung
# -----------------------------------------------------------------------------

# Listet alle Teilmengen aus den verfügbaren Karten auf, die die gegebene Treppe überstechen
#
# h: Liste mit der Anzahl der verfügbaren Karten für jeden Rang (Index entspricht den Rang)
# m: Länge der gegebenen Kombination
# r: Rang der gegebenen Kombination
def _get_subsets_of_stairs(h: list, m: int, r: int) -> list:
    # Bedingung für eine Treppe
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
                    if subset not in subsets:
                        subsets.append(subset)

    return subsets


# Listet alle Teilmengen aus den verfügbaren Karten auf, die die gegebene Straße überstechen
#
# h: Liste mit der Anzahl der verfügbaren Karten für jeden Rang (Index entspricht den Rang)
# m: Länge der gegebenen Kombination
# r: Rang der gegebenen Kombination
def _get_subsets_of_streets(h: list, m: int, r: int) -> list:
    # Bedingung für eine Straße
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
                    if subset not in subsets:
                        subsets.append(subset)

    return subsets


# Listet alle Teilmengen aus den verfügbaren Karten auf, die die gegebene Kombination überstechen
#
# h: Liste mit der Anzahl der verfügbaren Karten für jeden Rang (Index entspricht den Rang)
# figure: Typ, Länge und Rang der gegebenen Kombination
def get_subsets(h: list, figure: tuple) -> list:
    t, m, r = figure

    if t == SINGLE:  # Einzelkarte
        subsets = []  # todo

    elif t == PAIR:  # Paar
        subsets = []  # todo

    elif t == TRIPLE:  # Drilling
        subsets = []  # todo

    elif t == STAIR:  # Treppe
        subsets = _get_subsets_of_stairs(h, m, r)

    elif t == FULLHOUSE:  # Fullhouse
        subsets = []  # todo

    elif t == STREET:  # Straße
        subsets = _get_subsets_of_streets(h, m, r)

    elif t == BOMB and m == 4:  # 4er-Bombe
        subsets = []  # todo

    elif t == BOMB and m >= 5:  # Farbbombe
        subsets = []  # todo

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
# h: Liste mit der Anzahl der verfügbaren Karten für jeden Rang (Index entspricht den Rang)
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


# Berechnet die Wahrscheinlichkeit, dass die Hand die gegebene Kombination überstechen kann
#
# h: Liste mit der Anzahl der verfügbaren Karten für jeden Rang (Index entspricht den Rang)
# k: Anzahl der Handkarten
# figure: Typ, Länge und Rang der gegebenen Kombination
# r: Rang der gegebenen Kombination
def prob_of_hand(h: list[int], k: int, figure: tuple) -> float:
    assert 0 <= h[0] <= 1
    assert all(0 <= c <= 4 for c in h[1:])
    n = sum(h)  # Gesamtanzahl der verfügbaren Karten
    assert 0 <= n <= 56
    assert 0 <= k <= 14

    # Vorabprüfung: Sind genügend Karten vorhanden, um die gegebene Kombination zu bilden?
    m = figure[1]
    if n < m or k < m:
        return 0

    # Teilmengen finden, die die gegebene Kombination überstechen
    favorable_subsets = get_subsets(h, figure)
    if len(favorable_subsets) == 0:
        return 0

    # Vereinigungsmengen aus zwei oder mehr Teilmengen bilden
    favorable_unions = union_sets(favorable_subsets, k)

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

def test():  # pragma: no cover
    # # Treppe ohne Phönix
    # ("RK GK BD SD SB RB BB", 6, (4, 6, 12), 3, 7, 0.42857142857142855, "3er-Treppe ohne Phönix"),
    # ("SB RZ R9 G9 R8 G8 B4", 9, (4, 4, 9), 0, 0, 0.0, "2er-Treppe nicht möglich"),
    # ("RK GK BD SD GD R9 B2", 6, (4, 4, 12), 5, 7, 0.7142857142857143, "2er-Treppe aus Fullhouse"),
    # ("Dr GA BA GK BK SD BD", 6, (4, 4, 14), 0, 7, 0.0, "2er-Treppe über Ass"),
    print(f"{prob_of_hand([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 2, 2, 0, 0, 0], 6, (4, 6, 12)):<20} 0.42857142857142855  Treppe 1 ohne Phönix")
    print(f"{prob_of_hand([0, 0, 0, 0, 1, 0, 0, 0, 2, 2, 1, 1, 0, 0, 0, 0, 0], 9, (4, 4, 9)):<20} 0.0                  Treppe 2 ohne Phönix")
    print(f"{prob_of_hand([0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 3, 2, 0, 0, 0], 6, (4, 4, 12)):<20} 0.7142857142857143   Treppe 3 ohne Phönix")
    print(f"{prob_of_hand([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 1, 0], 6, (4, 4, 14)):<20} 0.0                  Treppe 4 ohne Phönix")

    # # Treppe mit Phönix
    # ("Ph GK BK SD SB RB BZ R9", 6, (4, 4, 10), 14, 28, 0.5, "2er-Treppe mit Phönix"),
    # ("Ph GK BK SD SB RB R9", 6, (4, 4, 10), 5, 7, 0.7142857142857143, "2er-Treppe mit Phönix (vereinfacht)"),
    # ("Ph GK BK SD SB R9 S4", 6, (4, 4, 10), 3, 7, 0.42857142857142855, "2er-Treppe mit Phönix (vereinfacht 2)"),
    # ("Ph GK BD SD SB RB BB", 6, (4, 6, 12), 3, 7, 0.42857142857142855, "3er-Treppe mit Phönix"),
    # ("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 4, (4, 4, 9), 13, 210, 0.06190476190476191, "2er-Treppe, Phönix übrig"),
    print(f"{prob_of_hand([0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 1, 2, 0, 0, 1], 6, (4, 4, 10)):<20} 0.5                  Treppe 1 mit Phönix")
    print(f"{prob_of_hand([0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 2, 1, 2, 0, 0, 1], 6, (4, 4, 10)):<20} 0.7142857142857143   Treppe 2 mit Phönix")
    print(f"{prob_of_hand([0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 1, 2, 0, 0, 1], 6, (4, 4, 10)):<20} 0.42857142857142855  Treppe 3 mit Phönix")
    print(f"{prob_of_hand([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 2, 1, 0, 0, 1], 6, (4, 6, 12)):<20} 0.42857142857142855  Treppe 4 mit Phönix")
    print(f"{prob_of_hand([0, 0, 0, 0, 1, 0, 0, 0, 2, 3, 2, 1, 0, 0, 0, 0, 1], 4, (4, 4, 9)):<20} 0.06190476190476191  Treppe 5 mit Phönix")

    # Straßen
    print(f"{prob_of_hand([0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0], 6, (6, 5, 10)):<20} 0.42857142857142855  Straße 1 ohne Joker")
    print(f"{prob_of_hand([0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0], 6, (6, 5, 10)):<20} 0.15476190476190477  Straße 2 ohne Joker")
    print(f"{prob_of_hand([0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0], 6, (6, 5, 10)):<20} 0.17857142857142858  Straße 3 ohne Joker")
    print(f"{prob_of_hand([0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 0, 0, 0], 6, (6, 5, 10)):<20} 0.21428571428571427  Straße 4 ohne Joker")
    print(f"{prob_of_hand([0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 0, 0, 0], 6, (6, 5, 10)):<20} 1.0                  Straße 5 ohne Joker")
    print(f"{prob_of_hand([0, 0, 1, 0, 1, 0, 0, 3, 3, 3, 3, 3, 0, 1, 0, 0, 0], 6, (6, 5, 10)):<20} 0.10471881060116355  Straße 6 ohne Joker")
    print(f"{prob_of_hand([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1], 6, (6, 5, 10)):<20} 1.0                  Straße 1 mit Joker")
    print(f"{prob_of_hand([0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 1], 6, (6, 5, 10)):<20} 1.0                  Straße 2 mit Joker")
    print(f"{prob_of_hand([0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1], 6, (6, 5, 10)):<20} 0.5595238095238095   Straße 3 mit Joker")


# noinspection DuplicatedCode
if __name__ == "__main__":  # pragma: no cover
    number = 1
    print(f"Gesamtzeit: {timeit(lambda: test(), number=number)*1000/number:.6f} ms")
