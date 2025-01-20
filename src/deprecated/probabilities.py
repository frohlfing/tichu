__all__ = "possible_hands_hi", "prob_of_hand"

import itertools
import math
from src.lib.cards import parse_cards, stringify_cards
from src.lib.combinations import SINGLE, PAIR, TRIPLE, STAIR, FULLHOUSE, STREET, BOMB, stringify_figure

# -----------------------------------------------------------------------------
# Wahrscheinlichkeitsberechnung
# -----------------------------------------------------------------------------

# Listet die möglichen Hände auf und markiert, welche eine Kombination hat, die die gegebene überstechen kann
#
# Diese Methode wird nur für Testzwecke verwendet. Je mehr ungespielte Karten es gibt, desto langsamer wird sie.
# Ab ca. 20 ist sie praktisch unbrauchbar.
#
# todo:
#  Falls die gegebene Kombination eine Farbbombe ist, kann sie von einer längeren Farbbombe überstochen werden, was auch berücksichtigt wird.
#  Falls die gegebene Kombination aber keine Farbbombe ist, kann sie von einer beliebigen Farbbombe überstochen werden, was NICHT berücksichtigt wird!
#  Ausnahme: Falls die gegebene Kombination eine Straße ist, wird eine Farbbombe, die einen höheren Rang hat, berücksichtigt.
#
# Beispiel:
# matches, hands = possible_hands(parse_cards("Dr RK GK BB SB RB R2"), 5, (2, 2, 11))
# for match, hand in zip(matches, hands):
#     print(match, stringify_cards(hand))
# print(f"Wahrscheinlichkeit für ein Bubenpärchen: {sum(matches) / len(hands)}")
#
# unplayed_cards: Ungespielte Karten
# k: Anzahl Handkarten
# figure: Typ, Länge, Rang der Kombination
def possible_hands_hi(unplayed_cards: list[tuple], k: int, figure: tuple) -> tuple[list, list]:
    hands = list(itertools.combinations(unplayed_cards, k))
    matches = []
    t, m, r = figure  # type, length, rank
    for hand in hands:
        b = False
        if t == SINGLE:  # Einzelkarte
            if r == 15:  # Drache
                b = False
            elif r < 15:  # bis zum Ass
                b = any(v > r for v, _ in hand)
            else:  # Phönix
                assert r == 16
                b = any(1 < v < 16 for v, _ in hand)
        else:
            for rhi in range(r + 1, 15):
                if t in [PAIR, TRIPLE]:  # Paar oder Drilling
                    b = sum(1 for v, _ in hand if v in [rhi, 16]) >= m

                elif t == STAIR:  # Treppe
                    steps = int(m / 2)
                    if any(v == 16 for v, _ in hand):  # Phönix vorhanden?
                        for j in range(steps):
                            b = all(sum(1 for v, _ in hand if v == rhi - i) >= (1 if i == j else 2) for i in range(steps))
                            if b:
                                break
                    else:
                        b = all(sum(1 for v, _ in hand if v == rhi - i) >= 2 for i in range(steps))

                elif t == FULLHOUSE:  # Fullhouse
                    if any(v == 16 for v, _ in hand):  # Phönix vorhanden?
                        for j in range(2, 15):
                            b = (sum(1 for v, _ in hand if v == rhi) >= (2 if rhi == j else 3)
                                 and any(sum(1 for v2, _ in hand if v2 == r2) >= (1 if r2 == j else 2) for r2 in range(2, 15) if r2 != rhi))
                            if b:
                                break
                    else:
                        b = (sum(1 for v, _ in hand if v == rhi) >= 3
                             and any(sum(1 for v2, _ in hand if v2 == r2) >= 2 for r2 in range(2, 15) if r2 != rhi))

                elif t == STREET:  # Straße
                    # colors = set([c for i in range(m) for v, c in hand if v == rhi - i])  # Auswahl an Farben in der Straße
                    if any(v == 16 for v, _ in hand):  # Phönix vorhanden?
                        for j in range(int(m)):
                            b = all(sum(1 for v, _ in hand if v == rhi - i) >= (0 if i == j else 1) for i in range(m))
                            if b:
                                break
                    # elif len(colors) == 1: # nur eine Auswahl an Farben → wenn eine Straße, dann Farbbombe
                    #     b = False
                    else:
                        b = all(sum(1 for v, _ in hand if v == rhi - i) >= 1 for i in range(m))

                elif t == BOMB and m == 4:  # 4er-Bombe
                    b = sum(1 for v, _ in hand if v == rhi) >= 4

                elif t == BOMB and m >= 5:  # Farbbombe (hier werden zunächst nur Farbbomben gleicher Länge verglichen)
                    b = any(all(sum(1 for v, c in hand if v == rhi - i and c == color) >= 1 for i in range(m)) for color in range(1, 5))
                else:
                    assert False

                if b:
                    break

        # falls die gegebene Kombination keine Bombe ist, kann sie von einer 4er-Bombe überstochen werden
        if not b and t != BOMB:
            for rhi in range(2, 15):
                b = sum(1 for v, _ in hand if v == rhi) >= 4
                if b:
                    break

        # falls die gegebene Kombination eine Farbbombe ist, kann sie von einer längeren Farbbombe überstochen werden
        if not b and t == BOMB and m >= 5:
            m2 = m + 1
            for rhi in range(m2 + 1, r + 1):
                b = any(all(sum(1 for v, c in hand if v == rhi - i and c == color) >= 1 for i in range(m2)) for color in range(1, 5))
                if b:
                    break

        # todo: Farbbombe berücksichtigen
        # # falls die gegebene Kombination keine Farbbombe ist, kann sie von einer beliebigen Farbbombe überstochen werden
        # if not b and not (t == BOMB and m >= 5):
        #     m2 = 5
        #     for rhi in range(m2 + 1, 15):
        #         b = any(all(sum(1 for v, c in hand if v == rhi - i and c == color) >= 1 for i in range(m2)) for color in range(1, 5))
        #         if b:
        #             break

        # oder beide Fälle zusammengefasst:
        # # falls die gegebene Kombination eine Farbbombe ist, kann sie von einer längeren Farbbombe überstochen werden, ansonsten von einer beliebigen
        # if not b:
        #     m2 = m + 1 if t == BOMB and m >= 5 else 5
        #     for rhi in range(m2 + 1, r + 1 if t == BOMB and m >= 5 else 15):
        #         b = any(all(sum(1 for v, c in hand if v == rhi - i and c == color) >= 1 for i in range(m2)) for color in range(1, 5))
        #         if b:
        #             break

        matches.append(b)
    return matches, hands


# todo
# Listet alle Teilmengen aus den verfügbaren Karten auf, die die gegebene Einzelkarte überstechen
#
# h: Verfügbaren Karten als Vektor (Index entspricht den Rang)
# r: Rang der gegebenen Kombination
def _get_subsets_of_single(h: list[int], r: int) -> list[dict]:
    assert 0 <= r <= 16

    subsets = []
    if r == 16:  # Phönix
        for i in range(2, 16):  # Phönix (im Anspiel) zählt 1.5; jede Karte zw. 2 und Drache ist höher
            if h[i] >= 1:
                subsets.append({i: (1, h[i])})

    elif r == 15:  # Drache
        # 4er-Bombe
        for i in range(2, 15):
            if h[i] == 4:
                subsets.append({i: (4, 4)})

    else:  # Hund, Mahjong, 2 bis Ass
        for i in range(r + 1, 17):
            if h[i] >= 1:
                subsets.append({i: (1, h[i])})
        # 4er-Bombe
        for i in range(2, r + 1):
            if h[i] == 4:
                subsets.append({i: (4, 4)})

    return subsets


# todo
# Listet alle Teilmengen aus den verfügbaren Karten auf, die das gegebene Pärchen überstechen
#
# h: Verfügbaren Karten als Vektor (Index entspricht den Rang)
# r: Rang der gegebenen Kombination
def _get_subsets_of_pair(h: list[int], r: int) -> list[dict]:
    assert 2 <= r <= 14

    subsets = []
    for i in range(r + 1, 15):
        # ohne Phönix
        if h[i] >= 2:
            subsets.append({i: (2, h[i])})

        # mit Phönix
        if h[16] and h[i] >= 1:
            subsets.append({i: (1, h[i]), 16: (1, 1)})

    # 4er-Bombe
    for i in range(2, r + 1):
        if h[i] == 4:
            subsets.append({i: (4, 4)})

    return subsets


# todo
# Listet alle Teilmengen aus den verfügbaren Karten auf, die das gegebene Drilling überstechen
#
# h: Verfügbaren Karten als Vektor (Index entspricht den Rang)
# r: Rang der gegebenen Kombination
def _get_subsets_of_triple(h: list[int], r: int) -> list[dict]:
    assert 2 <= r <= 14

    subsets = []
    for i in range(r + 1, 15):
        # ohne Phönix
        if h[i] >= 3:
            subsets.append({i: (3, h[i])})

        # mit Phönix
        if h[16] and h[i] >= 2:
            subsets.append({i: (2, h[i]), 16: (1, 1)})

    # 4er-Bombe
    for i in range(2, r + 1):
        if h[i] == 4:
            subsets.append({i: (4, 4)})

    return subsets


# todo
# Listet alle Teilmengen aus den verfügbaren Karten auf, die die gegebene Treppe überstechen
#
# h: Verfügbaren Karten als Vektor (Index entspricht den Rang)
# m: Länge der gegebenen Kombination
# r: Rang der gegebenen Kombination
def _get_subsets_of_stairs(h: list[int], m: int, r: int) -> list[dict]:
    assert m % 2 == 0
    assert 4 <= m <= 14
    steps = int(m / 2)
    assert steps + 1 <= r <= 14

    subsets = []
    for r_start in range((r + 1) - steps + 1, 15 - steps + 1):
        r_end = r_start + steps  # exklusiv

        # ohne Phönix
        if all(h[i] >= 2 for i in range(r_start, r_end)):
            subsets.append({i: (2, h[i]) for i in range(r_start, r_end)})

        # mit Phönix
        if h[16]:  # Phönix vorhanden?
            for r_pho in range(r_start, r_end):
                if all(h[i] >= (1 if i == r_pho else 2) for i in range(r_start, r_end)):
                    subset = {i: (1, h[i]) if i == r_pho else (2, h[i]) for i in range(r_start, r_end)}
                    subset[16] = (1, 1)
                    subsets.append(subset)

    # 4er-Bombe
    for i in range(2, 15):
        if h[i] == 4:
            subsets.append({i: (4, 4)})

    return subsets


# todo
# Listet alle Teilmengen aus den verfügbaren Karten auf, die das gegebene Fullhouse überstechen
#
# h: Verfügbaren Karten als Vektor (Index entspricht den Rang)
# r: Rang der gegebenen Kombination
def _get_subsets_of_fullhouse(h: list[int], r: int) -> list[dict]:
    assert 2 <= r <= 14

    subsets = []
    for i in range(r + 1, 15):
        # ohne Phönix
        if h[i] >= 3:
            for j in range(2, 15):
                if i != j and h[j] >= 2:
                    subsets.append({i: (3, h[i]), j: (2, h[j])})

        # mit Phönix im Pärchen
        if h[16] and h[i] >= 3:
            for j in range(2, 15):
                if i != j and h[j] >= 1:
                    subsets.append({i: (3, h[i]), j: (1, h[j]), 16: (1, 1)})


        # mit Phönix im Drilling
        if h[16] and h[i] >= 2:
            for j in range(2, 15):
                if i != j and h[j] >= 2:
                    subsets.append({i: (2, h[i]), j: (2, h[j]), 16: (1, 1)})

    # 4er-Bombe
    for i in range(2, 15):
        if h[i] == 4:
            subsets.append({i: (4, 4)})

    return subsets


# Listet alle möglichen Bedingungen für eine Straße auf
#
# Die Bedingungen schließen sich gegenseitig aus!
# Eine Bedingung wird als Dictionary beschrieben, wobei der Key der Rang und der Wert die Anzahl (Min, Max) ist.
#
# h: Verfügbaren Karten als Vektor (Index entspricht den Rang)
# m: Länge der Kombination
# r_min: niedrigster Rang der Kombination
# r_max: höchster Rang der Kombination
def _get_conditions_for_street(h: list[int], m: int, r_min: int, r_max: int) -> list[dict]:
    assert 5 <= m <= 14
    assert m <= r_min <= 14
    assert r_min <= r_max <= 14
    conditions = []
    remain = {}
    for r in range(r_min, r_max + 1):
        r_start = r - m + 1
        r_end = r + 1  # exklusiv

        # ohne Phönix
        if all(h[i] >= 1 for i in range(r_start, r_end)):  # Karten für die Kombination verfügbar?
            cond = remain.copy()
            for i in range(r_start, r_end):
                cond[i] = (1, h[i])
            conditions.append(cond)
            remain[r_start] = (0, 0)  # ausschließendes Kriterium für die restlichen Bedingungen

        # mit Phönix
        if h[16]:
            for j in range(r_start + (1 if r < 14 else 0), r_end):  # Rang, den der Phönix ersetzt
                if all(h[i] >= 1 for i in range(r_start, r_end) if i != j):  # Karten für die Kombination verfügbar?
                    cond = remain.copy()
                    for i in range(r_start, r_end):
                        cond[i] = (0, 0) if i == j else (1, h[i])
                    cond[16] = (1, 1)
                    conditions.append(cond)
                    remain[r_start] = (0, 0)  # ausschließendes Kriterium für die restlichen Bedingungen

    return conditions


# Listet alle möglichen Bedingungen für eine 4er-Bombe auf
#
# Die Bedingungen schließen sich gegenseitig aus!
# Eine Bedingung wird als Dictionary beschrieben, wobei der Key der Rang und der Wert die Anzahl (Min, Max) ist.
#
# h: Verfügbaren Karten als Vektor (Index entspricht den Rang)
# r_min: niedrigster Rang der Kombination
# r_max: höchster Rang der Kombination
def _get_conditions_for_4_bomb(h: list[int], r_min: int, r_max: int) -> list[dict]:
    assert 2 <= r_min <= 14
    assert r_min <= r_max <= 14
    conditions = []
    remain = {}

    for r in range(r_min, r_max + 1):
        if h[r] == 4:  # Karten für die Kombination verfügbar?
            cond = remain.copy()
            cond[r] = (4, 4)
            conditions.append(cond)
            remain[r] = (0, 3)  # ausschließendes Kriterium für die restlichen Bedingungen

    return conditions


# todo
# Listet alle Teilmengen aus den verfügbaren Karten auf, die die gegebene Farbbombe überstechen
#
# h: Verfügbaren Karten als Vektor (listet alle 56 Karten auf - nicht nur den Rang!)
# m: Länge der gegebenen Kombination
# r: Rang der gegebenen Kombination
def _get_subsets_of_color_bomb(h: list[int], m: int, r: int) -> list[dict]:
    assert 5 <= m <= 13
    assert m + 1 <= r <= 14

    subsets = []
    for r_start in range((r + 1) - m + 1, 14 - m + 2):
        r_end = r_start + m  # exklusiv
        for color in range(4):
            offset = 13 * color
            if all(h[i] == 1 for i in range(r_start + offset, r_end + offset)):
                subsets.append({i: (1, 1) for i in range(r_start + offset, r_end + offset)})

    # eine Farbbombe schlägt jede kürzere Farbbombe
    m2 = m + 1
    for r_start in range(2, r - m2 + 2):
        r_end = r_start + m2  # exklusiv
        for color in range(4):
            offset = 13 * color
            if all(h[i] == 1 for i in range(r_start + offset, r_end + offset)):
                subsets.append({i: (1, 1) for i in range(r_start + offset, r_end + offset)})

    return subsets


# Listet alle möglichen Bedingungen für eine Kombination auf, die die gegebene übersticht
#
# Die Bedingungen schließen sich gegenseitig aus!
# Eine Bedingung wird als Dictionary beschrieben, wobei der Key der Rang und der Wert die Anzahl (Min, Max) ist.
#
# h: Verfügbaren Karten als Vektor
# figure: Typ, Länge und Rang der gegebenen Kombination
def get_conditions(h: list[int], figure: tuple) -> list[dict]:
    t, m, r = figure

    if t == SINGLE:  # Einzelkarte
        conditions = _get_subsets_of_single(h, r)

    elif t == PAIR:  # Paar
        conditions = _get_subsets_of_pair(h, r)

    elif t == TRIPLE:  # Drilling
        conditions = _get_subsets_of_triple(h, r)

    elif t == STAIR:  # Treppe
        conditions = _get_subsets_of_stairs(h, m, r)

    elif t == FULLHOUSE:  # Fullhouse
        conditions = _get_subsets_of_fullhouse(h, r)

    elif t == STREET:  # Straße
        conditions = _get_conditions_for_street(h, m, r + 1, 14)

    elif t == BOMB:  # Bombe
        if m == 4:
            conditions = _get_conditions_for_4_bomb(h, r + 1, 14)
        else:
            conditions = _get_subsets_of_color_bomb(h, m, r)

    else:
        assert False

    return conditions


# Erzeugt die Bedingung für die Schnittmenge zweier Teilmengen
#
# Falls die Kombinationen dieser Schnittmenge nicht auf der Hand sein können, wird ein leeres Dictionary zurückgegeben.
#
# cond1: Bedingung für Teilmenge 1
# cond2: Bedingung für Teilmenge 2
# k: Anzahl Handkarten
def _get_condition_for_intersection(cond1: dict, cond2: dict, k: int) -> dict:
    keys = set(cond1.keys()).union(cond2.keys())
    union_set = {}
    c_min_total = 0
    for key in keys:
        v1 = cond1.get(key, (0, 4))
        v2 = cond2.get(key, (0, 4))
        c_min = max(v1[0], v2[0])  # Mindestanzahl notwendiger Karten für Schnittmenge
        c_max = min(v1[1], v2[1])  # Maximalanzahl notwendiger Karten für Schnittmenge
        if c_min > c_max:
            return {}  # keine Überschneidung
        c_min_total += c_min
        if c_min_total > k:
            return {}  # zu viele Karten notwendig, um beide Kombinationen gleichzeit auf der Hand zu haben
        union_set[key] = (c_min, c_max)
    return union_set


# Erzeugt die Bedingung für die Schnittmenge zweier Teilmengen
#
# Es werden alle Bedingungen für Teilmenge 1 mit allen Bedingungen für Teilmenge 2 kombiniert und jeweils die
# Bedingung für die Schnittmenge berechnet. Falls Kombinationen dieser Schnittmenge auf der Hand sein können,
# wird die kombinierte Bedingung aufgelistet.
#
# conditions1: Liste mit Bedingungen für Teilmenge 1
# conditions2: Liste mit Bedingungen für Teilmenge 2
# k: Anzahl Handkarten
def get_conditions_for_intersection(conditions1: list[dict], conditions2: list[dict], k: int) -> list[dict]:
    conditions = []
    for cond1 in conditions1:
        for cond2 in conditions2:
            cond_intersect = _get_condition_for_intersection(cond1, cond2, k)
            if cond_intersect:
                conditions.append(cond_intersect)
    return conditions


# Bildet Vereinigungsmengen aus zwei oder mehr Mengen
#
# Der erste Eintrag der zurückgegebenen Liste listet die gegebenen Ursprungsmengen auf.
# Der zweite Eintrag listet die Vereinigungsmengen auf, die aus zwei Ursprungsmengen bestehen.
# Der dritte Eintrag listet die auf, die aus drei Ursprungsmengen bestehen, usw.
#
# sets: Liste von Mengen (Ursprungsmengen)
# k: Maximal erlaubte Länge der Vereinigungsmenge
def union_sets(sets: list[dict], k: int) -> list[list[dict]]:
    length = len(sets)
    result = [sets] + [[] for _ in range(length - 1)]
    def _build_unions(s: dict, start: int, c: int):
        # s: Vereinigungsmenge, zu der eine weitere Ursprungsmenge hinzugefügt werden soll
        # start: sets[start] ist die hinzuzufügende Ursprungsmenge
        # c: Anzahl Teilmengen, die bereits in der Vereinigungsmenge sind
        for j in range(start, length):
            keys = set(s.keys()).union(sets[j].keys())
            union = {key: (
                max(s[key][0] if key in s else 0, sets[j][key][0] if key in sets[j] else 0),
                min(s[key][1] if key in s else 4, sets[j][key][1] if key in sets[j] else 4)) for key in keys}
            if sum(c_min for c_min, c_max in union.values()) <= k:
                result[c - 1].append(union)
                _build_unions(union, j + 1, c + 1)

        return result

    for i in range(length):
        _build_unions(sets[i], i + 1, 2)

    return result


# Zählt die Anzahl jeder eindeutigen Menge
# Zurückgegeben wird eine Liste mit Tupeln, wobei jedes Tupel eine eindeutige Menge und dessen Anzahl enthält
def count_sets(sets: list[dict]) -> list[tuple[dict, int]]:
    unique_sets = []
    counts = []
    for s in sets:
        if s in unique_sets:
            counts[unique_sets.index(s)] += 1
        else:
            unique_sets.append(s)
            counts.append(1)
    return list(zip(unique_sets, counts))


# # Hypergeometrische Verteilung
# #
# # Zurückgegeben wird die Anzahl der Kombinationen in der gegebenen Teilmenge.
# #
# # cond: Bedingung für die Teilmenge
# # h: Verfügbaren Karten als Vektor
# # k: Anzahl der Handkarten
# def hypergeom(cond: dict, h: list[int], k: int) -> int:
#     keys = list(cond)
#     length = len(cond)
#     n = sum(h)
#
#     # Tabelle dp[rank][n_remain][k_remain], um Teilergebnisse zu speichern (dynamische Programmierung)
#     dp = [[[0] * (k + 1) for _ in range(n + 1)] for _ in range(length + 1)]
#
#     # Basisfall: Wenn keine Karten übrig sind, ist es genau eine Möglichkeit (leere Menge)
#     for n_remain in range(n + 1):
#         dp[length][n_remain][0] = 1
#
#     # Iterative Berechnung
#     for index in range(length - 1, -1, -1):
#         r = keys[index]
#         c_min, c_max = cond[r]
#         assert 0 <= c_min <= h[r]
#         assert c_min <= c_max <= h[r]
#
#         for n_remain in range(n + 1):
#             for k_remain in range(k + 1):
#                 result = 0
#                 for c in range(c_min, c_max + 1):
#                     if c > h[r] or k_remain < c or n_remain < c:
#                         continue
#                     result += math.comb(h[r], c) * dp[index + 1][n_remain - c][k_remain - c]
#                 dp[index][n_remain][k_remain] = result
#
#     return dp[0][n][k]


# Hypergeometrische Verteilung
#
# Zurückgegeben wird die Anzahl der Kombinationen in der gegebenen Teilmenge.
#
# cond: Bedingung für die Teilmenge
# h: Verfügbaren Karten als Vektor
# k: Anzahl der Handkarten
def hypergeom(cond: dict, h: list[int], k: int) -> int:
    def _comb(index: int, n_remain, k_remain) -> int:
        r = keys[index]  # der aktuell zu untersuchende Kartenrang
        c_min, c_max = cond[r]  # erforderliche Anzahl Karten mit diesem Rang
        assert 0 <= c_min <= h[r]
        assert c_min <= c_max <= h[r]
        result = 0
        for c in range(c_min, c_max + 1):
            if k_remain < c:
                break
            if index + 1 < length:
                #print(math.comb(h[r], c), end=" ")
                result += math.comb(h[r], c) * _comb(index + 1, n_remain - h[r], k_remain - c)
            else:
                #print(math.comb(h[r] * math.comb(n_remain - h[r], k_remain - c), c))
                result += math.comb(h[r], c) * math.comb(n_remain - h[r], k_remain - c)
        return result

    keys = list(cond)
    length = len(cond)
    return _comb(0, sum(h), k)


# Zählt die möglichen Kombinationen, die mindestens eine der gegebenen Vereinigungsmengen beinhalten
#
# list_of_unions: Liste der Vereinigungsmengen (der Index ist die Anzahl der Ursprungsmengen)
# h: Verfügbaren Karten als Vektor
# k: Anzahl der Handkarten
def count_combinations(list_of_unions: list[list[dict]], h: list[int], k: int) -> int:
    matches = 0

    # für jede Vereinigungsmengen die möglichen Kombinationen zählen
    for j, unions in enumerate(list_of_unions):
        number_of_subsets_in_union = j + 1  # Anzahl der Teilmengen, die jede der aktuellen Vereinigungsmengen umfassen
        for union, c in count_sets(unions):
            # Hypergeometrische Verteilung
            matches_part = hypergeom(union, h, k) * c

            # Prinzip der Inklusion und Exklusion
            if number_of_subsets_in_union % 2 == 1:
                matches += matches_part  # inklusion bei ungerade Anzahl an Teilmengen
            else:
                matches -= matches_part  # exklusion bei gerade Anzahl an Teilmengen

    return matches

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


# Listet alle Teilmengen aus den verfügbaren Karten auf, die eine Farbbombe haben
#
# h: Verfügbaren Karten als Vektor (listet alle 56 Karten auf - nicht nur den Rang!)
def get_subsets_of_any_color_bomb(h: list[int]) -> list[dict]:
    subsets = []
    for r_start in range(2, 10):
        r_end = r_start + 5  # exklusiv
        for color in range(4):
            offset = 13 * color
            if all(h[i] == 1 for i in range(r_start + offset, r_end + offset)):
                subsets.append({i: 1 for i in range(r_start + offset, r_end + offset)})
    return subsets


# Berechnet die Wahrscheinlichkeit, dass die Hand eine Farbbombe hat
#
# cards: Verfügbare Karten
# k: Anzahl der Handkarten
def prob_color_bombs(cards: list[tuple], k: int) -> float:
    n = len(cards)  # Gesamtanzahl der verfügbaren Karten
    assert 0 <= n <= 56
    assert 0 <= k <= 14

    # Sind genügend Karten für eine Farbbombe vorhanden?
    if n < 5 or k < 5:
        return 0

    # die verfügbaren Karten in einen Vektor umwandeln
    h = cards_to_vector(cards)

    # Teilmengen finden, die die gegebene Kombination überstechen
    subsets = get_subsets_of_any_color_bomb(h)
    if len(subsets) == 0:
        return 0

    # Vereinigungsmengen aus zwei oder mehr Teilmengen bilden
    list_of_unions = union_sets(subsets, k)

    # für jede Vereinigungsmengen die möglichen Kombinationen zählen und summieren
    matches = count_combinations(list_of_unions, h, k)
    if matches == 0:
        return 0

    # Gesamtanzahl der möglichen Kombinationen
    total = math.comb(n, k)

    # Wahrscheinlichkeit
    return matches / total


# Berechnet die Wahrscheinlichkeit, dass die Hand die gegebene Kombination überstechen kann
#
# todo:
#  Falls die gegebene Kombination eine Farbbombe ist, kann sie von einer längeren Farbbombe überstochen werden, was auch berücksichtigt wird.
#  Falls die gegebene Kombination aber keine Farbbombe ist, kann sie von einer beliebigen Farbbombe überstochen werden, was NICHT berücksichtigt wird!
#  Ausnahme: Falls die gegebene Kombination eine Straße ist, wird eine Farbbombe, die einen höheren Rang hat, berücksichtigt.
#
# cards: Verfügbare Karten
# k: Anzahl der Handkarten
# figure: Typ, Länge und Rang der gegebenen Kombination
# r: Rang der gegebenen Kombination
def prob_of_hand(cards: list[tuple], k: int, figure: tuple) -> float:
    n = len(cards)  # Gesamtanzahl der verfügbaren Karten
    assert k <= n <= 56
    assert 0 <= k <= 14

    # die verfügbaren Karten in einen Vektor umwandeln
    t, m, _r = figure
    if t == BOMB and m >= 5:  # Farbbombe
        h = cards_to_vector(cards)
    else:
        h = ranks_to_vector(cards)  # wenn es keine Farbbombe ist, sind nur die Ränge der Karten von Interesse

    #print(h)

    # Bedingungen für eine Kombination auflisten, die die gegebene übersticht
    conditions = get_conditions(h, figure)

    # Anzahl Kombinationen mittels hypergeometrische Verteilung ermitteln
    matches = 0
    for cond in conditions:
        matches_part = hypergeom(cond, h, k)
        #print(cond, matches_part)
        matches += matches_part

    # Anzahl der 4er-Bomben hinzufügen
    if t != BOMB:
        conditions_bomb = _get_conditions_for_4_bomb(h, 2, 14)
        for cond in conditions_bomb:
            matches += hypergeom(cond, h, k)
        # die Schnittmenge wieder abziehen (Prinzip der Inklusion und Exklusion)
        conditions_intersection = get_conditions_for_intersection(conditions, conditions_bomb, k)
        for cond in conditions_intersection:
            matches -= hypergeom(cond, h, k)
        assert matches >= 0

    if matches == 0:
        return 0

    # Gesamtanzahl der möglichen Kombinationen
    total = math.comb(n, k)

    # Wahrscheinlichkeit
    p = matches / total
    return p


# -----------------------------------------------------------------------------
# Test
# -----------------------------------------------------------------------------

def inspect(cards, k, figure, verbose=True):  # pragma: no cover
    print(f"Kartenauswahl: {cards}")
    print(f"Anzahl Handkarten: {k}")
    print(f"Kombination: {stringify_figure(figure)}")

    print("Mögliche Handkarten:")
    matches, hands = possible_hands_hi(parse_cards(cards), k, figure)
    if verbose:
        for match, sample in zip(matches, hands):
            print("  ", stringify_cards(sample), match)
    matches_expected = sum(matches)
    total_expected = len(hands)
    p_expected = (matches_expected / total_expected) if total_expected else "nan"
    print(f"Gezählt:   p = {matches_expected}/{total_expected} = {p_expected}")

    p_actual = prob_of_hand(parse_cards(cards), k, figure)
    print(f"Berechnet: p = {(total_expected * p_actual):.0f}/{total_expected} = {p_actual}")


if __name__ == "__main__":  # pragma: no cover

    #inspect("GA RK GD RB GZ R9 S8", 6, (6, 5, 8))

    # todo Problem: Je größer k, desto langsamer wird es!
    from timeit import timeit
    for k_ in range(5, 10):
        print(f"k={k_}: {timeit(lambda: inspect("GA RK GD RB GZ R9 S8 B7 S6 S5 R4 S3 S2 Ph", k_, (6, 5, 8), verbose=False), number=1) * 1000:.6f} ms")

    # todo Problem: Farbbomben
    # inspect("SB RZ R9 R8 R7 R6", 5, (1, 1, 11))  # Einzelkarte mit Farbbombe
    # inspect("SB RZ R9 R8 R7 R6", 5, (2, 2, 11))  # Pärchen mit Farbbombe
    # inspect("SB RZ R9 R8 R7 R6", 5, (3, 3, 11))  # Drilling mit Farbbombe
    # inspect("SB RZ R9 R8 R7 R6", 5, (4, 4, 11))  # Treppe mit Farbbombe
    # inspect("SB RZ R9 R8 R7 R6", 5, (5, 5, 11))  # Fullhouse mit Farbbombe
    # inspect("SB RZ R9 R8 R7 R6", 5, (6, 5, 11))  # Straße mit Farbbombe
    # inspect("SD RZ R9 R8 R7 R6 R5", 6, (7, 5, 11))  # Farbbombe mit längerer Farbbombe
    # inspect("SK RB RZ R9 R8 R7 R6 S2", 7, (7, 5, 11))  # Farbbombe mit längerer Farbbombe

    #Gezählt: p = 1 / 1 = 1.0
    #Berechnet: p = 1 / 1 = 1.0
    #inspect("GB GZ G9 G8 G7", 5, (6, 5, 10))  # , 0, "5er-Straße ist Farbbombe")

    #Gezählt: p = 2 / 6 = 0.3333333333333333
    #Berechnet: p = 3 / 6 = 0.5555555555555556
    #inspect("GD GB GZ G9 G8 G7", 5, (6, 5, 10))  # , 0, "6er-Straße ist Farbbombe")

    #Gezählt: p = 3 / 7 = 0.42857142857142855
    #Berechnet: p = 4 / 7 = 0.5918367346938775
    #inspect("BK SD BD BB BZ B9 R3", 6, (6, 5, 12))  # , 0.42857142857142855, "5er-Straße mit 2 Damen und mit Farbbombe")

    #Gezählt: p = 73 / 78 = 0.9358974358974359
    #Berechnet: p = 76 / 78 = 0.9794543063773833
    #inspect("BK BD BB BZ B9 RK RD RB RZ R9 G2 G3 G4", 11, (6, 5, 12))  # , 0.9358974358974359, "5er-Straße mit 2 Farbbomben")

    #Gezählt: p = 9 / 1287 = 0.006993006993006993
    #Berechnet: p = 4/1287 = 0.003108003108003108
    #inspect("GA GK GD GB GZ G9 G8 G7 G6 G5 G4 G3 G2", 5, (6, 5, 10))  # , 0.0, "13er-Straße mit Farbbombe")

    #Gezählt:   p = 22/1287 = 0.017094017094017096
    #Berechnet: p = 21/1287 = 0.016317016317016316
    #inspect("GA GK GD GB GZ G9 R8 G7 G6 G5 G4 G3 Ph", 5, (6, 5, 10))  # , 0.017094017094017096, "13er-Straße mit 2 Farbbomben mit Phönix")

    #Gezählt: p = 516 / 1716 = 0.3006993006993007
    #Berechnet: p = 516/1716 = 0.3006993006993007
    #inspect("SK GB GZ G9 G8 G7 RB RZ R9 R8 R7 S4 Ph", 6, (6, 5, 10))  #, 0.3006993006993007, "2 5er-Straßen mit 2 Farbbomben")
    pass
