#!/usr/bin/env python

"""
Dieses Skript spielt eine auf der Brettspielwelt gespielte Partie nach und gibt jeden Entscheidungspunkt für das Ausspielen der Karten zurück.
"""

import argparse
import os
from datetime import datetime
from src import config
from src.lib.bsw.database import BSWDatabase
from time import time

from src.lib.cards import stringify_cards


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

    time_start = time()
    c = 0
    for datasets in db.datasets():
        if c > 1000:
            break
        c += 1
        for dataset in datasets:
            print(stringify_cards(dataset.start_hands[0]))
            print(stringify_cards(dataset.start_hands[1]))
            print(stringify_cards(dataset.start_hands[2]))
            print(stringify_cards(dataset.start_hands[3]))
            print(stringify_cards(dataset.given_schupf_cards[0]))
            print(stringify_cards(dataset.given_schupf_cards[1]))
            print(stringify_cards(dataset.given_schupf_cards[2]))
            print(stringify_cards(dataset.given_schupf_cards[3]))
            for player_index, cards, trick_collector_index in dataset.history:
                print(player_index, stringify_cards(cards), trick_collector_index)
            print(dataset)

    delay = time() - time_start
    print(f"delay={delay * 1000:.6f} ms")


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
