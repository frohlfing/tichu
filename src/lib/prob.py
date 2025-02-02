__all__ = "prob_of_hand",

import itertools
import math
from src.lib.cards import parse_cards, stringify_cards, ranks_to_vector, cards_to_vector
from src.lib.combinations import SINGLE, PAIR, TRIPLE, STAIR, FULLHOUSE, STREET, BOMB, stringify_figure, validate_figure
from src.lib.prob_files import load_table_hi
from time import time
from timeit import timeit

# -----------------------------------------------------------------------------
# Wahrscheinlichkeitsberechnung
# -----------------------------------------------------------------------------

# Berechnet die Wahrscheinlichkeit, dass die Hand die gegebene Farbbombe überstechen kann
# (entweder durch einen höheren Rang, oder durch eine längere Bombe)
#
# Mit m = r = 5 wird die Wahrscheinlichkeit berechnet, dass irgendeine Farbbombe auf der Hand ist.
#
# cards: Verfügbare Karten
# k: Anzahl der Handkarten
# m: Länge der gegebenen Kombination
# r: Rang der gegebenen Kombination
def prob_of_color_bomb(cards: list[tuple], k: int, m: int = 5, r: int = 5, verbose=False) -> float:  # pragma: no cover
    n = len(cards)  # Gesamtanzahl der verfügbaren Karten
    assert k <= n <= 56
    assert 0 <= k <= 14
    assert 5 <= m <= 14
    assert m == r == 5 or m + 1 <= r <= 14

    # Karten in einem Vektor umwandeln (die Werte in h sind 0 oder 1)
    h = cards_to_vector(cards)

    # Hilfstabellen laden
    table = load_table_hi(BOMB, m, verbose)
    table_longer = load_table_hi(BOMB, m + 1, verbose) if m < 14 and r > 5 else [{}, {}]

    # für jede der vier Farben alle Muster der Hilfstabelle durchlaufen und mögliche Kombinationen zählen
    matches = 0
    for color in range(4):
        for r_curr in range(6, 15):
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
                    if verbose:
                        print(f"r={r_curr}, color={color}, case={case}, matches_part={matches_part}")
                    # Anzahl Möglichkeiten, die sich aus den der übrigen Karten ergeben, berechnen und zum Gesamtergebnis addieren
                    matches += matches_part
                    # die Anzahl Möglichkeiten, zwei Bomben gleichzeitig zu haben, müssen wieder abgezogen werden (Prinzip von Inklusion und Exklusion)
                    for color2 in range(color + 1, 4):
                        for r_curr2 in range(6, 15):
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
                                    if verbose:
                                        print(f"r2={r_curr2}, color2={color2}, case2={case2}, matches_part2={matches_part2}")
                                    matches -= matches_part2

    # Wahrscheinlichkeit berechnen
    total = math.comb(n, k)  # Gesamtanzahl der möglichen Kombinationen
    p = matches / total
    return p


# # Berechnet die Wahrscheinlichkeit, dass die Hand eine 4er-Bombe hat
#
# cards: Verfügbare Karten
# k: Anzahl der Handkarten
def prob_of_any_4_bomb(cards: list[tuple], k: int) -> float:  # pragma: no cover
    n = len(cards)  # Gesamtanzahl der verfügbaren Karten
    assert k <= n <= 56
    assert 0 <= k <= 14

    # Anzahl der Karten je Rang zählen
    h = ranks_to_vector(cards)

    # Hilfstabellen laden
    table = load_table_hi(BOMB, 4)

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


# Berechnet die Wahrscheinlichkeit, dass die Hand die gegebene Kombination überstechen kann
#
# Wenn die gegebene Kombination der Phönix ist (d.h. als Einzelkarte), so wird sie als Anspielkarte gewertet.
# Sollte der Phönix nicht die Anspielkarte sein, so muss die vom Phönix gestochene Karte angegeben werden.
#
# cards: Verfügbare Karten
# k: Anzahl der Handkarten
# figure: Typ, Länge und Rang der gegebenen Kombination
def prob_of_hand(cards: list[tuple], k: int, figure: tuple, verbose=False) -> tuple[float, float]:  # pragma: no cover
    n = len(cards)  # Gesamtanzahl der verfügbaren Karten
    assert k <= n <= 56
    assert 0 <= k <= 14
    assert figure == (BOMB, 4, 1) or (figure != (0, 0, 0) and validate_figure(figure))
    t, m, r = figure  # Typ, Länge und Rang der gegebenen Kombination

    # Farbbombe ausrangieren
    if t == BOMB and m >= 5:
        p = prob_of_color_bomb(cards, k, m, r, verbose)
        return p, p

    # Anzahl der Karten je Rang zählen
    h = ranks_to_vector(cards)

    # Sonderbehandlung für Phönix als Einzelkarte
    if t == SINGLE and r == 16:
        # Rang des Phönix anpassen (der Phönix im Anspiel wird von der 2 geschlagen, aber nicht vom Mahjong)
        r = 1  # 1.5 abgerundet
        # Der verfügbare Phönix hat den Rang 15 (14.5 aufgerundet); er würde sich selbst schlagen.
        # Daher degradieren wir den verfügbaren Phönix zu einer Noname-Karte (n bleibt gleich, aber es gibt kein Phönix mehr!).
        h[16] = 0

    # Hilfstabellen laden
    table = load_table_hi(t, m, verbose)

    # alle Muster der Hilfstabelle durchlaufen und mögliche Kombinationen zählen
    matches = 0
    r_end = 16 if t == SINGLE else 15  # exklusiv (Drache + 1 bzw. Ass + 1)
    for pho in range(2 if h[16] and t != BOMB else 1):
        for r_higher in range(r + 1, r_end):
            for case in table[pho][r_higher]:
                if sum(case) + pho > k:
                    continue
                r_start = r_end - len(case)
                # jeweils den Binomialkoeffizienten von allen Rängen im Muster berechnen und multiplizieren
                matches_part = 1
                n_remain = n - h[16]
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
                    if verbose:
                        print(f"r={r_higher}, php={pho}, case={case}, matches={matches_part}")
                    matches += matches_part

    # Wahrscheinlichkeit berechnen
    total = math.comb(n, k)  # Gesamtanzahl der möglichen Kombinationen
    p = matches / total
    if t == BOMB:
        if m == 4:  # 4er-Bombe
            p_color = prob_of_color_bomb(cards, k)  # Wahrscheinlichkeit einer Farbbombe
            p_min = max(p, p_color)
            p_max = min(p + p_color, 1)
            return p_min, p_max
        else:  # Farbbombe
            return p, p

    else:  # keine Bombe
        p_4 = prob_of_any_4_bomb(cards, k)  # Wahrscheinlichkeit einer 4er-Bombe
        p_color = prob_of_color_bomb(cards, k)  # Wahrscheinlichkeit einer Farbbombe
        p_min = max([p, p_4, p_color])
        p_max = min(p + p_4 + p_color, 1)
        return p_min, p_max


# -----------------------------------------------------------------------------
# Test
# -----------------------------------------------------------------------------

# Listet die möglichen Hände auf und markiert, welche eine Kombination hat, die die gegebene überstechen kann
#
# Wenn k größer ist als die Anzahl der ungespielten Karten, werden leere Listen zurückgegeben.
#
# figure wird nicht validiert. So kann auch (BOMB, 5, 5) übergeben werden, um alle Farbbomben zu zählen.
#
# Diese Methode wird nur für Testzwecke verwendet. Je mehr ungespielte Karten es gibt, desto langsamer wird sie.
# Ab ca. 20 ist sie praktisch unbrauchbar.
#
# unplayed_cards: Ungespielte Karten
# k: Anzahl Handkarten
# figure: Typ, Länge, Rang der Kombination
def possible_hands_hi(unplayed_cards: list[tuple], k: int, figure: tuple) -> tuple[list, list]:
    hands = list(itertools.combinations(unplayed_cards, k))  # die Länge der Liste entspricht math.comb(len(unplayed_cards), k)
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

        # falls die gegebene Kombination keine Farbbombe ist, kann sie von einer beliebigen Farbbombe überstochen werden
        if not b and not (t == BOMB and m >= 5):
            m2 = 5
            for rhi in range(m2 + 1, 15):
                b = any(all(sum(1 for v, c in hand if v == rhi - i and c == color) >= 1 for i in range(m2)) for color in range(1, 5))
                if b:
                    break

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


# Ergebnisse untersuchen
def inspect(cards, k, figure, verbose=True):  # pragma: no cover
    print(f"Kartenauswahl: {cards}")
    print(f"Anzahl Handkarten: {k}")
    print(f"Kombination: {stringify_figure(figure)}")
    print("Mögliche Handkarten:")

    time_start = time()
    matches, hands = possible_hands_hi(parse_cards(cards), k, figure)
    if verbose:
        for match, sample in zip(matches, hands):
            print("  ", stringify_cards(sample), match)
    matches_expected = sum(matches)
    total_expected = len(hands)
    p_expected = (matches_expected / total_expected) if total_expected else "nan"
    print(f"Gezählt:   p = {matches_expected}/{total_expected} = {p_expected}"
          f" ({(time() - time_start) * 1000:.6f} ms)")

    time_start = time()
    p_min, p_max = prob_of_hand(parse_cards(cards), k, figure, verbose)
    if p_min == p_max:
        print(f"Berechnet: p = {(total_expected * p_min):.0f}/{total_expected} = {p_min}"
              f" ({(time() - time_start) * 1000:.6f} ms (inkl. Daten laden))")
    else:
        print(f"Berechnet: p = {(total_expected * p_min):.0f}/{total_expected} = {p_min}"
              f" bis {(total_expected * p_max):.0f}/{total_expected} = {p_max}"
              f" ({(time() - time_start) * 1000:.6f} ms (inkl. Daten laden))")
    #assert p_expected == p_actual


def inspect_single():  # pragma: no cover
    print(f"{timeit(lambda: inspect("RB GZ SZ BZ RZ R9 R8 R7", 5, (1, 1, 10), verbose=False), number=1) * 1000:.6f} ms")



def inspect_pair():  # pragma: no cover
    pass


def inspect_triple():  # pragma: no cover
    pass


def inspect_stair():  # pragma: no cover
    print(f"{timeit(lambda: inspect("GB SB RZ GZ BZ SZ", 5, (4, 4, 10), verbose=False), number=1) * 1000:.6f} ms")
    print(f"{timeit(lambda: inspect("GB SB RZ GZ BZ SZ", 5, (4, 4, 11), verbose=False), number=1) * 1000:.6f} ms")

    print(f"{timeit(lambda: inspect("GB RB GZ RZ R9 R8 R7", 5, (4, 4, 11), verbose=False), number=1) * 1000:.6f} ms")
    print(f"{timeit(lambda: inspect("GB RB GZ RZ R9 R8 R7", 5, (4, 4, 12), verbose=False), number=1) * 1000:.6f} ms")

    print(f"{timeit(lambda: inspect("GB RB GZ SZ BZ RZ R9 R8 R7", 5, (4, 4, 10), verbose=False), number=1) * 1000:.6f} ms")
    print(f"{timeit(lambda: inspect("GB RB GZ SZ BZ RZ R9 R8 R7", 5, (4, 4, 11), verbose=False), number=1) * 1000:.6f} ms")
    print(f"{timeit(lambda: inspect("GB RB GZ SZ BZ RZ R9 R8 R7", 6, (4, 4, 10), verbose=False), number=1) * 1000:.6f} ms")
    print(f"{timeit(lambda: inspect("GB RB GZ SZ BZ RZ R9 R8 R7", 6, (4, 4, 11), verbose=False), number=1) * 1000:.6f} ms")


def inspect_fullhouse():  # pragma: no cover
    print(f"{timeit(lambda: inspect("SB RZ GZ R9 G9 R8 G8 B4", 5, (5, 5, 9), verbose=False), number=1) * 1000:.6f} ms")


def inspect_street():  # pragma: no cover
    # print(f"{timeit(lambda: inspect("SB RZ GZ BZ SZ R9", 5, (6, 5, 11), verbose=False), number=1) * 1000:.6f} ms")
    #
    # print(f"{timeit(lambda: inspect("SB RZ R9 R8 R7 R6", 5, (6, 5, 11), verbose=False), number=1) * 1000:.6f} ms")
    # print(f"{timeit(lambda: inspect("GB GZ G9 G8 G7", 5, (6, 5, 10), verbose=False), number=1) * 1000:.6f} ms")
    # print(f"{timeit(lambda: inspect("GD GB GZ G9 G8 G7", 5, (6, 5, 10), verbose=False), number=1) * 1000:.6f} ms")
    # print(f"{timeit(lambda: inspect("BK SD BD BB BZ B9 R3", 6, (6, 5, 12), verbose=False), number=1) * 1000:.6f} ms")
    # print(f"{timeit(lambda: inspect("BK BD BB BZ B9 RK RD RB RZ R9 G2 G3 G4", 11, (6, 5, 12), verbose=False), number=1) * 1000:.6f} ms")
    # print(f"{timeit(lambda: inspect("GA GK GD GB GZ G9 G8 G7 G6 G5 G4 G3 G2", 5, (6, 5, 10), verbose=False), number=1) * 1000:.6f} ms")
    # print(f"{timeit(lambda: inspect("GA GK GD GB GZ G9 R8 G7 G6 G5 G4 G3 Ph", 5, (6, 5, 10), verbose=False), number=1) * 1000:.6f} ms")
    # print(f"{timeit(lambda: inspect("SK GB GZ G9 G8 G7 RB RZ R9 R8 R7 S4 Ph", 6, (6, 5, 10), verbose=False), number=1) * 1000:.6f} ms")

    # Straße mit 4er-Bombe und Farbbombe

    # n = 52, k = 5, figure = (6, 5, 6)
    # Gezählt:   p = 8816/2598960 = 0.0033921260812017117 (42438.135147 ms)
    # Berechnet: p = 8192/2598960 = 0.0031520300427863453 (662.052393 ms (inkl. Daten laden))
    # -> Differenz: 0.00024009603841536635
    print(f"{timeit(lambda: inspect("GA GK GD GB GZ G9 G8 G7 G6 G5 G4 G3 G2 SA SK SD SB SZ S9 S8 S7 S6 S5 S4 S3 S2 RA RK RD RB RZ R9 R8 R7 R6 R5 R4 R3 R2 BA BK BD BB BZ B9 B8 B7 B6 B5 B4 B3 B2", 5, (6, 5, 6), verbose=False), number=1) * 1000:.6f} ms")

    # n = 52, k = 6, figure = (6, 5, 6)
    # Gezählt:   p = 309576/20358520 = 0.015206213418264196 (368347.875834 ms)
    # Berechnet: p = 294912/20358520 = 0.014485925303018097 (670.219183 ms (inkl. Daten laden))
    # -> Differenz:  0.0007202881152460986   (0.0007202881152460986/0.00024009603841536635 == 3)
    print(f"{timeit(lambda: inspect("GA GK GD GB GZ G9 G8 G7 G6 G5 G4 G3 G2 SA SK SD SB SZ S9 S8 S7 S6 S5 S4 S3 S2 RA RK RD RB RZ R9 R8 R7 R6 R5 R4 R3 R2 BA BK BD BB BZ B9 B8 B7 B6 B5 B4 B3 B2", 6, (6, 5, 6), verbose=False), number=1) * 1000:.6f} ms")

    # n = 52, k = 5, figure = (6, 5, 13)
    # Gezählt:   p = 1648/2598960 = 0.0006340997937636593 (17087.398767 ms)
    # Berechnet: p = 1024/2598960 = 0.00039400375534829317 (565.371275 ms (inkl. Daten laden))
    # -> Differenz: 0.00024009603841536618
    print(f"{timeit(lambda: inspect("GA GK GD GB GZ G9 G8 G7 G6 G5 G4 G3 G2 SA SK SD SB SZ S9 S8 S7 S6 S5 S4 S3 S2 RA RK RD RB RZ R9 R8 R7 R6 R5 R4 R3 R2 BA BK BD BB BZ B9 B8 B7 B6 B5 B4 B3 B2", 5, (6, 5, 13), verbose=False), number=1) * 1000:.6f} ms")

    # n = 52, k = 5, figure = (6, 5, 14)
    # Gezählt:   p = 624/2598960 = 0.00024009603841536616 (12652.729511 ms)
    # Berechnet: p = 0/2598960 = 0.0 (541.404486 ms (inkl. Daten laden))
    # -> Differenz: 0.00024009603841536616
    print(f"{timeit(lambda: inspect("GA GK GD GB GZ G9 G8 G7 G6 G5 G4 G3 G2 SA SK SD SB SZ S9 S8 S7 S6 S5 S4 S3 S2 RA RK RD RB RZ R9 R8 R7 R6 R5 R4 R3 R2 BA BK BD BB BZ B9 B8 B7 B6 B5 B4 B3 B2", 5, (6, 5, 14), verbose=False), number=1) * 1000:.6f} ms")


def inspect_4_bomb():  # pragma: no cover
    pass


def inspect_color_bomb():  # pragma: no cover
    print(f"{timeit(lambda: inspect("RK RD RB RZ R9 BD BB BZ B9 B8 B7 S3 S2", 11, (7, 5, 12), verbose=False), number=1) * 1000:.6f} ms")


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


def benchmark_load_data():  # pragma: no cover
    # Ladezeit messen
    print(f"{timeit(lambda: load_table_hi(STREET, 5), number=10) * 1000 / 10:.6f} ms")  # 420 ms
    print(f"{timeit(lambda: load_table_hi(FULLHOUSE, 5), number=10) * 1000 / 10:.6f} ms")  # 420 ms


def report():  # pragma: no cover
    # Anzahl Muster je Tabelle
    table = load_table_hi(STREET, 5)
    print("STREET", len(table[0]), len(table[1]))  # 516570, 1236896

    table = load_table_hi(FULLHOUSE, 5)
    print("FULLHOUSE", sum(len(cases) for cases in table[0].values()), sum(len(cases) for cases in table[1].values()))  # 926393, 151034


if __name__ == "__main__":  # pragma: no cover
    inspect_single()
