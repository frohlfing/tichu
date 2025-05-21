"""
Dieses Modul bietet Funktionen zur Berechnung der Wahrscheinlichkeit, dass höhere Kartenkombinationen
gespielt werden können.
"""

__all__ = "prob_of_higher_combi", "prob_of_higher_combi_or_bomb",

import itertools
import math
from src.lib.cards import parse_cards, stringify_cards, ranks_to_vector, cards_to_vector, Cards
from src.lib.combinations import stringify_figure, validate_figure, CombinationType
from src.lib.prob.tables_hi import load_table_hi
from time import time
from timeit import timeit

# -----------------------------------------------------------------------------
# Wahrscheinlichkeitsberechnung p_high
# -----------------------------------------------------------------------------

# Berechnet die Wahrscheinlichkeit, dass die Hand die gegebene Farbbombe überstechen kann
# (entweder durch einen höheren Rang, oder durch eine längere Bombe).
#
# Mit m = r = 5 wird die Wahrscheinlichkeit berechnet, dass irgendeine Farbbombe auf der Hand ist.
#
# cards: Verfügbare Karten
# k: Anzahl der Handkarten
# m: Länge der gegebenen Farbbombe
# r: Rang der gegebenen Farbbombe
def prob_of_higher_color_bomb(cards: Cards, k: int, m: int = 5, r: int = 5) -> float:
    n = len(cards)  # Gesamtanzahl der verfügbaren Karten
    assert k <= n <= 56
    assert 0 <= k <= 14
    assert 5 <= m <= 14
    assert m == r == 5 or m + 1 <= r <= 14

    debug = False

    # Karten in einem Vektor umwandeln (die Werte in h sind 0 oder 1)
    h = cards_to_vector(cards)

    # Hilfstabellen laden
    table = load_table_hi(CombinationType.BOMB, m)
    table_longer = load_table_hi(CombinationType.BOMB, m + 1) if m < 14 and r > 5 else [{}, {}]

    # für jede der vier Farben alle Muster der Hilfstabelle durchlaufen und mögliche Kombinationen zählen
    matches = 0
    for color in range(4):
        for r_curr in range(6, 15):
            if r_curr <= r and r_curr < m + 2:
                continue
            cases = table[0][r_curr] if r_curr > r else table_longer[0][r_curr]
            for case in cases:
                if sum(case) > k:
                    continue
                r_start = 15 - len(case)
                # jeweils den Binomialkoeffizienten von allen Rängen im Muster berechnen und multiplizieren
                matches_part = 1
                n_remain = n
                k_remain = k
                for i in range(len(case)):
                    if h[color * 13 + r_start + i] < case[i]:
                        matches_part = 0
                        break
                    #matches_part *= math.comb(h[color * 13 + r_start + i], case[i])  # der Binomialkoeffizienten ist hier immer 1
                    n_remain -= h[color * 13 + r_start + i]
                    k_remain -= case[i]
                if matches_part == 1:
                    matches_part = math.comb(n_remain, k_remain)
                    if debug:
                        print(f"r={r_curr}, color={color}, case={case}, matches_part={matches_part}")
                    # Anzahl Möglichkeiten, die sich aus den übrigen Karten ergeben, berechnen und zum Gesamtergebnis addieren
                    matches += matches_part
                    # die Anzahl Möglichkeiten, zwei Bomben gleichzeitig zu haben, müssen wieder abgezogen werden (Prinzip von Inklusion und Exklusion)
                    for color2 in range(color + 1, 4):
                        for r_curr2 in range(6, 15):
                            if r_curr2 <= r and r_curr2 < m + 2:
                                continue
                            cases = table[0][r_curr2] if r_curr2 > r else table_longer[0][r_curr2]
                            for case2 in cases:
                                if sum(case2) > k_remain:
                                    continue
                                r_start2 = 15 - len(case2)
                                matches_part2 = 1
                                n_remain2 = n_remain
                                k_remain2 = k_remain
                                for i in range(len(case2)):
                                    if h[color2 * 13 + r_start2 + i] < case2[i]:
                                        matches_part2 = 0
                                        break
                                    n_remain2 -= h[color2 * 13 + r_start2 + i]
                                    k_remain2 -= case2[i]
                                if matches_part2 == 1:
                                    matches_part2 = math.comb(n_remain2, k_remain2)
                                    if debug:
                                        print(f"r2={r_curr2}, color2={color2}, case2={case2}, matches_part2={matches_part2}")
                                    matches -= matches_part2

    # Wahrscheinlichkeit berechnen
    total = math.comb(n, k)  # Gesamtanzahl der möglichen Kombinationen
    p = matches / total
    return p


# Berechnet die Wahrscheinlichkeit, dass die Hand eine 4er-Bombe hat
#
# cards: Verfügbare Karten
# k: Anzahl der Handkarten
def prob_of_any_4_bomb(cards: Cards, k: int) -> float:
    n = len(cards)  # Gesamtanzahl der verfügbaren Karten
    assert k <= n <= 56
    assert 0 <= k <= 14

    # Anzahl der Karten je Rang zählen.
    h = ranks_to_vector(cards)

    # Hilfstabelle laden
    table = load_table_hi(CombinationType.BOMB, 4)

    # alle Muster der Hilfstabelle durchlaufen und mögliche Kombinationen zählen
    matches = 0
    for r in range(2, 15):
        for case in table[0][r]:
            if sum(case) > k:
                continue
            r_start = 15 - len(case)
            matches_part = 1
            n_remain = n
            k_remain = k
            for i in range(len(case)):
                if h[r_start + i] < case[i]:
                    matches_part = 0
                    break
                matches_part *= math.comb(h[r_start + i], case[i])
                n_remain -= h[r_start + i]
                k_remain -= case[i]
            if matches_part > 0:
                matches += matches_part * math.comb(n_remain, k_remain)

    # Wahrscheinlichkeit berechnen
    total = math.comb(n, k)  # Gesamtanzahl der möglichen Kombinationen
    p = matches / total
    return p


# Berechnet die Wahrscheinlichkeit, dass die Hand die gegebene Kombination überstechen kann, ohne sie zu bomben.
#
# Sonderkarte Phönix:
# Wenn die gegebene Kombination der Phönix ist (d.h. als Einzelkarte), so wird sie als Anspielkarte gewertet.
# Sollte der Phönix nicht die Anspielkarte sein, so muss die vom Phönix gestochene Karte angegeben werden.
#
# Sonderkarte Hund:
# Mit dem Hund als gegebene Kombination wird 1.0 zurückgegeben (man wird "überstochen"; man verliert das
# Anspielrecht).
#
# cards: Verfügbare Karten
# k: Anzahl der Handkarten
# figure: Typ, Länge und Rang der gegebenen Kombination
def prob_of_higher_combi(cards: Cards, k: int, figure: tuple) -> float:
    if k == 0:
        return 0.0
    n = len(cards)  # Gesamtanzahl der verfügbaren Karten
    assert k <= n <= 56
    assert 0 <= k <= 14

    if figure == (1, 1, 0):  # Hund
        return 1.0  # wenn der Hund gespielt wird, verliert man das Anspielrecht (also als ob man überstochen wird)

    assert figure != (0, 0, 0) and validate_figure(figure)
    t, m, r = figure  # Typ, Länge und Rang der gegebenen Kombination

    #debug = True

    # Farbbombe ausrangieren
    if t == CombinationType.BOMB and m >= 5:
        return prob_of_higher_color_bomb(cards, k, m, r)

    # Anzahl der Karten je Rang zählen.
    h = ranks_to_vector(cards)

    # Sonderbehandlung für Phönix als Einzelkarte
    if t == CombinationType.SINGLE and r == 16:
        # Rang des Phönix anpassen (der Phönix im Anspiel wird von der 2 geschlagen, aber nicht vom Mahjong)
        r = 1  # 1.5 abgerundet
        # Der verfügbare Phönix hat den Rang 15 (14.5 aufgerundet); er würde sich selbst schlagen.
        # Daher degradieren wir den verfügbaren Phönix zu einer Noname-Karte (n bleibt gleich, aber es gibt kein Phönix mehr!).
        h[16] = 0

    # Hilfstabellen laden
    table = load_table_hi(t, m)

    # alle Muster der Hilfstabelle durchlaufen und mögliche Kombinationen zählen
    matches = 0
    r_end = 16 if t == CombinationType.SINGLE else 15  # exklusiv (Drache + 1 bzw. Ass + 1)
    for pho in range(2 if h[16] and t != CombinationType.BOMB else 1):
        for r_higher in range(r + 1, r_end):
            for case in table[pho][r_higher]:
                if sum(case) + pho > k:
                    continue
                r_start = r_end - len(case)
                # jeweils den Binomialkoeffizienten von allen Rängen im Muster berechnen und multiplizieren
                matches_part = 1
                n_remain = (n - h[16]) if t != CombinationType.BOMB else n
                k_remain = k - pho
                for i in range(len(case)):
                    if h[r_start + i] < case[i]:
                        matches_part = 0
                        break
                    matches_part *= math.comb(h[r_start + i], case[i])
                    n_remain -= h[r_start + i]
                    k_remain -= case[i]
                if matches_part > 0:
                    # Binomialkoeffizient vom Rest berechnen und mit dem Zwischenergebnis multiplizieren
                    matches_part *= math.comb(n_remain, k_remain)
                    # Zwischenergebnis zum Gesamtergebnis addieren
                    #if debug:
                    #    print(f"r={r_higher}, php={pho}, case={case}, matches={matches_part}")
                    matches += matches_part

    # Wahrscheinlichkeit berechnen
    total = math.comb(n, k)  # Gesamtanzahl der möglichen Kombinationen
    p = matches / total
    return p


# Berechnet die Wahrscheinlichkeit, dass die Hand die gegebene Kombination überstechen oder bomben kann
#
# Sonderkarte Phönix:
# Wenn die gegebene Kombination der Phönix ist (d.h. als Einzelkarte), so wird sie als Anspielkarte gewertet.
# Sollte der Phönix nicht die Anspielkarte sein, so muss die vom Phönix gestochene Karte angegeben werden.
#
# Sonderkarte Hund:
# Mit dem Hund als gegebene Kombination wird 1.0 zurückgegeben (man wird "überstochen"; man verliert das Anspielrecht).
#
# cards: Verfügbare Karten
# k: Anzahl der Handkarten
# figure: Typ, Länge und Rang der gegebenen Kombination
# return: Wahrscheinlichkeit `p_high`
def prob_of_higher_combi_or_bomb(cards: Cards, k: int, figure: tuple) -> tuple[float, float]:
    p_combi = prob_of_higher_combi(cards, k, figure)  # Wahrscheinlichkeit einer höheren Kombination als die gegebene
    t, m, r = figure
    if t == CombinationType.BOMB:
        if m == 4:  # 4er-Bombe
            p_color = prob_of_higher_color_bomb(cards, k)  # Wahrscheinlichkeit einer Farbbombe
            p_min = max(p_combi, p_color)
            p_max = min(p_combi + p_color, 1)
            return p_min, p_max
        else:  # Farbbombe
            return p_combi, p_combi
    else:  # keine Bombe
        p_4 = prob_of_any_4_bomb(cards, k)  # Wahrscheinlichkeit einer 4er-Bombe
        p_color = prob_of_higher_color_bomb(cards, k)  # Wahrscheinlichkeit einer Farbbombe
        p_min = max([p_combi, p_4, p_color])
        p_max = min(p_combi + p_4 + p_color, 1)
        return p_min, p_max


# -----------------------------------------------------------------------------
# Test
# -----------------------------------------------------------------------------

# Listet die möglichen Hände auf und markiert, welche eine Kombination hat, die die gegebene überstechen kann.
#
# Wenn k größer ist als die Anzahl der ungespielten Karten, werden leere Listen zurückgegeben.
#
# Diese Methode wird nur für Testzwecke verwendet. Je mehr ungespielte Karten es gibt, desto langsamer wird die Methode.
# Ab ca. 20 Karten ist sie praktisch unbrauchbar.
#
# unplayed_cards: Ungespielte Karten
# k: Anzahl Handkarten
# figure: Typ, Länge, Rang der Kombination
# with_bombs: Wenn gesetzt, werden auch Möglichkeiten markiert, die die gegebene Kombination bomben können
def possible_hands_hi(unplayed_cards: Cards, k: int, figure: tuple, with_bombs: bool) -> tuple[list, list]:
    hands = list(itertools.combinations(unplayed_cards, k))  # die Länge der Liste entspricht math.comb(len(unplayed_cards), k)
    matches = []
    t, m, r = figure  # type, length, rank
    for hand in hands:
        b = False
        if t == CombinationType.SINGLE:  # Einzelkarte
            if r == 15:  # Drache
                b = False
            elif 1 <= r <= 14:  # vom Mahjong bis zum Ass
                b = any(v > r for v, _ in hand)
            elif r == 0:  # Hund
                b = k > 0  # der Hund gibt das Anspielrecht an den Partner, das zählt so wie gestochen
            else:  # Phönix
                assert r == 16
                b = any(1 < v < 16 for v, _ in hand)
        else:
            for rhi in range(r + 1, 15):  # rhi = Rang größer als der Rang der gegebenen Kombination
                if t in [CombinationType.PAIR, CombinationType.TRIPLE]:  # Paar oder Drilling
                    b = sum(1 for v, _ in hand if v in [rhi, 16]) >= m

                elif t == CombinationType.STAIR:  # Treppe
                    steps = int(m / 2)
                    if any(v == 16 for v, _ in hand):  # Phönix vorhanden?
                        for j in range(steps):
                            b = all(sum(1 for v, _ in hand if v == rhi - i) >= (1 if i == j else 2) for i in range(steps))
                            if b:
                                break
                    else:
                        b = all(sum(1 for v, _ in hand if v == rhi - i) >= 2 for i in range(steps))

                elif t == CombinationType.FULLHOUSE:  # Fullhouse
                    if any(v == 16 for v, _ in hand):  # Phönix vorhanden?
                        for j in range(2, 15):
                            b = (sum(1 for v, _ in hand if v == rhi) >= (2 if rhi == j else 3)
                                 and any(sum(1 for v2, _ in hand if v2 == r2) >= (1 if r2 == j else 2) for r2 in range(2, 15) if r2 != rhi))
                            if b:
                                break
                    else:
                        b = (sum(1 for v, _ in hand if v == rhi) >= 3
                             and any(sum(1 for v2, _ in hand if v2 == r2) >= 2 for r2 in range(2, 15) if r2 != rhi))

                elif t == CombinationType.STREET:  # Straße
                    if any(v == 16 for v, _ in hand):  # Phönix vorhanden?
                        for j in range(int(m)):
                            b = all(sum(1 for v, _ in hand if v == rhi - i) >= (0 if i == j else 1) for i in range(m))
                            if b:
                                break
                    else:
                        b = all(sum(1 for v, _ in hand if v == rhi - i) >= 1 for i in range(m))

                elif t == CombinationType.BOMB and m == 4:  # 4er-Bombe
                    b = sum(1 for v, _ in hand if v == rhi) >= 4

                elif t == CombinationType.BOMB and m >= 5:  # Farbbombe (hier werden zunächst nur Farbbomben gleicher Länge verglichen)
                    b = any(all(sum(1 for v, c in hand if v == rhi - i and c == color) >= 1 for i in range(m)) for color in range(1, 5))
                else:
                    assert False

                if b:
                    break

        # falls die gegebene Kombination eine Farbbombe ist, kann sie von einer längeren Farbbombe überstochen werden
        if not b and t == CombinationType.BOMB and m >= 5:
            m2 = m + 1
            for rhi in range(m2 + 1, r + 1):
                b = any(all(sum(1 for v, c in hand if v == rhi - i and c == color) >= 1 for i in range(m2)) for color in range(1, 5))
                if b:
                    break

        if with_bombs:
            # falls die gegebene Kombination keine Bombe ist, kann sie von einer 4er-Bombe überstochen werden
            if not b and t != CombinationType.BOMB:
                for rhi in range(2, 15):
                    b = sum(1 for v, _ in hand if v == rhi) >= 4
                    if b:
                        break

            # falls die gegebene Kombination keine Farbbombe ist, kann sie von einer beliebigen Farbbombe überstochen werden
            if not b and not (t == CombinationType.BOMB and m >= 5):
                m2 = 5
                for rhi in range(m2 + 1, 15):
                    b = any(all(sum(1 for v, c in hand if v == rhi - i and c == color) >= 1 for i in range(m2)) for color in range(1, 5))
                    if b:
                        break

        matches.append(b)
    return matches, hands


# Ergebnisse untersuchen
def inspect(cards, k, figure, verbose=True):  # pragma: no cover
    print(f"Kartenauswahl: {cards}")
    print(f"Anzahl Handkarten: {k}")
    print(f"Kombination: {stringify_figure(figure)}")
    print("Mögliche Handkarten:")

    time_start = time()
    matches, hands = possible_hands_hi(parse_cards(cards), k, figure, with_bombs=True)
    if verbose:
        for match, sample in zip(matches, hands):
            print("  ", stringify_cards(sample), match)
    matches_expected = sum(matches)
    total_expected = len(hands)
    p_expected = (matches_expected / total_expected) if total_expected else "nan"
    print(f"Gezählt:   p = {matches_expected}/{total_expected} = {p_expected}"
          f" ({(time() - time_start) * 1000:.6f} ms)")

    time_start = time()
    p_min, p_max = prob_of_higher_combi_or_bomb(parse_cards(cards), k, figure)
    if p_min == p_max:
        print(f"Berechnet: p = {(total_expected * p_min):.0f}/{total_expected} = {p_min}"
              f" ({(time() - time_start) * 1000:.6f} ms (inkl. Daten laden))")
    else:
        print(f"Berechnet: p = {(total_expected * p_min):.0f}/{total_expected} = {p_min}"
              f" bis {(total_expected * p_max):.0f}/{total_expected} = {p_max}"
              f" ({(time() - time_start) * 1000:.6f} ms (inkl. Daten laden))")


def inspect_combination():  # pragma: no cover
    #inspect("BK BB BZ B9 B8 B7 B2", 5, (7, 5, 10), verbose=True)
    test = [
        ("Ph SB RB GZ BZ SZ R9 G9 B6 B5 B4 B3 B2 Ma", 14, (1, 1, 11), 0, 0, "foo"),
        #("RA BD BB RZ B9 B2 Ph", 6, (6, 5, 13), 0, 7, "5er-Straße aus 7 Karten mit Phönix (nicht hinten verlängert)"),
        #("SB RZ R9 G9 R8 G8 B4", 0, (1, 1, 0), 0, 1, "Hund, Test 1"),
        #("Dr Hu Ph Ma S4 R3 R2", 1, (1, 1, 0), 6, 7, "Einzelkarte Hund"),
        #("Ph SB RB GZ BZ SZ R9 G9 S9 R8 G8 B4 Hu", 1, (1, 1, 0), 12, 13, "Hund, Test 167"),

    ]
    for cards, k, figure, matches_expected, total_expected, msg in test:
        print(msg)
        inspect(cards, k, figure, verbose=True)


def benchmark():  # pragma: no cover
    # Test auf Geschwindigkeit

    # Straße mit der Länge 5 (hat die meisten Muster, daher nehmen wir diese Länge)
    # n = 14, k = 6, figure = (6, 5, 6)
    # Gezählt:   p = 288/3003 = 0.0959040959040959 (100.065470 ms)
    # Berechnet: p = 288/3003 = 0.0959040959040959 (498.227119 ms (inkl. Daten laden))
    for k_ in range(5, 10):
        if k_ != 6: continue
        print(f"k={k_}: {timeit(lambda: inspect("GA RK GD RB GZ R9 S8 B7 Ph", k_, (6, 5, 9), verbose=False), number=1) * 1000:.6f} ms")
        print(f"k={k_}: {timeit(lambda: inspect("GA RK GD RB GZ R9 S8 B7 S6 S5 R4 S3 S2 Ph", k_, (6, 5, 9), verbose=False), number=1) * 1000:.6f} ms")
        print(f"k={k_}: {timeit(lambda: inspect("GA RK GD RB GZ R9 S8 B7 S6 S5 R4 S3 S2 Ph", k_, (6, 5, 8), verbose=False), number=1) * 1000:.6f} ms")
        print(f"k={k_}: {timeit(lambda: inspect("GA RK GD RB GZ R9 S8 B7 S6 S5 R4 S3 S2 Ph", k_, (6, 5, 6), verbose=False), number=1) * 1000:.6f} ms")

    # Fullhouse
    print(f"{timeit(lambda: inspect("GA RK GD RB GZ RZ SZ B7 S7 R6 S6 S5 R4 B4 G4 S3 S2 Ph", 10, (5, 5, 6), verbose=False), number=1) * 1000:.6f} ms")
    print(f"{timeit(lambda: inspect("GA BA RA RK SK GD RB GZ RZ SZ B7 S7 S5 R4 S3 S2 B4 G4 S3 S2 Ma", 10, (5, 5, 6), verbose=False), number=1) * 1000:.6f} ms")


def report():  # pragma: no cover
    # Anzahl Muster je Tabelle
    table = load_table_hi(CombinationType.STREET, 5)
    print("CombinationType.STREET", len(table[0]), len(table[1]))  # 516570, 1236896

    table = load_table_hi(CombinationType.FULLHOUSE, 5)
    print("CombinationType.FULLHOUSE", sum(len(cases) for cases in table[0].values()), sum(len(cases) for cases in table[1].values()))  # 926393, 151034


if __name__ == "__main__":  # pragma: no cover
    inspect_combination()
