__all__ = "load_database",

import config
import gzip
import itertools
import pickle
from os import path, mkdir
from src.lib.combinations import SINGLE, PAIR, TRIPLE, STAIR, FULLHOUSE, STREET, BOMB, stringify_type

# -----------------------------------------------------------------------------
# Generiert Hilfstabellen für die Wahrscheinlichkeitsberechnung
# -----------------------------------------------------------------------------

# Gibt den Dateinamen für die Hilfstabellen
#
# t: Typ der Kombination
# m: Länge der Kombination (nur für Treppe, Straße und Bombe relevant)
def get_filename_hi(t: int, m: int = None):
    folder = path.join(config.DATA_PATH, "lib/~prob")
    if not path.exists(folder):
        mkdir(folder)
    name = stringify_type(t, m)
    file = path.join(folder, f"{name}_hi.pkl")
    return file


# Speichert die Hilfstabelle
#
# t: Typ der Kombination
# m: Länge der Kombination
def save_table_hi(t: int, m: int, table: list):
    file = get_filename_hi(t, m)

    # unkomprimiert speichern
    with open(file, 'wb') as fp:
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
#
# t: Typ der Kombination
# m: Länge der Kombination
def load_table_hi(t: int, m: int) -> list:
    file = get_filename_hi(t, m)
    with open(file, 'rb') as fp:
        table = pickle.load(fp)
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


# Ermittelt den höchsten Rang der gegebenen Kombination im Datensatz
#
# Datensatz bei einer Einzelkarte, r = 10:
# r=0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16
#  (0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1)
#   ^----------remain----------^  ^----unique----^  ^
#   |                             |              |  |
#   0                             r             dr pho
# r ist der Rang der Einzelkarte. Darunter muss nichts weiter betrachtet werden.
# Die Karten darüber bis zur 15 sind wichtig, um das Muster eindeutig zu halten.
#
# Datensatz beim Pärchen (und Drilling und 4er-Bombe), r = 10:
# r=0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16
#  (0, 0, 0, 0, 0, 0, 0, 2, 1, 2, 2, 0, 0, 1, 1, 0, 0)
#   ^----------remain----------^  ^---unique--^     ^
#   |                             |           |     |
#   0                             r          14    pho
# r ist der Rang des Pärchens. Darunter muss nichts weiter betrachtet werden.
# Die Karten darüber bis zur 14 sind wichtig, um das Muster eindeutig zu halten.
#
# Datensatz bei einer Treppe, steps = 5, r = 11:
# r=0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16
#  (0, 0, 0, 0, 0, 0, 0, 2, 1, 2, 2, 2, 0, 2, 1, 0, 1)
#   ^-----remain------^  ^-------unique-------^     ^
#   |                    | <-steps-> |        |     |
#   0                    r-steps+1   r       14    pho
# Von r-steps+1 bis r befindet sich die Treppe. Darunter muss nichts betrachtet werden.
# Die Karten darüber bis zur 14 sind wichtig, um das Muster eindeutig zu halten.
#
# Datensatz bei Fullhouse, r = 10:
# r=0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16
#  (0, 0, 1, 1, 0, 3, 1, 2, 1, 1, 3, 0, 1, 0, 1, 0, 0)
#   ^------remain-----^  ^-------unique-------^     ^
#   |                    |        |           |     |
#   0                    r_pair   r_triple   14    pho
# r_pair und r_triple sind die Ränge des Pärchens und des Drillings im Fullhouse.
# r_triple könnte auch vor r_pair liegen! Darunter muss nichts weiter betrachtet werden.
# Die Karten darüber bis zur 14 sind wichtig, um das Muster eindeutig zu halten.
#
# Datensatz bei einer Straße (und Farbbombe), m = 5, r = 11:
# r=0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16
#  (0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1)
#   ^------remain-----^  ^-------unique-------^     ^
#   |                    | <-  m  -> |        |     |
#   0                    r-m+1       r       14    pho
# Von r-m+1 bis r befindet sich die Straße. Darunter muss nicht weiter betrachtet werden.
# Die Karten darüber bis zur 14 sind wichtig, um das Muster eindeutig zu halten.
#
# Wenn die Kombination vorhanden ist, wird r und unique zurückgegeben, sonst -1.
#
# t: Typ der Kombination
# m: Länge der Kombination
# row: Datensatz, Kartenanzahl pro Rang (row[0] == Hund, ..., row[14] == Ass, row[15] == Drache, row[16] == Phönix)
def get_max_rank(t: int, m: int, row: tuple) -> tuple[int, list]:
    if t == SINGLE:
        # erst den Drachen prüfen, dann den Phönix (höchste Schlagkraft zuerst)
        for r in [15, 16, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]:
            if row[r] >= 1:
                if r == 16:  # Phönix ist die höchste Karte (Drache ist nicht vorhanden)
                    # Rang des Phönix an die Schlagkraft anpassen (der Phönix schlägt das Ass, aber nicht den Drachen)
                    r = 15  # 14.5 aufgerundet
                return r, row[r:-1]  # vom Rang der Einzelkarte bis zum Drachen

    if t == PAIR:
        for r in range(14, 1, -1):  # [14 ... 2] (höchster Rang zuerst)
            if row[16]:  # mit Phönix
                if row[r] >= 1:
                    return r, row[r:-2]  # vom Rang des Pärchens bis zum Ass
            else:  # ohne Phönix
                if row[r] >= 2:
                    return r, row[r:-2]  # vom Rang des Pärchens bis zum Ass

    elif t == TRIPLE:
        for r in range(14, 1, -1):  # [14 ... 2] (höchster Rang zuerst)
            if row[16]:  # mit Phönix
                if row[r] >= 2:
                    return r, row[r:-2]  # vom Rang des Drillings bis zum Ass
            else:  # ohne Phönix
                if row[r] >= 3:
                    return r, row[r:-2]  # vom Rang des Drillings bis zum Ass

    elif t == STAIR:
        steps = int(m / 2)
        for r in range(14, steps, -1):  # [14 ... 3] (höchster Rang zuerst)
            r_start = r - steps + 1
            r_end = r + 1  # exklusiv
            if row[16]:  # mit Phönix
                for r_pho in range(r, r_start - 1, -1):  # (vom Ende bis zum Anfang der Treppe)
                    if row[r_pho] >= 1 and all(row[i] >= 2 for i in range(r_start, r_end) if i != r_pho):
                        return r, row[r - steps + 1:-2]  # vom Anfang der Treppe bis zum Ass
            else:  # ohne Phönix
                if all(row[i] >= 2 for i in range(r_start, r_end)):
                    return r, row[r - steps + 1:-2]  # vom Anfang der Treppe bis zum Ass

    elif t == FULLHOUSE:
        for r in range(14, 1, -1):  # [14 ... 2] (höchster Rang zuerst)
            if row[16]:  # mit Phönix
                if row[r] >= 3:  # Drilling mit Rang r
                    for i in range(14, 1, -1):
                        if i != r and row[i] >= 1:  # irgendeine Einzelkarte zw. 14 und 2
                            return r, row[min(r, i):-2]  # vom Rang des Pärchens bzw. Drillings bis zum Ass
                if row[r] == 2:  # Pärchen mit Rang r
                    for i in range(14, 1, -1):
                        if i != r and row[i] >= 2:  # irgendein Pärchen zw. 14 und 2
                            return r, row[min(r, i):-2]  # vom Rang des Pärchens bzw. Drillings bis zum Ass
            else:  # ohne Phönix
                if row[r] >= 3:  # Drilling mit Rang r
                    for i in range(14, 1, -1):
                        if i != r and row[i] >= 2:  # irgendein Pärchen zw. 14 und 2
                            return r, row[min(r, i):-2]  # vom Rang des Pärchens bzw. Drillings bis zum Ass

    elif t == STREET:
        for r in range(14, m - 1, -1):  # [14 ... 5] (höchster Rang zuerst)
            r_start = r - m + 1
            r_end = r + 1  # exklusiv
            if row[16]:  # mit Phönix
                for r_pho in range(r, r_start - 1, -1):  # (vom Ende bis zum Anfang der Straße)
                    if row[r_pho] >= 0 and all(row[i] >= 1 for i in range(r_start, r_end) if i != r_pho):
                        return r, row[r - m + 1:-2]  # vom Anfang der Straße bis zum Ass
            else:  # ohne Phönix
                if all(row[i] >= 1 for i in range(r_start, r_end)):
                    return r, row[r - m + 1:-2]  # vom Anfang der Straße bis zum Ass

    elif t == BOMB:
        if m == 4:
            # 4er-Bombe
            for r in range(14, 1, -1):  # [14 ... 2] (höchster Rang zuerst)
                if row[r] == 4:
                    return r, row[r:-2]  # vom Rang der 4er-Bombe bis zum Ass
        else:
            # Farbbombe
            for r in range(14, m, -1):  # [14 ... 6] (höchster Rang zuerst)
                if all(row[i] == 1 for i in range(r - m + 1, r + 1)):
                    return r, row[r - m + 1:-2]  # vom Anfang der Farbbombe bis zum Ass

    return -1, []


# Generiert eine Hilfstabelle für den gegebenen Typ, höhere Ränge werden bevorzugt.
def create_table_hi(t: int, m: int = None):
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
    else:
        assert t == BOMB and 4 <= m <= 14

    # Mögliche Ränge von/bis
    r_start = 0 if t == SINGLE else int(m/2) + 1 if t == STAIR else m if t == STREET else m + 1 if t == BOMB and m >= 5 else 2
    r_end = 16 if t == SINGLE else 15  # exklusiv (Drache + 1 bzw. Ass + 1)

    # Wir suchen höhere Kombinationen, also brauchen wir den kleinstmöglichen Rang nicht zu speichern.
    # Nur für Bomben brauchen wir alle Ränge.
    if t != BOMB:
        r_start += 1

    # Hilfstabelle
    table = [
        {r: [] for r in range(r_start, r_end)},  # ohne Phönix
        {r: [] for r in range(r_start, r_end)},  # mit Phönix
    ]

    # 1. Schritt:
    # alle möglichen Kombinationen (Kartenanzahl je Rang reduziert) durchlaufen und passende auflisten

    for pho in range(1 if t == BOMB else 2):
        print(f"Erzeuge Hilfstabelle {stringify_type(t, m)}[{pho}]...")
        data = {r: [] for r in range(r_start, r_end)}

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
            assert t == BOMB
            if m == 4:  # 4er-Bombe
                a = [3, 4]
            else:  # Farbbombe
                a = [0, 1]

        # Iterator für die Product-Operation
        if t == SINGLE:
            #        0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15   16
            iter1 = [a, a, a, a, a, a, a, a, a, a, a, a, a, a, a, a, [pho]]
            c_max = len(a) ** 16
        elif t == STREET:
            #         0   1  2  3  4  5  6  7  8  9 10 11 12 13 14  15    16
            iter1 = [[0], a, a, a, a, a, a, a, a, a, a, a, a, a, a, [0], [pho]]  # Dummy für Hund und Drache
            c_max = len(a) ** 14
        else:
            #         0    1   2  3  4  5  6  7  8  9 10 11 12 13 14  15    16
            iter1 = [[0], [0], a, a, a, a, a, a, a, a, a, a, a, a, a, [0], [pho]]  # Dummy für Hund, Mahjong und Drache
            c_max = len(a) ** 13

        c = 0
        for row in itertools.product(*iter1):
            c += 1
            print(f"\r{c}/{c_max} = {100 * c / c_max:.1f} %", end="")
            r, unique = get_max_rank(t, m, row)
            if r >= r_start:
                if not unique in data[r]:
                    data[r].append(unique)
        print()

        # 2. Schritt:
        # Kartenanzahl expandieren zu Kartenanzahl 0,1,2,3,4 (bzw. 0,1 bei Sonderkarten)

        c = 0
        print(f"\rAnzahl Muster: {c}", end="")
        for r, uniques in data.items():
            for unique in uniques:
                cases = []
                for i, v in enumerate(unique):
                    if a == [0, 1]:
                        if t == BOMB:  # Farbbombe
                            assert m >= 5
                            # für die Berechnung einer Farbbombe werden die Karten je Farbe vorgelegt, es gibt sie also pro Rang nur einmal
                            v_expand = [v]
                        elif t in [SINGLE, STREET] and r - m + 1 + i in [0, 1, 15, 16]:  # Sonderkarte
                            v_expand = [v]
                        else:
                            v_expand = [1, 2, 3, 4] if v == 1 else [0]
                    elif a == [1, 2]:
                        v_expand = [2, 3, 4] if v == 2 else [0, 1]
                    elif a == [2, 3]:
                        v_expand = [3, 4] if v == 3 else [0, 1, 2]
                    elif a == [3, 4]:
                        v_expand = [4] if v == 4 else [0, 1, 2, 3]
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


# Erzeugt alle Hilfstabellen, falls nicht vorhanden
def create_tables_hi():
    for t in range(1, 8):
        if t == STAIR:
            for m in range(4, 15, 2):
                file = get_filename_hi(t, m)
                if not path.exists(file) and not path.exists(file + ".gz"):
                    create_table_hi(t, m)
        elif t == STREET:
            for m in range(5, 15):
                file = get_filename_hi(t, m)
                if not path.exists(file) and not path.exists(file + ".gz"):
                    create_table_hi(t, m)
        elif t == BOMB:
            for m in range(4, 15):
                file = get_filename_hi(t, m)
                if not path.exists(file) and not path.exists(file + ".gz"):
                    create_table_hi(t, m)
        else:
            assert t in [SINGLE, PAIR, TRIPLE, FULLHOUSE]
            file = get_filename_hi(t)
            if not path.exists(file) and not path.exists(file + ".gz"):
                create_table_hi(t)


# Legt eine Datenbank mit allen Hilfstabellen an
def create_database():
    # alle Hilfstabellen erzeugen, falls nicht vorhanden
    create_tables_hi()

    # Hilfstabellen laden und übernehmen
    print(f"Erzeuge Datenbank...")
    db = {"low": {}, "high": {}}
    for t in range(1, 8):
        print(f"Lade {stringify_type(t)}")
        db["high"][t] = {}
        if t == STAIR:
            for m in range(4, 15, 2):
                db["high"][t][m] = load_table_hi(t, m)
        elif t == STREET:
            for m in range(5, 15):
                db["high"][t][m] = load_table_hi(t, m)
        elif t == BOMB:
            for m in range(4, 15):
                db["high"][t][m] = load_table_hi(t, m)
        else:
            assert t in [SINGLE, PAIR, TRIPLE, FULLHOUSE]
            m = t
            db["high"][t][m] = load_table_hi(t, m)

    # # Datenbank speichern
    # file = path.join(config.DATA_PATH, "lib/prob.pkl")
    # # unkomprimiert speichern
    # print("Speicher lib/prob.pkl...")
    # with open(file, 'wb') as fp:
    #     # noinspection PyTypeChecker
    #     pickle.dump(db, fp)

    # Datenbank speichern (komprimiert)
    file = path.join(config.DATA_PATH, "lib/prob.pkl.gz")
    print("Speicher lib/prob.pkl.gz...")
    with gzip.open(file, "wb") as fp:
        # noinspection PyTypeChecker
        pickle.dump(db, fp)

    print("Datenbank gespeichert")


# Lädt die Datenbank mit den Hilfstabellen
#
# Die Datenbank hat folgende Struktur:
# cases = db["high"][t][m][pho][r]
def load_database() -> dict:
    # Datenbank laden
    # file = path.join(config.DATA_PATH, "lib/prob.pkl")
    # with open(file, 'rb') as fp:
    #     db = pickle.load(fp)

    # Datenbank laden (aus komprimierte Datei)
    file = path.join(config.DATA_PATH, "lib/prob.pkl.gz")
    with gzip.open(file, 'rb') as fp:
        db = pickle.load(fp)
    return db


if __name__ == '__main__':  # pragma: no cover
    #create_tables_hi()
    create_database()
