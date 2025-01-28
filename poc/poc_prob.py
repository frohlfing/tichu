import math
from poc.poc_prob_files import load_data_hi
from src.lib.cards import stringify_cards, parse_cards
from src.lib.combinations import stringify_figure, SINGLE, PAIR, TRIPLE, STAIR, FULLHOUSE, STREET, BOMB
from src.lib.probabilities import possible_hands_hi, ranks_to_vector
from time import time
from timeit import timeit


# Berechnet die Wahrscheinlichkeit, dass die Hand die gegebene Treppe überstechen kann
#
# h: Verfügbaren Karten als Vektor (Index entspricht den Rang)
# k: Anzahl Handkarten
# m: Länge der Treppe
# r: Rang der Treppe
def prob_of_stair_hi(h: list[int], k: int, m: int, r, verbose = False) -> float:
    n = sum(h)  # Gesamtanzahl der verfügbaren Karten
    assert k <= n <= 56
    assert 0 <= k <= 14
    assert m % 2 == 0
    assert 4 <= m <= 14
    steps = int(m / 2)
    assert steps + 1 <= r <= 14

    # Muster laden
    # todo: Daten im Speicher halten, so dass nur einmal geladen werden muss
    data = load_data_hi(STAIR, m, True)

    # alle Muster durchlaufen und mögliche Kombinationen zählen
    matches  = 0
    for pho in range(2 if h[16] else 1):
        for case in data[pho]:
            offset = 15 - len(case)
            r_higher = offset + steps - 1
            if r_higher <= r:
                break
            if sum(case) + pho > k:
                continue

            matches_part = 1
            n_remain = n - h[16]
            k_remain = k - pho
            for i in range(len(case)):
                matches_part *= math.comb(h[offset + i], case[i])
                if matches_part == 0:
                    break
                n_remain -= h[offset + i]
                k_remain -= case[i]

            matches_part *= math.comb(n_remain, k_remain)
            if matches_part > 0:
                if verbose:
                    print(f"r={r_higher}, php={pho}, case={case}, matches={matches_part}")
                matches += matches_part

    total = math.comb(n, k)  # Gesamtanzahl der möglichen Kombinationen
    p = matches / total  # Wahrscheinlichkeit
    return p


# Berechnet die Wahrscheinlichkeit, dass die Hand die gegebene Straße überstechen kann
#
# h: Verfügbaren Karten als Vektor (Index entspricht den Rang)
# k: Anzahl Handkarten
# m: Länge der Straße
# r: Rang der Straße
def prob_of_street_hi(h: list[int], k: int, m: int, r, verbose = False) -> float:
    n = sum(h)  # Gesamtanzahl der verfügbaren Karten
    assert k <= n <= 56
    assert 0 <= k <= 14
    assert 5 <= m <= 14
    assert m <= r <= 14

    if r == 14:
        return 0.0  # eine Straße mit Rang 14 kann nicht überstochen werden

    # Muster laden
    # todo: Daten im Speicher halten, so dass nur einmal geladen werden muss
    data = load_data_hi(STREET, m, True)

    # alle Muster durchlaufen und mögliche Kombinationen zählen
    matches  = 0
    for pho in range(2 if h[16] else 1):
        for case in data[pho]:
            offset = 15 - len(case)
            r_higher = offset + m - 1
            if r_higher <= r:
                break
            if sum(case) + pho > k:
                continue

            matches_part = 1
            n_remain = n - h[16]
            k_remain = k - pho
            for i in range(len(case)):
                matches_part *= math.comb(h[offset + i], case[i])
                if matches_part == 0:
                    break
                n_remain -= h[offset + i]
                k_remain -= case[i]

            matches_part *= math.comb(n_remain, k_remain)
            if matches_part > 0:
                if verbose:
                    print(f"r={r_higher}, php={pho}, case={case}, matches={matches_part}")
                matches += matches_part

    total = math.comb(n, k)  # Gesamtanzahl der möglichen Kombinationen
    p = matches / total  # Wahrscheinlichkeit
    return p


# -----------------------------------------------------------------------------
# Test
# -----------------------------------------------------------------------------

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
    print(f"Gezählt:   p = {matches_expected}/{total_expected} = {p_expected} "
          f"({(time() - time_start) * 1000:.6f} ms)")

    time_start = time()
    h = ranks_to_vector(parse_cards(cards))
    t, m, r = figure
    if t == SINGLE:  # Einzelkarte
        assert False
    elif t == PAIR:  # Paar
        assert False
    elif t == TRIPLE:  # Drilling
        assert False
    elif t == STAIR:  # Treppe
        p_actual = prob_of_stair_hi(h, k, m, r, verbose)
    elif t == FULLHOUSE:  # Full House
        assert False
    elif t == STREET:  # Straße
        p_actual = prob_of_street_hi(h, k, m, r, verbose)
    else:  # Bombe
        assert t == BOMB
        p_actual = 0.0

    print(f"Berechnet: p = {(total_expected * p_actual):.0f}/{total_expected} = {p_actual} "
          f"({(time() - time_start) * 1000:.6f} ms (inkl. Daten laden))")

    assert p_expected == p_actual


def inspect_stair():  # pragma: no cover
    # 2er-Treppe ohne Phönix
    print(f"{timeit(lambda: inspect("RK GK BD SD GD R9 B2", 6, (4, 4, 12), verbose=False), number=1) * 1000:.6f} ms")  # 10/10 = 1.0
    print(f"{timeit(lambda: inspect("Dr GA BA GK BK SD BD", 6, (4, 4, 14), verbose=False), number=1) * 1000:.6f} ms")  # 10/10 = 1.0

    # 2er-Treppe mit Phönix
    print(f"{timeit(lambda: inspect("Ph GK BK SD SB RB R9", 6, (4, 4, 10), verbose=False), number=1) * 1000:.6f} ms")  # 10/10 = 1.0
    print(f"{timeit(lambda: inspect("Ph GK BK SD SB R9 S4", 6, (4, 4, 10), verbose=False), number=1) * 1000:.6f} ms")  # 10/10 = 1.0
    print(f"{timeit(lambda: inspect("Ph GK BK SD SB RB BZ R9", 6, (4, 4, 10), verbose=False), number=1) * 1000:.6f} ms")  # 10/10 = 1.0
    print(f"{timeit(lambda: inspect("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 4, (4, 4, 9), verbose=False), number=1) * 1000:.6f} ms")  # 10/10 = 1.0

    # 3er-Treppe
    print(f"{timeit(lambda: inspect("RK GK BD SD SB RB BB", 6, (4, 6, 12), verbose=False), number=1) * 1000:.6f} ms")  # 10/10 = 1.0
    print(f"{timeit(lambda: inspect("Ph GK BD SD SB RB BB", 6, (4, 6, 12), verbose=False), number=1) * 1000:.6f} ms")  # 10/10 = 1.0

    # 5er-Treppe
    print(f"{timeit(lambda: inspect("GA RA GK RK SD BD SB BB GB BZ RZ G9 B9 R9 Ph", 13, (4,10, 12), verbose=False), number=1) * 1000:.6f} ms")

    # 6er-Treppe
    print(f"{timeit(lambda: inspect("GA RA GK RK SD BD SB BB GB BZ RZ G9 B9 R9 S7 R7 Ph", 14, (4, 12, 13), verbose=False), number=1) * 1000:.6f} ms")

    # 7er-Treppe
    print(f"{timeit(lambda: inspect("GA RA GK RK SD BD SB BB GB BZ RZ G9 B9 R9 S8 R8 S3 S2 Ma Ph", 14, (4, 14, 13), verbose=False), number=1) * 1000:.6f} ms")

    # Treppe mit 4er-Bombe
    #print(f"{timeit(lambda: inspect("SB RZ GZ BZ SZ R9", 5, (4, 4, 11), verbose=True), number=1) * 1000:.6f} ms")

    # Treppe mit Farbbombe
    # print(f"{timeit(lambda: inspect("SB RZ R9 R8 R7 R6", 5, (4, 4, 11), verbose=True), number=1) * 1000:.6f} ms")


def inspect_street():  # pragma: no cover
    # Test auf Fehler

    # Straße mit der Länge 5
    print(f"{timeit(lambda: inspect("GA RK GD RB GZ R9 S8 B7 S6 Ph", 9, (6, 5, 6), verbose=True), number=1) * 1000:.6f} ms")  # 10/10 = 1.0
    print(f"{timeit(lambda: inspect("GA RK GD RB GZ R9 S8 B7 Ph", 9, (6, 5, 6), verbose=False), number=1) * 1000:.6f} ms")  # 10/10 = 1.0
    print(f"{timeit(lambda: inspect("GA RK GD RB GZ R9 S8 B7", 5, (6, 5, 9), verbose=False), number=1) * 1000:.6f} ms")  # 4/56 = 0.07142857142857142
    print(f"{timeit(lambda: inspect("GA RK GD RB GZ R9 S8 B7 S6 S5 R4 S3 S2 Ph", 9, (6, 5, 6), verbose=False), number=1) * 1000:.6f} ms")  # 1476/2002 = 0.7372627372627373
    print(f"{timeit(lambda: inspect("GA RK GD BB GB RB GZ R9 S8 B7 B6 S6 S5 G4 B4 R4 S3 S2 Ma Ph", 9, (6, 5, 6), verbose=False), number=1) * 1000:.6f} ms")  # 56220/167960 = 0.3347225529888069

    # Straße mit der Länge 10
    print(f"{timeit(lambda: inspect("GA RK GD RB GZ R9 S8 B7 S6 S5 R4 S3 G2 S2 Ma Ph", 14, (6, 10, 10), verbose=False), number=1) * 1000:.6f} ms")  # 92/120 = 0.7666666666666667
    print(f"{timeit(lambda: inspect("GA RK GD RB GZ R9 S8 B7 S6 S5 R4 S3 G2 S2 Ma Ph", 14, (6, 10, 12), verbose=False), number=1) * 1000:.6f} ms")  # 75/120 = 0.625
    print(f"{timeit(lambda: inspect("GA RK GD BB GB RB GZ R9 S8 B7 B6 S6 S5 G4 B4 R4 S3 S2 Ma Ph", 14, (6, 10, 13), verbose=False), number=1) * 1000:.6f} ms")  # 3615/38760 = 0.09326625386996903
    print(f"{timeit(lambda: inspect("GA RK GD BB GB RB GZ R9 S8 B7 B6 S6 S5 G4 B4 R4 S3 S2 Ma Ph", 14, (6, 10, 14), verbose=False), number=1) * 1000:.6f} ms")  # 0/38760 = 0.0

    # Straße mit der Länge 13
    print(f"{timeit(lambda: inspect("GA RK GD RB GZ R9 S8 B7 S6 S5 R4 S3 S2 Ma Ph", 13, (6, 13, 13), verbose=False), number=1) * 1000:.6f} ms")  # 14/105 = 0.13333333333333333
    print(f"{timeit(lambda: inspect("GA RK GD RB GZ R9 S8 B7 S6 S5 R4 S3 G2 S2 Ma Ph", 14, (6, 13, 13), verbose=False), number=1) * 1000:.6f} ms")  # 42/120 = 0.35
    print(f"{timeit(lambda: inspect("GA RK GD BB GB RB GZ R9 S8 B7 B6 S6 S5 G4 B4 R4 S3 S2 Ma Ph", 14, (6, 13, 13), verbose=False), number=1) * 1000:.6f} ms") #  768/38760 = 0.019814241486068113

    # Straße mit der Länge 14
    print(f"{timeit(lambda: inspect("GA RK GD BB GB RB GZ R9 S8 B7 B6 S6 S5 G4 B4 R4 S3 S2 Ma Ph", 14, (6, 14, 14), verbose=False), number=1) * 1000:.6f} ms")  # 0/38760 = 0.0

    # # Test auf Geschwindigkeit (Straße mit der Länge 5 hat die meisten Muster, daher nehmen wir diese Länge)
    #
    # # n = 14, k = 6, figure = (6, 5, 6)
    # # Gezählt:   p = 288/3003 = 0.0959040959040959 (100.065470 ms)
    # # Berechnet: p = 288/3003 = 0.0959040959040959 (498.227119 ms (inkl. Daten laden))
    # for k_ in range(5, 10):
    #     if k_ != 6: continue
    #     print(f"k={k_}: {timeit(lambda: inspect("GA RK GD RB GZ R9 S8 B7 Ph", k_, (6, 5, 9), verbose=False), number=1) * 1000:.6f} ms")
    #     print(f"k={k_}: {timeit(lambda: inspect("GA RK GD RB GZ R9 S8 B7 S6 S5 R4 S3 S2 Ph", k_, (6, 5, 9), verbose=False), number=1) * 1000:.6f} ms")
    #     print(f"k={k_}: {timeit(lambda: inspect("GA RK GD RB GZ R9 S8 B7 S6 S5 R4 S3 S2 Ph", k_, (6, 5, 8), verbose=False), number=1) * 1000:.6f} ms")
    #     print(f"k={k_}: {timeit(lambda: inspect("GA RK GD RB GZ R9 S8 B7 S6 S5 R4 S3 S2 Ph", k_, (6, 5, 6), verbose=False), number=1) * 1000:.6f} ms")

    # todo: Differenz wegen 4er-Bombe (wird von possible_hands_hi() berücksichtigt, aber noch nicht von get_streets();
    #  Farbbomben werden von beiden Funktionen noch nicht berücksichtigt)

    # n = 52, k = 5, figure = (6, 5, 6)
    # Gezählt:   p = 8816/2598960 = 0.0033921260812017117 (42438.135147 ms)
    # Berechnet: p = 8192/2598960 = 0.0031520300427863453 (662.052393 ms (inkl. Daten laden))
    # -> Differenz: 0.00024009603841536635
    #print(f"{timeit(lambda: inspect("GA GK GD GB GZ G9 G8 G7 G6 G5 G4 G3 G2 SA SK SD SB SZ S9 S8 S7 S6 S5 S4 S3 S2 RA RK RD RB RZ R9 R8 R7 R6 R5 R4 R3 R2 BA BK BD BB BZ B9 B8 B7 B6 B5 B4 B3 B2", 5, (6, 5, 6), verbose=False), number=1) * 1000:.6f} ms")

    # n = 52, k = 6, figure = (6, 5, 6)
    # Gezählt:   p = 309576/20358520 = 0.015206213418264196 (368347.875834 ms)
    # Berechnet: p = 294912/20358520 = 0.014485925303018097 (670.219183 ms (inkl. Daten laden))
    # -> Differenz:  0.0007202881152460986   (0.0007202881152460986/0.00024009603841536635 == 3)
    #print(f"{timeit(lambda: inspect("GA GK GD GB GZ G9 G8 G7 G6 G5 G4 G3 G2 SA SK SD SB SZ S9 S8 S7 S6 S5 S4 S3 S2 RA RK RD RB RZ R9 R8 R7 R6 R5 R4 R3 R2 BA BK BD BB BZ B9 B8 B7 B6 B5 B4 B3 B2", 6, (6, 5, 6), verbose=False), number=1) * 1000:.6f} ms")

    # n = 52, k = 5, figure = (6, 5, 13)
    # Gezählt:   p = 1648/2598960 = 0.0006340997937636593 (17087.398767 ms)
    # Berechnet: p = 1024/2598960 = 0.00039400375534829317 (565.371275 ms (inkl. Daten laden))
    # -> Differenz: 0.00024009603841536618
    # print(f"{timeit(lambda: inspect("GA GK GD GB GZ G9 G8 G7 G6 G5 G4 G3 G2 SA SK SD SB SZ S9 S8 S7 S6 S5 S4 S3 S2 RA RK RD RB RZ R9 R8 R7 R6 R5 R4 R3 R2 BA BK BD BB BZ B9 B8 B7 B6 B5 B4 B3 B2", 5, (6, 5, 13), verbose=False), number=1) * 1000:.6f} ms")

    # n = 52, k = 5, figure = (6, 5, 14)
    # Gezählt:   p = 624/2598960 = 0.00024009603841536616 (12652.729511 ms)
    # Berechnet: p = 0/2598960 = 0.0 (541.404486 ms (inkl. Daten laden))
    # -> Differenz: 0.00024009603841536616
    #print(f"{timeit(lambda: inspect("GA GK GD GB GZ G9 G8 G7 G6 G5 G4 G3 G2 SA SK SD SB SZ S9 S8 S7 S6 S5 S4 S3 S2 RA RK RD RB RZ R9 R8 R7 R6 R5 R4 R3 R2 BA BK BD BB BZ B9 B8 B7 B6 B5 B4 B3 B2", 5, (6, 5, 14), verbose=False), number=1) * 1000:.6f} ms")

    pass


if __name__ == '__main__':  # pragma: no cover
    inspect_stair()
    #inspect_street()

    # Ladezeit messen
    #print(f"{timeit(lambda: load_data(STREET, 10), number=10) * 1000 / 10:.6f} ms")  # 420 ms
    #print(f"{timeit(lambda: load_data(STREET, 5), number=10) * 1000 / 10:.6f} ms")  # 420 ms
    pass