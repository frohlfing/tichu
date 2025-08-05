#!/usr/bin/env python

"""
Dieses Skript lädt Tichu-Logdateien vom Spiele-Portal "Brettspielwelt" herunter und speichert sie in Zip-Archiven.

Der erste existierende Eintrag ist 2007-01-09 19:03 (siehe http://tichulog.brettspielwelt.de/200701),
der letzte ist unter http://tichulog.brettspielwelt.de/ verlinkt.
"""

import argparse
from datetime import datetime
import os
from src import config
from src.lib.bw import download_logfiles_from_bw


def main(args: argparse.Namespace):
    """Main-Routine"""
    # Argumente auswerten
    y1, m1 = map(int, args.ym1.split("-"))
    y2, m2 = map(int, args.ym2.split("-"))
    path = args.path

    # Download starten
    print(f"Ab Datum: {y1:04d}-{m1:02d}")
    print(f"Bis Datum: {y2:04d}-{m2:02d}")
    print(f"Zielverzeichnis: {path}")
    download_logfiles_from_bw(path, y1, m1, y2, m2)
    print("fertig")


if __name__ == "__main__":
    print(f"BW Downloader")

    # Argumente parsen
    today_ = datetime.today().strftime("%Y-%m")
    path_ = os.path.join(config.DATA_PATH, "bw", "tichulog")
    parser = argparse.ArgumentParser(description="BW Downloader")
    parser.add_argument("--ym1", default="2007-01", help=f"ab Datum im Format yyyy-mm (Default: 2007-01")
    parser.add_argument("--ym2", default=f"{today_}", help=f"bis Datum im Format yyyy-mm (Default: heute)")
    parser.add_argument("--path", default=f"{path_}", help=f"Zielverzeichnis (Default: {path_})")

    # Main-Routine starten
    main(parser.parse_args())
