"""
Dieses Modul stellt Funktionen bereit, die mit Tichu-Logdateien vom Spiele-Portal "Brettspielwelt" umgehen können.
"""

__all__ = "download_logfiles_from_bw", \
    "bw_logfiles", "bw_count_logfiles", \
    "BWRoundData", "parse_bw_logfile", \
    "BWReplayError", "replay_play"

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


@dataclass
class BWRoundData:
    """
    Datencontainer für eine einzelne Runde.

    :ivar game_id: ID der Partie.
    :ivar round_index: Index der Runde innerhalb der Partie.
    :ivar player_names: Die Namen der 4 Spieler dieser Runde.
    :ivar grand_tichu_hands: Die ersten 8 Handkarten der vier Spieler zu Beginn der Runde.
    :ivar start_hands: Die 14 Handkarten der Spieler vor dem Schupfen.
    :ivar tichu_positions: Position in der Historie, an der ein Tichu angesagt wurde (-3 == kein Tichu, -2 == großes Tichu, -1 == Ansage vor Schupfen).
    :ivar given_schupf_cards: Abgegebene Tauschkarten (an rechten Gegner, Partner, linken Gegner).
    :ivar bomb_owners: Gibt für jeden Spieler an, ob eine Bombe auf der Hand ist.
    :ivar wish_value: Wunsch (2 bis 14; 0 == kein Wunsch geäußert).
    :ivar dragon_recipient: Index des Spielers, der den Drachen bekommen hat (-1 == Drache wurde bis zum Schluss nicht verschenkt).
    :ivar score: Punkte dieser Runde pro Team (Team20, Team31).
    :ivar history: Spielzüge. Jeder Spielzug ist ein Tuple aus Spieler-Index, Karten und Zeilenindex der Logdatei.
    :ivar year: Jahr der Logdatei.
    :ivar month: Monat der Logdatei.
    :ivar line_index: Zeilenindex der Logdatei, in der die Runde beginnt.
    :ivar parser_error: Bekannte Fehler, die nicht zu beheben sind todo wieder entfernen, sobald ich weiß, wie ich mit dem Fehler umgehen kann
    """
    game_id: int = -1
    round_index: int = -1
    player_names: List[str] = field(default_factory=lambda: ["", "", "", ""])
    grand_tichu_hands: List[str] = field(default_factory=lambda: ["", "", "", ""])
    start_hands: List[str] = field(default_factory=lambda: ["", "", "", ""])
    tichu_positions: List[int] = field(default_factory=lambda: [-3, -3, -3, -3])
    given_schupf_cards: List[Tuple[str, str, str]] = field(default_factory=lambda: [("", "", ""), ("", "", ""), ("", "", ""), ("", "", "")])
    bomb_owners: List[bool] = field(default_factory=lambda: [False, False, False, False])
    wish_value: int = 0
    dragon_recipient: int = -1
    score: Tuple[int, int] = (0, 0)
    history: List[Tuple[int, str, int]] = field(default_factory=list)
    year: int = -1
    month: int = -1
    line_index: int = -1
    parser_error: str = ""


# Type-Alias für Daten einer Partie
# BWGameData = List[BWRoundData]


# Type-Alias für eine strukturierte Aktion
Action = Dict[str, Any]


# class BWParserError(Exception):
#     """
#     Fehler, die beim Parsen auftreten können.
#     """
#     pass

class BWReplayError(Exception):
    """
    Fehler, beim Abspielen einer geparsten Partie.
    """
    def __init__(self, message: str, round_data: BWRoundData, history_index: int = None, *args):
        if history_index is None:
            message = f"{round_data.year:04d}{round_data.month:02d}/{round_data.game_id}.tch, ab Zeile {round_data.line_index + 1}\n{message}"
        else:
            message = f"{round_data.year:04d}{round_data.month:02d}/{round_data.game_id}.tch, Zeile {round_data.history[history_index][2] + 1}:\n{message}"
        super().__init__(message, *args)


# class BWParserErrorCode(enum.IntEnum):
#     """
#     Enum für Errorcodes (Auskommentierte Codes werden noch nicht benutzt!)
#     """
#     UNKNOWN_ERROR = 100
#     """Ein unbekannter Fehler ist aufgetreten."""
#
#     NO_RESULT = 101
#     """Runde wurde nicht zu Ende gespielt."""


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


def _validate_score(round_data: BWRoundData) -> bool:
    """
    Prüft, ob der Skore plausibel ist.

    :param round_data: Die geparsten Rundendaten.
    :return: True, wenn der Skore plausibel ist, sonst False.
    """
    # Punktzahl muss durch 5 teilbar sein.
    if round_data.score[0] % 5 != 0 or round_data.score[1] % 5 != 0:
        return False

    sum_score = round_data.score[0] + round_data.score[1]

    # Wer hat Tichu angesagt?
    tichus = [0, 0, 0, 0]
    for player_index in range(0, 4):
        if round_data.tichu_positions[player_index] != -3:
            tichus[player_index] = 2 if round_data.tichu_positions[player_index] == -2 else 1

    # Fälle durchspielen, wer zuerst fertig wurde
    for winner_index in range(0, 4):
        bonus = sum([(100 if winner_index == i else -100) * tichus[i] for i in range(0, 4)])
        if sum_score == bonus or sum_score == bonus + 200:  # normaler Sieg (die Karten ergeben in der Summe 0 Punkte) oder Doppelsieg
            return True
    return False


def parse_bw_logfile(game_id: int,  year: int, month: int, content: str) -> Optional[List[BWRoundData]]:
    """
    Parst eine Tichu-Logdatei vom Spiele-Portal "Brettspielwelt".

    Die Logdatei hält genau eine Partie fest. Zurückgegeben wird eine Liste mit den Rundendaten der Partie.
    Wenn die List syntaktisch fehlerhaft, also nicht wie erwartet aufgebaut ist, wird der Vorgang abgebrochen
    und None zurückgegeben. Bekannte Fehler werden abgefangen.

    :param game_id: Die ID der Partie.
    :param year: Das Jahr der Logdatei.
    :param month: Der Monat der Logdatei.
    :param content: Der Inhalt der Logdatei.
    :return: Die eingelesenen Rundendaten der Partie oder None bei unbekannten Fehlern.
    """
    result = []
    lines = content.splitlines()
    n = len(lines)  # Anzahl Zeilen
    i = 0 # Zeilenindex
    while i < n:
        # Datencontainer für eine Runde
        round_data = BWRoundData(game_id=game_id, round_index=len(result), year=year, month=month, line_index=i)
        first_history_index = [-1, -1, -1, -1]  # Position in der Historie für den ersten Spielzug
        dragon_giver = -1  # Index des Spielers, der den Drachen verschenkt
        try:
            # Jede Runde beginnt mir der Zeile "---------------Gr.Tichukarten------------------"

            separator = "---------------Gr.Tichukarten------------------"
            line = lines[i].strip()
            i += 1
            if line != separator:
                print(f"{year:04d}{month:02d}/{game_id}.tch, Zeile {i}: {line}\n'{separator}' erwartet")
                return None

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
                    line = lines[i].strip()
                    i += 1
                    if line != separator:
                        print(f"{year:04d}{month:02d}/{game_id}.tch, Zeile {i}: {line}\n'{separator}' erwartet")
                        return None
                for player_index in range(0, 4):
                    line = lines[i].strip()
                    i += 1
                    # Index des Spielers prüfen
                    if line[:3] != f"({player_index})":
                        print(f"{year:04d}{month:02d}/{game_id}.tch, Zeile {i}: {line}\nIndex des Spielers erwartet")
                        return None
                    j = line.find(" ")
                    if j == -1:
                        print(f"{year:04d}{month:02d}/{game_id}.tch, Zeile {i}: {line}\nLeerzeichen erwartet")
                        return None
                    name = line[3:j].strip()
                    # Handkarten prüfen
                    cards = line[j + 1:].replace("10", "Z")
                    if not validate_cards(cards):
                        print(f"{year:04d}{month:02d}/{game_id}.tch, Zeile {i}: {line}\nMindesten eine Karte ist ungültig")
                        return None
                    # Name des Spielers und Handkarten übernehmen
                    if k == 8:
                        round_data.player_names[player_index] = name if name != "" else f"Noname-{game_id}-{player_index}"
                        round_data.grand_tichu_hands[player_index] = cards
                    else:
                        round_data.start_hands[player_index] = cards

            # if len(round_data.player_names) != 4 or any(not name.strip() for name in round_data.player_names):
            #     print(f"{year:04d}{month:02d}/{game_id}.tch, Zeile {i}: {line}\nKeine 4 Spieler am Tisch")
            #     return None

            # Es folgen Zeilen mit "Grosses Tichu:", danach mit "Tichu:", sofern Tichu angesagt wurde, z.B.:
            # Tichu: (1)charliexyz

            for grand in [True, False]:
                while lines[i].strip().startswith("Grosses Tichu: " if grand else "Tichu: "):
                    line = lines[i].strip()
                    i += 1
                    # Index des Spielers prüfen
                    s = line[15:] if grand else line[7:]
                    if s[:3] not in ["(0)", "(1)", "(2)", "(3)"]:
                        print(f"{year:04d}{month:02d}/{game_id}.tch, Zeile {i}: {line}\nSpieler-Index erwartet")
                        return None
                    player_index = int(s[1])
                    # Tichu-Ansage übernehmen
                    round_data.tichu_positions[player_index] = -2 if grand else -1

            # Es folgt die Zeile "Schupfen:".

            line = lines[i].strip()
            i += 1
            if line != "Schupfen:":
                if game_id <= 2215951 and line == "---------------Gr.Tichukarten------------------":
                    # Bugfix: Hier wird abrupt eine neue Runde gestartet.
                    # In 201202/1045639.tch trat dieser Fehler erstmalig in Zeile 734 auf.
                    # Zwischen 2014-08 (ab 1792439.tch) und 2018-09 (bis 2215951.tch) trat er insgesamt 34 mal auf, und
                    # zwar immer in der ersten Runde (Zeile 11). Der Fehler wurde wohl gefixt und wird nicht mehr erwartet.
                    return result
                print(f"{year:04d}{month:02d}/{game_id}.tch, Zeile {i}: {line}\n'Schupfen:' erwartet")
                return None

            # Jetzt werden die 4 Spieler mit den Tauschkarten aufgelistet, z.B.:
            # (0)Smocker gibt: charliexyz: Hu - Amb4lamps23: BD - Andreavorn: R9 -
            # (1)charliexyz gibt: Amb4lamps23: S4 - Andreavorn: GA - Smocker: B3 -
            # (2)Amb4lamps23 gibt: Andreavorn: B2 - Smocker: G3 - charliexyz: S2 -
            # (3)Andreavorn gibt: Smocker: R7 - charliexyz: RB - Amb4lamps23: G2 -

            for player_index in range(0, 4):
                line = lines[i].strip()
                i += 1
                # Index des Spielers prüfen
                if line[:3] != f"({player_index})":
                    print(f"{year:04d}{month:02d}/{game_id}.tch, Zeile {i}: {line}\nIndex des Spielers erwartet")
                    return None
                j = line.find(" gibt: ")
                if j == -1:
                    print(f"{year:04d}{month:02d}/{game_id}.tch, Zeile {i}: {line}\n' gibt:' erwartet")
                    return None
                # Anzahl der Tauschkarten prüfen
                s = line[j + 7:].rstrip(" -").split(" - ")
                j = len(s)
                if j != 3:
                    print(f"{year:04d}{month:02d}/{game_id}.tch, Zeile {i}: {line}\nDrei Tauschkarten erwartet")
                    return None
                cards = ["", "", ""]
                for k in range(0, 3):
                    _player_name, card = s[k].split(": ")
                    # Tauschkarte prüfen
                    cards[k] = card.replace("10", "Z")
                    if not validate_card(cards[k]):
                        print(f"{year:04d}{month:02d}/{game_id}.tch, Zeile {i}: {line}\nKarte {card} ist ungültig")
                        return None
                # Tauschkarte übernehmen
                round_data.given_schupf_cards[player_index] = cards[0], cards[1], cards[2]
                # In seltenen Fällen wurde dieselbe Karte zweimal abgegeben.
                if len(set(round_data.given_schupf_cards[player_index])) != 3:
                    round_data.parser_error = "GIVEN_SCHUPF_ERROR"
                    result.append(round_data)
                    return result

            # Nun werden die Spieler mit einer Bombe aufgelistet, z.B
            # BOMBE: (0)Smocker (2)Amb4lamps23 (3)Andreavorn

            if lines[i].strip().startswith("BOMBE: "):
                line = lines[i].strip()
                i += 1
                for s in line[7:].split(" "):
                    # Index des Spielers prüfen
                    if s[:3] not in ["(0)", "(1)", "(2)", "(3)"]:
                        print(f"{year:04d}{month:02d}/{game_id}.tch, Zeile {i}: {line}\nSpieler-Index erwartet")
                        return None
                    player_index = int(s[1])
                    # Bomben-Besitzer übernehmen
                    round_data.bomb_owners[player_index] = True

            # Es folgt die Trennzeile "---------------Rundenverlauf------------------".

            separator = "---------------Rundenverlauf------------------"
            line = lines[i].strip()
            i += 1
            if line != separator:
                print(f"{year:04d}{month:02d}/{game_id}.tch, Zeile {i}: {line}\n'{separator}' erwartet")
                return None

            # Nun werden die Spielzüge gezeigt. Entweder ein Spieler spielt Karten oder er passt, z.B.:
            # (1)charliexyz passt.
            # (2)Amb4lamps23: R8 S8 B8 G8
            # Im Rundenverlauf können noch Zeilen stehen, die mit "Wunsch:", "Tichu: " oder "Drache an: " beginnen.
            # Die Runde endet mit der Zeile, die mit "Ergebnis: " beginnt.

            # Rundenverlauf
            while True:
                line = lines[i].strip()
                i += 1
                # Bugfix: Hier hat der letzte Spieler noch eine Bombe geworfen, obwohl die Runde vorbei war.
                if game_id == 1437889 and i == 735:  # 201303/1437889.tch, Zeile 735
                    continue

                if line[:3] in ["(0)", "(1)", "(2)", "(3)"]:  # z.B. "(1)charliexyz passt." oder "(2)Amb4lamps23: R8 S8"
                    # Index des Spielers prüfen
                    player_index = int(line[1])
                    j = line.find(" ")
                    if j == -1:
                        print(f"{year:04d}{month:02d}/{game_id}.tch, Zeile {i}: {line}\nLeerzeichen erwartet")
                        return None
                    # Aktion prüfen
                    action = line[j + 1:].rstrip(".")  # 201205/1150668.tch endet in dieser Zeile, sodass der Punkt fehlt
                    if action == "passt":
                        # Spielzug übernehmen
                        round_data.history.append((player_index, "", i - 1))
                    else:  # Karten ausgespielt
                        # Karten prüfen
                        cards = action.replace("10", "Z")
                        if not validate_cards(cards):
                            print(f"{year:04d}{month:02d}/{game_id}.tch, Zeile {i}: {line}\nMindesten eine Karte ist ungültig")
                            return None
                        if cards == "Dr":
                            dragon_giver = player_index
                        # Spielzug übernehmen
                        if first_history_index[player_index] == -1:
                            first_history_index[player_index] = len(round_data.history)
                        round_data.history.append((player_index, cards, i - 1))

                elif line.startswith("Wunsch:"):  # z.B. "Wunsch:2"
                    wish = line[7:]
                    if wish not in ["2", "3", "4", "5", "6", "7", "8", "9", "10", "B", "D", "K", "A"]:
                        print(f"{year:04d}{month:02d}/{game_id}.tch, Zeile {i}: {line}\nWunsch: zwischen 2 und 14 erwartet")
                        return None
                    # Wunsch übernehmen
                    round_data.wish_value = 14 if wish == "A" else 13 if wish == "K" else 12 if wish == "D" else 11 if wish == "B" else int(wish)

                elif line.startswith("Tichu: "):  # "Tichu: (3)Andreavorn"
                    # Index des Spielers prüfen
                    s = line[7:]
                    if s[:3] not in ["(0)", "(1)", "(2)", "(3)"]:
                        print(f"{year:04d}{month:02d}/{game_id}.tch, Zeile {i}: {line}\nSpieler-Index erwartet")
                        return None
                    player_index = int(s[1])
                    # Tichu-Ansage übernehmen
                    if round_data.tichu_positions[player_index] == -3:  # es kommt vor, dass mehrmals direkt hintereinander Tichu angesagt wurde (Spieler zu hektisch geklickt?)
                        round_data.tichu_positions[player_index] = len(round_data.history)
                        # Bugfix: Falls erst Karten abgelegt und danach Tichu angesagt wurde, Position korrigieren.
                        if first_history_index[player_index] != -1:
                            round_data.tichu_positions[player_index] = first_history_index[player_index]

                elif line.startswith("Drache an: "):  # z.B. "Drache an: (1)charliexyz"
                    # Index des Spielers prüfen
                    s = line[11:]
                    if s[:3] not in ["(0)", "(1)", "(2)", "(3)"]:
                        print(f"{year:04d}{month:02d}/{game_id}.tch, Zeile {i}: {line}\nSpieler-Index erwartet")
                        return None
                    player_index = int(s[1])
                    # Empfänger des Drachens übernehmen
                    round_data.dragon_recipient = player_index

                elif line.startswith("Ergebnis: "):  # z.B. "Ergebnis: 40 - 60"
                    values = line[10:].split(" - ")
                    if len(values) != 2:
                        print(f"{year:04d}{month:02d}/{game_id}.tch, Zeile {i}: {line}\nZwei Werte getrennt mit ' - ' erwartet")
                        return None
                    try:
                        round_data.score = int(values[0]), int(values[1])
                    except ValueError:
                        print(f"{year:04d}{month:02d}/{game_id}.tch, Zeile {i}: {line}\nZwei Integer erwartet")
                        return None
                    break  # While-Schleife für Rundenverlauf verlassen

                else:
                    print(f"{year:04d}{month:02d}/{game_id}.tch, Zeile {i}: {line}\nSpielzug erwartet")
                    return None

            # Rundenverlauf Ende

        except IndexError as e:
            if i >= n:
                # Abruptes Ende der Logdatei, d.h., die Runde wurde nicht zu Ende gespielt.
                # Das ist normal und wird nicht als Fehler betrachtet.
                return result
            else: # Runde wurde zu Ende gespielt, der Fehler liegt woanders
                print(f"{year:04d}{month:02d}/{game_id}.tch, Zeile {i}: {lines[i]}\nUnbekannter Fehler: {e}")
                import traceback
                traceback.print_exc()
                return None

        except Exception as e:
            print(f"{year:04d}{month:02d}/{game_id}.tch, Zeile {i}: {lines[i]}\nUnbekannter Fehler: {e}")
            import traceback
            traceback.print_exc()
            return None

        # Runde ist beendet.

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

        # Rechenfehler? Auch das kommt immer wieder mal vor. Bis 2010 ständig, mittlerweile nur noch selten.
        if not _validate_score(round_data):
            round_data.parser_error = "SCORE_ERROR"
            result.append(round_data)
            return result

        # Runde in die Rückgabeliste hinzufügen
        result.append(round_data)

        # Leerzeilen überspringen
        while i < n and lines[i].strip() == "":
            i += 1

    return result


def _take_trick(pub: PublicState, round_data: BWRoundData, history_index: int):
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


def replay_play(all_round_data: List[BWRoundData]) -> Generator[Tuple[PublicState, List[PrivateState], Tuple[Cards, Combination]]]:
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
            cards = round_data.given_schupf_cards[player_index]
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

