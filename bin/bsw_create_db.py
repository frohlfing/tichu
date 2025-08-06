#!/usr/bin/env python

"""
Dieses Modul importiert die vom Spiele-Portal "Brettspielwelt" heruntergeladenen Logdateien in eine SQLite-Datenbank.
"""

import argparse
import os
from datetime import datetime
from src import config
from src.lib.bsw.database import update_database


def main(args: argparse.Namespace):
    """Main-Routine"""
    # Argumente auswerten
    y1, m1 = map(int, args.ym1.split("-"))
    y2, m2 = map(int, args.ym2.split("-"))
    path = args.path # Pfad zu den heruntergeladenen Log-Archiven
    database = args.database # SQLite-Datenbankdatei

    # Aktualisierung starten
    print(f"Ab Datum: {y1:04d}-{m1:02d}")
    print(f"Bis Datum: {y2:04d}-{m2:02d}")
    print(f"Zip-Archiven: {path}")
    print(f"SQLite-Datenbank: {database}")
    update_database(database, path, y1, m1, y2, m2)
    print("fertig")


if __name__ == "__main__":
    print(f"BW Database Updater")

    # Argumente parsen
    today_ = datetime.today().strftime("%Y-%m")
    path_ = os.path.join(config.DATA_PATH, "bsw", "tichulog")
    database_ = os.path.join(config.DATA_PATH, "bsw", "bsw.sqlite")
    parser = argparse.ArgumentParser(description="Aktualisiert die SQLite-Datenbank für Tichu-Logs.")
    parser.add_argument("--ym1", default="2007-01", help="Start-Datum im Format YYYY-MM")
    parser.add_argument("--ym2", default=today_, help="End-Datum im Format YYYY-MM")
    parser.add_argument("--path", default=path_, help="Pfad zu den Zip-Archiven")
    parser.add_argument("--database", default=database_, help="SQLite-Datenbankdatei")

    # Main-Routine starten
    main(parser.parse_args())
