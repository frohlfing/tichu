#!/usr/bin/env python

"""
Dieses Modul importiert die vom Spiele-Portal "Brettspielwelt" heruntergeladenen Logdateien in eine Sqlite-DB.
"""

import argparse
import os
from datetime import datetime
from src import config
from src.lib.bw import bw_logfiles, parse_bw_logfile, bw_count_logfiles
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
        result = parse_bw_logfile(game_id, year, month, content)
        if result is None:
            ok = False
            save_dirty_logfile(game_id, year, month, content)
            #break

    if ok:
        print("fertig")


import os
import zipfile

def flatten_zip_archives(path: str, dest: str):
    """
    Entfernt das erste Verzeichniselement innerhalb jeder ZIP-Datei (z. B. '2024/')
    und schreibt eine neue ZIP ohne diese Struktur ins Zielverzeichnis.

    :param path: Quellverzeichnis mit ZIP-Dateien
    :param dest: Zielverzeichnis für bereinigte ZIP-Dateien
    """
    os.makedirs(dest, exist_ok=True)

    for fname in sorted(os.listdir(path)):
        if not fname.endswith(".zip"):
            continue

        src_zip_path = os.path.join(path, fname)
        dst_zip_path = os.path.join(dest, fname)

        with zipfile.ZipFile(src_zip_path, 'r') as src_zip:
            with zipfile.ZipFile(dst_zip_path, 'w', zipfile.ZIP_DEFLATED) as dst_zip:
                for name in src_zip.namelist():
                    # Entferne das erste Verzeichnislevel (Jahr)
                    new_name = name[5:]
                    # Inhalt kopieren
                    data = src_zip.read(name)
                    dst_zip.writestr(new_name, data)

        print(f"✔ Archiv '{fname}' verarbeitet → {dst_zip_path}")




if __name__ == "__main__":
    flatten_zip_archives(os.path.join(config.DATA_PATH, "bw/tichulog"), os.path.join(config.DATA_PATH, "bw/tichulog2"))
    exit(0)

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
