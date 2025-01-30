__all__ = "load_data_hi",

import config
import gzip
import itertools
import pickle
from os import path, mkdir
from src.lib.combinations import SINGLE, PAIR, TRIPLE, STAIR, FULLHOUSE, STREET, BOMB
from time import time

# -----------------------------------------------------------------------------
# Generiert Hilfstabellen für die Wahrscheinlichkeitsberechnung
# -----------------------------------------------------------------------------

# Gibt den Dateinamen für die Hilfstabellen
def get_filename_hi(t: int, m: int = None):
    folder = path.join(config.DATA_PATH, "lib/prob")
    if not path.exists(folder):
        mkdir(folder)
    name = ['single', 'pair', 'triple', 'stair', 'fullhouse', 'street', 'bomb'][t - 1]
    if t in (STAIR, STREET, BOMB):
        name += f"{m:02}"
    file = path.join(folder, f"{name}_hi.pkl")
    return file


# Speichert die Hilfstabellen
def save_data_hi(t: int, m: int, data: list):
    file = get_filename_hi(t, m)

    # unkomprimiert speichern
    with open(file, 'wb') as fp:
        # noinspection PyTypeChecker
        pickle.dump(data, fp)

    # Komprimiert speichern
    with gzip.open(file + ".gz", "wb") as fp:
        # noinspection PyTypeChecker
        pickle.dump(data, fp)

    # zusätzlich als Textdatei speichern (nützlich zum Debuggen)
    with open(file[:-4] + ".txt", "w") as datei:
        for pho in range(2):
            datei.write(f"Pho={pho}\n")
            for row in data[pho]:
                datei.write(f"{row}\n")

    print(f"Daten in {path.basename(file)} gespeichert", )


# Lädt die Hilfstabellen
def load_data_hi(t: int, m: int, verbose = False) -> list:
    time_start = time()
    file = get_filename_hi(t, m)
    if path.exists(file):
        with open(file, 'rb') as fp:
            data = pickle.load(fp)
    else:
        file += ".gz"
        with gzip.open(file, 'rb') as fp:
            data = pickle.load(fp)
    if verbose:
        print(f"Daten aus {path.basename(file)} geladen ({(time() - time_start) * 1000:.6f} ms)")
    return data


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


# --------------------------------------------------------------------------------

# Ermittelt die höchste Einzelkarte im Datensatz
#
# row: row[0] == Hund, row[1] == Mahjong, row[2] bis row[14] == 2 bis 14, row[15] == Drache, row[16] == Phönix
def get_max_rank_of_single(row: tuple) -> int:
    # erst den Drachen prüfen, dann den Phönix (höchste Schlagkraft zuerst)
    for r in [15, 16, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]:
        if row[r] >= 1:
            return r
    return -1


# Ermittelt das höchste Pärchen im Datensatz
#
# Wenn ein Pärchen vorhanden ist, wird der Rang des Pärchens zurückgegeben, sonst -1.
#
# row: row[0] == Phönix, row[1] bis row[14] == Rang 1 bis 14
def get_max_rank_of_pair(row: tuple) -> int:
    for r in range(14, 1, -1):  # [14 ... 2] (höchster Rang zuerst)
        if row[0]:  # mit Phönix
            if row[r] >= 1:
                return r
        else:  # ohne Phönix
            if row[r] >= 2:
                return r
    return -1


# Ermittelt den höchsten Drilling im Datensatz
#
# Wenn ein Drilling vorhanden ist, wird der Rang des Drillings zurückgegeben, sonst -1.
#
# row: row[0] == Phönix, row[1] bis row[14] == Rang 1 bis 14
def get_max_rank_of_triple(row: tuple) -> int:
    for r in range(14, 1, -1):  # [14 ... 2] (höchster Rang zuerst)
        if row[0]:  # mit Phönix
            if row[r] >= 2:
                return r
        else:  # ohne Phönix
            if row[r] >= 3:
                return r
    return -1


# Ermittelt die höchste Treppe im Datensatz
#
# Wenn eine Treppe vorhanden ist, wird der Rang der Treppe zurückgegeben, sonst -1.
#
# steps = 2: 2,3 bis K,A
# steps = 3: 2,3,4 bis Q,K,A
# steps = 7: 2,3,4,5,6,7,8 bis 8,9,10,J,Q,K,A
#
# row: row[0] == Phönix, row[1] bis row[14] == Rang 1 bis 14
# steps: Anzahl Stufen der Treppe
def get_max_rank_of_stair(row: tuple, steps: int) -> int:
    for r in range(14, steps, -1):  # [14 ... 3] (höchster Rang zuerst)
        r_start = r - steps + 1
        r_end = r + 1  # exklusiv
        if row[0]:  # mit Phönix
            for r_pho in range(r, r_start - 1, -1):  # (vom Ende bis zum Anfang der Treppe)
                if row[r_pho] >= 1 and all(row[i] >= 2 for i in range(r_start, r_end) if i != r_pho):
                    return r
        else:  # ohne Phönix
            if all(row[i] >= 2 for i in range(r_start, r_end)):
                return r
    return -1


# Ermittelt das höchste Fullhouse im Datensatz
#
# Wenn ein Fullhouse vorhanden ist, wird der Rang des Fullhouses zurückgegeben, sonst -1.
#
# row: row[0] == Phönix, row[1] bis row[14] == Rang 1 bis 14
def get_max_rank_of_fullhouse(row: tuple) -> int:
    # todo
    # for r in range(14, 1, -1):  # [14 ... 2] (höchster Rang zuerst)
    #     if row[0]:  # mit Phönix
    #         if row[r] >= 1:
    #             return r
    #     else:  # ohne Phönix
    #         if row[r] >= 2:
    #             return r
    return -1


# Ermittelt die höchste Straße im Datensatz
#
# Wenn eine Straße vorhanden ist, wird der Rang der Straße zurückgegeben, sonst -1.
#
# m = 5:  MAH,2,3,4,5 bis 10,J,Q,K,A
# m = 6:  MAH,2,3,4,5,6 bis 9,10,J,Q,K,A
# m = 14: MAH,2,3,4,5,6,7,8,9,10,J,Q,K,A
#
# row: row[0] == Phönix, row[1] bis row[14] == Rang 1 bis 14
# m: Länge der Straße
def get_max_rank_of_street(row: tuple, m: int) -> int:
    for r in range(14, m - 1, -1):  # [14 ... 5] (höchster Rang zuerst)
        r_start = r - m + 1
        r_end = r + 1  # exklusiv
        if row[0]:  # mit Phönix
            for r_pho in range(r, r_start - 1, -1):  # (vom Ende bis zum Anfang der Straße)
                if row[r_pho] >= 0 and all(row[i] >= 1 for i in range(r_start, r_end) if i != r_pho):
                    return r
        else:  # ohne Phönix
            if all(row[i] >= 1 for i in range(r_start, r_end)):
                return r
    return -1


# Ermittelt die höchste Bombe im Datensatz
#
# Wenn eine Bombe vorhanden ist, wird der Rang der Bombe zurückgegeben, sonst -1.
#
# row: row[0] == undefined, row[1] bis row[14] == Rang 1 bis 14
# m: Länge der Bombe
def get_max_rank_of_bomb(row: tuple, m: int) -> int:
    if m == 4:
        # 4er-Bombe
        for r in range(14, 1, -1):  # [14 ... 2] (höchster Rang zuerst)
            if row[r] == 4:
                return r
    else:
        # Farbbombe
        for r in range(14, m, -1):  # [14 ... 6] (höchster Rang zuerst)
            if all(row[i] == 1 for i in range(r - m + 1, r + 1)):
                return r
    return -1


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
        r = get_max_rank_of_single(row)
        if r >= 0:  # mindestens eine Einzelkarte ist vorhanden
            if r == 16:  # Phönix ist die höchste Karte (Drache ist nicht vorhanden)
                # Rang des Phönix an die Schlagkraft anpassen (der Phönix schlägt das Ass, aber nicht den Drachen)
                r = 15  # 14.5 aufgerundet
            unique = row[r:-1]  # vom aktuellen Rang bis zum Drachen (Phönix wird abgeschnitten)
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
    save_data_hi(SINGLE, 1, table)


# Generiert eine Datei mit allen möglichen Pärchen, höheres Pärchen wird bevorzugt.
def generate_pair_file_hi():
    time_start = time()

    # 1. Schritt:
    # alle möglichen Kombinationen (reduziert 2 Karten/1 Karte/fehlt) durchlaufen und Pärchen auflisten

    c_all = 0
    c_matches = 0
    c_unique = 0
    data = []
    a = [0, 1, 2]                 # 0     1   2  3  4  5  6  7  8  9 10 11 12 13 14
    for row in itertools.product([0, 1], [0], a, a, a, a, a, a, a, a, a, a, a, a, a):  # sortiert nach Rang absteigend (zuerst ohne Phönix, dann mit)
        # Beispiel für row (r = 10):
        # r = 1  2  3  4  5  6  7  8  9 10 11 12 13 14
        # (0, 0, 0, 0, 0, 0, 0, 2, 1, 2, 2, 0, 0, 1, 1)
        #  ^     ^------remain--------^  ^---unique--^
        #  |     |                    |  |           |
        # pho    2                  r-1  r          14
        # r ist der Rang des Pärchens. Darunter muss nicht weiter betrachtet werden.
        # Die Karten darüber sind wichtig, um das Muster eindeutig zu halten.
        c_all += 1
        print(f"\r{c_all}/3188646 = {100 * c_all / 3188646:.1f} %", end="")  # 3188646 == 2 * 3^13
        r = get_max_rank_of_pair(row)
        if r >= 0:  # mindestens ein Pärchen ist vorhanden
            unique = row[r:]
            c_matches += 1
            found = (r, row[0], unique) in data
            if not found:
                # das Pärchen ist noch nicht gelistet
                c_unique += 1
                data.append((r, row[0], unique))
    print("\nmatches:", c_matches)
    print("unique:", c_unique)

    # 2. Schritt:
    # 2 Karten/1 Karte/fehlt expandieren zu Kartenanzahl 0,1,2,3,4

    table = [[], []]  # erste Liste ohne Phönix, zweite Liste mit Phönix
    c = 0
    for r, pho, unique in data:
        if r == 2:
            # Der kleinste Rang eines Pärchens ist 2.
            # Wir suchen höhere Pärchen, also brauchen wir den kleinstmöglichen Rang nicht zu speichern.
            continue
        cases = []
        for v in unique:
            cases = combine_lists(cases, list(range(2, 5) if v == 2 else [v]), 14)
            if not cases:
                break
        if cases:
            c += len(cases)
            print(f"\r{c}", end="")
            table[pho].extend(cases)
    print("\nExpandiert:", c)
    print(f"{(time() - time_start) * 1000:.6f} ms")

    # Daten speichern
    save_data_hi(PAIR, 2, table)


# Generiert eine Datei mit allen möglichen Drillinge, höherer Drilling wird bevorzugt.
def generate_triple_file_hi():
    time_start = time()

    # 1. Schritt:
    # alle möglichen Kombinationen (reduziert auf mind. 3 Karten/2 Karten/weniger) durchlaufen und Drillinge auflisten

    c_all = 0
    c_matches = 0
    c_unique = 0
    data = []
    a = [1, 2, 3]                 # 0     1   2  3  4  5  6  7  8  9 10 11 12 13 14
    for row in itertools.product([0, 1], [0], a, a, a, a, a, a, a, a, a, a, a, a, a):  # sortiert nach Rang absteigend (zuerst ohne Phönix, dann mit)
        # Beispiel für row (r = 10):
        # r = 1  2  3  4  5  6  7  8  9 10 11 12 13 14
        # (1, 1, 1, 1, 1, 1, 1, 2, 1, 2, 3, 1, 1, 1, 1)
        #  ^     ^------remain--------^  ^---unique--^
        #  |     |                    |  |           |
        # pho    2                  r-1  r          14
        # r ist der Rang des Drillings. Darunter muss nicht weiter betrachtet werden.
        # Die Karten darüber sind wichtig, um das Muster eindeutig zu halten.
        c_all += 1
        print(f"\r{c_all}/3188646 = {100 * c_all / 3188646:.1f} %", end="")  # 3188646 == 2 * 3^13
        r = get_max_rank_of_triple(row)
        if r >= 0:  # mindestens ein Drilling ist vorhanden
            unique = row[r:]
            c_matches += 1
            found = (r, row[0], unique) in data
            if not found:
                # der Drilling ist noch nicht gelistet
                c_unique += 1
                data.append((r, row[0], unique))
    print("\nmatches:", c_matches)
    print("unique:", c_unique)

    # 2. Schritt:
    # 3 Karten/2 Karten/weniger expandieren zu Kartenanzahl 0,1,2,3,4

    table = [[], []]  # erste Liste ohne Phönix, zweite Liste mit Phönix
    c = 0
    for r, pho, unique in data:
        if r == 2:
            # Der kleinste Rang eines Drillings ist 2.
            # Wir suchen höhere Drillinge, also brauchen wir den kleinstmöglichen Rang nicht zu speichern.
            continue
        cases = []
        for v in unique:
            cases = combine_lists(cases, [3, 4] if v == 3 else [2] if v == 2 else [0, 1], 14)
            if not cases:
                break
        if cases:
            c += len(cases)
            print(f"\r{c}", end="")
            table[pho].extend(cases)
    print("\nExpandiert:", c)
    print(f"{(time() - time_start) * 1000:.6f} ms")

    # Daten speichern
    save_data_hi(TRIPLE, 3, table)


# Generiert eine Datei mit allen möglichen Treppen der Länge m, höhere Treppe wird bevorzugt.
def generate_stair_file_hi(m: int):
    assert m % 2 == 0
    assert 4 <= m <= 14
    steps = int(m / 2)

    time_start = time()

    # 1. Schritt:
    # alle möglichen Kombinationen (reduziert auf mind. 2 Karten/1 Karte/fehlt) durchlaufen und Treppen auflisten

    c_all = 0
    c_matches = 0
    c_unique = 0
    data = []
    a = [0, 1, 2]  #                0     1   2  3  4  5  6  7  8  9 10 11 12 13 14
    for row in itertools.product([0, 1], [0], a, a, a, a, a, a, a, a, a, a, a, a, a):  # sortiert nach Rang absteigend (zuerst ohne Phönix, dann mit)
        # Beispiel für row (steps = 5, r = 11):
        # r = 1  2  3  4  5  6  7  8  9 10 11 12 13 14
        # (1, 0, 0, 0, 0, 0, 0, 2, 1, 2, 2, 2, 0, 2, 1)
        #  ^     ^--remain---^  ^-------unique-------^
        #  |     |           |  | <-steps-> |        |
        # pho    2     r-steps  r-steps+1   r       14
        # Von r-m+1 bis r befindet sich die Treppe. Darunter muss nicht weiter betrachtet werden.
        # Die Karten darüber (r+1 bis 14) sind wichtig, um das Muster eindeutig zu halten.
        c_all += 1
        print(f"\r{c_all}/3188646 = {100 * c_all / 3188646:.1f} %", end="")  # 3188646 == 2 * 3^13
        r = get_max_rank_of_stair(row, steps)
        if r >= 0:  # mindestens eine Treppe ist vorhanden
            unique = row[r - steps + 1:]
            c_matches += 1
            found = (r, row[0], unique) in data
            if not found:
                # die Treppe ist noch nicht gelistet
                c_unique += 1
                data.append((r, row[0], unique))
    print("\nmatches:", c_matches)
    print("unique:", c_unique)

    # 2. Schritt:
    # Karte mind. 2 Karten/1 Karte/fehlt expandieren zu Kartenanzahl 0,1,2,3,4

    table = [[], []]  # erste Liste ohne Phönix, zweite Liste mit Phönix
    c = 0
    for r, pho, unique in data:
        if r <= steps + 1:
            # Der kleinste Rang einer 2er-Treppe ist 3, der einer 3er-Treppe ist 4, usw.
            # Wir suchen höhere Treppen, also brauchen wir den kleinstmöglichen Rang nicht zu speichern.
            continue
        cases = []
        for v in unique:
            cases = combine_lists(cases, list(range(2, 5) if v == 2 else [v]), 14)
            if not cases:
                break
        if cases:
            c += len(cases)
            print(f"\r{c}", end="")
            table[pho].extend(cases)
    print("\nExpandiert:", c)
    print(f"{(time() - time_start) * 1000:.6f} ms")

    # Daten speichern
    save_data_hi(STAIR, m, table)


# Generiert eine Datei mit allen möglichen Fullhouses, höheres Fullhouse wird bevorzugt.
def generate_fullhouse_file_hi():
    # todo
    pass


# Generiert eine Datei mit allen möglichen Straßen der Länge m, höhere Straße wird bevorzugt.
def generate_street_file_hi(m: int):
    assert 5 <= m <= 14

    time_start = time()

    # 1. Schritt:
    # alle möglichen Kombinationen (reduziert auf Karte verfügbar/fehlt) durchlaufen und Straßen auflisten

    c_all = 0
    c_matches = 0
    c_unique = 0
    data = []
    for row in itertools.product(range(2), repeat=15):  # sortiert nach Rang absteigend (zuerst ohne Phönix, dann mit)
        # Beispiel für row (m = 5, r = 11):
        # r = 1  2  3  4  5  6  7  8  9 10 11 12 13 14
        # (1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1)
        #  ^  ^----remain----^  ^-------unique-------^
        #  |  |              |  | <-  m  -> |        |
        # pho 1            r-m  r-m+1       r       14
        # Von r-m+1 bis r befindet sich die Straße. Darunter muss nicht weiter betrachtet werden.
        # Die Karten darüber (r+1 bis 14) sind wichtig, um das Muster eindeutig zu halten.
        c_all += 1
        print(f"\r{c_all}/32768 = {100 * c_all / 32768:.1f} %", end="")  # 32768 == 2^15
        r = get_max_rank_of_street(row, m)
        if r >= 0:
            # im Datensatz ist mindestens eine Straße vorhanden
            unique = row[r - m + 1:]
            c_matches += 1
            found = (r, row[0], unique) in data
            if not found:
                # die Straße ist noch nicht gelistet
                c_unique += 1
                data.append((r, row[0], unique))
    print("\nmatches:", c_matches)
    print("unique:", c_unique)

    # 2. Schritt:
    # Karte verfügbar/fehlt expandieren zu Kartenanzahl 0,1,2,3,4

    table = [[], []]  # erste Liste ohne Phönix, zweite Liste mit Phönix
    c = 0
    for r, pho, unique in data:
        if r <= m:
            # Der kleinste Rang einer 5er-Straße ist 5, der einer 6er-Straße ist 6, usw.
            # Wir suchen höhere Straßen, also brauchen wir den kleinstmöglichen Rang nicht zu speichern.
            # Eine Straße, die mit dem Mahjong beginnt, fällt also raus.
            continue
        cases = []
        for v in unique:
            cases = combine_lists(cases, list(range(1, 5) if v == 1 else [0]), 14)
            if not cases:
                break
        if cases:
            c += len(cases)
            print(f"\r{c}", end="")
            table[pho].extend(cases)
    print("\nExpandiert:", c)
    print(f"{(time() - time_start) * 1000:.6f} ms")

    # Daten speichern
    save_data_hi(STREET, m, table)


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
    save_data_hi(BOMB, 4, table)


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
    save_data_hi(BOMB, m, table)

# --------------------------------------------------------------------------------

def generate_files_hi():
    file = get_filename_hi(SINGLE)
    if not path.exists(file) and not path.exists(file + ".gz"):
        generate_single_file_hi()

    #file = get_filename_hi(PAIR)
    #if not path.exists(file) and not path.exists(file + ".gz"):
    #    generate_pair_file_hi()

    #file = get_filename_hi(TRIPLE)
    #if not path.exists(file) and not path.exists(file + ".gz"):
    #    generate_triple_file_hi()

    #for m in range(4, 15, 2):
    #    file = get_filename_hi(STAIR, m)
    #    if not path.exists(file) and not path.exists(file + ".gz"):
    #        generate_stair_file_hi(m)

    #file = get_filename_hi(FULLHOUSE)
    #if not path.exists(file) and not path.exists(file + ".gz"):
    #    generate_fullhouse_file_hi()

    #for m in range(5, 15):
    #    file = get_filename_hi(STREET, m)
    #    if not path.exists(file) and not path.exists(file + ".gz"):
    #        generate_street_file_hi(m)

    #file = get_filename_hi(BOMB, 4)
    #if not path.exists(file) and not path.exists(file + ".gz"):
    #    generate_4_bomb_file_hi()

    #for m in range(5, 14):
    #    file = get_filename_hi(BOMB, m)
    #    if not path.exists(file) and not path.exists(file + ".gz"):
    #        generate_color_bomb_file_hi(m)


if __name__ == '__main__':  # pragma: no cover
    #generate_files_hi()
    generate_single_file_hi()
    #generate_color_bomb_file_hi(12)
