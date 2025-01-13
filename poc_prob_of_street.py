import math
from timeit import timeit


# Listet alle Teilmengen aus den verfügbaren Karten auf, die die gegebene Kombinationen entsprechen
#
# h: Liste mit der Anzahl der verfügbaren Karten für jeden Rang (Index entspricht den Rang)
# m: Länge der gegebenen Kombination
# r: Rang der gegebenen Kombination
def build_favorable_sets(h: list, m: int, r: int) -> list:
    # Bedingung für eine Straße
    assert 5 <= m <= 14
    assert m <= r <= 14

    subsets = []
    for r_start in range((r + 1) - m + 1, 15 - m + 1):
        r_end = r_start + m  # exklusiv

        # ohne Phönix
        if all(h[i] >= 1 for i in range(r_start, r_end)):
            subsets.append(set(range(r_start, r_end)))

        # mit Phönix
        if h[0]:  # Phönix vorhanden?
            for r_joker in range(max(r_start, 2), r_end):  # max(r_start, 2) berücksichtigt die Ausnahmeregel, dass der Phönix die 1 nicht ersetzen kann
                if all(h[i] + (1 if i == r_joker else 0) >= 1 for i in range(r_start, r_end)):
                    subset = {i if i != r_joker else 0 for i in range(r_start, r_end)}
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
# k: Maximal erlaubte Länge der Vereinigungsmenge
def build_unions(subsets: list, k: int) -> list[list]:
    length = len(subsets)
    unions = [subsets] + [[] for _ in range(length - 1)]

    def _build_unions(subset: set, start: int, c: int):
        # subset: Vereinigungsmenge, zu der eine weitere Teilmenge hinzugefügt werden soll
        # start: subsets[start] ist die hinzuzufügende Teilmenge
        # c: Anzahl Teilmengen, die bereits in der Vereinigungsmenge sind
        for j in range(start, length):
            union = set(subset).union(subsets[j])
            if len(union) <= k:
                unions[c - 1].append(union)
                _build_unions(union, j + 1, c + 1)
        return unions

    for i in range(length):
        _build_unions(subsets[i], i + 1, 2)

    return unions


# Hypergeometrische Verteilung
#
# Zurückgegeben wird die Anzahl der möglichen Kombinationen, die die gegebene Teilmenge beinhalten.
#
# subset: Teilmenge
# h: Liste mit der Anzahl der verfügbaren Karten für jeden Rang (Index entspricht den Rang)
# k: Anzahl der Handkarten
def hypergeom(subset: set, h: list, k: int) -> int:
    def _hypergeom(index: int, n_remain, k_remain) -> int:
        r = subset[index]  # der aktuell zu untersuchende Kartenrang
        n_fav = h[r]  # Anzahl der verfügbaren Karten mit diesem Rang
        result = 0
        for c in range(1, n_fav + 1):
            if k_remain < c:
                break
            if index + 1 < length:
                result += math.comb(n_fav, c) * _hypergeom(index + 1, n_remain - n_fav, k_remain - c)
            else:
                result += math.comb(n_fav, c) * math.comb(n_remain - n_fav, k_remain - c)
        return result

    subset = list(subset)
    length = len(subset)
    return _hypergeom(0, sum(h), k)


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
    print(f"{calc([0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1], 6, 5, 10):<20} 0.42857142857142855  Testfall 1 ohne Joker")
    print(f"{calc([0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1], 6, 5, 10):<20} 0.15476190476190477  Testfall 2 ohne Joker")
    print(f"{calc([0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0], 6, 5, 10):<20} 0.17857142857142858  Testfall 3 ohne Joker")
    print(f"{calc([0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 0], 6, 5, 10):<20} 0.21428571428571427  Testfall 4 ohne Joker")
    print(f"{calc([0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 0], 6, 5, 10):<20} 1.0                  Testfall 5 ohne Joker")
    print(f"{calc([0, 0, 1, 0, 1, 0, 0, 3, 3, 3, 3, 3, 0, 1, 0], 6, 5, 10):<20} 0.10471881060116355  Testfall 6 ohne Joker")
    print(f"{calc([1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1], 6, 5, 10):<20} 1.0                  Testfall 1 mit Joker")
    print(f"{calc([1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1], 6, 5, 10):<20} 1.0                  Testfall 2 mit Joker")
    print(f"{calc([1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1], 6, 5, 10):<20} 0.5595238095238095   Testfall 3 mit Joker")


# noinspection DuplicatedCode
if __name__ == "__main__":  # pragma: no cover
    number = 1
    print(f"Gesamtzeit: {timeit(lambda: test(), number=number)*1000/number:.6f} ms")
