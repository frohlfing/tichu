"""
Dieses Modul stellt Funktionen bereit, die mit Tichu-Logdateien vom Spiele-Portal "Brettspielwelt" umgehen können.
"""

__all__ = "download_logfiles_from_bw", "bw_logfiles", "bw_count_logfiles", "BWParserError", "parse_bw_logfile"

import copy
import enum
import os
import requests
from dataclasses import dataclass, field
from datetime import datetime
from src.lib.cards import validate_card, validate_cards, parse_card, parse_cards, Cards, CARD_MAH
from src.lib.combinations import get_combination
from src.public_state import PublicState
from src.private_state import PrivateState
from tqdm import tqdm
from typing import List, Tuple, Union, Optional, Generator, Dict, Any
from zipfile import ZipFile, ZIP_DEFLATED

# Type-Alias für eine strukturierte Aktion
Action = Dict[str, Any]

# Type-Alias für Daten einer Partie
# BWGameData = List[BWRoundData]


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


@dataclass
class BWRoundData:
    """
    Datencontainer für eine einzelne Runde.

    :ivar player_names: Die Namen der 4 Spieler dieser Runde.
    :ivar grand_tichu_hands: Die ersten 8 Handkarten der vier Spieler zu Beginn der Runde.
    :ivar start_hands: Die 14 Handkarten der Spieler vor dem Schupfen.
    :ivar tichu_positions: Position in der Historie, an der ein Tichu angesagt wurde (-3 == kein Tichu, -2 == großes Tichu, -1 == Ansage vor Schupfen).
    :ivar given_schupf_cards: Abgegebene Tauschkarten (an rechten Gegner, Partner, linken Gegner).
    :ivar bomb_owners: Gibt für jeden Spieler an, ob eine Bombe auf der Hand ist.
    :ivar wish_value: Wunsch (2 bis 14; 0 == kein Wunsch geäußert).
    :ivar dragon_recipient: Index des Spielers, der den Drachen bekommen hat (-1 == Drache wurde bis zum Schluss nicht verschenkt).
    :ivar score_entry: Punkte dieser Runde pro Team (Team20, Team31).
    :ivar history: Spielzüge. Jeder Spielzug ist ein Tuple aus Spieler-Index und Karten, oder beim Passen nur der Spieler-Index.
    """
    player_names: List[str] = field(default_factory=lambda: ["", "", "", ""])
    grand_tichu_hands: List[str] = field(default_factory=lambda: ["", "", "", ""])
    start_hands: List[str] = field(default_factory=lambda: ["", "", "", ""])
    tichu_positions: List[int] = field(default_factory=lambda: [-3, -3, -3, -3])
    given_schupf_cards: List[Tuple[str, str, str]] = field(default_factory=lambda: [("", "", ""), ("", "", ""), ("", "", ""), ("", "", "")])
    bomb_owners: List[bool] = field(default_factory=lambda: [False, False, False, False])
    wish_value: int = 0
    dragon_recipient: int = -1
    score_entry: Tuple[int, int] = (0, 0)
    history: List[Union[Tuple[int, str], int]] = field(default_factory=list)


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
        round_data = BWRoundData()
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
                        round_data.player_names[player_index] = name
                        round_data.grand_tichu_hands[player_index] = cards
                    else:
                        round_data.start_hands[player_index] = cards

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
                    # Es wird abrupt eine neue Runde gestartet.
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
                for k in range(0, 2):
                    _player_name, card = s[k].split(": ")
                    # Tauschkarte prüfen
                    cards[k] = card.replace("10", "Z")
                    if not validate_card(cards[k]):
                        print(f"{year:04d}{month:02d}/{game_id}.tch, Zeile {i}: {line}\nKarte {card} ist ungültig")
                        return None
                # Tauschkarte übernehmen
                round_data.given_schupf_cards[player_index] = cards[0], cards[1], cards[2]

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

            while True:  # Rundenverlauf
                line = lines[i].strip()
                i += 1

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
                        round_data.history.append(player_index)
                    else:
                        # Karten prüfen
                        cards = action.replace("10", "Z")
                        if not validate_cards(cards):
                            print(f"{year:04d}{month:02d}/{game_id}.tch, Zeile {i}: {line}\nMindesten eine Karte ist ungültig")
                            return None
                        # Spielzug übernehmen
                        round_data.history.append((player_index, cards))

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
                    round_data.tichu_positions[player_index] = len(round_data.history)

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
                return None

        except Exception as e:
            print(f"{year:04d}{month:02d}/{game_id}.tch, Zeile {i}: {lines[i]}\nUnbekannter Fehler: {e}")
            return None

        # Runde ist beendet.

        # Runde in die Rückgabeliste hinzufügen
        result.append(round_data)

        # Leerzeilen überspringen
        while i < n and lines[i].strip() == "":
            i += 1

    return result


def validate_bw_data(_datas: List[BWRoundData]) -> bool:
    """
    Prüft, ob die Daten der gegebenen Partie laut Regelwerk plausibel sind.

    Bei Bedarf werden die Daten korrigiert, sofern möglich.

    :param _datas: Die Daten der Partie (mutable).
    :return: True, wenn die Daten laut Regelwerk plausibel sind oder korrigiert werden konnten, ansonst False.
    """
    #todo
    pass


# todo Funktion überarbeiten
def replay_round(round_data: BWRoundData) -> Generator[Tuple[PublicState, List[PrivateState], Action], None, None]:
    """
    Spielt eine Runde aus BWRoundData nach und gibt für jeden Entscheidungspunkt
    den Zustand (PublicState, List[PrivateState]) und die ausgeführte Aktion zurück.

    :param round_data: Die geparsten Daten einer einzelnen Runde.
    :return: Ein Generator, der (pub_state, priv_states, action) Tupel liefert.
    """

    # 1. Initialisiere die Zustände aus den Start-Daten der Runde
    # -----------------------------------------------------------

    pub = PublicState(
        table_name="bw_replay",
        player_names=round_data.player_names,
        game_score=(round_data.score_entry, (0, 0))  # Simulierter Spielstand
    )
    privs = [PrivateState(player_index=i) for i in range(4)]

    # Setze die Handkarten vor dem Schupfen
    for i in range(4):
        privs[i].hand_cards = parse_cards(round_data.start_hands[i])
        pub.count_hand_cards[i] = len(privs[i].hand_cards)
        if CARD_MAH in privs[i].hand_cards:
            pub.start_player_index = i
            pub.current_turn_index = i

    # TODO: Grand-Tichu Entscheidung als erste Aktion yielden (optional)

    # 2. Simuliere das Schupfen
    # --------------------------
    # TODO: Schupfen als Aktion yielden (optional, aber gut für ein Schupf-Modell)

    given_cards = [parse_cards(" ".join(c)) for c in round_data.given_schupf_cards]
    received_cards = [[], [], [], []]
    # Berechne, wer welche Karten erhält
    for giver_idx, cards_given in enumerate(given_cards):
        if not cards_given: continue  # Manchmal fehlen Schupf-Daten
        # [an rechten Gegner, an Partner, an linken Gegner]
        privs[giver_idx].given_schupf_cards = tuple(cards_given)
        received_cards[(giver_idx + 1) % 4].append(cards_given[0])  # Rechter Gegner
        received_cards[(giver_idx + 2) % 4].append(cards_given[1])  # Partner
        received_cards[(giver_idx + 3) % 4].append(cards_given[2])  # Linker Gegner

    # Aktualisiere die Handkarten nach dem Schupfen
    for i in range(4):
        privs[i].hand_cards = [card for card in privs[i].hand_cards if card not in given_cards[i]]
        privs[i].hand_cards.extend(received_cards[i])
        privs[i].hand_cards.sort(reverse=True)
        privs[i].received_schupf_cards = tuple(received_cards[i])
        pub.count_hand_cards[i] = len(privs[i].hand_cards)

    # 3. Spiele die History Zug für Zug nach
    # ---------------------------------------

    trick_owner = -1

    for move in round_data.history:
        player_index = -1

        # Zustand vor dem Zug sichern
        pub_before_move = copy.deepcopy(pub)
        privs_before_move = copy.deepcopy(privs)

        # Aktion extrahieren und Zustand aktualisieren
        action: Action = {}

        if isinstance(move, int):  # Passen
            player_index = move
            pub.current_turn_index = (player_index + 1) % 4
            action = {'type': 'pass', 'player_index': player_index}

        elif isinstance(move, tuple):  # Karten spielen
            player_index, cards_str = move
            played_cards = parse_cards(cards_str)

            # Kombination ermitteln
            combination = get_combination(list(played_cards), pub.trick_combination[2])

            action = {'type': 'play', 'player_index': player_index, 'cards': played_cards, 'combination': combination}

            # Update States
            privs[player_index].hand_cards = [c for c in privs[player_index].hand_cards if c not in played_cards]
            pub.count_hand_cards[player_index] -= len(played_cards)
            pub.played_cards.extend(played_cards)

            # Stich-Logik
            if trick_owner == player_index or trick_owner == -1:  # Neuer Stich
                trick_owner = player_index
            else:  # Stich wird fortgesetzt
                pass  # trick_owner bleibt

            all_passed = True  # Annahme für die Rekonstruktion
            # TODO: Hier muss die Logik zur Stich-Erkennung verfeinert werden.
            # Aus den Logs allein ist schwer zu sehen, wann ein Stich abgeräumt wird.
            # Wir nehmen an: Wenn der `trick_owner` wieder an der Reihe ist, räumt er ab.
            # Für die Rekonstruktion des Zustands *vor* dem Zug ist das aber weniger wichtig.

            pub.trick_owner_index = player_index
            pub.trick_combination = combination
            pub.current_turn_index = (player_index + 1) % 4

        if player_index != -1:
            # Gib den Zustand VOR der Aktion und die Aktion selbst zurück
            yield (pub_before_move, privs_before_move, action)

    # TODO: Dragon-Geschenk und Tichu als Aktionen einbauen.
    # Man muss die `tichu_positions` und `dragon_recipient` Felder auswerten
    # und an der richtigen Stelle in der History einfügen.
