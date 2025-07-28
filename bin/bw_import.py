#!/usr/bin/env python

"""
Dieses Modul importiert die vom Spiele-Portal "Brettspielwelt" heruntergeladenen Logdateien in eine Sqlite-DB.
"""

import argparse
import os
from datetime import datetime
from src import config
from src.lib.bw import bw_logfiles, parse_bw_logfile, bw_count_logfiles, validate_bw_data
from tqdm import tqdm


def save_dirty_logfile(game_id, year, month, content):
    file = os.path.join(config.DATA_PATH, f"bw/dirty/{year:04d}{month:02d}/{game_id}.tch")
    os.makedirs(os.path.dirname(file), exist_ok=True)
    with open(file, "w") as f:
        f.write(content)


def main(args: argparse.Namespace):
    """Main-Routine"""
    # Argumente auswerten
    y1, m1 = map(int, args.ym1.split("-"))
    y2, m2 = map(int, args.ym2.split("-"))
    path = args.path

    # Import starten
    print(f"Ab Datum: {y1:04d}-{m1:02d}")
    print(f"Bis Datum: {y2:04d}-{m2:02d}")
    total = bw_count_logfiles(path, y1, m1, y2, m2)
    ok = True
    for game_id, year, month, content in tqdm(bw_logfiles(path, y1, m1, y2, m2), total=total, desc="Parse Logdateien", unit=" Datei"):
        bw_round_datas = parse_bw_logfile(game_id, year, month, content)
        if bw_round_datas is None:
            ok = False
            save_dirty_logfile(game_id, year, month, content)

    if ok:
        print("fertig")


if __name__ == "__main__":
    print(f"BW Importer")

    # Argumente parsen
    today_ = datetime.today().strftime("%Y-%m")
    path_ = os.path.join(config.DATA_PATH, "bw/tichulog")
    parser = argparse.ArgumentParser(description="BW Importer")
    parser.add_argument("--ym1", default="2007-01", help=f"ab Datum im Format yyyy-mm (Default: 2007-01")
    parser.add_argument("--ym2", default=f"{today_}", help=f"bis Datum im Format yyyy-mm (Default: heute)")
    parser.add_argument("--path", default=f"{path_}", help=f"Zielverzeichnis (Default: {path_})")

    # Main-Routine starten
    main(parser.parse_args())
