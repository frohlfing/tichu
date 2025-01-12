# Aufgabenbeschreibung
#
# In einer Urne befinden sich Kugeln. Auf jeder Kugel steht eine Zahl zw. 1 und 14. Jeder Zahl kann bis zu 4-mal vorkommen.
# Die Anzahl der Kugeln in der Urne ist in eine Liste h mit 15 Integer gespeichert
# Beispiel: In der Urne befinden sich noch 10 Kugeln: 3 Kugeln mit der Zahl 5, 2 mit der Zahl 6 und 1 mit der Zahl 7
# Index: 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14
#   h = [0, 0, 0, 0, 0, 3, 2, 1, 0, 0, 0, 0, 0, 0, 0]
#
# Als Besonderheit befindet sich eine Kugel mit einem Stern (*) statt einer Ziffer in der Urne. Das ist ein Joker und kann eine
# beliebige Zahl zw. 2 und 14 ersetzen.
# Zum Beispiel lässt sich aus den Kugeln 5, 6, 7, 8 mit dem Joker die Reihe *(Joker für 4), 5, 6, 7, 8 sowie 5, 6, 7, 8, *(Joker für 9) bilden.
# Ob ein Joker verfügbar ist, steht im ersten Element von h.
#
# Definition Reihe:
# - Eine Reihe sind mehrere Kugeln (mindestens 5) mit Zahlen jeweils um 1 aufsteigend, also z.B. 6, 7, 8, 9, 10
# - Eine Reihe kann angegeben werden mit der Länge m (Anzahl Kugeln) und dem Rang r (die höchste Zahl).
#   Zum Beispiel bilden die Kugeln 3, 4, 5, 6, 7 eine Reihe der Länge m = 5 und dem Rang r = 7
# - Eine höherwertige Reihe ist eine Reihe mit höherem Rang, aber gleicher Länge. Reihen mit unterschiedlicher Längen sind nicht vergleichbar.
#   Zum Beispiel ist Reihe 6, 7, 8, 9, 10 höher als 3, 4, 5, 6, 7.
#
# Es wird eine bestimmte Anzahl (k) Kugeln blind aus der Urne gezogen.
#
# Programmiere mit Python eine Methode, die die Wahrscheinlichkeit berechnet, dass man aus den gezogenen Kugeln eine Reihe bilden kann,
# die höher ist als eine vorgegebene Reihe Länge m und Rang r.

#import itertools
import math
import time
from timeit import timeit


# Findet günstige Teilmengen (Straßen)
def build_favorable_sets(h: list, m: int, r: int) -> list:
    subsets = []
    for r_start in range((r + 1) - m + 1, 15 - m + 1):
        r_end = r_start + m  # exklusiv

        # ohne Joker
        if all(h[i] > 0 for i in range(r_start, r_end)):
            subsets.append(set(range(r_start, r_end)))

        # mit Joker
        if h[0]:  # Joker vorhanden?
            for r_joker in range(max(r_start, 2), r_end):  # max(r_start, 2) berücksichtigt die Ausnahmeregel, dass der Joker die 1 nicht ersetzen kann
                if all(h[i] + (1 if r_joker == i else 0) > 0 for i in range(r_start, r_end)):
                    subset = {i if r_joker != i else 0 for i in range(r_start, r_end)}
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
# k: maximale Länge der Vereinigungsmenge
# return: Vereinigungsmengen unterteilt nach Anzahl Teilmengen, die die Vereinigungsmengen umschließen
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


# sehr langsam!
# def build_unions_slowly(subsets: list, k: int) -> list[list]:
#     unions = [subsets]
#
#     for number_of_subsets_in_union in range(2, len(subsets) + 1):  # Anzahl der Teilmengen, die die Vereinigungsmenge umfasst
#         unions_ = []
#         for subsets_ in itertools.combinations(subsets, number_of_subsets_in_union):  # zu vereinigenden Teilmengen, z.B. [7, 0, 9, 10, 11], [0, 9, 10, 11, 12]
#             union = set().union(*subsets_)  # Vereinigungsmenge, z.B. {0, 7, 9, 10, 11, 12}
#             if len(union) <= k:
#                 unions_.append(union)
#         unions.append(unions_)
#
#     return unions


# Hypergeometrische Verteilung
#
# Zurückgegeben wird die Anzahl der möglichen Kombinationen, die die gegebene Vereinigungsmenge beinhalten.
#
# union: Vereinigungsmenge
# h: Liste mit der Anzahl der Kugeln für jede Zahl (Index entspricht der Zahl, h[0] = Joker)
# n: Gesamtanzahl der Kugeln in der Urne
# k: Anzahl der zu ziehenden Kugeln
def hypergeom(union: list, h: list, n: int, k: int) -> int:
    def _hypergeom(index: int, n_remain, k_remain) -> int:
        # index: union[index] ist die aktuelle Zahl, die untersucht wird
        # n_remain: Verbleibende Kugeln
        # k_remain: Verbleibende zu ziehende Kugeln
        result = 0
        r_cur = union[index]
        for c in range(1, h[r_cur] + 1):
            if k_remain < c:
                break
            if index + 1 < length:
                result += math.comb(h[r_cur], c) * _hypergeom(index + 1, n_remain - h[r_cur], k_remain - c)
            else:
                result += math.comb(h[r_cur], c) * math.comb(n_remain - h[r_cur], k_remain - c)
        return result

    length = len(union)
    return _hypergeom(0, n, k)


# Berechnet die Wahrscheinlichkeit, aus den gezogenen Kugeln eine gültige Reihe zu bilden.
#
# h: Liste mit der Anzahl der Kugeln für jede Zahl (Index entspricht der Zahl, h[0] = Joker)
# k: Anzahl der zu ziehenden Kugeln
# m: Länge der Reihe (Anzahl der Kugeln in der Reihe)
# r: Rang der vorgegebenen Reihe (höchste Zahl der Reihe)
def calc(h: list[int], k: int, m: int, r: int) -> float:
    assert 0 <= h[0] <= 1
    assert all(0 <= c <= 4 for c in h[1:])
    n = sum(h)  # Gesamtanzahl der Kugeln in der Urne
    assert 0 <= n <= 56
    assert 1 <= k <= 14
    assert 5 <= m <= 14
    assert m <= r <= 14

    # Vorabprüfung: Sind genügend Kugeln vorhanden, um eine gültige Reihe zu bilden?
    if n < m or k < m:
        return 0

    # günstige Teilmengen finden
    favorable_subsets = build_favorable_sets(h, m, r)

    # Vereinigungsmengen aus zwei oder mehr Teilmengen bilden
    favorable_unions = build_unions(favorable_subsets, k)

    # für jede Vereinigungsmengen die möglichen Kombinationen zählen
    matches = 0
    for j, unions in enumerate(favorable_unions):
        number_of_subsets_in_union = j + 1  # Anzahl der Teilmengen, die jede der aktuellen Vereinigungsmengen umfassen
        for union in unions:
            union = sorted(union)
            # Hypergeometrische Verteilung
            matches_part = hypergeom(union, h, n, k)
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

def test(v):
    print(f"{calc([0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1], 6, 5, 10):<20} 0.42857142857142855  Testfall 1 ohne Joker")
    print(f"{calc([0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1], 6, 5, 10):<20} 0.15476190476190477  Testfall 2 ohne Joker")
    print(f"{calc([0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0], 6, 5, 10):<20} 0.17857142857142858  Testfall 3 ohne Joker")
    print(f"{calc([0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 0], 6, 5, 10):<20} 0.21428571428571427  Testfall 4 ohne Joker")
    print(f"{calc([0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 0], 6, 5, 10):<20} 1.0                  Testfall 5 ohne Joker")
    print(f"{calc([0, 0, 1, 0, 1, 0, 0, 3, 3, 3, 3, 3, 0, 1, 0], 6, 5, 10):<20} 0.10471881060116355  Testfall 6 ohne Joker")
    print(f"{calc([1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1], 6, 5, 10):<20} 1.0                  Testfall 1 mit Joker")
    print(f"{calc([1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1], 6, 5, 10):<20} 1.0                  Testfall 2 mit Joker")
    print(f"{calc([1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1], 6, 5, 10):<20} 0.5595238095238095   Testfall 3 mit Joker (Version 1)")

# noinspection DuplicatedCode
if __name__ == "__main__":  # pragma: no cover
    number = 1
    print(f"Gesamtzeit: {timeit(lambda: test(1), number=number)*1000/number:.6f} ms")
    print(f"Gesamtzeit: {timeit(lambda: test(2), number=number)*1000/number:.6f} ms")