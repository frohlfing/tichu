import gzip

import config
import itertools
import math
import numpy as np
import pickle
from os import path, mkdir
from src.lib.cards import stringify_cards, parse_cards
from src.lib.combinations import stringify_figure, SINGLE, PAIR, TRIPLE, STAIR, FULLHOUSE, STREET, BOMB
from src.lib.probabilities import possible_hands_hi, ranks_to_vector
from time import time
from timeit import timeit


def get_filename(t: int, m: int):
    folder = path.join(config.DATA_PATH, "cache/prob")
    if not path.exists(folder):
        mkdir(folder)
    name = ['single', 'pair', 'triple', 'stair', 'fullhouse', 'street', 'bomb'][t - 1]
    if t in (STAIR, STREET, BOMB):
        name += f"{m:02}"
    file = path.join(folder, f"{name}_hi.pkl")
    #file = path.join(folder, f"{name}_hi.pkl.gz")
    return file


# Daten speichern
def save_data(t: int, m: int, data: list):
    file = get_filename(t, m)

    # Komprimiert speichern
    if file[-3:] == '.gz':
        with gzip.open(file, "wb") as fp:
            # noinspection PyTypeChecker
            pickle.dump(data, fp)
    else:
        with open(file, 'wb') as fp:
            # noinspection PyTypeChecker
            pickle.dump(data, fp)

    # zusätzlich als Textdatei speichern (nützlich zum Debuggen)
    with open(file[:-7] if file[-7:] == '.pkl.gz' else file[:-4] + ".txt", "w") as datei:
        for pho in range(2):
            datei.write(f"Pho={pho}\n")
            for row in data[pho]:
                datei.write(f"{row}\n")

    print(f"Daten in {path.basename(file)} gespeichert", )


# Daten laden
def load_data(t: int, m: int, verbose = False) -> list:
    time_start = time()
    file = get_filename(t, m)
    if file[-3:] == '.gz':
        with gzip.open(file, 'rb') as fp:
            data = pickle.load(fp)
    else:
        with open(file, 'rb') as fp:
            data = pickle.load(fp)
    if verbose:
        print(f"Daten aus {path.basename(file)} geladen ({(time() - time_start) * 1000:.6f} ms)")
    return data


# Bildet das Produkt beider Listen
# todo umbenennen nach product_of_lists ?
#
# Die erste Liste beinhaltet mögliche Muster (Anzahl Karten pro Rang).
# Die zweite Liste führt die mögliche Anzahl Karten für den nächsten Rang.
# Jedes Muster der ersten Liste wird mit jeder möglichen Anzahl Karten erweitert.
# Die kombinierten Muster, die mehr als k Karten haben, werden herausgefiltert.
#
# Beispiel:
# combine_lists(
#    [(1, 1, 1), (1, 1, 2), (1, 1, 3)],
#    [4, 5],
# 9))
# Ergibt: [(1, 1, 1, 4), (1, 1, 1, 5), (1, 1, 2, 4), (1, 1, 2, 5), (1, 1, 3, 4)]
#
# list1: Mögliche Muster
# list2: Anzahl Karten für den nächsten Rang
# k: Anzahl Handkarten
def combine_lists(list1, list2, k: int):
    if not list1:
        list1 = [()]
    result = []
    for subset in list1:
        for value in list2:
            if sum(subset) + value <= k:
                result.append(subset + (value,))
    return result


# Ermittelt die höchste Straße im Datensatz
#
# Wenn eine Straße vorhanden ist, wird der Rang der Straße zurückgegeben
# (und ein Kennzeichen, ob der Phönix verwendet wird)
#
# row: row[0] == Phönix, row[1] bis row[14] == Rang 1 bis 14
# m: Länge der Straße
def get_max_rank_of_street(row: tuple, m: int):
    for r in range(14, m - 1, -1):  # [14 ... 5] (höchster Rang zuerst)
        r_start = r - m + 1
        r_end = r + 1  # exklusiv
        if row[0]:  # mit Phönix
            for pho in range(r, r_start - 1, -1):  # (vom Ende bis zum Anfang der Straße)
                if all(row[i] for i in range(r_start, r_end) if i != pho):
                    return r, 1
        else:  # ohne Phönix
            if all(row[i] for i in range(r_start, r_end)):
                return r, 0
    return False


# -----------------------------------------------------------------------------
# Straßen
# -----------------------------------------------------------------------------

# Generiert eine Tabelle mit allen möglichen Straßen der Länge m, höhere Straße wird bevorzugt.
# Diese Informationen werden in eine Datei gespeichert.
def generate_street_table(m: int):  # pragma: no cover
    # Eine 14er-Straße kann nicht überstochen werden (sie geht von Mahjong zum As).
    # Die Tabelle dazu muss also nicht gespeichert werden.
    assert 5 <= m <= 13

    time_start = time()

    # 1. Schritt:
    # alle möglichen Kombinationen (reduziert auf Karte verfügbar/fehlt) durchlaufen und Straßen davon auflisten

    # Kombinationen bei Straße der Länge 5, r = 11:
    # r = 1  2  3  4  5  6  7  8  9 10 11 12 13 14
    # (1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0)
    # (1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 1)
    # (1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0)
    # (1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1)
    # (1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 1, 0)
    # (1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0)
    # (1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 0, 0, 1)
    # (1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 0, 1, 0)
    # (1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 0, 1, 1)
    # (1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0)
    # (1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 1)
    # (1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 0)
    # (1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1)
    #  ^  ^----remain----^  ^-------unique-------^
    #  |  |              |  | <-  m  -> |        |
    # pho 1            r-m  r-m+1       r       14

    # Die Karten von 1 bis r-m sind einzeln nicht relevant.
    # Von r-m+1 bis r befindet sich die Straße. An der Stelle des Phönix ist eine 0 (keine Karte mit
    # diesem Rang), an jeder anderen Stelle der Straße ist eine 1 (mindestens eine Karte erforderlich).
    # Die Karten überhalb der Straße (r+1 bis 14) sind wichtig, um das Muster eindeutig zu halten.
    # Dadurch schließen sich die Teilmengen gegenseitig aus.

    c_all = 0
    c_matches = 0
    c_unique = 0
    data = []
    for row in itertools.product(range(2), repeat=15):
        # row[0] == Phönix, row[1] bis row[14] == Rang 1 bis 14
        c_all += 1
        res = get_max_rank_of_street(row, m)
        if res:
            # im Datensatz ist mindestens eine Straße vorhanden
            r, pho = res
            unique = row[r - m + 1:]
            c_matches += 1
            found = (r, pho, unique) in data  # zählt 1673 Fälle
            if not found:
                # die Straße ist noch nicht gelistet
                c_unique += 1
                data.append((r, pho, unique))
            #     print(row, f" -> r: {r} (start: {r - m + 1}), pho: {pho}, top: {top}")
            # else:
            #     print(row, f"r: {r}")
    print("all:", c_all)
    print("matches:", c_matches)
    print("unique:", c_unique)

    # data listet nun folgende Daten:
    # r: Rang der Straße (von 14 bis 5)
    # pho: 1, wenn der Phönix verwendet wird, sonst 0
    # unique: Muster von r-m+1 bis 14
    #
    # Zuerst werden die Fälle ohne Phönix aufgeführt, sortiert nach Rang (absteigend).
    # Dann werden die Fälle mit Phönix aufgeführt, wieder sortiert nach Rang (absteigend).

    # Schritt 2:
    # Karte verfügbar/fehlt expandieren zu Kartenanzahl 0,1,2,3,4

    table = [[], []]  # erste Liste ohne Phönix, zweite Liste mit Phönix
    c = 0
    for r, pho, unique in data:
        if r <= m:
            # Der kleinste Rang einer 5er-Straße ist 5, der einer 6er-Straße ist 6, usw.
            # Eir suchen höhere Straßen, also brauchen wir den kleinstmöglichen Rang nicht speichern.
            continue
        cases = []
        for v in unique:
            cases = combine_lists(cases, list(range(1, 5) if v == 1 else [0]), 14)
        # if r == 14:
        #     for case in cases:
        #         print(f"r: {r}, pho: {pho}, case: {unique}", f" -> r: {r}, pho: {pho}, case: {case}")
        c += len(cases)
        table[pho].extend(cases)  # for case in cases: table[pho].append(case)
    print("Expandiert:", c)
    print(f"{(time() - time_start) * 1000:.6f} ms")

    # Daten speichern
    save_data(STREET, m, table)


def generate_street_tables_if_not_exists():
    for m in range(5, 14):
        file = get_filename(STREET, m)
        if not path.exists(file):
            generate_street_table(m)


# Listet die möglichen Straßen auf, die die gegebene Straße überstechen
#
# h: Verfügbaren Karten als Vektor (Index entspricht den Rang)
# k: Anzahl Handkarten
# m: Länge der Straße
# r: Rang der Straße
def get_streets(h: list[int], k: int, m: int, r, verbose = False) -> float:
    n = sum(h)  # Gesamtanzahl der verfügbaren Karten
    assert k <= n <= 56
    assert 0 <= k <= 14
    assert 5 <= m <= 14
    assert m <= r <= 14

    if r == 14:
        return 0.0  # eine Straße mit Rang 14 kann nicht überstochen werden

    # Muster laden
    # todo: Daten im Speicher halten, so dass nur einmal geladen werden muss
    data = load_data(STREET, m, True)

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
        assert False
    elif t == FULLHOUSE:  # Full House
        assert False
    elif t == STREET:  # Straße
        p_actual = get_streets(h, k, m, r, verbose)
    else:  # Bombe
        assert t == BOMB
        p_actual = 0.0

    print(f"Berechnet: p = {(total_expected * p_actual):.0f}/{total_expected} = {p_actual} "
          f"({(time() - time_start) * 1000:.6f} ms (inkl. Daten laden))")

    assert p_expected == p_actual


def inspect_street():  # pragma: no cover
    # Test auf Fehler

    # # Straße mit der Länge 5
    # print(f"{timeit(lambda: inspect("GA RK GD RB GZ R9 S8 B7 S6 Ph", 9, (6, 5, 6), verbose=True), number=1) * 1000:.6f} ms")  # 10/10 = 1.0
    # print(f"{timeit(lambda: inspect("GA RK GD RB GZ R9 S8 B7 Ph", 9, (6, 5, 6), verbose=False), number=1) * 1000:.6f} ms")  # 10/10 = 1.0
    # print(f"{timeit(lambda: inspect("GA RK GD RB GZ R9 S8 B7", 5, (6, 5, 9), verbose=False), number=1) * 1000:.6f} ms")  # 4/56 = 0.07142857142857142
    # print(f"{timeit(lambda: inspect("GA RK GD RB GZ R9 S8 B7 S6 S5 R4 S3 S2 Ph", 9, (6, 5, 6), verbose=False), number=1) * 1000:.6f} ms")  # 1476/2002 = 0.7372627372627373
    # print(f"{timeit(lambda: inspect("GA RK GD BB GB RB GZ R9 S8 B7 B6 S6 S5 G4 B4 R4 S3 S2 Ma Ph", 9, (6, 5, 6), verbose=False), number=1) * 1000:.6f} ms")  # 56220/167960 = 0.3347225529888069
    #
    # # Straße mit der Länge 10
    # print(f"{timeit(lambda: inspect("GA RK GD RB GZ R9 S8 B7 S6 S5 R4 S3 G2 S2 Ma Ph", 14, (6, 10, 10), verbose=False), number=1) * 1000:.6f} ms")  # 92/120 = 0.7666666666666667
    # print(f"{timeit(lambda: inspect("GA RK GD RB GZ R9 S8 B7 S6 S5 R4 S3 G2 S2 Ma Ph", 14, (6, 10, 12), verbose=False), number=1) * 1000:.6f} ms")  # 75/120 = 0.625
    # print(f"{timeit(lambda: inspect("GA RK GD BB GB RB GZ R9 S8 B7 B6 S6 S5 G4 B4 R4 S3 S2 Ma Ph", 14, (6, 10, 13), verbose=False), number=1) * 1000:.6f} ms")  # 3615/38760 = 0.09326625386996903
    # print(f"{timeit(lambda: inspect("GA RK GD BB GB RB GZ R9 S8 B7 B6 S6 S5 G4 B4 R4 S3 S2 Ma Ph", 14, (6, 10, 14), verbose=False), number=1) * 1000:.6f} ms")  # 0/38760 = 0.0
    #
    # # Straße mit der Länge 13
    # print(f"{timeit(lambda: inspect("GA RK GD RB GZ R9 S8 B7 S6 S5 R4 S3 S2 Ma Ph", 13, (6, 13, 13), verbose=False), number=1) * 1000:.6f} ms")  # 14/105 = 0.13333333333333333
    # print(f"{timeit(lambda: inspect("GA RK GD RB GZ R9 S8 B7 S6 S5 R4 S3 G2 S2 Ma Ph", 14, (6, 13, 13), verbose=False), number=1) * 1000:.6f} ms")  # 42/120 = 0.35
    # print(f"{timeit(lambda: inspect("GA RK GD BB GB RB GZ R9 S8 B7 B6 S6 S5 G4 B4 R4 S3 S2 Ma Ph", 14, (6, 13, 13), verbose=False), number=1) * 1000:.6f} ms") #  768/38760 = 0.019814241486068113
    #
    # # Straße mit der Länge 14
    # print(f"{timeit(lambda: inspect("GA RK GD BB GB RB GZ R9 S8 B7 B6 S6 S5 G4 B4 R4 S3 S2 Ma Ph", 14, (6, 14, 14), verbose=False), number=1) * 1000:.6f} ms")  # 0/38760 = 0.0

    # Test auf Geschwindigkeit (Straße mit der Länge 5 hat die meisten Muster, daher nehmen wir diese Länge)

    # n = 14, k = 6, figure = (6, 5, 6)
    # Gezählt:   p = 288/3003 = 0.0959040959040959 (100.065470 ms)
    # Berechnet: p = 288/3003 = 0.0959040959040959 (498.227119 ms (inkl. Daten laden))
    for k_ in range(5, 10):
        if k_ != 6: continue
        # print(f"k={k_}: {timeit(lambda: inspect("GA RK GD RB GZ R9 S8 B7 Ph", k_, (6, 5, 9), verbose=False), number=1) * 1000:.6f} ms")
        # print(f"k={k_}: {timeit(lambda: inspect("GA RK GD RB GZ R9 S8 B7 S6 S5 R4 S3 S2 Ph", k_, (6, 5, 9), verbose=False), number=1) * 1000:.6f} ms")
        # print(f"k={k_}: {timeit(lambda: inspect("GA RK GD RB GZ R9 S8 B7 S6 S5 R4 S3 S2 Ph", k_, (6, 5, 8), verbose=False), number=1) * 1000:.6f} ms")
        print(f"k={k_}: {timeit(lambda: inspect("GA RK GD RB GZ R9 S8 B7 S6 S5 R4 S3 S2 Ph", k_, (6, 5, 6), verbose=False), number=1) * 1000:.6f} ms")

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
    #print(f"{timeit(lambda: inspect("GA GK GD GB GZ G9 G8 G7 G6 G5 G4 G3 G2 SA SK SD SB SZ S9 S8 S7 S6 S5 S4 S3 S2 RA RK RD RB RZ R9 R8 R7 R6 R5 R4 R3 R2 BA BK BD BB BZ B9 B8 B7 B6 B5 B4 B3 B2", 5, (6, 5, 13), verbose=False), number=1) * 1000:.6f} ms")

    # n = 52, k = 5, figure = (6, 5, 14)
    # Gezählt:   p = 624/2598960 = 0.00024009603841536616 (12652.729511 ms)
    # Berechnet: p = 0/2598960 = 0.0 (541.404486 ms (inkl. Daten laden))
    # -> Differenz: 0.00024009603841536616
    #print(f"{timeit(lambda: inspect("GA GK GD GB GZ G9 G8 G7 G6 G5 G4 G3 G2 SA SK SD SB SZ S9 S8 S7 S6 S5 S4 S3 S2 RA RK RD RB RZ R9 R8 R7 R6 R5 R4 R3 R2 BA BK BD BB BZ B9 B8 B7 B6 B5 B4 B3 B2", 5, (6, 5, 14), verbose=False), number=1) * 1000:.6f} ms")

    pass


if __name__ == '__main__':  # pragma: no cover
    #generate_street_table(5)
    generate_street_tables_if_not_exists()
    inspect_street()

    #print(f"{timeit(lambda: load_data(STREET, 10), number=10) * 1000 / 10:.6f} ms")  # 420 ms
    #print(f"{timeit(lambda: load_data(STREET, 5), number=10) * 1000 / 10:.6f} ms")  # 420 ms
