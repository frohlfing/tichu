__all__ = "get_table",

import config
import gzip
import pickle
from os import path
from src.lib.combinations import SINGLE, PAIR, TRIPLE, STAIR, FULLHOUSE, STREET, BOMB, stringify_type
from src.lib.prob.tables_hi import create_tables_hi, load_table_hi
from src.lib.prob.tables_lo import create_tables_lo, load_table_lo
from time import time
from timeit import timeit


# Legt eine Datenbank mit allen Hilfstabellen an
def create_database(zipped = True):
    # alle Hilfstabellen erzeugen, falls nicht vorhanden
    create_tables_lo()
    create_tables_hi()

    # Hilfstabellen laden und übernehmen
    print(f"Erzeuge Datenbank...")
    db = {"low": {}, "high": {}}

    # low
    for t in range(1, 8):
        print(f"Lade {stringify_type(t)}")
        db["low"][t] = {}
        if t == STAIR:
            for m in range(4, 15, 2):
                db["low"][t][m] = load_table_lo(t, m)
        elif t == STREET:
            for m in range(5, 15):
                db["low"][t][m] = load_table_lo(t, m)
        elif t == BOMB:
            for m in range(4, 15):
                db["low"][t][m] = load_table_lo(t, m)
        else:
            assert t in [SINGLE, PAIR, TRIPLE, FULLHOUSE]
            if t == FULLHOUSE:
                continue  # todo
            m = t
            db["low"][t][m] = load_table_lo(t, m)

    # high
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

    # Datenbank speichern
    if zipped:
        # komprimiert
        file = path.join(config.DATA_PATH, "lib/prob.pkl.gz")
        print("Speicher lib/prob.pkl.gz... ", end="")
        with gzip.open(file, "wb") as fp:
            # noinspection PyTypeChecker
            pickle.dump(db, fp)
    else:
        # unkomprimiert
        file = path.join(config.DATA_PATH, "lib/prob.pkl")
        # unkomprimiert speichern
        print("Speicher lib/prob.pkl... ", end="")
        with open(file, 'wb') as fp:
            # noinspection PyTypeChecker
            pickle.dump(db, fp)
    print("Ok")


# Lädt die Datenbank mit den Hilfstabellen
#
# Die Datenbank hat folgende Struktur:
# cases = db["high"][t][m][pho][r]
def load_database() -> dict:
    # Datenbank laden
    file = path.join(config.DATA_PATH, "lib/prob.pkl")
    if path.exists(file):
        with open(file, 'rb') as fp:
            db = pickle.load(fp)
        return db

    # Datenbank laden (aus komprimierte Datei)
    file = path.join(config.DATA_PATH, "lib/prob.pkl.gz")
    with gzip.open(file, 'rb') as fp:
        db = pickle.load(fp)
    return db


def benchmark_load_data():  # pragma: no cover
    # Ladezeit messen
    print(f"{timeit(lambda: load_database(), number=5) * 1000 / 5:.6f} ms")  # 1890 ms


# Datenbank mit Hilfstabellen
_db = None


# Datenbank laden und Hilfstabelle zurückgeben
#
# low_or_high: "low" oder "high"
# t: Typ der Kombination
# m: Länge der Kombination
def get_table(low_or_high: str, t: int, m: int) -> list:
    global _db
    if not _db:
        print("Lade Datenbank... ", end="")
        time_start = time()
        _db = load_database()
        print(f"({(time() - time_start) * 1000:.3f} ms) ok")
    return _db[low_or_high][t][m]


if __name__ == '__main__':  # pragma: no cover
    create_database(zipped=False)
