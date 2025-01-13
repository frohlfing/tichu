import math
from timeit import timeit


# Listet alle Teilmengen aus den verfügbaren Karten auf, die die gegebene Kombinationen entsprechen
#
# h: Liste mit der Anzahl der verfügbaren Karten für jeden Rang (Index entspricht den Rang)
# m: Länge der gegebenen Kombination
# r: Rang der gegebenen Kombination
def build_favorable_sets(h: list, m: int, r: int) -> list:
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
        if h[0]:  # Phönix vorhanden?
            for r_joker in range(r_start, r_end):
                if all(h[i] >= (1 if i == r_joker else 2) for i in range(r_start, r_end)):
                    subset = {i: 1 if i == r_joker else 2 for i in range(r_start, r_end)}
                    subset[0] = 1
                    if subset not in subsets:
                        subsets.append(subset)

    return subsets


# Bildet Vereinigungsmengen aus zwei oder mehr Teilmengen
#
# Der erste Eintrag der zurückgegebenen Liste listet die gegebenen Teilmengen auf.
# Der zweite Eintrag listet die Vereinigungsmengen auf, die aus zwei Teilmengen bestehen.
# Der dritte Eintrag listet die auf, die aus drei Teilmengen bestehen, usw.
#
# subsets: Liste von Teilmengen
# minimums: Erforderliche Mindestanzahl der Karten
# k: Maximal erlaubte Länge der Vereinigungsmenge
def build_unions(subsets: list, k: int) -> list[list]:
    length = len(subsets)
    unions = [subsets] + [[] for _ in range(length - 1)]

    def _build_unions(subset: dict, start: int, c: int):
        # subset: Vereinigungsmenge, zu der eine weitere Teilmenge hinzugefügt werden soll
        # start: subsets[start] ist die hinzuzufügende Teilmenge
        # c: Anzahl Teilmengen, die bereits in der Vereinigungsmenge sind
        for j in range(start, length):
            keys = set(subset.keys()).union(subsets[j].keys())
            union = {key: max(subset[key] if key in subset else 0, subsets[j][key] if key in subsets[j] else 0) for key in keys}
            if sum(union.values()) <= k:
                unions[c - 1].append(union)
                _build_unions(union, j + 1, c + 1)
        return unions

    for i in range(length):
        _build_unions(subsets[i], i + 1, 2)

    return unions


# Zählt die Anzahl jeder eindeutigen Teilmenge
# Zurückgegeben wird eine Liste mit Tupeln, wobei jedes Tupel eine eindeutige Teilmenge und dessen Anzahl enthält
def count_sets(subsets: list) -> list:
    unique_sets = []
    counts = []
    for subset in subsets:
        if subset in unique_sets:
            counts[unique_sets.index(subset)] += 1
        else:
            unique_sets.append(subset)
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
    def _hypergeom(index: int, n_remain, k_remain) -> int:
        r = keys[index]  # der aktuell zu untersuchende Kartenrang
        n_fav = h[r]  # Anzahl der verfügbaren Karten mit diesem Rang
        c_min = subset[r]  # erforderliche Anzahl Karten mit diesem Rang
        result = 0
        for c in range(c_min, n_fav + 1):
            if k_remain < c:
                break
            if index + 1 < length:
                result += math.comb(n_fav, c) * _hypergeom(index + 1, n_remain - n_fav, k_remain - c)
            else:
                result += math.comb(n_fav, c) * math.comb(n_remain - n_fav, k_remain - c)
        return result

    keys = list(subset)
    length = len(subset)
    return _hypergeom(0, sum(h), k)


# Berechnet die Wahrscheinlichkeit, dass die Hand die gegebene Kombination überstechen kann
#
# h: Liste mit der Anzahl der verfügbaren Karten für jeden Rang (Index entspricht den Rang)
# k: Anzahl der Handkarten
# m: Länge der gegebenen Kombination
# r: Rang der gegebenen Kombination
def calc(h: list[int], k: int, m: int, r: int) -> float:
    assert 0 <= h[0] <= 1
    assert all(0 <= c <= 4 for c in h[1:])
    n = sum(h)  # Gesamtanzahl der verfügbaren Karten
    assert 0 <= n <= 56
    assert 0 <= k <= 14

    # Vorabprüfung: Sind genügend Karten vorhanden, um die Kombination zu bilden?
    if n < m or k < m:
        return 0

    # günstige Teilmengen finden
    favorable_subsets = build_favorable_sets(h, m, r)
    if len(favorable_subsets) == 0:
        return 0

    # Vereinigungsmengen aus zwei oder mehr Teilmengen bilden
    favorable_unions = build_unions(favorable_subsets, k)

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

def test():
    # # Treppe ohne Phönix
    # ("RK GK BD SD SB RB BB", 6, (4, 6, 12), 3, 7, 0.42857142857142855, "3er-Treppe ohne Phönix"),
    # ("SB RZ R9 G9 R8 G8 B4", 9, (4, 4, 9), 0, 0, 0.0, "2er-Treppe nicht möglich"),
    # ("RK GK BD SD GD R9 B2", 6, (4, 4, 12), 5, 7, 0.7142857142857143, "2er-Treppe aus Fullhouse"),
    print(f"{calc([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 2, 2, 0], 6, 6, 12):<20} 0.42857142857142855  Testfall 1 ohne Joker")
    print(f"{calc([0, 0, 0, 0, 1, 0, 0, 0, 2, 2, 1, 1, 0, 0, 0], 9, 4,  9):<20} 0.0                  Testfall 2 ohne Joker")
    print(f"{calc([0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 3, 2, 0], 6, 4, 12):<20} 0.7142857142857143   Testfall 3 ohne Joker")

    # # Treppe mit Phönix
    # ("Ph GK BK SD SB RB BZ R9", 6, (4, 4, 10), 14, 28, 0.5, "2er-Treppe mit Phönix"),
    # ("Ph GK BK SD SB RB R9", 6, (4, 4, 10), 5, 7, 0.7142857142857143, "2er-Treppe mit Phönix (vereinfacht)"),
    # ("Ph GK BK SD SB R9 S4", 6, (4, 4, 10), 3, 7, 0.42857142857142855, "2er-Treppe mit Phönix (vereinfacht 2)"),
    # ("Ph GK BD SD SB RB BB", 6, (4, 6, 12), 3, 7, 0.42857142857142855, "3er-Treppe mit Phönix"),
    # ("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 4, (4, 4, 9), 13, 210, 0.06190476190476191, "2er-Treppe, Phönix übrig"),
    print(f"{calc([1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 1, 2, 0], 6, 4, 10):<20} 0.5                  Testfall 1 mit Joker")
    print(f"{calc([1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 2, 1, 2, 0], 6, 4, 10):<20} 0.7142857142857143   Testfall 2 mit Joker")
    print(f"{calc([1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 1, 2, 0], 6, 4, 10):<20} 0.42857142857142855  Testfall 3 mit Joker")
    print(f"{calc([1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 2, 1, 0], 6, 6, 12):<20} 0.42857142857142855  Testfall 4 mit Joker")
    print(f"{calc([1, 0, 0, 0, 1, 0, 0, 0, 2, 3, 2, 1, 0, 0, 0], 4, 4,  9):<20} 0.06190476190476191  Testfall 5 mit Joker")


# noinspection DuplicatedCode
if __name__ == "__main__":  # pragma: no cover
    number = 1
    print(f"Gesamtzeit: {timeit(lambda: test(), number=number)*1000/number:.6f} ms")
