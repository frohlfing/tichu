__all__ = "load_table_hi",

import config
import gzip
import itertools
import pickle
from os import path, mkdir
from src.lib.combinations import SINGLE, PAIR, TRIPLE, STAIR, FULLHOUSE, STREET, BOMB, stringify_type
from time import time

# -----------------------------------------------------------------------------
# Generiert Hilfstabellen für die Wahrscheinlichkeitsberechnung
# -----------------------------------------------------------------------------

# Gibt den Dateinamen für die Hilfstabellen
def get_filename_hi(t: int, m: int = None):
    folder = path.join(config.DATA_PATH, "lib/prob")
    if not path.exists(folder):
        mkdir(folder)
    name = stringify_type(t, m)
    file = path.join(folder, f"{name}_hi.pkl")
    return file


# Speichert die Hilfstabelle
def save_table_hi(t: int, m: int, table: list):
    file = get_filename_hi(t, m)

    # unkomprimiert speichern
    with open(file, 'wb') as fp:
        # noinspection PyTypeChecker
        pickle.dump(table, fp)

    # Komprimiert speichern
    with gzip.open(file + ".gz", "wb") as fp:
        # noinspection PyTypeChecker
        pickle.dump(table, fp)

    # zusätzlich als Textdatei speichern (nützlich zum Debuggen)
    with open(file[:-4] + ".txt", "w") as datei:
        for pho in range(2):
            datei.write(f"Pho={pho}\n")
            for r, cases in table[pho].items():
                for case in cases:
                    datei.write(f"{r}, {case}\n")

    print(f"Hilfstabelle in {path.basename(file)} gespeichert", )


# Lädt die Hilfstabelle
def load_table_hi(t: int, m: int, verbose = False) -> list:
    time_start = time()
    file = get_filename_hi(t, m)
    if path.exists(file):
        with open(file, 'rb') as fp:
            table = pickle.load(fp)
    else:
        file += ".gz"
        with gzip.open(file, 'rb') as fp:
            table = pickle.load(fp)
    if verbose:
        print(f"Hilfstabelle aus {path.basename(file)} geladen ({(time() - time_start) * 1000:.6f} ms)")
    return table


# Bildet das Produkt beider Listen
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


# Ermittelt dan höchsten Rang der gegebenen Kombination im Datensatz
#
# Wenn die Kombination vorhanden ist, wird der Rang der Kombination und das eindeutige Muster zurückgegeben, sonst -1.
#
# row: row[0] == Phönix, row[1] bis row[14] == Rang 1 bis 14
def get_max_rank(t: int, m: int, row: tuple) -> tuple[int, list]:

    if t == SINGLE:
        # todo: Vereinheitlichen
        # row: row[0] == Hund, row[1] == Mahjong, row[2] bis row[14] == 2 bis 14, row[15] == Drache, row[16] == Phönix
        # erst den Drachen prüfen, dann den Phönix (höchste Schlagkraft zuerst)
        for r in [15, 16, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]:
            if row[r] >= 1:
                if r == 16:  # Phönix ist die höchste Karte (Drache ist nicht vorhanden)
                    # Rang des Phönix an die Schlagkraft anpassen (der Phönix schlägt das Ass, aber nicht den Drachen)
                    r = 15  # 14.5 aufgerundet
                return r, row[r:-1]  # vom aktuellen Rang bis zum Drachen (Phönix wird abgeschnitten)

    if t == PAIR:
        for r in range(14, 1, -1):  # [14 ... 2] (höchster Rang zuerst)
            if row[0]:  # mit Phönix
                if row[r] >= 1:
                    return r, row[r:]
            else:  # ohne Phönix
                if row[r] >= 2:
                    return r, row[r:]

    elif t == TRIPLE:
        for r in range(14, 1, -1):  # [14 ... 2] (höchster Rang zuerst)
            if row[0]:  # mit Phönix
                if row[r] >= 2:
                    return r, row[r:]
            else:  # ohne Phönix
                if row[r] >= 3:
                    return r, row[r:]

    elif t == STAIR:
        steps = int(m / 2)
        for r in range(14, steps, -1):  # [14 ... 3] (höchster Rang zuerst)
            r_start = r - steps + 1
            r_end = r + 1  # exklusiv
            if row[0]:  # mit Phönix
                for r_pho in range(r, r_start - 1, -1):  # (vom Ende bis zum Anfang der Treppe)
                    if row[r_pho] >= 1 and all(row[i] >= 2 for i in range(r_start, r_end) if i != r_pho):
                        return r, row[r - steps + 1:]
            else:  # ohne Phönix
                if all(row[i] >= 2 for i in range(r_start, r_end)):
                    return r, row[r - steps + 1:]

    elif t == FULLHOUSE:
        for r in range(14, 1, -1):  # [14 ... 2] (höchster Rang zuerst)
            if row[0]:  # mit Phönix
                if row[r] >= 3:  # Drilling mit Rang r
                    for i in range(14, 1, -1):
                        if i != r and row[i] >= 1:  # irgendeine Einzelkarte zw. 14 und 2
                            return r, row[min(r, i):]
                if row[r] == 2:  # Pärchen mit Rang r
                    for i in range(14, 1, -1):
                        if i != r and row[i] >= 2:  # irgendein Pärchen zw. 14 und 2
                            return r, row[min(r, i):]
            else:  # ohne Phönix
                if row[r] >= 3:  # Drilling mit Rang r
                    for i in range(14, 1, -1):
                        if i != r and row[i] >= 2:  # irgendein Pärchen zw. 14 und 2
                            return r, row[min(r, i):]

    elif t == STREET:
        for r in range(14, m - 1, -1):  # [14 ... 5] (höchster Rang zuerst)
            r_start = r - m + 1
            r_end = r + 1  # exklusiv
            if row[0]:  # mit Phönix
                for r_pho in range(r, r_start - 1, -1):  # (vom Ende bis zum Anfang der Straße)
                    if row[r_pho] >= 0 and all(row[i] >= 1 for i in range(r_start, r_end) if i != r_pho):
                        return r, row[r - m + 1:]
            else:  # ohne Phönix
                if all(row[i] >= 1 for i in range(r_start, r_end)):
                    return r, row[r - m + 1:]

    elif t == BOMB:
        if m == 4:
            # 4er-Bombe
            for r in range(14, 1, -1):  # [14 ... 2] (höchster Rang zuerst)
                if row[r] == 4:
                    return r, row[r:]
        else:
            # Farbbombe
            for r in range(14, m, -1):  # [14 ... 6] (höchster Rang zuerst)
                if all(row[i] == 1 for i in range(r - m + 1, r + 1)):
                    return r, row[r - m + 1:]

    return -1, []


# --------------------------------------------------------------------------------

# Generiert eine Datei mit allen möglichen Einzelkarten, höhere Einzelkarte wird bevorzugt.
def generate_single_file_hi():
    time_start = time()

    # 1. Schritt:
    # alle möglichen Kombinationen (reduziert auf Karte verfügbar/fehlt) durchlaufen und Einzelkarte auflisten

    c_all = 0
    c_matches = 0
    c_unique = 0
    data = []

    for row in itertools.product(range(2), repeat=17):  # sortiert nach Rang absteigend
        # Beispiel für row (r = 10):
        # r=0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16
        #  (0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1)
        #   ^----------remain----------^  ^----unique----^  ^
        #   |                          |  |              |  |
        #  Hu                        r-1  r             Dr Ph
        # r ist der Rang der Einzelkarte. Darunter muss nicht weiter betrachtet werden.
        # Die Karten darüber sind wichtig, um das Muster eindeutig zu halten.
        c_all += 1
        print(f"\r{c_all}/131072 = {100 * c_all / 131072:.1f} %", end="")  # 131072 == 2^17
        r, unique = get_max_rank(SINGLE, 1, row)
        if r >= 0:  # mindestens eine Einzelkarte ist vorhanden
            c_matches += 1
            found = (r, row[16], unique) in data
            if not found:
                # die Einzelkarte ist noch nicht gelistet
                c_unique += 1
                data.append((r, row[16], unique))

    print("\nmatches:", c_matches)
    print("unique:", c_unique)

    # 2. Schritt:
    # Karte verfügbar/fehlt expandieren zu Kartenanzahl 0,1,2,3,4 (bzw. 0,1 bei Sonderkarten)

    table = [[], []]  # erste Liste ohne Phönix, zweite Liste mit Phönix
    c = 0
    for r, pho, unique in data:
        if r == 0:
            # Wir suchen höhere Einzelkarte, also brauchen wir den Hund nicht zu speichern.
            continue
        cases = []
        for i, v in enumerate(unique):
            a = 1 if r + i in [0, 1, 15, 16] else 4  # Kartenanzahl = 1 wenn Sonderkarte, sonst 4
            cases = combine_lists(cases, list(range(1, a + 1) if v == 1 else [0]), 14)
            if not cases:
                break
        if cases:
            c += len(cases)
            print(f"\r{c}", end="")
            table[pho].extend(cases)
    print("\nExpandiert:", c)
    print(f"{(time() - time_start) * 1000:.6f} ms")

    # Daten speichern
    save_table_hi(SINGLE, 1, table)


# Generiert eine Hilfstabelle für den gegebenen Typ, höhere Ränge werden bevorzugt.
def generate_file_hi(t: int, m: int = None):
    if t == SINGLE:
        m = 1
    elif t == PAIR:
        m = 2
    elif t == TRIPLE:
        m = 3
    elif t == STAIR:
        assert 4 <= m <= 14
    elif t == FULLHOUSE:
        m = 5
    elif t == STREET:
        assert 5 <= m <= 14
    elif t == BOMB:
        assert 4 <= m <= 14
    else:
        assert False

    # Mögliche Ränge von/bis
    r_start = 0 if t == SINGLE else 1 if t == STREET else 2
    r_end = 16 if t == SINGLE else 15  # exklusiv (Drache + 1 bzw. Ass + 1)

    # Hilfstabelle
    table = [
        {r: [] for r in range(r_start, r_end)},  # ohne Phönix
        {r: [] for r in range(r_start, r_end)},  # mit Phönix
    ]

    # 1. Schritt:
    # alle möglichen Kombinationen (Kartenanzahl je Rang reduziert) durchlaufen und passende auflisten

    for pho in range(2):
        print(f"Generiere Hilfstabelle {stringify_type(t, m)}[{pho}]...")

        data = {r: [] for r in range(2, 15)}

        # reduzierte Kartenanzahl je Rang
        if t == SINGLE:
            a = [0, 1]
        elif t == PAIR:
            a = [0, 1] if pho else [1, 2]
        elif t == TRIPLE:
            a = [1, 2] if pho else [2, 3]
        elif t == STAIR:
            a = [0, 1, 2] if pho else [1, 2]
        elif t == FULLHOUSE:
            a = [0, 1, 2, 3] if pho else [1, 2, 3]
        elif t == STREET:
            a = [0, 1]
        else:
            assert False

        # Iterator für die Product-Operation
        if t == SINGLE:
            #          0    1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
            iter1 = [[pho], a, a, a, a, a, a, a, a, a, a, a, a, a, a, a]
            c_max = len(a) ** 15
        elif t == STREET:
            #          0    1  2  3  4  5  6  7  8  9 10 11 12 13 14
            iter1 = [[pho], a, a, a, a, a, a, a, a, a, a, a, a, a, a]
            c_max = len(a) ** 14
        else:
            #          0     1   2  3  4  5  6  7  8  9 10 11 12 13 14
            iter1 = [[pho], [0], a, a, a, a, a, a, a, a, a, a, a, a, a]  # Dummy für Mahjong (wird nicht betrachtet)
            c_max = len(a) ** 13

        c = 0
        for row in itertools.product(*iter1):
            # Beispiel für row beim Pärchen, r = 10:
            # r = 1  2  3  4  5  6  7  8  9 10 11 12 13 14
            # (0, 0, 0, 0, 0, 0, 0, 2, 1, 2, 2, 0, 0, 1, 1)
            #  ^     ^------remain--------^  ^---unique--^
            #  |     |                    |  |           |
            # pho    2                  r-1  r          14
            # r ist der Rang des Pärchens. Darunter muss nicht weiter betrachtet werden.
            # Die Karten darüber sind wichtig, um das Muster eindeutig zu halten.

            # Beispiel für row bei Fullhouse, r = 10:
            # r = 1  2  3  4  5  6  7  8  9 10 11 12 13 14
            # (0, 0, 1, 1, 0, 3, 1, 2, 1, 1, 3, 0, 1, 0, 1)
            #  ^     ^---remain--^  ^-------unique-------^
            #  |     |           |  |        |           |
            # pho    2              r_pair   r_triple   14

            # Beispiel für row bei einer Treppe (steps = 5, r = 11):
            # r = 1  2  3  4  5  6  7  8  9 10 11 12 13 14
            # (1, 0, 0, 0, 0, 0, 0, 2, 1, 2, 2, 2, 0, 2, 1)
            #  ^     ^--remain---^  ^-------unique-------^
            #  |     |           |  | <-steps-> |        |
            # pho    2     r-steps  r-steps+1   r       14
            # Von r-steps+1 bis r befindet sich die Treppe. Darunter muss nicht weiter betrachtet werden.
            # Die Karten darüber (r+1 bis 14) sind wichtig, um das Muster eindeutig zu halten.

            # Beispiel für row bei einer Straße (m = 5, r = 11):
            # r = 1  2  3  4  5  6  7  8  9 10 11 12 13 14
            # (1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1)
            #  ^  ^----remain----^  ^-------unique-------^
            #  |  |              |  | <-  m  -> |        |
            # pho 1            r-m  r-m+1       r       14
            # Von r-m+1 bis r befindet sich die Straße. Darunter muss nicht weiter betrachtet werden.
            # Die Karten darüber (r+1 bis 14) sind wichtig, um das Muster eindeutig zu halten.

            c += 1
            print(f"\r{c}/{c_max} = {100 * c / c_max:.1f} %", end="")
            r, unique = get_max_rank(t, m, row)
            if r >= 0:
                if not unique in data[r]:
                    data[r].append(unique)
        print()

        # Daten zwischenspeichern
        with open(path.join(config.DATA_PATH, f"lib/prob/~{stringify_type(t, m)}.pkl"), 'wb') as fp:
            # noinspection PyTypeChecker
            pickle.dump(data, fp)

        # 2. Schritt:
        # Kartenanzahl expandieren zu Kartenanzahl 0,1,2,3,4 (bzw. 0,1 bei Sonderkarten)

        c = 0
        for r, uniques in data.items():
            w = r - m + 1
            for unique in uniques:
                cases = []
                for i, v in enumerate(unique):
                    assert r_end - len(unique) == r - m + 1
                    if a == [0, 1]:
                        if r - m + 1 + i in [0, 1, 15, 16]:  # Sonderkarte
                            assert t in [SINGLE, STREET]
                            v_expand = [v]
                        else:
                            v_expand = [1, 2, 3, 4] if v == 1 else [0]
                    elif a == [1, 2]:
                        v_expand = [2, 3, 4] if v == 2 else [0, 1]
                    elif a == [2, 3]:
                        v_expand = [3, 4] if v == 3 else [0, 1, 2]
                    elif a == [0, 1, 2]:
                        v_expand = [2, 3, 4] if v == 2 else [v]
                    elif a == [1, 2, 3]:
                        v_expand = [3, 4] if v == 3 else [2] if v == 2 else [0, 1]
                    elif a == [0, 1, 2, 3]:
                        v_expand = [3, 4] if v == 3 else [v]
                    else:
                        assert False
                    cases = combine_lists(cases, v_expand, 14)
                    if not cases:
                        break
                c += len(cases)
                print(f"\rAnzahl Muster: {c}", end="")
                for case in cases:
                    table[pho][r].append(case)
        print()

    # Daten speichern
    save_table_hi(t, m, table)


# Generiert eine Datei mit allen möglichen 4er-Bomben, höhere Bombe wird bevorzugt.
def generate_4_bomb_file_hi():
    time_start = time()

    # 1. Schritt:
    # alle möglichen Kombinationen (reduziert auf mind. 4 Karten/weniger) durchlaufen und 4er-Bomben auflisten

    c_all = 0
    c_matches = 0
    c_unique = 0
    data = []
    a = [3, 4]                  # 0    1   2  3  4  5  6  7  8  9 10 11 12 13 14
    for row in itertools.product([0], [0], a, a, a, a, a, a, a, a, a, a, a, a, a):  # sortiert nach Rang absteigend
        # Beispiel für row (r = 10):
        # r = 1  2  3  4  5  6  7  8  9 10 11 12 13 14
        # (0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 4, 3, 3, 3, 3)
        #        ^------remain--------^  ^---unique--^
        #        |                    |  |           |
        #        2                  r-1  r          14
        # r ist der Rang des Drillings. Darunter muss nicht weiter betrachtet werden.
        # Die Karten darüber sind wichtig, um das Muster eindeutig zu halten.
        c_all += 1
        print(f"\r{c_all}/8192 = {100 * c_all / 8192:.1f} %", end="")  # 8192 == 2^13
        r = get_max_rank_of_bomb(row, 4)
        if r >= 0:  # mindestens eine 4er-Bombe ist vorhanden
            unique = row[r:]
            c_matches += 1
            found = (r, row[0], unique) in data
            if not found:
                # die 4er-Bombe ist noch nicht gelistet
                c_unique += 1
                data.append((r, row[0], unique))
    print("\nmatches:", c_matches)
    print("unique:", c_unique)

    # 2. Schritt:
    # 3 Karten/2 Karten/weniger expandieren zu Kartenanzahl 0,1,2,3,4

    table = [[], []]  # erste Liste ohne Phönix, zweite Liste mit Phönix (bleibt bei Bomben leer)
    c = 0
    for r, pho, unique in data:
        if r == 2:
            # Der kleinste Rang einer 4er-Bombe ist 2.
            # Wir suchen höhere 4er-Bomben, also brauchen wir den kleinstmöglichen Rang nicht zu speichern.
            continue
        cases = []
        for v in unique:
            cases = combine_lists(cases, list([4] if v == 4 else range(4)), 14)
            if not cases:
                break
        if cases:
            c += len(cases)
            print(f"\r{c}", end="")
            table[pho].extend(cases)
    print("\nExpandiert:", c)
    print(f"{(time() - time_start) * 1000:.6f} ms")

    # Daten speichern
    save_table_hi(BOMB, 4, table)


# Generiert eine Datei mit allen möglichen Farbbomben der Länge m, höhere Bombe wird bevorzugt.
# Es wird vorausgesetzt, dass die Karten nur in einer Farbe vorliegen!
def generate_color_bomb_file_hi(m: int):
    assert 5 <= m <= 13  # die längste Farbbombe besteht aus 13 Karten (von 2 bis Ass)

    # todo

    time_start = time()

    # 1. Schritt:
    # alle möglichen Kombinationen (reduziert auf Karte verfügbar/fehlt für 1 Farbe) durchlaufen und Farbbomben auflisten

    c_all = 0
    c_matches = 0
    c_unique = 0
    data = []
    a = [0, 1]                  # 0    1   2  3  4  5  6  7  8  9 10 11 12 13 14
    for row in itertools.product([0], [0], a, a, a, a, a, a, a, a, a, a, a, a, a):  # sortiert nach Rang absteigend
        # Beispiel für row (m = 5, r = 11):
        # r = 1  2  3  4  5  6  7  8  9 10 11 12 13 14
        # (0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 1)
        #        ^--remain---^  ^-------unique-------^
        #        |           |  | <-  m  -> |        |
        #        1         r-m  r-m+1       r       14
        # Von r-m+1 bis r befindet sich die Farbbombe. Darunter muss nicht weiter betrachtet werden.
        # Die Karten darüber (r+1 bis 14) sind wichtig, um das Muster eindeutig zu halten.
        c_all += 1
        print(f"\r{c_all}/8192 = {100 * c_all / 8192:.1f} %", end="")  # 8192 == 2^13
        r = get_max_rank_of_bomb(row, m)
        if r >= 0:
            # im Datensatz ist mindestens eine Farbbombe vorhanden
            unique = row[r - m + 1:]
            c_matches += 1
            found = (r, row[0], unique) in data
            if not found:
                # die Farbbombe ist noch nicht gelistet
                c_unique += 1
                data.append((r, row[0], unique))
    print("\nmatches:", c_matches)
    print("unique:", c_unique)

    # Daten zwischenspeichern
    with open(path.join(config.DATA_PATH, f"cache/prob/~bomb{m:02}.pkl"), 'wb') as fp:
        # noinspection PyTypeChecker
        pickle.dump(data, fp)

    # 2. Schritt:
    # Karte verfügbar/fehlt expandieren zu Kartenanzahl 0,1,2,3,4

    table = [[], []]  # erste Liste ohne Phönix, zweite Liste mit Phönix (bleibt bei Bomben leer)
    c = 0
    for r, pho, unique in data:
        if r <= m + 1:
            # Der kleinste Rang einer 5er-Farbbombe ist 6, der einer 6er-Farbbombe ist 7, usw.
            # Wir suchen höhere Farbbomben, also brauchen wir den kleinstmöglichen Rang nicht zu speichern.
            continue
        cases = []
        for v in unique:
            cases = combine_lists(cases, [v], 14)
            if not cases:
                break
        if cases:
            c += len(cases)
            print(f"\r{c}", end="")
            table[pho].extend(cases)
    print("\nExpandiert:", c)
    print(f"{(time() - time_start) * 1000:.6f} ms")

    # Daten speichern
    save_table_hi(BOMB, m, table)

# --------------------------------------------------------------------------------

def generate_files_hi():
    for t in range(1, 8):
        if t in [SINGLE, BOMB]:  # todo
            continue

        if t == STAIR:
            for m in range(4, 15, 2):
                file = get_filename_hi(t, m)
                if not path.exists(file) and not path.exists(file + ".gz"):
                    generate_file_hi(t, m)
        elif t == STREET:
            for m in range(5, 15):
                file = get_filename_hi(t, m)
                if not path.exists(file) and not path.exists(file + ".gz"):
                    generate_file_hi(t, m)
        elif t == BOMB:
            for m in range(4, 15):
                file = get_filename_hi(t, m)
                if not path.exists(file) and not path.exists(file + ".gz"):
                    generate_file_hi(t, m)
        else:
            assert t in [SINGLE, PAIR, TRIPLE, FULLHOUSE]
            file = get_filename_hi(t)
            if not path.exists(file) and not path.exists(file + ".gz"):
                generate_file_hi(t)


if __name__ == '__main__':  # pragma: no cover
    generate_files_hi()

