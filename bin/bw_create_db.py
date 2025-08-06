#!/usr/bin/env python

"""
Dieses Modul importiert die vom Spiele-Portal "Brettspielwelt" heruntergeladenen Logdateien in eine SQLite-Datenbank.
"""

import argparse
import os
from datetime import datetime
from src import config
from src.lib.bw import update_bw_database, BWValidationStats, migrate


def main(args: argparse.Namespace):
    """Main-Routine"""
    migrate(database=args.database)
    exit(0)

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
    stats: BWValidationStats = {"games_total": 0, "games_fails": 0, "rounds_total": 0, "rounds_fails": 0, "error_summary": {}, "duration": 0}
    try:
        stats = update_bw_database(database, path, y1, m1, y2, m2)
    except KeyboardInterrupt:
        print("\nUpdate durch Benutzer abgebrochen.")
    except Exception as e:
        print(f"\nEin Fehler ist aufgetreten: {e}")

    print(f"Anzahl Partien gesamt: {stats.get("games_total")}")
    print(f"Anzahl Partien fehlerhaft: {stats.get("games_fails")}")
    print(f"Anzahl Runden gesamt: {stats.get("rounds_total")}")
    print(f"Anzahl Runden fehlerhaft: {stats.get("rounds_fails")}")
    print(f"Gesamtzeit: {stats.get("duration", 0) / 60:.0f} Minuten")
    if stats.get("games_total"):
        print(f"Zeit pro Partie: {stats.get("duration", 0) * 1000 / stats.get("games_total"):.3f} ms")
    for code, count in stats.get("error_summary", {}).items():
        print(f"{code.name}: {count} Fehler")


if __name__ == "__main__":
    print(f"BW Database Updater")

    # Argumente parsen
    today_ = datetime.today().strftime("%Y-%m")
    path_ = os.path.join(config.DATA_PATH, "bw", "tichulog")
    database_ = os.path.join(config.DATA_PATH, "bw", "bw.sqlite")
    parser = argparse.ArgumentParser(description="Aktualisiert die SQLite-Datenbank für Tichu-Logs.")
    parser.add_argument("--ym1", default="2007-01", help="Start-Datum im Format YYYY-MM")
    parser.add_argument("--ym2", default=today_, help="End-Datum im Format YYYY-MM")
    parser.add_argument("--path", default=path_, help="Pfad zu den Zip-Archiven")
    parser.add_argument("--database", default=database_, help="SQLite-Datenbankdatei")

    # Main-Routine starten
    main(parser.parse_args())
