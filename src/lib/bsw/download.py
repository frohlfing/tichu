"""
Download der Tichu-Logdateien vom Spiele-Portal "Brettspielwelt".
"""

__all__ = "download_logfiles", "logfiles", "count_logfiles",

import os
import requests
from datetime import datetime
from tqdm import tqdm
from typing import Tuple, Optional, Generator
from zipfile import ZipFile, ZIP_DEFLATED


def download_logfiles(path: str, y1: int, m1: int, y2: int, m2: int):
    """
    Lädt Tichu-Logdateien vom Spiele-Portal "Brettspielwelt" herunter.

    Hierbei wird ein Fortschrittsbalken angezeigt.

    Der erste existierende Eintrag ist 2007-01-09 19:03 (siehe http://tichulog.brettspielwelt.de/200701),
    der letzte ist unter http://tichulog.brettspielwelt.de/ verlinkt.

    :param path: Das Zielverzeichnis.
    :param y1: ab Jahr
    :param m1: ab Monat
    :param y2: bis Jahr (einschließlich)
    :param m2: bis Monat (einschließlich)
    """
    # Zeitpunkt des Downloads
    now = datetime.today()

    for y in range(y1, y2 + 1):
        zip_path = f"{path}/{y:04d}.zip"

        # Lade alle bestehenden Dateinamen aus dem Zip
        existing_files = set()
        if os.path.exists(zip_path):
            with ZipFile(zip_path, 'r') as zf:
                existing_files.update(zf.namelist())

        # Monat von/bis bestimmen
        a = m1 if y == y1 else 1
        b = m2 if y == y2 else 12

        # Jahr herunterladen
        with ZipFile(zip_path, 'a' if os.path.exists(zip_path) else 'w', ZIP_DEFLATED) as zf:
            for m in range(a, b + 1):
                zip_folder = f"{y:04d}{m:02d}"

                # Index einlesen
                index_name = f"{zip_folder}/index.html"
                if index_name in existing_files:
                    # Index aus Zip-Archiv laden
                    with zf.open(index_name) as fp:
                        index_content = fp.read().decode()
                else:  # Index nicht vorhanden
                    # Index herunterladen
                    url = f"http://tichulog.brettspielwelt.de/{y:04d}{m:02d}"
                    r = requests.get(url)
                    if r.status_code != 200:
                        raise Exception(f"Download fehlgeschlagen: {url}")
                    # Index-Dateien zw. 2014-09 und 2018-01 haben ungültige UTF-8-Zeichen. decode().encode() bereinigt das.
                    index_content = r.content.decode(errors="ignore")
                    # Index speichern, sofern der Monat in der Vergangenheit liegt (ansonst kommen ja u.U. noch weitere Einträge hinzu).
                    if y < now.year or (y == now.year and m < now.month):
                        zf.writestr(index_name, index_content.encode())

                # Ersten und letzten Eintrag aus Index entnehmen
                i1 = 0
                i2 = 0
                for line in index_content.splitlines():
                    line = line.strip()
                    if line.startswith("<a href="):
                        k = line.find(".tch")
                        i2 = int(line[10:k])
                        if i1 == 0:
                            i1 = i2

                # Log-Dateien runterladen (sofern nicht vorhanden)
                for i in tqdm(range(i1, i2 + 1), desc=f"Download {y:04d}-{m:02d}"):
                    log_name = f"{zip_folder}/{i}.tch"
                    if log_name not in existing_files:
                        url = f"http://tichulog.brettspielwelt.de/{i}.tch"
                        r = requests.get(url)
                        if r.status_code != 200:
                            raise Exception(f"Download fehlgeschlagen: {url}")
                        zf.writestr(log_name, r.content)


def logfiles(path: str, y1: Optional[int] = None, m1: Optional[int] = None, y2: Optional[int] = None, m2: Optional[int] = None) -> Generator[Tuple[int, int, int, str]]:
    """
    Liefert die vom Spiele-Portal "Brettspielwelt" heruntergeladenen Logdateien aus.

    :param path: Das Verzeichnis, in dem die Zip-Archive liegen.
    :param y1: (Optional) ab Jahr
    :param m1: (Optional) ab Monat
    :param y2: (Optional) bis Jahr (einschließlich)
    :param m2: (Optional) bis Monat (einschließlich)
    :return: Ein Generator, der die Game-ID, Jahr, Monat und Inhalt der *.tch-Datei liefert.
    """
    for zip_name in sorted(os.listdir(path)):
        if not zip_name.endswith(".zip"):
            continue

        # Zip-Archiv außerhalb des Jahresbereichs überspringen
        try:
            year = int(zip_name[:4])
        except ValueError:
            continue
        if (y1 and year < y1) or (y2 and year > y2):
            continue

        # Zip-Archiv öffnen und alle Logdateien durchlaufen
        zip_path = os.path.join(path, zip_name)
        with ZipFile(zip_path, 'r') as zf:
            for name in sorted(zf.namelist()):  # z.B. "202507/2410688.tch"
                if not name.endswith(".tch"):
                    continue

                # Logdatei außerhalb des Zeitraums überspringen
                parts = name.split("/")
                month = int(parts[0][4:])
                if (y1 and m1 and year == y1 and month < m1) or (y2 and m2 and year == y2 and month > m2):
                    continue
                game_id = int(parts[1][:-4])

                # Logdatei öffnen und Inhalt ausliefern
                yield game_id, year, month, zf.read(name).decode()


def count_logfiles(path: str, y1: Optional[int] = None, m1: Optional[int] = None, y2: Optional[int] = None, m2: Optional[int] = None) -> int:
    """
    Zählt die im angegebenen Zeitraum heruntergeladenen Logdateien.

    :param path: Das Verzeichnis, in dem die Zip-Archive liegen.
    :param y1: (Optional) ab Jahr
    :param m1: (Optional) ab Monat
    :param y2: (Optional) bis Jahr (einschließlich)
    :param m2: (Optional) bis Monat (einschließlich)
    :return: Anzahl der Logdateien.
    """
    count = 0
    for zip_name in sorted(os.listdir(path)):
        if not zip_name.endswith(".zip"):
            continue

        # Zip-Archiv außerhalb des Jahresbereichs überspringen
        try:
            year = int(zip_name[:4])
        except ValueError:
            continue
        if (y1 and year < y1) or (y2 and year > y2):
            continue

        # Zip-Archiv öffnen und alle Logdateien durchlaufen
        zip_path = os.path.join(path, zip_name)
        with ZipFile(zip_path, 'r') as zf:
            for name in zf.namelist():  # z.B. "202507/2410688.tch"
                if not name.endswith(".tch"):
                    continue

                # Logdatei außerhalb des Zeitraums überspringen
                parts = name.split("/")
                month = int(parts[0][4:])
                if (y1 and m1 and year == y1 and month < m1) or (y2 and m2 and year == y2 and month > m2):
                    continue

                count += 1
    return count