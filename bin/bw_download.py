#!/usr/bin/env python

"""
Dieses Modul lädt Tichu-Logdateien vom Spiele-Portal "Brettspielwelt" herunter.

Der erste existierende Eintrag ist 2007-01-09 19:03 (siehe http://tichulog.brettspielwelt.de/200701),
der letzte ist unter http://tichulog.brettspielwelt.de/ verlinkt.
"""

import argparse
from datetime import datetime
from tqdm import tqdm
import requests
import os
import codecs
import gzip
import itertools
import pickle
from src import config
from time import time
import zipfile


def download(path: str, y1: int, m1: int, y2: int, m2: int):
    """
    Lädt Tichu-Logdateien vom Spiele-Portal "Brettspielwelt" herunter.

    :param path: Das Zielverzeichnis.
    :param y1: ab Jahr
    :param m1: ab Monat
    :param y2: bis Jahr (einschließlich)
    :param m2: bis Monat (einschließlich)
    """
    for y in range(y1, y2 + 1):
        # Unterordner für das Jahr anlegen
        if not os.path.exists(f"{path}/{y:04d}"):
            os.makedirs(f"{path}/{y:04d}")

        # Jahr herunterladen
        a = m1 if y == y1 else 1
        b = m2 if y == y2 else 12
        for m in range(a, b + 1):
            print(f"Download {y:04d}-{m:02d}...")

            # Unterordner für den Monat anlegen
            subfolder = f"{y:04d}/{y:04d}{m:02d}"
            if not os.path.exists(f"{path}/{subfolder}"):
                os.makedirs(f"{path}/{subfolder}")

            # Index herunterladen (sofern nicht vorhanden) bzw. letzten Monat aktualisieren
            file = f"{path}/{subfolder}/index.html"
            if not os.path.exists(file) or (y == y2 and m == m2):
                url = f"http://tichulog.brettspielwelt.de/{y:04d}{m:02d}"
                r = requests.get(url)
                if r.status_code != 200:
                    raise Exception(f"Download fehlgeschlagen: {url}")
                with open(file, "wb") as fp:
                    fp.write(r.content)

            # Dateien zw. 2014-09 und 2018-01 werfen ein UnicodeDecodeError :-(
            ok = True
            with open(file, "r") as fp:
                # noinspection PyBroadException
                try:
                    for line in fp:
                        line = line.strip()
                except:
                    ok = False
            if not ok:
                print(f"Repariere {file}")
                with codecs.open(file, "r", "utf-8", errors="ignore") as fp:
                    contents = fp.read()
                with codecs.open(f"{file}.txt", "w", "utf-8") as fp:
                    fp.write(contents)

            # Ersten und letzten Eintrag aus Index entnehmen
            i1 = 0
            i2 = 0
            with open(file, 'r') as fp:
                for line in fp:
                    line = line.strip()
                    if line.startswith('<a href='):
                        k = line.find('.tch')
                        i2 = int(line[10:k])
                        if i1 == 0:
                            i1 = i2

            # Log-Dateien runterladen (sofern nicht vorhanden)
            for i in tqdm(range(i1, i2 + 1)):
                file = f"{path}/{subfolder}/{i}.tch"
                if not os.path.exists(file):
                    url = f"http://tichulog.brettspielwelt.de/{i}.tch"
                    r = requests.get(url)
                    if r.status_code != 200:
                        raise Exception(f"Download fehlgeschlagen: {url}")
                    with open(file, "wb") as fp:
                        fp.write(r.content)

        # Jahr zippen
        if not os.path.exists(f"{path}/{y:04d}.zip"):
            with zipfile.ZipFile(f"{path}/{y:04d}.zip", 'w', zipfile.ZIP_DEFLATED) as target:
                for m in range(a, b + 1):
                    subfolder = f"{y:04d}/{y:04d}{m:02d}"
                    files = sorted(os.listdir(f"{path}/{subfolder}"))
                    for file in files:
                        target.write(f"{path}/{subfolder}/{file}", f"{subfolder}/{file}")

    print("fertig")



def main(args: argparse.Namespace):
    """Main-Routine"""

    # Argumente auswerten
    y1, m1 = map(int, args.ym1.split("-"))
    y2, m2 = map(int, args.ym2.split("-"))
    path = args.path

    # Download starten
    print(f"Ab Datum: {y1}-{m1:02d}")
    print(f"Bis Datum: {y2}-{m2:02d}")
    print(f"Zielverzeichnis: {path}")
    download(os.path.join(os.path.join(path, "~download")), y1, m1, y2, m2)


if __name__ == "__main__":
    print(f'Tichu-Logdateien vom Spiele-Portal "Brettspielwelt" herunterladen')

    # Argumente parsen
    today_ = datetime.today().strftime("%Y-%m")
    path_ = os.path.join(config.DATA_PATH, "bw/tichulog")
    parser = argparse.ArgumentParser(description="Tichu-Logdateien herunterladen.")
    parser.add_argument("--ym1", default="2007-01", help=f"ab Datum im Format yyyy-mm (Default: 2007-01")
    parser.add_argument("--ym2", default=f"{today_}", help=f"bis Datum im Format yyyy-mm (Default: heute)")
    parser.add_argument("--path", default=f"{path_}", help=f"Zielverzeichnis (Default: {path_})")

    # Main-Routine starten
    main(parser.parse_args())
