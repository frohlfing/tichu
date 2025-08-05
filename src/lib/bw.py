"""
Dieses Modul definiert Funktionen zum Aufbau einer Datenbank mit Tichu-Logdateien vom Spiele-Portal "Brettspielwelt".
"""

__all__ = "download_logfiles_from_bw", "bw_logfiles", "bw_count_logfiles", \
    "BWLog", "BWLogEntry", "BWParserError", "parse_bw_logfile", \
    "BWErrorCode", "BWValidationStats", "validate_bw_log", \
    "update_bw_database", \
    "replay_play"

import enum
import json
import os
import requests
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from src.lib.cards import Cards, validate_cards, parse_card, stringify_card, sum_card_points, is_wish_in, other_cards, CardSuit
from src.lib.combinations import get_trick_combination, Combination, CombinationType, build_action_space, build_combinations
from src.public_state import PublicState
from src.private_state import PrivateState
from time import time
from tqdm import tqdm
from typing import List, Tuple, Optional, Generator, TypedDict
from zipfile import ZipFile, ZIP_DEFLATED

# ------------------------------------------------------
# 1) Download
# ------------------------------------------------------

def download_logfiles_from_bw(path: str, y1: int, m1: int, y2: int, m2: int):
    """
    Lädt Tichu-Logdateien vom Spiele-Portal "Brettspielwelt" herunter.

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


def bw_logfiles(path: str, y1: Optional[int] = None, m1: Optional[int] = None, y2: Optional[int] = None, m2: Optional[int] = None) -> Generator[Tuple[int, int, int, str]]:
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

                # Logdatei öffnen und Inhalt zurückgeben
                yield game_id, year, month, zf.read(name).decode()


def bw_count_logfiles(path: str, y1: Optional[int] = None, m1: Optional[int] = None, y2: Optional[int] = None, m2: Optional[int] = None) -> int:
    """
    Ermittelt die Anzahl der Logdateien im angegebenen Zeitraum.

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

# ------------------------------------------------------
# 2) Parsen
# ------------------------------------------------------

class BWParserError(Exception):
    """
    Ein Fehler, der beim Parsen einer Logdatei aufgetreten ist.
    """
    def __init__(self, message: str, game_id: int, year: int, month: int, line_index: int, *args):
        """
        :param message: Fehlermeldung.
        :param game_id: ID der Partie.
        :param year: Jahr der Logdatei.
        :param month: Monat der Logdatei.
        :param line_index: Zeilenindex der Logdatei.
        """
        super().__init__(message, *args)
        self.message = message
        self.game_id = game_id
        self.year = year
        self.month = month
        self.line_index = line_index

    def __str__(self):
        return f"{self.message} - {self.year:04d}{self.month:02d}/{self.game_id}.tch, Zeile {self.line_index + 1}"


@dataclass
class BWLogEntry:
    """
    Datencontainer für eine geparste Runde aus der Logdatei.

    :ivar game_id: ID der Partie.
    :ivar round_index: Index der Runde innerhalb der Partie.
    :ivar line_index: Zeilenindex der Logdatei, in der die Runde beginnt.
    :ivar content: Abschnitt aus der Logdatei mit dieser Runde.
    :ivar player_names: Die Namen der 4 Spieler dieser Runde.
    :ivar grand_tichu_hands: Die ersten 8 Handkarten der vier Spieler zu Beginn der Runde.
    :ivar start_hands: Die 14 Handkarten der Spieler vor dem Schupfen.
    :ivar given_schupf_cards: Abgegebene Tauschkarten (an rechten Gegner, Partner, linken Gegner).
    :ivar tichu_positions: Position in der Historie, an der Tichu angesagt wurde (-3 == kein Tichu, -2 == großes Tichu, -1 == Ansage vor oder während des Schupfens).
    :ivar bomb_owners: Gibt für jeden Spieler an, ob eine Bombe auf der Hand ist.
    :ivar wish_value: Der gewünschte Kartenwert (2 bis 14, -1 == kein Eintrag).
    :ivar dragon_recipient: Index des Spielers, der den Drachen bekommen hat (-1 == kein Eintrag).
    :ivar score: Rundenergebnis (Team20, Team31)
    :ivar history: Spielzüge. Jeder Spielzug ist ein Tuple: Spieler-Index + gespielte Karten + Zeilenindex der Logdatei.
    :ivar year: Jahr der Logdatei.
    :ivar month: Monat der Logdatei.

    """
    game_id: int = -1
    round_index: int = -1
    line_index: int = -1
    content: str = ""
    player_names: List[str] = field(default_factory=lambda: ["", "", "", ""])
    grand_tichu_hands: List[str] = field(default_factory=lambda: ["", "", "", ""])
    start_hands: List[str] = field(default_factory=lambda: ["", "", "", ""])
    given_schupf_cards: List[str] = field(default_factory=lambda: ["", "", "", ""])
    tichu_positions: List[int] = field(default_factory=lambda: [-3, -3, -3, -3])
    bomb_owners: List[bool] = field(default_factory=lambda: [False, False, False, False])
    wish_value: int = 0
    dragon_recipient: int = -1
    score: Tuple[int, int] = (0, 0)
    history: List[Tuple[int, str, int]] = field(default_factory=list)
    year: int = -1
    month: int = -1


# Type-Alias für die geparsten Daten einer Logdatei (einer Partie)
BWLog = List[BWLogEntry]


def parse_bw_logfile(game_id: int, year: int, month: int, content: str) -> Optional[BWLog]:
    """
    Parst eine Tichu-Logdatei vom Spiele-Portal "Brettspielwelt".

    Zurückgegeben wird eine Liste mit den Rundendaten der Partie.
    Wurde die letzte Runde abgebrochen, wird sie ignoriert.

    :param game_id: ID der Partie.
    :param year: Jahr der Logdatei.
    :param month: Monat der Logdatei.
    :param content: Inhalt der Logdatei (eine Partie).
    :return: Die eingelesenen Rundendaten der Partie.
    :raises BWParserError: Wenn die Logdatei syntaktisch unerwartet ist. Bekannte Fehler werden abgefangen.
    """
    bw_log = []  # Liste der Rundendaten
    lines = content.splitlines()
    num_lines = len(lines)  # Anzahl Zeilen
    line_index = 0 # Zeilenindex
    while line_index < num_lines:
        # Datencontainer für eine Runde aus der Logdatei
        log_entry = BWLogEntry(game_id=game_id, round_index=len(bw_log), line_index=line_index, year=year, month=month)
        try:
            # Jede Runde beginnt mir der Zeile "---------------Gr.Tichukarten------------------"

            separator = "---------------Gr.Tichukarten------------------"
            line = lines[line_index].strip()
            if line != separator:
                raise BWParserError(f"Seperator 'Gr.Tichukarten' erwartet", game_id, year, month, line_index)
            line_index += 1

            # Es folgt die Aufzählung der 4 Spieler mit ihren ersten 8 Handkarten, z.B.:
            # (0)Smocker Dr BD R9 G8 B6 G5 G4 Hu
            # (1)charliexyz GD BB R10 S9 G9 S6 B5 S4
            # (2)Amb4lamps23 B10 B9 R8 B7 B4 S3 G3 S2
            # (3)Andreavorn GK SD RB G7 R7 G6 R4 G2

            # Nach der Trennzeile "---------------Startkarten------------------"
            # werden die Spieler nochmals genauso aufgeführt, diesmal aber mit 14 Handkarten.

            for k in [8, 14]:
                if k == 14:
                    separator = "---------------Startkarten------------------"
                    line = lines[line_index].strip()
                    if line != separator:
                        raise BWParserError(f"Seperator 'Startkarten' erwartet", game_id, year, month, line_index)
                    line_index += 1
                for player_index in range(4):
                    line = lines[line_index].strip()
                    # Index des Spielers prüfen
                    if line[:3] != f"({player_index})":
                        raise BWParserError("Spieler-Index erwartet", game_id, year, month, line_index)
                    j = line.find(" ")
                    if j == -1:
                        raise BWParserError("Leerzeichen erwartet", game_id, year, month, line_index)
                    name = line[3:j].strip()
                    cards = line[j + 1:].replace("10", "Z")
                    # Name des Spielers und Handkarten übernehmen
                    if k == 8:
                        log_entry.player_names[player_index] = name
                        log_entry.grand_tichu_hands[player_index] = cards
                    else:
                        log_entry.start_hands[player_index] = cards
                    line_index += 1

            # Es folgen Zeilen mit "Grosses Tichu:", danach mit "Tichu:", sofern Tichu angesagt wurde, z.B.:
            # Tichu: (1)charliexyz

            for grand in [True, False]:
                while lines[line_index].strip().startswith("Grosses Tichu: " if grand else "Tichu: "):
                    line = lines[line_index].strip()
                    # Index des Spielers ermitteln
                    s = line[15:] if grand else line[7:]
                    if s[:3] not in ["(0)", "(1)", "(2)", "(3)"]:
                        raise BWParserError("Spieler-Index erwartet", game_id, year, month, line_index)
                    player_index = int(s[1])
                    # Tichu-Ansage übernehmen
                    log_entry.tichu_positions[player_index] = -2 if grand else -1
                    line_index += 1

            # Es folgt die Zeile "Schupfen:".

            line = lines[line_index].strip()
            if line != "Schupfen:":
                if game_id <= 2215951 and line == "---------------Gr.Tichukarten------------------":
                    # Bugfix: Hier wird abrupt eine neue Runde gestartet.
                    # In 201202/1045639.tch trat dieser Fehler erstmalig in Zeile 734 auf.
                    # Zwischen 2014-08 (ab 1792439.tch) und 2018-09 (bis 2215951.tch) trat er insgesamt 34 mal auf, und
                    # zwar immer in der ersten Runde (Zeile 11). Der Fehler wurde wohl gefixt und wird nicht mehr erwartet.
                    return bw_log
                raise BWParserError("'Schupfen:' erwartet", game_id, year, month, line_index)
            line_index += 1

            # Jetzt werden die 4 Spieler mit den Tauschkarten aufgelistet, z.B.:
            # (0)Smocker gibt: charliexyz: Hu - Amb4lamps23: BD - Andreavorn: R9 -
            # (1)charliexyz gibt: Amb4lamps23: S4 - Andreavorn: GA - Smocker: B3 -
            # (2)Amb4lamps23 gibt: Andreavorn: B2 - Smocker: G3 - charliexyz: S2 -
            # (3)Andreavorn gibt: Smocker: R7 - charliexyz: RB - Amb4lamps23: G2 -

            for player_index in range(4):
                line = lines[line_index].strip()
                # Index des Spielers prüfen
                if line[:3] != f"({player_index})":
                    raise BWParserError("Spieler-Index erwartet", game_id, year, month, line_index)
                j = line.find(" gibt: ")
                if j == -1:
                    raise BWParserError("' gibt:' erwartet", game_id, year, month, line_index)
                # Anzahl der Tauschkarten prüfen
                s = line[j + 7:].rstrip(" -").split(" - ")
                j = len(s)
                if j != 3:
                    raise BWParserError("Drei Tauschkarten erwartet", game_id, year, month, line_index)
                cards = ["", "", ""]
                # Tauschkarten ermitteln
                for k in range(0, 3):
                    _player_name, card_label = s[k].split(": ")
                    cards[k] = card_label.replace("10", "Z")
                # Tauschkarten übernehmen
                log_entry.given_schupf_cards[player_index] = " ".join(cards)
                line_index += 1

            # Nun werden die Spieler mit einer Bombe aufgelistet, z.B
            # BOMBE: (0)Smocker (2)Amb4lamps23 (3)Andreavorn

            if lines[line_index].strip().startswith("BOMBE: "):
                line = lines[line_index].strip()
                for s in line[7:].split(" "):
                    # Index des Spielers ermitteln
                    if s[:3] not in ["(0)", "(1)", "(2)", "(3)"]:
                        raise BWParserError("Spieler-Index erwartet", game_id, year, month, line_index)
                    player_index = int(s[1])
                    # Bomben-Besitzer übernehmen
                    log_entry.bomb_owners[player_index] = True
                line_index += 1

            # Es folgt die Trennzeile "---------------Rundenverlauf------------------".

            separator = "---------------Rundenverlauf------------------"
            line = lines[line_index].strip()
            if line != separator:
                raise BWParserError(f"Seperator 'Rundenverlauf' erwartet", game_id, year, month, line_index)
            line_index += 1

            # Nun werden die Spielzüge gezeigt. Entweder ein Spieler spielt Karten oder er passt, z.B.:
            # (1)charliexyz passt.
            # (2)Amb4lamps23: R8 S8 B8 G8
            # Im Rundenverlauf können noch Zeilen stehen, die mit "Wunsch:", "Tichu: " oder "Drache an: " beginnen.
            # Die Runde endet mit der Zeile, die mit "Ergebnis: " beginnt.

            # Rundenverlauf
            while True:
                line = lines[line_index].strip()
                if line[:3] in ["(0)", "(1)", "(2)", "(3)"]:  # normaler Spielzug (z.B. "(1)charliexyz passt." oder "(2)Amb4lamps23: R8 S8")
                    # Index des Spielers ermitteln
                    player_index = int(line[1])
                    j = line.find(" ")
                    if j == -1:
                        raise BWParserError("Leerzeichen erwartet", game_id, year, month, line_index)
                    # Aktion auswerten (Karten gespielt oder gepasst?)
                    action = line[j + 1:].rstrip(".")  # 201205/1150668.tch endet in dieser Zeile, sodass der Punkt fehlt
                    cards = action.replace("10", "Z") if action != "passt" else ""
                    # Spielzug übernehmen
                    log_entry.history.append((player_index, cards, line_index))
                    line_index += 1

                elif line.startswith("Wunsch:"):  # Wunsch geäußert (z.B. "Wunsch:2")
                    # Wunsch ermitteln
                    wish = line[7:]
                    if wish not in ["2", "3", "4", "5", "6", "7", "8", "9", "10", "B", "D", "K", "A"]:  # 0 == "ohne Wunsch" wird nicht geloggt
                        raise BWParserError("Kartenwert als Wunsch erwartet", game_id, year, month, line_index)
                    # Wunsch übernehmen
                    log_entry.wish_value = 14 if wish == "A" else 13 if wish == "K" else 12 if wish == "D" else 11 if wish == "B" else int(wish)
                    line_index += 1

                elif line.startswith("Tichu: "):  # Tichu angesagt (z.B. "Tichu: (3)Andreavorn")
                    # Index des Spielers ermitteln
                    s = line[7:]
                    if s[:3] not in ["(0)", "(1)", "(2)", "(3)"]:
                        raise BWParserError("Spieler-Index erwartet", game_id, year, month, line_index)
                    player_index = int(s[1])
                    # Tichu-Ansage übernehmen
                    if log_entry.tichu_positions[player_index] == -3:  # es kommt vor, dass mehrmals direkt hintereinander Tichu angesagt wurde (Spieler zu hektisch geklickt?)
                        log_entry.tichu_positions[player_index] = len(log_entry.history)
                    line_index += 1

                elif line.startswith("Drache an: "):  # Drache verschenkt (z.B. "Drache an: (1)charliexyz")
                    # Index des Spielers ermitteln, der den Drachen bekommt
                    s = line[11:]
                    if s[:3] not in ["(0)", "(1)", "(2)", "(3)"]:
                        raise BWParserError("Spieler-Index erwartet", game_id, year, month, line_index)
                    player_index = int(s[1])
                    # Empfänger des Drachens übernehmen
                    log_entry.dragon_recipient = player_index
                    line_index += 1

                elif line.startswith("Ergebnis: "):  # z.B. "Ergebnis: 40 - 60"
                    # Score ermitteln
                    values = line[10:].split(" - ")
                    if len(values) != 2:
                        raise BWParserError("Zwei Werte getrennt mit ' - ' erwartet", game_id, year, month, line_index)
                    try:
                        score = int(values[0]), int(values[1])
                    except ValueError:
                        raise BWParserError("Zwei Integer erwartet", game_id, year, month, line_index)
                    # Score übernehmen
                    log_entry.score = score
                    line_index += 1
                    break  # While-Schleife für Rundenverlauf verlassen

                else:
                    raise BWParserError("Spielzug erwartet", game_id, year, month, line_index)

            # Rundenverlauf Ende

        except IndexError as e:
            if line_index >= num_lines:
                # Abruptes Ende der Logdatei, d.h., die Runde wurde nicht zu Ende gespielt.
                # Das ist normal und wird nicht als Fehler betrachtet.
                return bw_log
            else: # Runde wurde zu Ende gespielt, der Fehler liegt woanders
                raise e

        # Runde ist beendet.

        # Ausschnitt der Logdatei für Debug-Zwecke übernehmen
        log_entry.content = "\n".join(lines[log_entry.line_index:line_index])

        # Runde in die Rückgabeliste hinzufügen
        bw_log.append(log_entry)

        # Leerzeilen überspringen
        while line_index < num_lines and lines[line_index].strip() == "":
            line_index += 1

    return bw_log

# ------------------------------------------------------
# 3) Validieren
# ------------------------------------------------------

class BWErrorCode(enum.IntEnum):
    """
    Fehlercodes für Logs der Brettspielwelt.
    """
    NO_ERROR = 0
    """Kein Fehler"""

    # 2) Karten

    INVALID_CARD_LABEL = 20
    """Unbekanntes Kartenlabel."""

    INVALID_CARD_COUNT = 21
    """Anzahl der Karten ist fehlerhaft."""

    DUPLICATE_CARD = 22
    """Karten mehrmals vorhanden."""

    CARD_NOT_IN_HAND = 23
    """Karte gehört nicht zu den Handkarten."""

    CARD_ALREADY_PLAYED = 24
    """Karte bereits gespielt."""

    # 3) Spielzüge

    PASS_NOT_POSSIBLE = 30
    """Passen nicht möglich."""

    WISH_NOT_FOLLOWED = 31
    """Wunsch nicht beachtet."""

    COMBINATION_NOT_PLAYABLE = 32
    """Kombination nicht spielbar."""

    SMALLER_OF_AMBIGUOUS_RANK = 33
    """Es wurde der kleinere Rang bei einem mehrdeutigen Rang gewählt."""

    PLAYER_NOT_ON_TURN = 34
    """Der Spieler ist nicht am Zug."""

    HISTORY_TOO_SHORT = 35
    """Es fehlen Einträge in der Historie."""

    HISTORY_TOO_LONG = 36  # todo könnte ignoriert werden
    """Karten ausgespielt, obwohl die Runde vorbei ist (wurde korrigiert)."""

    # 4) Drache verschenken

    DRAGON_NOT_GIVEN = 40
    """Drache hat den Stich nicht gewonnen, wurde aber nicht verschenkt."""

    DRAGON_GIVEN_TO_OWN_TEAM = 41
    """Drache an eigenes Team verschenkt."""

    DRAGON_GIVEN_WITHOUT_BEAT = 42
    "Drache verschenkt, aber niemand hat durch den Drachen ein Stich gewonnen."

    # 5) Wunsch

    WISH_WITHOUT_MAHJONG = 50
    """Wunsch geäußert, aber kein Mahjong gespielt."""

    # 6) Tichu-Ansage

    ANNOUNCEMENT_NOT_POSSIBLE = 60
    """Tichu-Ansage an der geloggten Position nicht möglich (wurde korrigiert)."""

    # 7) Endergebnis

    SCORE_MISMATCH = 70
    """Geloggtes Rundenergebnis stimmt nicht mit dem berechneten Ergebnis überein (wurde korrigiert)."""

    SCORE_NOT_POSSIBLE = 71
    """Rechenfehler! Geloggtes Rundenergebnis ist nicht möglich (wurde korrigiert)."""

    # 8) Gesamt-Punktestand der Partie

    PLAYED_AFTER_GAME_OVER  = 80
    """Runde gespielt, obwohl die Partie bereits entschieden ist."""


@dataclass
class BWDataset:
    """
    Datencontainer für eine validierte Runde.

    :ivar game_id: ID der Partie.
    :ivar game_faulty: True, wenn mindestens eine Runde fehlerhaft ist, sonst False.
    :ivar round_index: Index der Runde innerhalb der Partie.
    :ivar total_score: Gesamtergebnis der Partie zu Beginn dieser Runde (Team20, Team31).
    :ivar player_names: Die Namen der 4 Spieler dieser Runde.
    :ivar start_hands: Handkarten der Spieler vor dem Schupfen (zuerst die 8 Grand-Tichu-Karten, danach die restlichen).
    :ivar given_schupf_cards: Abgegebene Tauschkarten (an rechten Gegner, Partner, linken Gegner).
    :ivar tichu_positions: Position in der Historie, an der Tichu angesagt wurde (-3 == kein Tichu, -2 == großes Tichu, -1 == Ansage vor oder während des Schupfens).
    :ivar wish_value: Der gewünschte Kartenwert (2 bis 14, 0 == ohne Wunsch, -1 == kein Mahjong gespielt).
    :ivar dragon_recipient: Index des Spielers, der den Drachen bekommen hat (-1 == Drache wurde nicht verschenkt).
    :ivar winner_index: Index des Spielers, der zuerst in der aktuellen Runde fertig wurde (-1 == kein Spieler).
    :ivar loser_index: Index des Spielers, der in der aktuellen Runde als letztes übrig blieb (-1 == kein Spieler).
    :ivar is_double_victory: Gibt an, ob die Runde durch einen Doppelsieg beendet wurde.
    :ivar score: Rundenergebnis (Team20, Team31).
    :ivar history: Spielzüge. Jeder Spielzug ist ein Tuple: Spieler-Index + gespielte Karten + Index des Spielers, der den Stich nach dem Zug kassiert (-1 == Stich nicht kassiert).
    :ivar year: Jahr der Logdatei.
    :ivar month: Monat der Logdatei.
    :ivar error_code: Fehlercode.
    :ivar error_line_index: Im Fehlerfall der Index der fehlerhaften Zeile in der Logdatei, sonst None.
    :ivar error_content: Im Fehlerfall der betroffene Abschnitt aus der Logdatei, sonst None.
    """
    game_id: int = -1
    game_faulty: bool = False
    round_index: int = -1
    player_names: List[str] = field(default_factory=lambda: ["", "", "", ""])
    total_score: Tuple[int, int] = (0, 0)
    start_hands: List[str] = field(default_factory=lambda: ["", "", "", ""])
    given_schupf_cards: List[str] = field(default_factory=lambda: ["", "", "", ""])
    tichu_positions: List[int] = field(default_factory=lambda: [-3, -3, -3, -3])
    wish_value: int = 0
    dragon_recipient: int = -1
    winner_index: int = -1,
    loser_index: int = -1,
    is_double_victory: bool = False,
    score: Tuple[int, int] = (0, 0)
    history: List[Tuple[int, str, int]] = field(default_factory=list)
    year: int = -1
    month: int = -1
    error_code: BWErrorCode = BWErrorCode.NO_ERROR
    error_line_index: Optional[int] = None
    error_content: Optional[str] = None


def can_score_be_ok(score: Tuple[int, int], announcements: List[int]) -> bool:
    """
    Prüft, ob der Skore plausibel ist.

    :param score: Rundenergebnis (Team20, Team31)
    :param announcements: Tichu-Ansagen pro Spieler (0 == keine Ansage, 1 == einfaches Tichu, 2 == großes Tichu).
    :return: True, wenn der Skore plausibel ist, sonst False.
    """
    # Punktzahl muss durch 5 teilbar sein.
    if score[0] % 5 != 0 or score[1] % 5 != 0:
        return False

    # Fälle durchspielen, wer zuerst fertig wurde
    sum_score = score[0] + score[1]
    for winner_index in range(4):
        bonus = sum([(100 if winner_index == i else -100) * announcements[i] for i in range(4)])
        if sum_score == bonus or sum_score == bonus + 200:  # normaler Sieg (die Karten ergeben in der Summe 0 Punkte) oder Doppelsieg
            return True
    return False


def _schupf(start_hands: List[List[str]], given_schupf_cards: List[List[str]]) -> List[List[str]]:
    """
    Ermittelt die Handkarten nach dem Schupfen.

    :param start_hands: Handkarten der vier Spieler vor dem Schupfen.
    :param given_schupf_cards: Die abgegebenen Tauschkarten der vier Spieler (an rechten Gegner, Partner, linken Gegner).
    :return: Die neuen Handkarten der vier Spieler nach dem Schupfen.
    """
    hands = []
    for player_index in range(4):  # Geber
        # Tauschkarten abgeben.
        start_cards = start_hands[player_index]
        given_cards = given_schupf_cards[player_index]
        remaining_cards = [label for label in start_cards if label not in given_cards]
        # Tauscharten aufnehmen.
        received_cards = [
            given_schupf_cards[(player_index + 1) % 4][2],
            given_schupf_cards[(player_index + 2) % 4][1],
            given_schupf_cards[(player_index + 3) % 4][0],
        ]
        cards = remaining_cards + received_cards
        hands.append(cards)
    return hands


def validate_bw_log(bw_log: BWLog) -> List[BWDataset]:
    """
    Validiert die geparste Logdatei auf Plausibilität.

    Der erste zutreffende Fehler wird dokumentiert.

    :param bw_log: Die geparsten Logdatei (eine Partie).
    :return: Die validierten Rundendaten.
    """
    datasets = []
    game_faulty = False
    total_score = [0, 0]
    for log_entry in bw_log:
        error_code = BWErrorCode.NO_ERROR
        error_line_index = -1

        # Karten aufsplitten
        grand_tichu_hands: List[List[str]] = []
        start_hands: List[List[str]] = []
        given_schupf_cards: List[List[str]] = []
        for player_index in range(4):
            grand_tichu_hands.append(log_entry.grand_tichu_hands[player_index].split(" "))
            start_hands.append(log_entry.start_hands[player_index].split(" "))
            given_schupf_cards.append(log_entry.given_schupf_cards[player_index].split(" "))

        # Handkarten prüfen
        for player_index in range(4):
            grand_cards = grand_tichu_hands[player_index]
            start_cards = start_hands[player_index]
            given_cards = given_schupf_cards[player_index]

            # Grand-Hand-Karten
            if not validate_cards(log_entry.grand_tichu_hands[player_index]):  # Kartenlabel
                error_code = BWErrorCode.INVALID_CARD_LABEL
                error_line_index = log_entry.line_index + 1 + player_index
                break
            elif len(grand_cards) != 8:  # Anzahl
                error_code = BWErrorCode.INVALID_CARD_COUNT
                error_line_index = log_entry.line_index + 1 + player_index
                break
            elif len(set(grand_cards)) != 8:  # Duplikate
                error_code = BWErrorCode.DUPLICATE_CARD
                error_line_index = log_entry.line_index + 1 + player_index
                break
            elif any(label not in start_cards for label in grand_cards):  # sind Handkarten?
                error_code = BWErrorCode.CARD_NOT_IN_HAND
                error_line_index = log_entry.line_index + 1 + player_index
                break

            # Startkarten
            elif not validate_cards(log_entry.start_hands[player_index]):  # Kartenlabel
                error_code = BWErrorCode.INVALID_CARD_LABEL
                error_line_index = log_entry.line_index + 6 + player_index
                break
            elif len(start_cards) != 14:  # Anzahl
                error_code = BWErrorCode.INVALID_CARD_LABEL
                error_line_index = log_entry.line_index + 6 + player_index
                break
            elif len(set(start_cards)) != 14:  # Duplikate
                error_code = BWErrorCode.DUPLICATE_CARD
                error_line_index = log_entry.line_index + 6 + player_index
                break

            # Tauschkarten
            elif not validate_cards(log_entry.given_schupf_cards[player_index]):  # Kartenlabel
                error_code = BWErrorCode.INVALID_CARD_LABEL
                error_line_index = log_entry.line_index + 11 + player_index
                break
            elif len(given_cards) != 3:  # Anzahl
                error_code = BWErrorCode.INVALID_CARD_LABEL
                error_line_index = log_entry.line_index + 11 + player_index
                break
            elif len(set(given_cards)) != 3:  # Duplikate
                error_code = BWErrorCode.DUPLICATE_CARD
                error_line_index = log_entry.line_index + 11 + player_index
                break
            elif any(label not in start_cards for label in given_cards):  # sind Handkarten?
                error_code = BWErrorCode.CARD_NOT_IN_HAND
                error_line_index = log_entry.line_index + 11 + player_index
                break

        # Sind alle Karten verteilt und keine mehrfach vergeben?
        if error_code == BWErrorCode.NO_ERROR:
            if len(set(start_hands[0] + start_hands[1] + start_hands[2] + start_hands[3])) != 56:
                error_code = BWErrorCode.DUPLICATE_CARD
                error_line_index = log_entry.line_index

        # Handkarten nach dem Schupfen ermitteln
        hands = _schupf(start_hands, given_schupf_cards)
        num_hand_cards = [14, 14, 14, 14]

        # Kombinationsmöglichkeiten berechnen
        combinations = []
        for player_index in range(4):
            cards = hands[player_index]
            combinations.append(build_combinations([parse_card(label) for label in cards]))

        # Startspieler ermitteln
        current_turn_index = -1
        for player_index in range(4):
            if "Ma" in hands[player_index]:
                current_turn_index = player_index
                break

        # Histore bereinigen.

        # Leider wird nicht geloggt, wer den Stich kassiert. Stattdessen "passt" der Spieler in dem Moment des Kassierens :-(
        # Daher bauen wir eine neue Historie auf, die festhält, wer den Stich kassiert, ohne überflüssiges Passen.
        history = []

        trick_owner_index = -1
        trick_combination = CombinationType.PASS, 0, 0
        trick_points = 0
        points = [0, 0, 0, 0]
        played_cards = []
        first_pos = [-1, -1, -1, -1]  # die erste Position in der Historie, in der der Spieler Karten ausspielt
        tichu_positions = [log_entry.tichu_positions[i] for i in range(4)]
        is_trick_rank_ambiguous = False  # True, wenn der Rang des Tricks mehrdeutig ist
        wish_value = -1
        dragon_giver= -1  # Index des Spielers, der den Drachen verschenkt hat
        winner_index = -1
        loser_index = -1
        is_round_over = False
        is_double_victory = False
        history_too_long = False
        for player_index, card_str, line_index in log_entry.history:
            if is_round_over:
                # Runde ist vorbei, aber es gibt noch weitere Einträge in der Historie
                if card_str == "":
                    continue  # Passen am Ende der Runde ignorieren wir
                history_too_long = True
                break

            if card_str == "":
                # Falls alle Mitspieler zuvor gepasst haben, schaut der Spieler jetzt auf seinen eigenen Stich und kann diesen abräumen.
                if player_index == trick_owner_index and trick_combination != (CombinationType.SINGLE, 1, 0):  # der Hund bleibt liegen
                    # Stich kassieren
                    if trick_combination[2] == 15:  # der Drache hat den Stich gewonnen
                        dragon_giver = trick_owner_index
                        trick_collector_index = log_entry.dragon_recipient
                    else:
                        trick_collector_index = trick_owner_index
                    history[-1] = history[-1][0], history[-1][1], trick_collector_index
                    points[trick_collector_index] += trick_points
                    trick_points = 0
                    trick_combination = CombinationType.PASS, 0, 0
                    trick_owner_index = -1
                    # tichu_positions anpassen, da wir diesen Eintrag nicht übernehmen
                    for i in range(4):
                        if tichu_positions[i] >= len(history):
                            tichu_positions[i] -= 1
                    continue # nächsten Eintrag in der Historie lesen

                # Spieler hat gepasst.
                history.append((player_index, "", -1))

                # Im Anspiel gepasst?
                if trick_owner_index == -1:
                    error_code = BWErrorCode.PASS_NOT_POSSIBLE
                    error_line_index = line_index
                    break

                # Wunsch beachtet?
                if wish_value > 0:
                    action_space = build_action_space(combinations[player_index], trick_combination, wish_value)
                    if action_space[0][1][0] != CombinationType.PASS:  # Wunsch wurde nicht beachtet!
                        error_code = BWErrorCode.WISH_NOT_FOLLOWED
                        error_line_index = line_index
                        break

                # Prüfen, ob der Spieler dran war
                if player_index != current_turn_index:
                    if error_code == BWErrorCode.NO_ERROR:
                        error_code = BWErrorCode.PLAYER_NOT_ON_TURN
                        error_line_index = line_index
                    break
            else:
                # Spieler hat Karten gespielt
                history.append((player_index, card_str, -1))

                # Die erste Position für jeden Spieler merken
                if first_pos[player_index] == -1:
                    first_pos[player_index] = len(history) - 1

                # Karten prüfen
                cards = card_str.split(" ")
                if not validate_cards(card_str):  # Kartenlabel bekannt?
                    if error_code == BWErrorCode.NO_ERROR:
                        error_code = BWErrorCode.INVALID_CARD_LABEL
                        error_line_index = line_index
                    break
                elif len(cards) != len(set(cards)):  # Duplikate?
                    if error_code == BWErrorCode.NO_ERROR:
                        error_code = BWErrorCode.DUPLICATE_CARD
                        error_line_index = line_index
                    break
                elif any(label not in hands[player_index] for label in cards):  # gehören die Karten zur Hand?
                    if error_code == BWErrorCode.NO_ERROR:
                        error_code = BWErrorCode.CARD_NOT_IN_HAND
                        error_line_index = line_index
                    break
                elif any(label in played_cards for label in cards):  # bereits gespielt?
                    if error_code == BWErrorCode.NO_ERROR:
                        error_code = BWErrorCode.CARD_ALREADY_PLAYED
                        error_line_index = line_index
                    break

                # Gespielte Karten merken
                played_cards += cards

                # Kombination prüfen
                parsed_cards = [parse_card(label) for label in cards]
                combination = get_trick_combination(parsed_cards, trick_combination[2], shift_phoenix=True)
                action_space = build_action_space(combinations[player_index], trick_combination, wish_value)
                if not any(set(parsed_cards) == set(playable_cards) for playable_cards, _playable_combination in action_space):
                    if error_code == BWErrorCode.NO_ERROR:
                        if wish_value > 0 and is_wish_in(wish_value, action_space[0][0]):
                            error_code = BWErrorCode.WISH_NOT_FOLLOWED  # Wunsch wurde nicht beachtet
                        elif is_trick_rank_ambiguous:
                            error_code = BWErrorCode.SMALLER_OF_AMBIGUOUS_RANK  # es wurde der kleinere Rang bei einem mehrdeutigen Stich angenommen
                        else:
                            error_code = BWErrorCode.COMBINATION_NOT_PLAYABLE
                        error_line_index = line_index
                    break

                # Wenn kein Anspiel ist, kann das Zugrecht durch eine Bombe erobert werden
                if trick_owner_index != -1 and combination[0] == CombinationType.BOMB:
                    current_turn_index = player_index

                # Prüfen, ob der Spieler dran war
                if player_index != current_turn_index:
                    if error_code == BWErrorCode.NO_ERROR:
                        error_code = BWErrorCode.PLAYER_NOT_ON_TURN
                        error_line_index = line_index
                    break

                # Handkarten aktualisieren
                hands[player_index] = [label for label in hands[player_index] if label not in cards]
                num_hand_cards[player_index] -= len(cards)
                combinations[player_index] = build_combinations([parse_card(label) for label in hands[player_index]])

                # Stich aktualisieren
                trick_points += sum_card_points(parsed_cards)
                trick_combination = combination
                trick_owner_index = player_index
                # Der Rang ist nicht eindeutig, wenn beim Fullhouse der Phönix in der Mitte liegt oder bei der Straße am Ende bzw. Ende.
                is_trick_rank_ambiguous = (
                      (combination[0] == CombinationType.FULLHOUSE and parsed_cards[2][0] == 16) or
                      (combination[0] == CombinationType.STREET and parsed_cards[0][0] == 16)
                )

                # Wunsch erfüllt?
                if wish_value > 0 and is_wish_in(wish_value, parsed_cards):
                    wish_value = 0

                # Runde vorbei?
                if num_hand_cards[player_index] == 0:
                    finished_players = num_hand_cards.count(0)
                    if finished_players == 1:
                        winner_index = player_index
                    elif finished_players == 2:
                        if num_hand_cards[(player_index + 2) % 4] == 0:
                            is_double_victory = True
                            is_round_over = True
                    else:
                        for i in range(4):
                            if num_hand_cards[i] > 0:
                                loser_index = i
                                break
                        is_round_over = True
                    # Falls die Runde vorbei ist, zum nächsten Eintrag in der Historie springen.
                    # Dürfte es nicht mehr geben ud somit den Schleifendurchlauf beenden.
                    if is_round_over:
                        continue

                # Falls ein MahJong ausgespielt wurde, kann der Spieler sich einen Kartenwert wünschen.
                if 'Ma' in cards:
                    wish_value = log_entry.wish_value

            # Nächsten Spieler ermitteln
            if trick_combination == (CombinationType.SINGLE, 1, 0) and trick_owner_index == current_turn_index:
                current_turn_index = (current_turn_index + 2) % 4
            else:
                current_turn_index = (current_turn_index + 1) % 4

            # Spieler ohne Handkarten überspringen (für diese gibt es keine Logeinträge)
            while num_hand_cards[current_turn_index] == 0:
                # Wenn der Spieler auf seinen eigenen Stich schaut, kassiert er ihn, selbst wenn er keine Handkarten mehr hat.
                if current_turn_index == trick_owner_index and trick_combination != (CombinationType.SINGLE, 1, 0):  # der Hund bleibt liegen
                    # Stich kassieren
                    if trick_combination[2] == 15:  # der Drache hat den Stich gewonnen
                        dragon_giver = trick_owner_index
                        trick_collector_index = log_entry.dragon_recipient
                    else:
                        trick_collector_index = trick_owner_index
                    history[-1] = history[-1][0], history[-1][1], trick_collector_index
                    points[trick_collector_index] += trick_points
                    trick_points = 0
                    trick_combination = CombinationType.PASS, 0, 0
                    trick_owner_index = -1
                current_turn_index = (current_turn_index + 1) % 4

        # Historie zu kurz oder zu lang?
        if not is_round_over:
            if error_code == BWErrorCode.NO_ERROR:
                error_code = BWErrorCode.HISTORY_TOO_SHORT
                error_line_index = log_entry.line_index
        elif history_too_long:
            if error_code == BWErrorCode.NO_ERROR:
                error_code = BWErrorCode.HISTORY_TOO_LONG
                error_line_index = log_entry.line_index

        # Runde ist beendet

        # letzten Stich kassieren
        if trick_combination[2] == 15:  # der Drache hat den Stich gewonnen
            dragon_giver = trick_owner_index
            trick_collector_index = log_entry.dragon_recipient
        else:
            trick_collector_index = trick_owner_index
        history[-1] = history[-1][0], history[-1][1], trick_collector_index
        points[trick_collector_index] += trick_points

        # Empfänger des Drachens prüfen
        if dragon_giver != -1 and log_entry.dragon_recipient == -1:
            # Drache hat Stich gewonnen, wurde aber nicht verschenkt
            if not (history[-1][1] == "Dr" and is_double_victory):  # Ausnahme: Drache im letzten Stich führt zum Doppelsieg (dann wird der Drache nicht verschenkt, weil egal)
                if error_code == BWErrorCode.NO_ERROR:
                    error_code = BWErrorCode.DRAGON_NOT_GIVEN
                    error_line_index = log_entry.line_index
        elif dragon_giver != -1 and log_entry.dragon_recipient not in [(dragon_giver + 1) % 4, (dragon_giver + 3) % 4]:
            # Drache hat Stich gewonnen, wurde aber an das eigene Team verschenkt
            if error_code == BWErrorCode.NO_ERROR:
                error_code = BWErrorCode.DRAGON_GIVEN_TO_OWN_TEAM
                error_line_index = log_entry.line_index
        elif dragon_giver == -1 and log_entry.dragon_recipient != -1:
            # Drache hat keinen Stich gewonnen, wurde aber verschenkt
            if error_code == BWErrorCode.NO_ERROR:
                error_code = BWErrorCode.DRAGON_GIVEN_WITHOUT_BEAT
                error_line_index = log_entry.line_index

        # Falls der Mahjong gespielt wurde, aber kein Wunsch geäußert wurde (was legitim ist), 0 für "ohne Wunsch" eintragen.
        wish_value = log_entry.wish_value
        if wish_value == -1:
            if "Ma" in played_cards:
                log_entry.wish_value = 0
            else:
                error_code = BWErrorCode.WISH_WITHOUT_MAHJONG
                error_line_index = log_entry.line_index

        # Position der Tichu-Ansage prüfen und korrigieren
        for player_index in range(4):
            if tichu_positions[player_index] - first_pos[player_index] > 1:
                if error_code == BWErrorCode.NO_ERROR:
                    error_code = BWErrorCode.ANNOUNCEMENT_NOT_POSSIBLE
                    error_line_index = log_entry.line_index
                tichu_positions[player_index] = first_pos[player_index]

        # Endwertung der Runde
        if is_double_victory:
            # Doppelsieg! Das Gewinnerteam kriegt 200 Punkte. Die Gegner nichts.
            points = [0, 0, 0, 0]
            points[winner_index] = 200
        elif loser_index >= 0:
            # a) Der letzte Spieler gibt seine Handkarten an das gegnerische Team.
            leftover_points = 100 - sum_card_points([parse_card(label) for label in played_cards])
            points[(loser_index + 1) % 4] += leftover_points
            # b) Der letzte Spieler übergibt seine Stiche an den Spieler, der zuerst fertig wurde.
            points[winner_index] += points[loser_index]
            points[loser_index] = 0
        else:
            # Rundenergebnis aufgrund Fehler im Spielverlauf nicht berechenbar
            points = [0, 0, 0, 0]

        # Bonus für Tichu-Ansage
        for player_index in range(4):
            if tichu_positions[player_index] != -3:
                bonus = 200 if tichu_positions[player_index] == -2 else 100
                points[player_index] += bonus if player_index == winner_index else -bonus

        # Rundenergebnis mit dem geloggten Eintrag vergleichen
        score = points[2] + points[0], points[3] + points[1]
        if score != log_entry.score:
            if error_code == BWErrorCode.NO_ERROR:
                # Wer hat Tichu angesagt?
                announcements = [0, 0, 0, 0]
                for player_index in range(4):
                    if log_entry.tichu_positions[player_index] != -3:
                        announcements[player_index] = 2 if log_entry.tichu_positions[player_index] == -2 else 1
                error_code = BWErrorCode.SCORE_MISMATCH if can_score_be_ok(log_entry.score, announcements) else BWErrorCode.SCORE_NOT_POSSIBLE
                error_line_index = log_entry.line_index

        # Spielerliste prüfen
        player_names = []
        for player_index in range(4):
            # Spielernamen generieren, wenn er nicht vorhanden ist (oder nur aus Leerzeichen besteht)
            name = log_entry.player_names[player_index]
            if name == "":
                name = f"Noname-{log_entry.game_id}"

            # Sicherstellen, dass der Name eindeutig ist.
            i = 1
            while name in player_names:
                i += 1
                name = f"{log_entry.player_names[player_index]} ({i})"
                # if error_code == BWErrorCode.NO_ERROR:
                #     error_code = BWErrorCode.DUPLICATE_PLAYER_NAME
                #     error_line_index = log_entry.line_index + 1 + player_index
            player_names.append(name)

        # Gesamt-Punktestand der Partie aktualisieren
        if total_score[0] >= 1000 or total_score[1] >= 1000:
            if error_code == BWErrorCode.NO_ERROR:
                error_code = BWErrorCode.PLAYED_AFTER_GAME_OVER
                error_line_index = log_entry.line_index
        total_score[0] += score[0]
        total_score[1] += score[1]

        if error_code != BWErrorCode.NO_ERROR:
            game_faulty = True

        # Startkarten so sortieren, dass erst die Grand-Tichu-Karten aufgelistet sind
        sorted_start_hands = []
        for player_index in range(4):
            grand_cards = grand_tichu_hands[player_index]
            start_cards = start_hands[player_index]
            remaining_cards = [label for label in start_cards if label not in grand_cards]
            if error_code != BWErrorCode.INVALID_CARD_LABEL:
                cards = sorted([parse_card(label) for label in grand_cards], reverse=True)
                grand_cards = [stringify_card(card) for card in cards]
                cards = sorted([parse_card(label) for label in remaining_cards], reverse=True)
                remaining_cards = [stringify_card(card) for card in cards]
            sorted_start_hands.append(" ".join(grand_cards + remaining_cards))

        datasets.append(BWDataset(
            game_id=log_entry.game_id,
            game_faulty=game_faulty,
            round_index=log_entry.round_index,
            player_names=player_names,
            total_score=(total_score[0], total_score[1]),
            start_hands=sorted_start_hands,
            given_schupf_cards=log_entry.given_schupf_cards,
            tichu_positions=tichu_positions,
            wish_value=wish_value,
            dragon_recipient=log_entry.dragon_recipient,
            winner_index = winner_index,
            loser_index = loser_index,
            is_double_victory = is_double_victory,
            score=score,
            history=history,
            year=log_entry.year,
            month=log_entry.month,
            error_code=error_code,
            error_line_index=error_line_index if error_code != BWErrorCode.NO_ERROR else None,
            error_content=log_entry.content if error_code != BWErrorCode.NO_ERROR else None,
        ))
    return datasets

# ------------------------------------------------------
# 4) Datenbankimport
# ------------------------------------------------------

def _create_tables(conn: sqlite3.Connection):
    """
    Erstellt die Tabellen in der SQLite-Datenbank, falls sie nicht existieren.
    """
    cursor = conn.cursor()

    # Tabelle "rounds" speichert alle validierten Runden
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rounds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,   -- Eindeutige interne ID der Runde
        game_id INTEGER NOT NULL,               -- ID der Partie
        game_faulty INTEGER NOT NULL,           -- 1: mindestens eine Runde fehlerhaft, 0: fehlerfrei
        round_index INTEGER NOT NULL,           -- Index der Runde innerhalb der Partie (0, 1, 2, ...)
        player_name_0 TEXT NOT NULL,            -- Name des Spielers an Position 0
        player_name_1 TEXT NOT NULL,            -- Name des Spielers an Position 1
        player_name_2 TEXT NOT NULL,            -- Name des Spielers an Position 2
        player_name_3 TEXT NOT NULL,            -- Name des Spielers an Position 3
        total_score_20 INTEGER NOT NULL,        -- Gesamtergebnis Team 20 zu Beginn dieser Runde
        total_score_31 INTEGER NOT NULL,        -- Gesamtergebnis Team 31 zu Beginn dieser Runde
        hand_cards_0 TEXT NOT NULL,             -- Handkarten von Spieler 0 vor dem Schupfen
        hand_cards_1 TEXT NOT NULL,             -- Handkarten von Spieler 1 vor dem Schupfen
        hand_cards_2 TEXT NOT NULL,             -- Handkarten von Spieler 2 vor dem Schupfen
        hand_cards_3 TEXT NOT NULL,             -- Handkarten von Spieler 3 vor dem Schupfen
        schupf_cards_0 TEXT NOT NULL,           -- Abgegebene Tauschkarten von Spieler 0
        schupf_cards_1 TEXT NOT NULL,           -- Abgegebene Tauschkarten von Spieler 1
        schupf_cards_2 TEXT NOT NULL,           -- Abgegebene Tauschkarten von Spieler 2
        schupf_cards_3 TEXT NOT NULL,           -- Abgegebene Tauschkarten von Spieler 3
        tichu_pos_0 INTEGER NOT NULL,           -- Tichu-Ansage-Position Spieler 0 (-3…-1, ≥0 = Zug-Index)
        tichu_pos_1 INTEGER NOT NULL,           -- Tichu-Ansage-Position Spieler 1
        tichu_pos_2 INTEGER NOT NULL,           -- Tichu-Ansage-Position Spieler 2
        tichu_pos_3 INTEGER NOT NULL,           -- Tichu-Ansage-Position Spieler 3
        wish_value INTEGER NOT NULL,            -- Gewünschter Kartenwert (2–14, 0 = ohne Wunsch, -1 = kein Mahjong)
        dragon_recipient INTEGER NOT NULL,      -- Index des Spielers, der den Drachen erhielt (-1 = niemand)
        winner_index INTEGER NOT NULL,          -- Index des Spielers, der als Erster ausspielt (-1 = niemand)
        loser_index INTEGER NOT NULL,           -- Index des Spielers, der als Letzter übrig bleibt (-1 = niemand)
        is_double_victory INTEGER NOT NULL,     -- 1 = Doppelsieg, 0 = normales Ende
        score_20 INTEGER NOT NULL,              -- Rundenergebnis Team 20
        score_31 INTEGER NOT NULL,              -- Rundenergebnis Team 31
        history TEXT NOT NULL,                  -- Spielzüge als JSON-Array [(spieler, karten, stichnehmer), …]
        log_year INTEGER NOT NULL,              -- Jahr der Logdatei
        log_month INTEGER NOT NULL,             -- Monat der Logdatei
        error_code TEXT NOT NULL,               -- Fehlercode (Enum-Wert)
        error_line_index INTEGER,               -- Index der fehlerhaften Zeile (NULL, wenn kein Fehler)
        error_content TEXT                      -- Betroffener Log-Abschnitt (NULL, wenn kein Fehler)
    );
    """)
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_rounds_game_id_round_index ON rounds (game_id, round_index);")
    conn.commit()


def _create_indexes(conn: sqlite3.Connection):
    """
    Erstellt Indizes für die Tabellen in der SQLite-Datenbank zur Beschleunigung typischer Abfragen.
    """
    cursor = conn.cursor()

    # rounds
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_game_faulty       ON rounds (game_faulty);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_player_name_0     ON rounds (player_name_0);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_player_name_1     ON rounds (player_name_1);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_player_name_2     ON rounds (player_name_2);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_player_name_3     ON rounds (player_name_3);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_total_score_20    ON rounds (total_score_20);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_total_score_31    ON rounds (total_score_31);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_tichu_pos_0       ON rounds (tichu_pos_0);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_tichu_pos_1       ON rounds (tichu_pos_1);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_tichu_pos_2       ON rounds (tichu_pos_2);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_tichu_pos_3       ON rounds (tichu_pos_3);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_wish_value        ON rounds (wish_value);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_dragon_recipient  ON rounds (dragon_recipient);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_double_victory    ON rounds (is_double_victory);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_score_20          ON rounds (score_20);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_score_31          ON rounds (score_31);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_log_year_month    ON rounds (log_year, log_month);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_error_code        ON rounds (error_code);")
    conn.commit()


class BWValidationStats(TypedDict):
    """
    Ergebniszusammenfassung der Datenbankaktualisierung.

    :ivar games_total: Gesamtanzahl der Partien.
    :ivar games_fails: Anzahl der fehlerhaften Partien.
    :ivar rounds_total: Gesamtanzahl der Runden.
    :ivar rounds_fails: Anzahl fehlerhafter Runden.
    :ivar error_summary: Fehler in Runden pro Fehlercode.
    :ivar duration: Gesamtdauer des Imports in Sekunden.
    """
    games_total: int
    games_fails: int
    rounds_total: int
    rounds_fails: int
    error_summary: dict[BWErrorCode, int]
    duration: float


def update_bw_database(database: str, path: str, y1: int, m1: int, y2: int, m2: int) -> BWValidationStats:
    """
    Aktualisiert die SQLite-Datenbank für die vom Spiele-Portal "Brettspielwelt" heruntergeladenen Logdateien.

    :param database: Die SQLite-Datenbankdatei.
    :param path: Das Verzeichnis, in dem die Zip-Archive liegen.
    :param y1: ab Jahr
    :param m1: ab Monat
    :param y2: bis Jahr (einschließlich)
    :param m2: bis Monat (einschließlich)
    """
    # Verbindung zur Datenbank herstellen und Tabellen einrichten
    os.makedirs(os.path.dirname(database), exist_ok=True)
    conn = sqlite3.connect(database)
    _create_tables(conn)
    cursor = conn.cursor()

    game_ids = cursor.execute("SELECT DISTINCT game_id FROM rounds WHERE error_code in (80, 81, 60);").fetchall()
    game_ids = [game_id[0] for game_id in game_ids]

    # Aktualisierung starten
    log_file_counter = 0
    try:
        progress_bar = tqdm(
            bw_logfiles(path, y1, m1, y2, m2),
            total=bw_count_logfiles(path, y1, m1, y2, m2),
            desc="Verarbeite Log-Dateien",
            unit=" Datei")
        games_total = 0
        games_fails = 0
        rounds_total = 0
        rounds_fails = 0
        error_summary = {}
        time_start = time()
        for game_id, year, month, content in progress_bar:
            if game_id not in game_ids:
                continue
            # Logdatei parsen und validieren
            games_total += 1
            bw_log = parse_bw_logfile(game_id, year, month, content)
            datasets = validate_bw_log(bw_log)
            if any(ds.error_code != BWErrorCode.NO_ERROR for ds in datasets):
                games_fails += 1

            # Datensätze schreiben
            for ds in datasets:
                # Runden und Fehler zählen
                rounds_total += 1
                if ds.error_code != BWErrorCode.NO_ERROR:
                    if ds.error_code not in error_summary:
                        error_summary[ds.error_code] = 0
                    error_summary[ds.error_code] += 1
                    rounds_fails += 1
                # Datensatz einfügen
                cursor.execute("""
                    INSERT OR REPLACE INTO rounds (
                        game_id, 
                        game_faulty, 
                        round_index, 
                        player_name_0, player_name_1, player_name_2, player_name_3,
                        total_score_20, total_score_31, 
                        hand_cards_0, hand_cards_1, hand_cards_2, hand_cards_3,
                        schupf_cards_0, schupf_cards_1, schupf_cards_2, schupf_cards_3,
                        tichu_pos_0, tichu_pos_1, tichu_pos_2, tichu_pos_3,
                        wish_value, 
                        dragon_recipient, 
                        winner_index, 
                        loser_index, 
                        is_double_victory, 
                        score_20, score_31, 
                        history,
                        log_year, log_month, 
                        error_code, error_line_index, error_content
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ds.game_id,
                        int(ds.game_faulty),
                        ds.round_index,
                        ds.player_names[0], ds.player_names[1], ds.player_names[2], ds.player_names[3],
                        ds.total_score[0], ds.total_score[1],
                        ds.start_hands[0], ds.start_hands[1], ds.start_hands[2], ds.start_hands[3],
                        ds.given_schupf_cards[0], ds.given_schupf_cards[1], ds.given_schupf_cards[2], ds.given_schupf_cards[3],
                        ds.tichu_positions[0], ds.tichu_positions[1], ds.tichu_positions[2], ds.tichu_positions[3],
                        ds.wish_value,
                        ds.dragon_recipient,
                        ds.winner_index,
                        ds.loser_index,
                        int(ds.is_double_victory),
                        ds.score[0], ds.score[1],
                        json.dumps(ds.history),
                        ds.year, ds.month,
                        ds.error_code.value, ds.error_line_index, ds.error_content
                    )
                )

            # Transaktion alle 1000 Dateien committen
            log_file_counter += 1
            if log_file_counter % 1000 == 0:
                progress_bar.set_postfix_str(f"Commit DB...")
                conn.commit()

            # Fortschritt aktualisieren
            progress_bar.set_postfix({
                "Partien": games_total,
                "Fehlerhaft": games_fails,
                "Runden": rounds_total,
                "Datei": f"{year:04d}{month:02d}/{game_id}.tch"
            })

        # Indizes erst am Ende einrichten, damit der Import schneller durchläuft.
        _create_indexes(conn)

    # Alle verbleibenden Änderungen speichern und Datenbank schließen.
    finally:
        conn.commit()
        conn.close()

    return {
        "games_total": games_total,
        "games_fails": games_fails,
        "rounds_total": rounds_total,
        "rounds_fails": rounds_fails,
        "error_summary": error_summary,
        "duration": time() - time_start,
    }

# ------------------------------------------------------
# 5) Replay-Simulator
# ------------------------------------------------------

def replay_play(all_round_data: List[BWLogEntry]) -> Generator[Tuple[PublicState, List[PrivateState], Tuple[Cards, Combination]]]:
    """
    Spielt eine geloggte Partie nach und gibt jeden Entscheidungspunkt für das Ausspielen der Karten zurück.

    :param all_round_data: Die geparsten Daten einer geloggten Partie.
    :return: Ein Generator, der den öffentlichen Spielzustand, die 4 privaten Spielzustände und die ausgeführte Aktion liefert.
    """
    if len(all_round_data) == 0:
        return None

    # aktueller Spielzustand
    pub = PublicState(
        table_name="BW Replay",
        player_names=["A", "B", "C", "D"],
    )
    privs = [PrivateState(player_index=i) for i in range(4)]
    action = [(1, CardSuit.SPECIAL)], (CombinationType.SINGLE, 1, 1)
    yield pub, privs, action
    return None
