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

from scipy.special import log_expit

from src.lib.cards import validate_card, validate_cards, parse_card, parse_cards, Cards, CARD_MAH, CARD_DRA, deck, stringify_cards, sum_card_points, is_wish_in, other_cards, stringify_card
from src.lib.combinations import get_trick_combination, Combination, CombinationType, build_action_space, build_combinations
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

    Der erste zutreffende Fehler wird in `BWLog` festgehalten.
    """
    NO_ERROR = 0
    """Kein Fehler"""

    # 1) Gesamt-Punktestand der Partie
    PLAYED_AFTER_GAME_OVER  = 10
    """Runde gespielt, obwohl die Partie bereits entschieden ist."""

    # 1) Karten

    INVALID_CARD_LABEL = 20
    """Ungültiges Karten-Label."""

    INVALID_CARD_COUNT = 21
    """Anzahl der Karten ist fehlerhaft."""

    DUPLICATE_CARD = 22
    """Karten mehrmals vorhanden."""

    CARD_NOT_IN_HAND = 23
    """Karte gehört nicht zu den Handkarten."""

    CARD_ALREADY_PLAYED = 24
    """Karte bereits gespielt."""

    # 2) Spielzüge

    PASS_NOT_POSSIBLE = 30
    """Passen nicht möglich."""

    WISH_NOT_FOLLOWED = 31
    """Wunsch nicht beachtet (hätte erfüllt werden können)."""

    COMBINATION_NOT_PLAYABLE = 32
    """Kombination nicht spielbar."""

    SMALLER_OF_AMBIGUOUS_RANK = 33
    """Es wurde der kleinere Rang bei einem mehrdeutigen Rang gewählt."""

    PLAYER_NOT_ON_TURN = 34
    """Der Spieler ist nicht am Zug."""

    HISTORY_TOO_SHORT = 35
    """Es fehlen Einträge in der Historie."""

    HISTORY_TOO_LONG = 36
    """Karten ausgespielt, obwohl die Runde vorbei ist (wird ignoriert)."""

    # 3) Drache verschenken

    DRAGON_NOT_GIVEN = 40
    """Drache hat den Stich nicht gewonnen, wurde aber nicht verschenkt."""

    DRAGON_GIVEN_TO_OWN_TEAM = 41
    """Drache an eigenes Team verschenkt."""

    DRAGON_GIVEN_WITHOUT_BEAT = 42
    "Drache verschenkt, aber niemand hat durch den Drachen ein Stich gewonnen."

    # 4) Wunsch

    WISH_WITHOUT_MAHJONG = 50
    """Wunsch geäußert, aber kein Mahjong gespielt."""

    # 6) Spielerliste

    PLAYER_NAME_MISSING = 60
    """Name des Spieler fehlt (wurde korrigiert)."""

    DUPLICATE_PLAYER_NAME = 61
    """Name des Spieler ist nicht eindeutig (wurde korrigiert)."""

    # 8) Tichu-Ansage

    ANNOUNCEMENT_NOT_POSSIBLE = 70
    """Tichu-Ansage an der geloggten Position nicht möglich (wurde korrigiert)."""

    # 6) Endergebnis

    SCORE_MISMATCH = 80
    """Rundenergebnis stimmt nicht."""

    SCORE_MISMATCH_AT_2_GRANDS = 81
    """Bekannter Rechenfehler bei zwei Grand Tichus im selben Team."""

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
    Datencontainer für eine geparste Runde aus der Logdatei.

    :ivar game_id: ID der Partie.
    :ivar round_index: Index der Runde innerhalb der Partie.
    :ivar line_index: Zeilenindex der Logdatei, in der die Runde beginnt.
    :ivar player_names: Die Namen der 4 Spieler dieser Runde.
    :ivar grand_tichu_hands: Die ersten 8 Handkarten der vier Spieler zu Beginn der Runde.
    :ivar start_hands: Die 14 Handkarten der Spieler vor dem Schupfen.
    :ivar given_schupf_cards: Abgegebene Tauschkarten (an rechten Gegner, Partner, linken Gegner).
    :ivar tichu_positions: Position in der Historie, an der Tichu angesagt wurde (-3 == kein Tichu, -2 == großes Tichu, -1 == Ansage vor oder während des Schupfens).
    :ivar bomb_owners: Gibt für jeden Spieler an, ob eine Bombe auf der Hand ist.
    :ivar wish_value: Der gewünschte Kartenwert (2 bis 14, -1 == kein Eintrag).
    :ivar dragon_recipient: Index des Spielers, der den Drachen bekommen hat (-1 == kein Eintrag).
    :ivar score: Geloggtes Ergebnis dieser Runde pro Team (Team20, Team31)
    :ivar history: Spielzüge. Jeder Spielzug ist ein Tuple: Spieler-Index + gespielte Karten + Zeilenindex der Logdatei.
    :ivar year: Jahr der Logdatei.
    :ivar month: Monat der Logdatei.
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
                for player_index in range(4):
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

            for player_index in range(4):
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
    for player_index in range(4):
        if log_entry.tichu_positions[player_index] != -3:
            tichus[player_index] = 2 if log_entry.tichu_positions[player_index] == -2 else 1

    # Fälle durchspielen, wer zuerst fertig wurde
    for winner_index in range(4):
        bonus = sum([(100 if winner_index == i else -100) * tichus[i] for i in range(4)])
        if sum_score == bonus or sum_score == bonus + 200:  # normaler Sieg (die Karten ergeben in der Summe 0 Punkte) oder Doppelsieg
            return True
    return False


@dataclass
class BWDataset:
    """
    Datencontainer für eine validierte Runde.

    :ivar game_id: ID der Partie.
    :ivar round_index: Index der Runde innerhalb der Partie.
    :ivar player_names: Die Namen der 4 Spieler dieser Runde.
    :ivar start_hands: Handkarten der Spieler vor dem Schupfen (zuerst die 8 Grand-Tichu-Karten, danach die restlichen).
    :ivar given_schupf_cards: Abgegebene Tauschkarten (an rechten Gegner, Partner, linken Gegner).
    :ivar tichu_positions: Position in der Historie, an der Tichu angesagt wurde (-3 == kein Tichu, -2 == großes Tichu, -1 == Ansage vor oder während des Schupfens).
    :ivar wish_value: Der gewünschte Kartenwert (2 bis 14, 0 == ohne Wunsch, -1 == kein Mahjong gespielt).
    :ivar dragon_recipient: Index des Spielers, der den Drachen bekommen hat (-1 == Drache wurde nicht verschenkt).
    :ivar winner_index: Index des Spielers, der zuerst in der aktuellen Runde fertig wurde (-1 == kein Spieler).
    :ivar loser_index: Index des Spielers, der in der aktuellen Runde als letztes übrig blieb (-1 == kein Spieler).
    :ivar is_double_victory: Gibt an, ob die Runde durch einen Doppelsieg beendet wurde.
    :ivar score: Berechnetes Rundenergebnis (Team20, Team31).
    :ivar history: Spielzüge. Jeder Spielzug ist ein Tuple: Spieler-Index + gespielte Karten + Index des Spielers, der den Stich nach dem Zug kassiert (-1 == Stich nicht kassiert).
    :ivar year: Jahr der Logdatei.
    :ivar month: Monat der Logdatei.
    :ivar error_code: Fehlercode.
    :ivar error_line_index: Index der fehlerhaften Zeile in der Logdatei (-1 == fehlerlos).
    :ivar score_logged: Geloggtes Rundenergebnis (Team20, Team31), falls es vom berechneten Rundenergebnis abweicht, sonst None.
    """
    game_id: int = -1
    round_index: int = -1
    player_names: List[str] = field(default_factory=lambda: ["", "", "", ""])
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
    error_line_index: int = -1
    score_logged: Optional[Tuple[int, int]] = None


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
        assert len(remaining_cards) == 11
        # Tauscharten aufnehmen.
        received_cards = [
            given_schupf_cards[(player_index + 1) % 4][2],
            given_schupf_cards[(player_index + 2) % 4][1],
            given_schupf_cards[(player_index + 3) % 4][0],
        ]
        cards = remaining_cards + received_cards
        assert len(cards) == 14
        assert len(set(cards)) == 14
        hands.append(cards)
    return hands


def validate_bw_log(bw_log: BWLog) -> List[BWDataset]:
    """
    Validiert die geparste Logdatei auf Plausibilität.

    Schritt 1) Untersuchung auf Schwerwiegende Fehler:
    Sobald der erste Prio1-Fehler gefunden wurde, wird der Fehler-Code in `bw_log` festgehalten und
    False zurückgegeben.

    Schritt 2) Untersuchung auf korrigierbare oder vernachlässigbare Fehler
    Wenn kein Prio1-Fehler gefunden wird, werden alle Prio2-Fehler untersucht und u.U. korrigiert, aber
    nur der erste wird in `bw_log` festgehalten.

    :param bw_log: Die geparsten Rundendaten der Partie (mutable).
    :return: Die validierten Daten.
    """
    datasets = []
    total_score = [0, 0]
    for log_entry in bw_log:
        error_code = BWErrorCode.NO_ERROR
        error_line_index = -1

        if total_score[0] >= 1000 or total_score[1] >= 1000:
            error_code = BWErrorCode.PLAYED_AFTER_GAME_OVER
            error_line_index = log_entry.line_index

        # Karten aufsplitten
        grand_tichu_hands: List[List[str]] = []
        start_hands: List[List[str]] = []
        given_schupf_cards: List[List[str]] = []
        for player_index in range(4):
            grand_tichu_hands.append(log_entry.grand_tichu_hands[player_index].split(" "))
            start_hands.append(log_entry.start_hands[player_index].split(" "))
            given_schupf_cards.append(log_entry.given_schupf_cards[player_index].split(" "))

        # Handkarten prüfen
        if error_code == BWErrorCode.NO_ERROR:
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
            assert 0 <= player_index <= 3

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
                    assert len(history) > 0 and history[-1][2] == -1
                    if trick_combination[2] == 15:  # der Drache hat den Stich gewonnen
                        dragon_giver = trick_owner_index
                        trick_collector_index = log_entry.dragon_recipient
                    else:
                        trick_collector_index = trick_owner_index
                    history[-1] = history[-1][0], history[-1][1], trick_collector_index
                    points[trick_collector_index] += trick_points
                    assert -25 <= points[trick_owner_index] <= 125
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
                assert len(hands[player_index]) == num_hand_cards[player_index]  # todo raus
                combinations[player_index] = build_combinations([parse_card(label) for label in hands[player_index]])

                # Stich aktualisieren
                trick_points += sum_card_points(parsed_cards)
                assert -25 <= trick_points <= 125
                trick_combination = combination
                trick_owner_index = player_index
                # Der Rang ist nicht eindeutig, wenn beim Fullhouse der Phönix in der Mitte liegt oder bei der Straße am Ende bzw. Ende.
                is_trick_rank_ambiguous = (
                      (combination[0] == CombinationType.FULLHOUSE and parsed_cards[2][0] == 16) or
                      (combination[0] == CombinationType.STREET and parsed_cards[0][0] == 16)
                )

                # Wunsch erfüllt?
                if wish_value > 0 and is_wish_in(wish_value, parsed_cards):
                    assert "Ma" in played_cards
                    wish_value = 0

                # Runde vorbei?
                if num_hand_cards[player_index] == 0:
                    finished_players = num_hand_cards.count(0)
                    if finished_players == 1:
                        assert winner_index == -1
                        winner_index = player_index
                    elif finished_players == 2:
                        assert winner_index != -1
                        if num_hand_cards[(player_index + 2) % 4] == 0:
                            is_double_victory = True
                            is_round_over = True
                    else:
                        assert finished_players == 3
                        for i in range(4):
                            if num_hand_cards[i] > 0:
                                loser_index = i
                                break
                        assert loser_index != -1
                        is_round_over = True
                    # Falls die Runde vorbei ist, zum nächsten Eintrag in der Historie springen.
                    # Dürfte es nicht mehr geben ud somit den Schleifendurchlauf beenden.
                    if is_round_over:
                        continue

                # Falls ein MahJong ausgespielt wurde, kann der Spieler sich einen Kartenwert wünschen.
                if 'Ma' in cards:
                    wish_value = log_entry.wish_value

            # Nächsten Spieler ermitteln
            assert 0 <= current_turn_index <= 3
            if trick_combination == (CombinationType.SINGLE, 1, 0) and trick_owner_index == current_turn_index:
                current_turn_index = (current_turn_index + 2) % 4
            else:
                current_turn_index = (current_turn_index + 1) % 4

            # Spieler ohne Handkarten überspringen (für diese gibt es keine Logeinträge)
            while num_hand_cards[current_turn_index] == 0:
                # Wenn der Spieler auf seinen eigenen Stich schaut, kassiert er ihn, selbst wenn er keine Handkarten mehr hat.
                if current_turn_index == trick_owner_index and trick_combination != (CombinationType.SINGLE, 1, 0):  # der Hund bleibt liegen
                    # Stich kassieren
                    assert len(history) > 0 and history[-1][2] == -1
                    if trick_combination[2] == 15:  # der Drache hat den Stich gewonnen
                        dragon_giver = trick_owner_index
                        trick_collector_index = log_entry.dragon_recipient
                    else:
                        trick_collector_index = trick_owner_index
                    history[-1] = history[-1][0], history[-1][1], trick_collector_index
                    points[trick_collector_index] += trick_points
                    assert -25 <= points[trick_owner_index] <= 125
                    trick_points = 0
                    trick_combination = CombinationType.PASS, 0, 0
                    trick_owner_index = -1
                current_turn_index = (current_turn_index + 1) % 4
            assert num_hand_cards[current_turn_index] > 0

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
        assert len(history) > 0 and history[-1][2] == -1
        if trick_combination[2] == 15:  # der Drache hat den Stich gewonnen
            dragon_giver = trick_owner_index
            trick_collector_index = log_entry.dragon_recipient
        else:
            trick_collector_index = trick_owner_index
        history[-1] = history[-1][0], history[-1][1], trick_collector_index
        points[trick_collector_index] += trick_points
        assert -25 <= points[trick_owner_index] <= 125

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

        # Spielerliste prüfen
        player_names = []
        for player_index in range(4):
            # Spielernamen generieren, wenn er nicht vorhanden ist (oder nur aus Leerzeichen besteht)
            name = log_entry.player_names[player_index]
            if name == "":
                name = f"Noname-{log_entry.game_id}"
                if error_code == BWErrorCode.NO_ERROR:
                    error_code = BWErrorCode.PLAYER_NAME_MISSING
                    error_line_index = log_entry.line_index + 1 + player_index
            # Sicherstellen, dass der Name eindeutig ist.
            i = 1
            while name in player_names:
                i += 1
                name = f"{log_entry.player_names[player_index]} ({i})"
                if error_code == BWErrorCode.NO_ERROR:
                    error_code = BWErrorCode.DUPLICATE_PLAYER_NAME
                    error_line_index = log_entry.line_index + 1 + player_index
            player_names.append(name)

        # Position der Tichu-Ansage prüfen und korrigieren
        for player_index in range(4):
            if tichu_positions[player_index] > first_pos[player_index]:
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
            assert winner_index >= 0
            # a) Der letzte Spieler gibt seine Handkarten an das gegnerische Team.
            leftover_points = 100 - sum_card_points([parse_card(label) for label in played_cards])
            assert leftover_points == sum_card_points(other_cards([parse_card(label) for label in played_cards]))  # todo raus
            points[(loser_index + 1) % 4] += leftover_points
            # b) Der letzte Spieler übergibt seine Stiche an den Spieler, der zuerst fertig wurde.
            points[winner_index] += points[loser_index]
            points[loser_index] = 0
            if sum(points) != 100:
                assert sum(points) == 100, points
                assert all(-25 <= p <= 125 for p in points), points
        else:
            # Rundenergebnis aufgrund Fehler im Spielverlauf nicht berechenbar
            assert error_code != BWErrorCode.NO_ERROR
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
                if (tichu_positions[0] == -2 and tichu_positions[2] == -2) or (tichu_positions[1] == -2 and tichu_positions[3] == -2):
                    error_code = BWErrorCode.SCORE_MISMATCH_AT_2_GRANDS
                else:
                    error_code = BWErrorCode.SCORE_MISMATCH
                error_line_index = log_entry.line_index

        # Gesamt-Punktestand der Partie aktualisieren
        total_score[0] += score[0]
        total_score[1] += score[1]

        # Startkarten so sortieren, dass erst die Grand-Tichu-Karten aufgelistet sind
        sorted_start_hands = []
        for player_index in range(4):
            grand_cards = grand_tichu_hands[player_index]
            start_cards = start_hands[player_index]
            remaining_cards = [label for label in start_cards if label not in grand_cards]
            assert len(remaining_cards) == 6
            if error_code != BWErrorCode.INVALID_CARD_LABEL:
                cards = sorted([parse_card(label) for label in grand_cards], reverse=True)
                grand_cards = [stringify_card(card) for card in cards]
                cards = sorted([parse_card(label) for label in remaining_cards], reverse=True)
                remaining_cards = [stringify_card(card) for card in cards]
            sorted_start_hands.append(" ".join(grand_cards + remaining_cards))

        datasets.append(BWDataset(
            game_id=log_entry.game_id,
            round_index=log_entry.round_index,
            player_names=player_names,
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
            error_line_index=error_line_index,
            score_logged=log_entry.score if log_entry.score != score else None
        ))
    return datasets


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


def replay_play(all_round_data: List[BWLogEntry]) -> Generator[Tuple[PublicState, List[PrivateState], Tuple[Cards, Combination]]]:
    """
    Spielt eine geloggte Partie nach und gibt jeden Entscheidungspunkt für das Ausspielen der Karten zurück.

    :param all_round_data: Die geparsten Daten einer geloggten Partie.
    :return: Ein Generator, der den öffentlichen Spielzustand, die 4 privaten Spielzustände und die ausgeführte Aktion liefert.
    """
    if len(all_round_data) == 0:
        return None


    return None


# # Bugfix: Hier hat der letzte Spieler noch eine Bombe geworfen, obwohl die Runde vorbei war.
# if game_id == 1437889 and i == 735:  # 201303/1437889.tch, Zeile 735
#     continue