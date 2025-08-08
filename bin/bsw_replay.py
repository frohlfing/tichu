#!/usr/bin/env python

"""
Dieses Skript spielt eine auf der Brettspielwelt gespielte Partie nach und gibt jeden Entscheidungspunkt für das Ausspielen der Karten zurück.
"""

import argparse
import os
from datetime import datetime
from src import config
from src.lib.bsw.database import BSWDatabase


def main(args: argparse.Namespace):
    """Main-Routine"""
    # Argumente auswerten
    y1, m1 = map(int, args.ym1.split("-"))
    y2, m2 = map(int, args.ym2.split("-"))
    database = args.database # SQLite-Datenbankdatei
    db = BSWDatabase(database)

    # Simulation starten
    print(f"Ab Datum: {y1:04d}-{m1:02d}")
    print(f"Bis Datum: {y2:04d}-{m2:02d}")
    print(f"SQLite-Datenbank: {database}")
    db.replay(y1, m1, y2, m2)
    print("fertig")


if __name__ == "__main__":
    print(f"BSW Replay-Simulator")

    # Argumente parsen
    today_ = datetime.today().strftime("%Y-%m")
    path_ = os.path.join(config.DATA_PATH, "bsw", "tichulog")
    database_ = os.path.join(config.DATA_PATH, "bsw", "bsw.sqlite")
    parser = argparse.ArgumentParser(description="BSW Replay-Simulator")
    parser.add_argument("--ym1", default="2007-01", help="Start-Datum im Format YYYY-MM")
    parser.add_argument("--ym2", default=today_, help="End-Datum im Format YYYY-MM")
    parser.add_argument("--database", default=database_, help="SQLite-Datenbankdatei")

    # Main-Routine starten
    main(parser.parse_args())
