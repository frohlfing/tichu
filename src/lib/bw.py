"""
Dieses Modul stellt Funktionen bereit, die mit Tichu-Logdateien vom Spiele-Portal "Brettspielwelt" umgehen können.
"""

__all__ = "download_logfiles_from_bw", "bw_logfiles", "BWParserError", "BWParserErrorCode", "parse_bw_logfile"


import enum
import os
import requests
from datetime import datetime
from tqdm import tqdm
from typing import Optional
from zipfile import ZipFile, ZIP_DEFLATED


def download_logfiles_from_bw(path: str, y1: int, m1: int, y2: int, m2: int):
    """
    Lädt Tichu-Logdateien vom Spiele-Portal "Brettspielwelt" herunter.

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
                zip_folder = f"{y:04d}/{y:04d}{m:02d}"

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
                    content = r.content.decode(errors="ignore").encode()
                    # Index speichern, sofern der Monat in der Vergangenheit liegt (ansonst kommen ja u.U. noch weitere Einträge hinzu).
                    if y < now.year or (y == now.year and m < now.month):
                        zf.writestr(index_name, content)

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


def bw_logfiles(path: str, y1: Optional[int] = None, m1: Optional[int] = None, y2: Optional[int] = None, m2: Optional[int] = None):
    """
    Generator, der die vom Spiele-Portal "Brettspielwelt" heruntergeladenen Logdateien ausliefert.

    :param path: Das Verzeichnis, in dem die Zip-Archive liegen.
    :param y1: (Optional) ab Jahr
    :param m1: (Optional) ab Monat
    :param y2: (Optional) bis Jahr (einschließlich)
    :param m2: (Optional) bis Monat (einschließlich)
    :yield: (context, Inhalt der *.tch-Datei)
    """
    for zip_name in sorted(os.listdir(path)):
        if not zip_name.endswith('.zip'):
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
            for name in sorted(zf.namelist()):  # z.B. "2025/202507/2410688.tch"
                if not name.endswith('.tch'):
                    continue

                # Logdatei außerhalb des Zeitraums überspringen
                parts = name.split("/")
                month = int(parts[1][4:])
                if (y1 and m1 and year == y1 and month < m1) or (y2 and m2 and year == y2 and month > m2):
                    continue
                game_id = int(parts[2][:-4])

                # Logdatei öffnen und Inhalt zurückgeben
                yield game_id, year, month, zf.read(name).decode()


class BWParserError(Exception):
    """
    Fehler, die beim Parsen auftreten können.
    """
    pass


class BWParserErrorCode(enum.IntEnum):
    """
    Enum für Errorcodes (Auskommentierte Codes werden noch nicht benutzt!)
    """
    UNKNOWN_ERROR = 100
    """Ein unbekannter Fehler ist aufgetreten."""

    NO_RESULT = 101
    """Runde wurde nicht zu Ende gespielt."""


def parse_bw_logfile(game_id: int,  year: int, month: int, content: str) -> dict | None:
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    n = len(lines)  # Anzahl Zeilen

    data = {
        "game_id": game_id,
        "year": year,
        "month": month,
        "player_names": [],
        "rounds": [],
    }

    # Start- und Endezeile jeder Runde finden
    sections = []
    separator = "---------------Gr.Tichukarten------------------"
    if lines[0] != separator:
        print(f"{game_id}, Zeile 1: {lines[0]}\n'{separator}' erwartet")
        return None
    i1 = 0
    for i2 in range(1, n):
        if lines[i2] == separator:
            if not lines[i2-1].startswith('Ergebnis: '):
                print(f"{game_id}, Zeile {n}: {lines[-1]}\n'Ergebnis:' erwartet")
                return None
            sections.append((i1, i2))
            i1 = i2

    # Alle Runden durchlaufen und parsen
    for _section in sections:
        # todo
        pass

    return data

