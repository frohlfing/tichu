"""
Dieses Modul stellt Funktionen bereit, die mit Tichu-Logdateien vom Spiele-Portal "Brettspielwelt" umgehen können.
"""

__all__ = "download_logfiles_from_bw", \
    "bw_logfiles", "bw_count_logfiles", \
    "BWLog", "BWLogEntry", "BWErrorCode", "BWParserError", "parse_bw_logfile", "validate_bw_log", \
    "BWReplayError", "replay_play"

import enum
import os
import requests
from dataclasses import dataclass, field
from datetime import datetime
from src.lib.cards import validate_card, validate_cards, parse_card, parse_cards, Cards, CARD_MAH, deck, stringify_cards, sum_card_points, is_wish_in, other_cards, CARD_DRA
from src.lib.combinations import get_combination, Combination, CombinationType, build_action_space
from src.public_state import PublicState
from src.private_state import PrivateState
from tqdm import tqdm
from typing import List, Tuple, Optional, Generator, Dict, Any
from zipfile import ZipFile, ZIP_DEFLATED


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


class BWErrorCode(enum.IntEnum):
    """
    Fehlercodes für Logs der Brettspielwelt.

    Der erste Fehler wird in `BWLog` festgehalten.
    """
    NO_ERROR = 0
    """Kein Fehler"""

    # Prio 1: Schwerwiegende Fehler

    # 1) Karten

    INVALID_CARD_DISTRIBUTION = 10
    """Eine oder mehrere Karten wurden nicht korrekt verteilt."""

    INVALID_CARD_LABEL = 11
    """Ungültiges Karten-Label."""

    INVALID_CARD_COUNT = 12
    """Anzahl der Karten ist fehlerhaft."""

    DUPLICATE_CARD = 13
    """Karten mehrmals vorhanden."""

    CARD_NOT_IN_HAND = 14
    """Karte gehört nicht zu den Handkarten."""

    CARD_ALREADY_PLAYED = 15
    """Karte bereits gespielt."""

    # 2) Zugwechsel

    PLAYER_NOT_ON_TURN = 20
    """Der Spieler ist nicht am Zug."""

    # 3) Spielzug

    INVALID_COMBINATION = 30
    """Ungültige Kombination."""

    COMBINATION_NOT_PLAYABLE = 31
    """Kombination nicht spielbar."""

    PASS_NOT_POSSIBLE = 32
    """Passen nicht möglich."""

    TURN_MISSING = 33
    """Es fehlen Einträge in der Historie."""

    # 4) Wunsch

    WISH_WITHOUT_MAHJONG = 40
    """Wunsch geäußert, aber kein Mahjong gespielt."""

    WISH_NOT_FOLLOWED = 41
    """Wunsch nicht beachtet (hätte erfüllt werden können)."""

    # 5) Drache verschenken

    DRAGON_GIVEN_WITHOUT_BEAT = 50
    "Drache verschenkt, aber Drache hat den Stich nicht gewonnen."

    DRAGON_NOT_GIVEN = 51
    """Drache hat den Stich nicht gewonnen, wurde aber nicht verschenkt."""

    DRAGON_GIVEN_TO_TEAM = 52
    """Drache an eigenes Team verschenkt."""

    # Prio 2: Korrigierte oder vernachlässigbare Fehler

    # 6) Spielerliste

    PLAYER_NAME_MISSING = 60
    """Name des Spielers fehlt (wurde korrigiert)."""

    # 7) Endergebnis

    SCORE_MISMATCH = 70
    """Rundenergebnis stimmt nicht."""

    # 8) Überflüssige Spielzüge

    PASSED_AFTER_ROUND_OVER = 81
    """Gepasst, obwohl die Runde vorbei ist (wird ignoriert)."""

    PLAYED_AFTER_ROUND_OVER = 82
    """Karten ausgespielt, obwohl die Runde vorbei ist (wird ignoriert)."""

    PLAYED_AFTER_GAME_OVER  = 83
    """Runde gespielt, obwohl die Partie bereits entschieden ist (wird ignoriert)."""

    # 9) Tichu-Ansage

    ANNOUNCEMENT_NOT_POSSIBLE = 90
    """Tichu-Ansage an der geloggten Position nicht möglich (wurde korrigiert)."""

class BWParserError(Exception):
    """
    Ein Fehler, der beim Parsen einer Logdatei aufgetreten ist.
    """
    def __init__(self, message: str, game_id: int, round_index: int, line_index: int, line: str, year: int, month: int, *args):
        """
        :param message: Fehlermeldung.
        :param game_id: ID der Partie.
        :param round_index: Index der Runde in der Partie.
        :param line_index: Zeilenindex der Logdatei.
        :param line: Zeile der Logdatei.
        :param year: Jahr der Logdatei.
        :param month: Monat der Logdatei.
        """
        super().__init__(message, *args)
        self.message = message
        self.game_id = game_id
        self.round_index = round_index
        self.line_index = line_index
        self.line = line
        self.year = year
        self.month = month

    def __str__(self):
        return f"{self.message} - {self.year:04d}{self.month:02d}/{self.game_id}.tch, Zeile {self.line_index + 1}: '{self.line}'"


@dataclass
class BWLogEntry:
    """
    Datencontainer für eine einzelne Runde in der Logdatei.

    :ivar game_id: ID der Partie.
    :ivar round_index: Index der Runde innerhalb der Partie.
    :ivar line_index: Zeilenindex der Logdatei, in der die Runde beginnt.
    :ivar player_names: Die Namen der 4 Spieler dieser Runde.
    :ivar grand_tichu_hands: Die ersten 8 Handkarten der vier Spieler zu Beginn der Runde.
    :ivar start_hands: Die 14 Handkarten der Spieler vor dem Schupfen.
    :ivar given_schupf_cards: Abgegebene Tauschkarten (an rechten Gegner, Partner, linken Gegner).
    :ivar tichu_positions: Position in der Historie, an der ein Tichu angesagt wurde (-3 == kein Tichu, -2 == großes Tichu, -1 == Ansage vor Schupfen).
    :ivar bomb_owners: Gibt für jeden Spieler an, ob eine Bombe auf der Hand ist.
    :ivar wish_value: Der gewünschte Kartenwert (2 bis 14, 0 == ohne Wunsch, -1 == kein Wunscheintrag).
    :ivar dragon_recipient: Index des Spielers, der den Drachen bekommen hat (-1 == Drache wurde nicht verschenkt).
    :ivar score: Geloggtes Ergebnis dieser Runde pro Team (Team20, Team31)
    :ivar score_expected: Erwartetes Ergebnis pro Team (Team20, Team31). Wird beim Validieren berechnet.
    :ivar history: Spielzüge. Jeder Spielzug ist ein Tuple: Spieler-Index, gespielte Karten, Zeilenindex der Logdatei.
    :ivar adjusted_history: Bereinigte Spielzüge. Jeder Spielzug ist ein Tuple: Spieler-Index, gespielte Karten, Index des Spielers, der den Stich nach dem Zug kassiert, Zeilenindex der Logdatei. Wird beim Validieren gesetzt.
    :ivar year: Jahr der Logdatei.
    :ivar month: Monat der Logdatei.
    :ivar error_code: Fehlercode.
    :ivar error_line_index: Index der fehlerhaften Zeile in der Logdatei (-1 == fehlerlos).
    """
    game_id: int = -1
    round_index: int = -1
    line_index: int = -1
    player_names: List[str] = field(default_factory=lambda: ["", "", "", ""])
    grand_tichu_hands: List[str] = field(default_factory=lambda: ["", "", "", ""])
    start_hands: List[str] = field(default_factory=lambda: ["", "", "", ""])
    given_schupf_cards: List[str] = field(default_factory=lambda: ["", "", "", ""])
    tichu_positions: List[int] = field(default_factory=lambda: [-3, -3, -3, -3])
    bomb_owners: List[bool] = field(default_factory=lambda: [False, False, False, False])
    wish_value: int = 0
    dragon_recipient: int = -1
    score: Tuple[int, int] = (0, 0)
    score_expected: Tuple[int, int] = (0, 0)
    history: List[Tuple[int, str, int]] = field(default_factory=list)
    adjusted_history: List[Tuple[int, str, int]] = field(default_factory=list)
    year: int = -1
    month: int = -1
    error_code: BWErrorCode = BWErrorCode.NO_ERROR
    error_line_index: int = -1


# Type-Alias für Daten einer Partie
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
        # Datencontainer für eine Runde in der Logdatei
        log_entry = BWLogEntry(game_id=game_id, round_index=len(bw_log), line_index=line_index, year=year, month=month)
        try:
            # Jede Runde beginnt mir der Zeile "---------------Gr.Tichukarten------------------"

            separator = "---------------Gr.Tichukarten------------------"
            line = lines[line_index].strip()
            if line != separator:
                raise BWParserError(f"Seperator 'Gr.Tichukarten' erwartet", game_id, len(bw_log), line_index, line, year, month)
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
                        raise BWParserError(f"Seperator 'Startkarten' erwartet", game_id, len(bw_log), line_index, line, year, month)
                    line_index += 1
                for player_index in range(0, 4):
                    line = lines[line_index].strip()
                    # Index des Spielers prüfen
                    if line[:3] != f"({player_index})":
                        raise BWParserError("Spieler-Index erwartet", game_id, len(bw_log), line_index, line, year, month)
                    j = line.find(" ")
                    if j == -1:
                        raise BWParserError("Leerzeichen erwartet", game_id, len(bw_log), line_index, line, year, month)
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
                        raise BWParserError("Spieler-Index erwartet", game_id, len(bw_log), line_index, line, year, month)
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
                raise BWParserError("'Schupfen:' erwartet", game_id, len(bw_log), line_index, line, year, month)
            line_index += 1

            # Jetzt werden die 4 Spieler mit den Tauschkarten aufgelistet, z.B.:
            # (0)Smocker gibt: charliexyz: Hu - Amb4lamps23: BD - Andreavorn: R9 -
            # (1)charliexyz gibt: Amb4lamps23: S4 - Andreavorn: GA - Smocker: B3 -
            # (2)Amb4lamps23 gibt: Andreavorn: B2 - Smocker: G3 - charliexyz: S2 -
            # (3)Andreavorn gibt: Smocker: R7 - charliexyz: RB - Amb4lamps23: G2 -

            for player_index in range(0, 4):
                line = lines[line_index].strip()
                # Index des Spielers prüfen
                if line[:3] != f"({player_index})":
                    raise BWParserError("Spieler-Index erwartet", game_id, len(bw_log), line_index, line, year, month)
                j = line.find(" gibt: ")
                if j == -1:
                    raise BWParserError("' gibt:' erwartet", game_id, len(bw_log), line_index, line, year, month)
                # Anzahl der Tauschkarten prüfen
                s = line[j + 7:].rstrip(" -").split(" - ")
                j = len(s)
                if j != 3:
                    raise BWParserError("Drei Tauschkarten erwartet", game_id, len(bw_log), line_index, line, year, month)
                cards = ["", "", ""]
                # Tauschkarten ermitteln
                for k in range(0, 3):
                    _player_name, card = s[k].split(": ")
                    cards[k] = card.replace("10", "Z")
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
                        raise BWParserError("Spieler-Index erwartet", game_id, len(bw_log), line_index, line, year, month)
                    player_index = int(s[1])
                    # Bomben-Besitzer übernehmen
                    log_entry.bomb_owners[player_index] = True
                line_index += 1

            # Es folgt die Trennzeile "---------------Rundenverlauf------------------".

            separator = "---------------Rundenverlauf------------------"
            line = lines[line_index].strip()
            if line != separator:
                raise BWParserError(f"Seperator 'Rundenverlauf' erwartet", game_id, len(bw_log), line_index, line, year, month)
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
                        raise BWParserError("Leerzeichen erwartet", game_id, len(bw_log), line_index, line, year, month)
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
                        raise BWParserError("Kartenwert als Wunsch erwartet", game_id, len(bw_log), line_index, line, year, month)
                    # Wunsch übernehmen
                    log_entry.wish_value = 14 if wish == "A" else 13 if wish == "K" else 12 if wish == "D" else 11 if wish == "B" else int(wish)
                    line_index += 1

                elif line.startswith("Tichu: "):  # Tichu angesagt (z.B. "Tichu: (3)Andreavorn")
                    # Index des Spielers ermitteln
                    s = line[7:]
                    if s[:3] not in ["(0)", "(1)", "(2)", "(3)"]:
                        raise BWParserError("Spieler-Index erwartet", game_id, len(bw_log), line_index, line, year, month)
                    player_index = int(s[1])
                    # Tichu-Ansage übernehmen
                    if log_entry.tichu_positions[player_index] == -3:  # es kommt vor, dass mehrmals direkt hintereinander Tichu angesagt wurde (Spieler zu hektisch geklickt?)
                        log_entry.tichu_positions[player_index] = len(log_entry.history)
                    line_index += 1

                elif line.startswith("Drache an: "):  # Drache verschenkt (z.B. "Drache an: (1)charliexyz")
                    # Index des Spielers ermitteln, der den Drachen bekommt
                    s = line[11:]
                    if s[:3] not in ["(0)", "(1)", "(2)", "(3)"]:
                        raise BWParserError("Spieler-Index erwartet", game_id, len(bw_log), line_index, line, year, month)
                    player_index = int(s[1])
                    # Empfänger des Drachens übernehmen
                    log_entry.dragon_recipient = player_index
                    line_index += 1

                elif line.startswith("Ergebnis: "):  # z.B. "Ergebnis: 40 - 60"
                    # Score ermitteln
                    values = line[10:].split(" - ")
                    if len(values) != 2:
                        raise BWParserError("Zwei Werte getrennt mit ' - ' erwartet", game_id, len(bw_log), line_index, line, year, month)
                    try:
                        score = int(values[0]), int(values[1])
                    except ValueError:
                        raise BWParserError("Zwei Integer erwartet", game_id, len(bw_log), line_index, line, year, month)
                    # Score übernehmen
                    log_entry.score = score
                    line_index += 1
                    break  # While-Schleife für Rundenverlauf verlassen

                else:
                    raise BWParserError("Spielzug erwartet", game_id, len(bw_log), line_index, line, year, month)

            # Rundenverlauf Ende

        except IndexError as e:
            if line_index >= num_lines:
                # Abruptes Ende der Logdatei, d.h., die Runde wurde nicht zu Ende gespielt.
                # Das ist normal und wird nicht als Fehler betrachtet.
                return bw_log
            else: # Runde wurde zu Ende gespielt, der Fehler liegt woanders
                raise e

        # Runde ist beendet.

        # Runde in die Rückgabeliste hinzufügen
        bw_log.append(log_entry)

        # Leerzeilen überspringen
        while line_index < num_lines and lines[line_index].strip() == "":
            line_index += 1

    return bw_log


def _validate_score(log_entry: BWLogEntry) -> bool:
    """
    Prüft, ob der Skore plausibel ist.

    :param log_entry: Die geparsten Rundendaten.
    :return: True, wenn der Skore plausibel ist, sonst False.
    """
    # Punktzahl muss durch 5 teilbar sein.
    if log_entry.score[0] % 5 != 0 or log_entry.score[1] % 5 != 0:
        return False

    sum_score = log_entry.score[0] + log_entry.score[1]

    # Wer hat Tichu angesagt?
    tichus = [0, 0, 0, 0]
    for player_index in range(0, 4):
        if log_entry.tichu_positions[player_index] != -3:
            tichus[player_index] = 2 if log_entry.tichu_positions[player_index] == -2 else 1

    # Fälle durchspielen, wer zuerst fertig wurde
    for winner_index in range(0, 4):
        bonus = sum([(100 if winner_index == i else -100) * tichus[i] for i in range(0, 4)])
        if sum_score == bonus or sum_score == bonus + 200:  # normaler Sieg (die Karten ergeben in der Summe 0 Punkte) oder Doppelsieg
            return True
    return False


def validate_bw_log(bw_log: BWLog) -> bool:
    """
    Validiert die geparste Logdatei auf Plausibilität.

    Schritt 1) Untersuchung auf Schwerwiegende Fehler:
    Sobald der erste Prio1-Fehler gefunden wurde, wird der Fehler-Code in `bw_log` festgehalten und
    False zurückgegeben.

    Schritt 2) Untersuchung auf korrigierbare oder vernachlässigbare Fehler
    Wenn kein Prio1-Fehler gefunden wird, werden alle Prio2-Fehler untersucht und u.U. korrigiert, aber
    nur der erste wird in `bw_log` festgehalten.

    :param bw_log: Die geparsten Rundendaten der Partie (mutable).
    :return: True, wenn kein Prio1-Fehler in der gesamten Partie valide gefunden wurde, sonst False.
    """
    for log_entry in bw_log:

        # ------------------------------------------------------
        # Prio 1: Schwerwiegende Fehler
        # ------------------------------------------------------

        # Einzelne Handkarten vor dem Schupfen
        start_hands = []
        for player_index in range(0, 4):
            hand = log_entry.start_hands[player_index]
            start_hands.append(hand.split(" "))

        # 1) Karten validieren

        # Sind alle Karten verteilt und keine mehrfach vergeben?
        check_deck = start_hands[0] + start_hands[1] + start_hands[2] + start_hands[3]
        if len(check_deck) != 56 or list(deck) != len(set(check_deck)):
            log_entry.error_code = BWErrorCode.INVALID_CARD_DISTRIBUTION
            log_entry.error_line_index = log_entry.line_index
            break

        # Grand-Tichu-Karten prüfen
        for player_index in range(0, 4):
            # Kartenlabel
            card_str = log_entry.grand_tichu_hands[player_index]
            if not validate_cards(card_str):
                log_entry.error_code = BWErrorCode.INVALID_CARD_LABEL
                log_entry.error_line_index = log_entry.line_index + 1 + player_index
                break

            # Anzahl
            cards = card_str.split(" ")
            if len(cards) != 8:
                log_entry.error_code = BWErrorCode.INVALID_CARD_COUNT
                log_entry.error_line_index = log_entry.line_index + 1 + player_index
                break

            # Duplikate
            if len(set(cards)) != 8:
                log_entry.error_code = BWErrorCode.DUPLICATE_CARD
                log_entry.error_line_index = log_entry.line_index + 1 + player_index
                break

            # Ist Handkarte
            if any(card not in start_hands[player_index] for card in cards):
                log_entry.error_code = BWErrorCode.CARD_NOT_IN_HAND
                log_entry.error_line_index = log_entry.line_index + 1 + player_index
                break

        # Startkarten prüfen
        for player_index in range(0, 4):
            # Kartenlabel
            card_str = log_entry.start_hands[player_index]
            if not validate_cards(card_str):
                log_entry.error_code = BWErrorCode.INVALID_CARD_LABEL
                log_entry.error_line_index = log_entry.line_index + 6 + player_index
                break

            # Anzahl
            cards = card_str.split(" ")
            if len(cards) != 14:
                log_entry.error_code = BWErrorCode.INVALID_CARD_COUNT
                log_entry.error_line_index = log_entry.line_index + 6 + player_index
                break

            # Duplikate
            if len(set(cards)) != 14:
                log_entry.error_code = BWErrorCode.DUPLICATE_CARD
                log_entry.error_line_index = log_entry.line_index + 6 + player_index
                break

        # Schupfkarten prüfen
        for player_index in range(0, 4):
            # Kartenlabel
            card_str = log_entry.given_schupf_cards[player_index]
            if not validate_cards(card_str):
                log_entry.error_code = BWErrorCode.INVALID_CARD_LABEL
                log_entry.error_line_index = log_entry.line_index + 11 + player_index
                break

            # Anzahl
            cards = card_str.split(" ")
            if len(cards) != 3:
                log_entry.error_code = BWErrorCode.INVALID_CARD_COUNT
                log_entry.error_line_index = log_entry.line_index + 11 + player_index
                break

            # Duplikate
            if len(set(cards)) != 3:
                log_entry.error_code = BWErrorCode.DUPLICATE_CARD
                log_entry.error_line_index = log_entry.line_index + 11 + player_index
                break

            # Ist Handkarte
            if any(card not in start_hands[player_index] for card in cards):
                log_entry.error_code = BWErrorCode.CARD_NOT_IN_HAND
                log_entry.error_line_index = log_entry.line_index + 11 + player_index
                break

        # Handkarten nach dem Schupfen ermitteln
        hand_cards = []
        for player_index in range(4):  # Geber
            # Tauschkarten abgeben.
            given_schupf_cards = log_entry.given_schupf_cards[player_index].split(" ")
            remaining_cards = [card for card in start_hands[player_index] if card not in given_schupf_cards]
            assert len(remaining_cards) == 11
            # Tauscharten aufnehmen.
            received_schupf_cards = [
                log_entry.given_schupf_cards[(player_index + 1) % 4].split(" ")[2],
                log_entry.given_schupf_cards[(player_index + 2) % 4].split(" ")[1],
                log_entry.given_schupf_cards[(player_index + 3) % 4].split(" ")[0],
            ]
            cards = remaining_cards + received_schupf_cards
            assert len(cards) == 14
            assert len(set(cards)) == 14, "Es sind doppelte Karten im Spiel."
            hand_cards.append(cards)

        # Gespielte Karten prüfen
        for history_index, (player_index, card_str, line_index) in enumerate(log_entry.history):
            if card_str:
                # Kartenlabel
                if not validate_cards(card_str):
                    log_entry.error_code = BWErrorCode.INVALID_CARD_LABEL
                    log_entry.error_line_index = line_index
                    break

                # Duplikate
                cards = card_str.split(" ")
                if len(set(cards)) != len(cards):
                    log_entry.error_code = BWErrorCode.DUPLICATE_CARD
                    log_entry.error_line_index = line_index
                    break

                # Ist Handkarte
                if any(card not in log_entry.start_hands[player_index].split(" ") for card in cards):
                    log_entry.error_code = BWErrorCode.CARD_NOT_IN_HAND
                    log_entry.error_line_index = line_index
                    break

        # 2) Zugwechsel
        for history_index, (player_index, card_str, line_index) in enumerate(log_entry.history):
            pass

            # PLAYER_NOT_ON_TURN = 20
            # Der Spieler ist nicht am Zug.

        # 3) Spielzug

        # CARD_ALREADY_PLAYED = 14
        # Karte bereits gespielt.

        # INVALID_COMBINATION = 30
        # Ungültige Kombination.

        # COMBINATION_NOT_PLAYABLE = 31
        # Kombination nicht spielbar.

        # PASS_NOT_POSSIBLE = 32
        # Passen nicht möglich.

        # TURN_MISSING = 33
        # Es fehlen Einträge in der Historie."""

        # 4) Wunsch

        # WISH_WITHOUT_MAHJONG = 40
        # Wunsch geäußert, aber kein Mahjong gespielt.

        # WISH_NOT_FOLLOWED = 41
        # Wunsch nicht beachtet (hätte erfüllt werden können).

        # Korrektur: "ohne Wunsch" (0) eintragen, wenn der Mahjong gespielt wurde, aber kein Wunsch geäußert wurde (was legitim ist).
        if log_entry.wish_value == -1:
            if any(card == "Ma" for card in cards.split(" ")):
                log_entry.wish_value = 0

        # 5) Drache verschenken

        # DRAGON_GIVEN_WITHOUT_BEAT = 50
        # Drache verschenkt, aber Drache hat den Stich nicht gewonnen.

        # DRAGON_NOT_GIVEN = 51
        # Drache hat den Stich nicht gewonnen, wurde aber nicht verschenkt.

        # DRAGON_GIVEN_TO_TEAM = 52
        # Drache an eigenes Team verschenkt.

        # Drache an sich selbst oder an den Partner verschenkt?
        # Das kommt immer wieder mal vor.
        if round_data.dragon_recipient != -1:
            if dragon_giver == -1:
                print(f"{year:04d}{month:02d}/{game_id}.tch, Zeile {i}: {line}\nDrache wurde verschenkt, aber niemals gespielt")
                return None
            if round_data.dragon_recipient not in [(dragon_giver + 1) % 4, (dragon_giver + 3) % 4]:
                round_data.parser_error = "DRAGON_RECIPIENT_ERROR"
                result.append(round_data)
                return result

        # ------------------------------------------------------
        # Prio 2: Korrigierte oder vernachlässigbare Fehler
        # ------------------------------------------------------

        # 6) Spielerliste

        # Falls der Name eines Spielers fehlt (oder nur aus Leerzeichen besteht), generieren wir einen eindeutigen Namen.
        for player_index in range(0, 4):
            if log_entry.player_names[player_index] != "":
                log_entry.player_names[player_index] = f"Noname-{log_entry.game_id}-{player_index}"
                log_entry.error_code = BWErrorCode.PLAYER_NAME_MISSING
                log_entry.error_line_index = log_entry.line_index + 1 + player_index

        # 7) Endergebnis

        # SCORE_MISMATCH = 60
        # Rundenergebnis stimmt nicht (wurde korrigiert).

        # Rechenfehler? Auch das kommt immer wieder mal vor. Bis 2010 ständig, mittlerweile nur noch selten.
        if not _validate_score(round_data):
            round_data.parser_error = "SCORE_ERROR"
            result.append(round_data)
            return result

        # 8) Überflüssige Spielzüge

        # PASSED_AFTER_ROUND_END = 91
        # Gepasst, obwohl die Runde vorbei ist (wird ignoriert).

        # PLAYED_AFTER_ROUND_END = 92
        # Karten ausgespielt, obwohl die Runde vorbei ist (wird ignoriert).

        # PLAYED_AFTER_GAME_OVER  = 93
        # Runde gespielt, obwohl die Partie bereits entschieden ist (wird ignoriert)."""

        # 9) Tichu-Ansage

        # ANNOUNCEMENT_NOT_POSSIBLE = 80
        # Tichu-Ansage an der geloggten Position nicht möglich (wurde korrigiert).




    return True


class BWReplayError(Exception):
    """
    Ein Fehler, der beim Abspielen einer geparsten Partie aufgetreten ist
    """
    def __init__(self, message: str, round_data: BWLogEntry, history_index: int = None, *args):
        if history_index is None:
            message = f"{round_data.year:04d}{round_data.month:02d}/{round_data.game_id}.tch, ab Zeile {round_data.line_index + 1}\n{message}"
        else:
            message = f"{round_data.year:04d}{round_data.month:02d}/{round_data.game_id}.tch, Zeile {round_data.history[history_index][2] + 1}:\n{message}"
        super().__init__(message, *args)


def _take_trick(pub: PublicState, round_data: BWLogEntry, history_index: int):
    """
    Räumt den Stich ab.

    :param pub: Der öffentliche Spielzustand.
    :param round_data: Die geparsten Daten einer Runde.
    """
    assert pub.trick_combination[0] != CombinationType.PASS
    assert pub.trick_owner_index == pub.current_turn_index
    if pub.trick_combination == (CombinationType.SINGLE, 1, 15) and not pub.is_double_victory:  # Drache kassiert? Muss verschenkt werden, wenn kein Doppelsieg!
        # Stich verschenken
        recipient = round_data.dragon_recipient
        if recipient == -1:
            raise BWReplayError("'dragon_recipient' fehlt", round_data, history_index)
        if not recipient in ((1, 3) if pub.current_turn_index in (0, 2) else (0, 2)):
            raise BWReplayError(f"Spieler {pub.current_turn_index} muss Drache an Gegner verschenken, gibt ihn aber an Spieler {recipient}", round_data, history_index)
        assert CARD_DRA in pub.played_cards
        assert pub.dragon_recipient == -1
        pub.dragon_recipient = recipient
    else:
        # Stich selbst kassieren
        recipient = pub.trick_owner_index

    # Punkte im Stich dem Spieler Gut schreiben.
    pub.points[recipient] += pub.trick_points
    assert -25 <= pub.points[recipient] <= 125

    # Stich zurücksetzen
    pub.trick_owner_index = -1
    pub.trick_cards = []
    pub.trick_combination = (CombinationType.PASS, 0, 0)
    pub.trick_points = 0
    pub.trick_counter += 1


def replay_play(all_round_data: List[BWLogEntry]) -> Generator[Tuple[PublicState, List[PrivateState], Tuple[Cards, Combination]]]:
    """
    Spielt eine geloggte Partie nach und gibt jeden Entscheidungspunkt für das Ausspielen der Karten zurück.

    :param all_round_data: Die geparsten Daten einer geloggten Partie.
    :return: Ein Generator, der den öffentlichen Spielzustand, die 4 privaten Spielzustände und die ausgeführte Aktion liefert.
    """
    if len(all_round_data) == 0:
        return None

    # Spielzustand initialisieren
    pub = PublicState(table_name="bw_replay", player_names=all_round_data[0].player_names)
    privs = [PrivateState(player_index=i) for i in range(4)]
    pub.is_running = True

    # Partie spielen
    for round_data in all_round_data:
        if round_data.parser_error:
            continue

        # Neue Runde...
        pub.player_names = round_data.player_names

        # Spielzustand für eine neue Runde zurücksetzen.
        pub.reset_round()
        for priv in privs:
            priv.reset_round()

        # Die ersten 8 Karten aufnehmen.
        for player_index in range(4):
            privs[player_index].hand_cards = parse_cards(round_data.grand_tichu_hands[player_index])
            assert len(privs[player_index].hand_cards) == 8, f"'grand_tichu_hands' müssen 8 Karten sein. Es sind nur {len(privs[player_index].hand_cards)}."
            pub.count_hand_cards[player_index] = 8

        # Hat ein Spieler ein großes Tichu angesagt?
        for player_index in range(4):
            if round_data.tichu_positions[player_index] == -2:
                pub.announcements[player_index] = 2

        # Die restlichen Karten aufnehmen.
        for player_index in range(4):
            privs[player_index].hand_cards = parse_cards(round_data.start_hands[player_index])
            assert len(privs[player_index].hand_cards) == 14, f"'start_hands' müssen 14 Karten sein. Es sind nur {len(privs[player_index].hand_cards)}."
            pub.count_hand_cards[player_index] = 14

        # Hat ein Spieler ein normales Tichu angesagt?
        for player_index in range(4):
            if round_data.tichu_positions[player_index] == -1:
                pub.announcements[player_index] = 1

        # Jetzt müssen die Spieler schupfen (Tauschkarten abgeben).
        for player_index in range(4):
            cards = round_data.given_schupf_cards[player_index].split(" ")
            privs[player_index].given_schupf_cards = parse_card(cards[0]), parse_card(cards[1]), parse_card(cards[2])
            privs[player_index].hand_cards = [card for card in privs[player_index].hand_cards if card not in privs[player_index].given_schupf_cards]
            if len(privs[player_index].hand_cards) != 11:
                raise BWReplayError("11 Handkarten erwartet", round_data)
            pub.count_hand_cards[player_index] = 11

        # Tauscharten aufnehmen.
        for player_index in range(4):  # Nehmer
            priv = privs[player_index]
            priv.received_schupf_cards = (
                privs[(player_index + 1) % 4].given_schupf_cards[2],
                privs[(player_index + 2) % 4].given_schupf_cards[1],
                privs[(player_index + 3) % 4].given_schupf_cards[0],
            )
            assert not set(priv.received_schupf_cards).intersection(priv.hand_cards), "Es sind doppelte Karten im Spiel."
            priv.hand_cards += priv.received_schupf_cards
            assert len(priv.hand_cards) == 14
            pub.count_hand_cards[player_index] = 14

        # Startspieler bekannt geben
        for player_index in range(4):
            if CARD_MAH in privs[player_index].hand_cards:
                assert pub.start_player_index == -1
                pub.start_player_index = player_index
                pub.current_turn_index = player_index
                break
        assert 0 <= pub.start_player_index <= 3, "Der Mahjong fehlt."

        # Sicherstellen, dass alle Karten verteilt und keine doppelt vergeben sind.
        check_deck = sorted(privs[0].hand_cards + privs[1].hand_cards + privs[2].hand_cards + privs[3].hand_cards)
        assert check_deck == list(deck), "Es wurden nicht alle Karten verteilt oder es sind welche doppelt."

        # Los geht's - das eigentliche Spiel kann beginnen.
        # Spiele die History Zug für Zug nach
        for history_index, (player_index, card_labels, line_index) in enumerate(round_data.history):
            if pub.is_round_over:
                # Falls ein Spieler nach Rundenende gepasst hat, ignorieren wir es einfach.
                if card_labels == "":
                    continue
                raise BWReplayError(f"Die Historie hat noch Einträge, aber die Runde {round_data.round_index + 1} ist beendet.", round_data, history_index)

            assert 0 <= pub.count_hand_cards[pub.current_turn_index] <= 14

            # Hat ein Spieler ein normales Tichu angesagt?
            for i in range(4):
                if round_data.tichu_positions[i] == history_index:
                    assert pub.announcements[i] == 0, "Der Spieler hat bereits ein Tichu angesagt."
                    if pub.count_hand_cards[i] != 14:
                        raise BWReplayError("Spieler kann kein Tichu ansagen, hat bereits Karten ausgespielt", round_data, history_index)
                    assert pub.count_hand_cards[i] == 14, "Der Spieler kann kein Tichu mehr ansagen. Er hat bereits Karten ausgespielt."
                    pub.announcements[i] = 1

            if card_labels == "":
                # Passen
                cards = []
                combination = CombinationType.PASS, 0, 0
            else:
                # Karten spielen
                cards = parse_cards(card_labels)
                combination = get_combination(cards, pub.trick_combination[2])
                if combination[0] == CombinationType.BOMB:
                    pub.current_turn_index = player_index

            # Ist der Spieler in der Historie auch der aktuelle Spieler?
            if player_index != pub.current_turn_index:
                raise BWReplayError("Spieler ist nicht am Zug", round_data, history_index)

            if combination[0] == CombinationType.PASS:
                # Falls alle gepasst haben, schaut der Spieler auf seinen eigenen Stich und kann diesen abräumen.
                if pub.trick_owner_index == pub.current_turn_index and pub.trick_combination != (CombinationType.SINGLE, 1, 0):  # der Hund bleibt liegen
                    _take_trick(pub, round_data, history_index)
                    #if combination[0] == CombinationType.PASS:
                    # Falls hier ein Passen-Eintrag in der History steht, können wir den einfach überspringen.
                    continue

                assert pub.trick_owner_index != -1 and len(pub.tricks) > 0, "Beim Anspiel darf nicht gepasst werden."

                if pub.wish_value > 0:
                    # Wird der Wunsch beachtet?
                    action_space = build_action_space(privs[player_index].combinations, pub.trick_combination, pub.wish_value)
                    if action_space[0][1][0] != CombinationType.PASS:
                        raise BWReplayError("Wunsch wurde nicht beachtet", round_data, history_index)

                # Entscheidungspunkt für "play"
                yield pub, privs, (cards, combination)

                # Entscheidung des Spielers festhalten
                pub.tricks[-1].append((player_index, cards, combination))
            else:
                # Karten spielen
                if any(card not in privs[player_index].hand_cards for card in cards):
                    raise BWReplayError("Ausgespielte Karten waren nicht auf der Hand", round_data, history_index)

                ok = False
                action_space = build_action_space(privs[player_index].combinations, pub.trick_combination, pub.wish_value)
                for playable_cards, playable_combination in action_space:
                    if set(cards) == set(playable_cards):
                        ok = True
                        break
                if not ok:
                    if pub.wish_value > 0:
                        if action_space[0][1][0] != CombinationType.PASS:
                            if is_wish_in(pub.wish_value, action_space[0][0]):
                                raise BWReplayError("Wunsch wurde nicht beachtet", round_data, history_index)
                    raise BWReplayError("Ausgespielte Karten sind nicht spielbar", round_data, history_index)

                # Entscheidungspunkt für "play"
                yield pub, privs, (cards, combination)

                # Entscheidung des Spielers festhalten
                if pub.trick_owner_index == -1:  # neuer Stich?
                    pub.tricks.append([(player_index, cards, combination)])
                else:
                    assert len(pub.tricks) > 0
                    pub.tricks[-1].append((player_index, cards, combination))

                # Handkarten aktualisieren
                privs[player_index].hand_cards = [card for card in privs[player_index].hand_cards if card not in cards]
                pub.count_hand_cards[player_index] -= combination[1]
                assert pub.count_hand_cards[player_index] == len(privs[player_index].hand_cards)

                # Stich aktualisieren
                pub.trick_owner_index = player_index
                pub.trick_cards = cards
                if combination == (CombinationType.SINGLE, 1, 16):
                    assert pub.trick_combination[0] == CombinationType.PASS or pub.trick_combination[0] == CombinationType.SINGLE
                    assert pub.trick_combination != (CombinationType.SINGLE, 1, 15)  # Phönix auf Drachen geht nicht
                    # Der Phönix ist eigentlich um 0.5 größer als der Stich, aber gleichsetzen geht auch (Anspiel == 1).
                    if pub.trick_combination[2] == 0:  # Anspiel oder Hund?
                        pub.trick_combination = (CombinationType.SINGLE, 1, 1)
                else:
                    pub.trick_combination = combination
                pub.trick_points += sum_card_points(cards)
                assert -25 <= pub.trick_points <= 125

                # Gespielte Karten merken
                assert not set(cards).intersection(pub.played_cards), f"cards: {stringify_cards(cards)},  played_cards: {stringify_cards(pub.played_cards)}"  # darf keine Schnittmenge bilden
                pub.played_cards += cards

                # Ist der erste Spieler fertig?
                if pub.count_hand_cards[pub.current_turn_index] == 0:
                    n = pub.count_active_players
                    assert 1 <= n <= 3
                    if n == 3:
                        assert pub.winner_index == -1
                        pub.winner_index = pub.current_turn_index

                # Wunsch erfüllt?
                assert pub.wish_value == -1 or pub.wish_value == 0 or -2 >= pub.wish_value >= -14 or 2 <= pub.wish_value <= 14
                if pub.wish_value > 0 and is_wish_in(pub.wish_value, cards):
                    assert CARD_MAH in pub.played_cards
                    pub.wish_value = -pub.wish_value

                # Ist die Runde beendet?
                if pub.count_hand_cards[pub.current_turn_index] == 0:
                    n = pub.count_active_players
                    assert 1 <= n <= 3
                    if n == 2:
                        assert 0 <= pub.winner_index <= 3
                        if (pub.current_turn_index + 2) % 4 == pub.winner_index:  # Doppelsieg?
                            pub.is_round_over = True
                            pub.is_double_victory = True
                    elif n == 1:
                        pub.is_round_over = True
                        for loser_index in range(4):
                            if pub.count_hand_cards[loser_index] > 0:
                                assert pub.loser_index == -1
                                pub.loser_index = loser_index
                                break

                # Runde vorbei?
                if pub.is_round_over:
                    # Runde ist vorbei; letzten Stich abräumen und die Schleife für Kartenausspielen beenden
                    _take_trick(pub, round_data, history_index)
                    continue  # Nächsten Eintrag aus der Historie holen (sollte nicht mehr vorhanden sein, also endet der Schleifendurchlauf)

                # Falls ein MahJong ausgespielt wurde, muss ein Wunsch geäußert werden.
                if CARD_MAH in cards:
                    assert pub.wish_value == 0
                    pub.wish_value = round_data.wish_value if round_data.wish_value > 0 else -1  # todo umkodieren
                    assert 2 <= pub.wish_value <= 14 or pub.wish_value == -1

            # Nächsten Spieler ermitteln
            assert 0 <= pub.current_turn_index <= 3
            if pub.trick_combination == (CombinationType.SINGLE, 1, 0) and pub.trick_owner_index == pub.current_turn_index:
                pub.current_turn_index = (pub.current_turn_index + 2) % 4
            else:
                pub.current_turn_index = (pub.current_turn_index + 1) % 4

            # Spieler ohne Handkarten überspringen (für diese gibt es keine Logeinträge)
            while pub.count_hand_cards[pub.current_turn_index] == 0:
                if pub.trick_owner_index == pub.current_turn_index and pub.trick_combination != (CombinationType.SINGLE, 1, 0):  # der Hund bleibt liegen
                    _take_trick(pub, round_data, history_index)  # Der Spieler hat zwar keine Karten mehr, den Stich räumt er aber dennoch ab.
                pub.current_turn_index = (pub.current_turn_index + 1) % 4
            assert pub.count_hand_cards[pub.current_turn_index] > 0

        # Runde ist beendet
        # Endwertung der Runde

        assert pub.is_round_over, "Die Historie hat keine Einträge mehr, aber die Runde läuft noch."
        if pub.is_double_victory:
            # Doppelsieg! Das Gewinnerteam kriegt 200 Punkte. Die Gegner nichts.
            assert sum(1 for n in pub.count_hand_cards if n > 0) == 2
            assert 0 <= pub.winner_index <= 3
            pub.points = [0, 0, 0, 0]
            pub.points[pub.winner_index] = 200
        else:
            # a) Der letzte Spieler gibt seine Handkarten an das gegnerische Team.
            assert 0 <= pub.loser_index <= 3
            leftover_points = 100 - sum_card_points(pub.played_cards)
            assert leftover_points == sum_card_points(other_cards(pub.played_cards))
            pub.points[(pub.loser_index + 1) % 4] += leftover_points
            # b) Der letzte Spieler übergibt seine Stiche an den Spieler, der zuerst fertig wurde.
            assert pub.winner_index >= 0
            pub.points[pub.winner_index] += pub.points[pub.loser_index]
            pub.points[pub.loser_index] = 0
            assert sum(pub.points) == 100, pub.points
            assert -25 <= pub.points[0] <= 125
            assert -25 <= pub.points[1] <= 125
            assert -25 <= pub.points[2] <= 125
            assert -25 <= pub.points[3] <= 125

        # Bonus für Tichu-Ansage
        for player_index in range(4):
            if pub.announcements[player_index]:
                if player_index == pub.winner_index:
                    pub.points[player_index] += 100 * pub.announcements[player_index]
                else:
                    pub.points[player_index] -= 100 * pub.announcements[player_index]

        # Ergebnis der Runde in die Punktetabelle der Partie eintragen.
        if pub.points[2] + pub.points[0] != round_data.score[0] or pub.points[3] + pub.points[1] != round_data.score[1]:
            raise BWReplayError(f"Ergebnis der Runde stimmt nicht: {pub.points} != {round_data.score}", round_data)
        pub.game_score[0].append(round_data.score[0])
        pub.game_score[1].append(round_data.score[1])

    # Partie ist beendet
    pub.is_running = False
    return None


# # Bugfix: Hier hat der letzte Spieler noch eine Bombe geworfen, obwohl die Runde vorbei war.
# if game_id == 1437889 and i == 735:  # 201303/1437889.tch, Zeile 735
#     continue