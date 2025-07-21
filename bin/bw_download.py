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
        folder = path + '/{0:04d}'.format(y)
        if not os.path.exists(folder):
            os.makedirs(folder)

        # Jahr herunterladen
        a = m1 if y == y1 else 1
        b = m2 if y == y2 else 12
        for m in range(a, b + 1):
            print('Download {0:04d}-{1:02d}...'.format(y, m))

            # Unterordner für den Monat anlegen
            folder = path + '/{0:04d}/{1:04d}{2:02d}'.format(y, y, m)
            if not os.path.exists(folder):
                os.makedirs(folder)

            # Index herunterladen (sofern nicht vorhanden) bzw. letzten Monat aktualisieren
            file = folder + '/index.html'
            if not os.path.exists(file) or (y == y2 and m == m2):
                url = 'http://tichulog.brettspielwelt.de/{0:04d}{1:02d}'.format(y, m)
                r = requests.get(url)
                if r.status_code != 200:
                    raise Exception('Download fehlgeschlagen:' + url)
                with open(file, 'wb') as fp:
                    fp.write(r.content)

            # Dateien zw. 2014-09 und 2018-01 werfen ein UnicodeDecodeError :-(
            ok = True
            with open(file, 'r') as fp:
                # noinspection PyBroadException
                try:
                    for line in fp:
                        line = line.strip()
                except:
                    ok = False
            if not ok:
                print('Repariere ' + file)
                with codecs.open(file, 'r', 'utf-8', errors="ignore") as fp:
                    contents = fp.read()
                with codecs.open(file + '.txt', 'w', 'utf-8') as fp:
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
                file = folder + '/{0}.tch'.format(i)
                if not os.path.exists(file):
                    url = 'http://tichulog.brettspielwelt.de/{0}.tch'.format(i)
                    r = requests.get(url)
                    if r.status_code != 200:
                        raise Exception('Download fehlgeschlagen:' + url)
                    with open(file, 'wb') as fp:
                        fp.write(r.content)

        # Jahr zippen
        with zipfile.ZipFile(path + '/{0:04d}.zip'.format(y), 'w', zipfile.ZIP_DEFLATED) as target:
            for m in range(a, b + 1):
                folder = path + '/{0:04d}/{1:04d}{2:02d}'.format(y, y, m)
                files = sorted(os.listdir(folder))
                for file in files:
                    target.write(folder + '/' + file, '{0:04d}/{1:04d}{2:02d}/'.format(y, y, m) + file)

    print('fertig')


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
