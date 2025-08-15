#!/usr/bin/env python

"""
Dieses Skript lädt Tichu-Logdateien vom Spiele-Portal "Brettspielwelt" herunter und speichert sie in Zip-Archiven.

Der erste existierende Eintrag ist 2007-01-09 19:03 (siehe http://tichulog.brettspielwelt.de/200701),
der letzte ist unter http://tichulog.brettspielwelt.de/ verlinkt.
"""

import argparse
import os
from datetime import datetime
from src import config
from src.lib.bsw.download import download_logfiles


def main(args: argparse.Namespace):
    # Argumente auswerten
    y1, m1 = map(int, args.ym1.split("-"))
    y2, m2 = map(int, args.ym2.split("-"))
    path = args.path

    # Download starten
    print(f"Ab Datum: {y1:04d}-{m1:02d}")
    print(f"Bis Datum: {y2:04d}-{m2:02d}")
    print(f"Zielverzeichnis: {path}")
    download_logfiles(path, y1, m1, y2, m2)
    print("fertig")


if __name__ == "__main__":
    print(f"BSW Downloader")

    # Argumente parsen
    today_ = datetime.today().strftime("%Y-%m")
    path_ = os.path.join(config.DATA_PATH, "bsw", "tichulog")
    parser = argparse.ArgumentParser(description="BSW Downloader")
    parser.add_argument("--ym1", default="2007-01", help=f"ab Datum im Format yyyy-mm (Default: 2007-01")
    parser.add_argument("--ym2", default=f"{today_}", help=f"bis Datum im Format yyyy-mm (Default: heute)")
    parser.add_argument("--path", default=f"{path_}", help=f"Zielverzeichnis (Default: {path_})")

    # Main-Routine starten
    main(parser.parse_args())
