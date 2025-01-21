import itertools
import pickle
from os import path, mkdir

import config


# Ermittelt die höchste Straße im Datensatz
#
# Wenn eine Straße vorhanden ist, wird der Rang der Straße und der des Phönix zurückgegeben (0 für kein Phönix),
# andernfalls False.
#
# row: row[0] == Phönix, row[1] bis row[14] == Rang 1 bis 14
# m: Länge der Straße
def get_max_rank(row: tuple, m: int):
    for r in range(14, m - 1, -1):  # [14 ... 5] (höchste Rang zuerst)
        r_start = r - m + 1
        r_end = r + 1  # exklusiv
        if row[0]:  # mit Phönix
            for j in range(r_start, r_end):
                if all(row[i] for i in range(r_start, r_end) if i != j):
                    return r, j
        else:  # ohne Phönix
            if all(row[i] for i in range(r_start, r_end)):
                return r, 0
    return False


# Prüft, ob der relevante Bereich des Datensatzes bereits in der Tabelle steht
def is_already_in_table(table: list, row: tuple, m: int, r: int):
    unique = row[r - m + 1:]
    for row_ in table:
        if row_[0] == row[0] and row_[r - m + 1:] == unique:
            return True
    return False


def get_filename():
    folder = path.join(config.DATA_PATH, "lib")
    if not path.exists(folder):
        mkdir(folder)
    file = path.join(folder, "street5_hi.pkl")
    return file


# Daten speichern
def save_data(data):
    file = get_filename()
    with open(file, 'wb') as fp:
        # noinspection PyTypeChecker
        pickle.dump(data, fp)

    # zusätzlich als Textdatei speichern (nützlich zum Debuggen)
    with open(file[:-4] + ".txt", "w") as datei:
        datei.write("pho, r, top\n")
        for row in data:
            datei.write(f"{row}\n")

    print("Daten gespeichert", file)


# Daten laden
def load_data():
    with open(get_filename(), 'rb') as fp:
        data = pickle.load(fp)
    return data


# Generiert eine Tabelle mit allen möglichen Straßen der Länge m, höchster Rang zuerst
#
# Es werden erst alle Fälle ohne Phönix aufgeführt, dann mit.
# Die relevanten Informationen werden in eine Datei gespeichert.
#
# Beispiel für Straße der Länge 5, Ausschnitt bei r = 11:
# Generierter Tabelle                              relevante Info
# r = 1  2  3  4  5  6  7  8  9 10 11 12 13 14     (pho, r  (  top  ))
# (1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0)    ( 8, 11, (0, 0, 0))
# (1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 1)    ( 8, 11, (0, 0, 1))
# (1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0)    ( 9, 11, (0, 0, 0))
# (1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1)    ( 9, 11, (0, 0, 1))
# (1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 1, 0)    ( 9, 11, (0, 1, 0))
# (1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0)    (10, 11, (0, 0, 0))
# (1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 0, 0, 1) -> (10, 11, (0, 0, 1))
# (1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 0, 1, 0)    (10, 11, (0, 1, 0))
# (1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 0, 1, 1)    (10, 11, (0, 1, 1))
# (1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0)    (11, 11, (0, 0, 0))
# (1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 1)    (11, 11, (0, 0, 1))
# (1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 0)    (11, 11, (0, 1, 0))
# (1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1)    (11, 11, (0, 1, 1))
#  ^  ^---remain-----^  ^----comb---^  ^-top-^
# pho 1            r-m  r-m+1       r  r+1  14
#
# relevante Info:
# r: höchster Rang
# pho: Rang des Phönix (0 == ohne Phönix)
# top: Muster von r+1 bis 14
#
# Die Karten von 1 bis r-m sind einzeln nicht relevant.
# Von r-m+1 bis r befindet sich die Straße. An der Stelle des Phönix ist eine 0 (keine Karte mit
# diesem Rang), an jeder anderen Stelle der Straße ist eine 1 (mindestens eine Karte erforderlich).
# Die Karten überhalb der Straße (r+1 bis 14) sind wichtig, um das Muster eindeutig zu halten.
# Dadurch schließen sich die Teilmengen gegenseitig aus.
def generate_table(m: int):  # pragma: no cover
    c_all = 0
    c_matches = 0
    c_unique = 0
    table = []
    data = []
    for row in itertools.product(range(2), repeat=15):  # alle möglichen Kombinationen durchlaufen...
        c_all += 1
        res = get_max_rank(row, m)
        if res:
            # im Datensatz ist mindestens eine Straße vorhanden
            r, pho = res
            c_matches += 1
            found = is_already_in_table(table, row, m, r)
            if not found:
                # die Straße ist noch nicht in der Tabelle aufgeführt
                c_unique += 1
                top = row[r + 1:]
                table.append(row)  # Datensatz zwischenspeichern
                data.append((pho, r, top))  # relevante Daten übernehmen
                print(row, f" -> pho: {pho}, r: {r} (start: {r - m + 1}), top: {top}")
            # else:
            #     print(row, f"r: {r}")

    print("all:", c_all)
    print("matches:", c_matches)
    print("unique:", c_unique)

    # relevante Daten speichern
    save_data(data)
    data = load_data()
    print("Datensätze:", len(data))


if __name__ == '__main__':  # pragma: no cover
    generate_table(5)
