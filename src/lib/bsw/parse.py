"""
Parsen der vom Spiele-Portal "Brettspielwelt" heruntergeladenen Tichu-Logdateien.
"""

__all__ = "BSWLog", "BSWLogEntry", "BSWParserError", "parse_logfile",

from dataclasses import dataclass, field
from typing import List, Tuple, Optional


class BSWParserError(Exception):
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
class BSWLogEntry:
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
    :ivar history: Spielzüge. Jeder Spielzug ist ein Tuple: Spieler-Index + gespielte Karten.
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
    history: List[Tuple[int, str]] = field(default_factory=list)
    year: int = -1
    month: int = -1


# Type-Alias für die geparsten Daten einer Logdatei (einer Partie)
BSWLog = List[BSWLogEntry]


def parse_logfile(game_id: int, year: int, month: int, content: str) -> Optional[BSWLog]:
    """
    Parst eine Tichu-Logdatei vom Spiele-Portal "Brettspielwelt".

    Zurückgegeben wird eine Liste mit den Rundendaten der Partie.
    Wurde die letzte Runde abgebrochen, wird sie ignoriert.

    :param game_id: ID der Partie.
    :param year: Jahr der Logdatei.
    :param month: Monat der Logdatei.
    :param content: Inhalt der Logdatei (eine Partie).
    :return: Die eingelesenen Rundendaten der Partie.
    :raises BSWParserError: Wenn die Logdatei syntaktisch unerwartet ist. Bekannte Fehler werden abgefangen.
    """
    bsw_log = []  # Liste der Rundendaten
    lines = content.splitlines()
    num_lines = len(lines)  # Anzahl Zeilen
    line_index = 0 # Zeilenindex
    while line_index < num_lines:
        # Datencontainer für eine Runde aus der Logdatei
        log_entry = BSWLogEntry(game_id=game_id, round_index=len(bsw_log), line_index=line_index, year=year, month=month)
        try:
            # Jede Runde beginnt mir der Zeile "---------------Gr.Tichukarten------------------"

            separator = "---------------Gr.Tichukarten------------------"
            line = lines[line_index].strip()
            if line != separator:
                raise BSWParserError(f"Separator 'Gr.Tichukarten' erwartet", game_id, year, month, line_index)
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
                        raise BSWParserError(f"Separator 'Startkarten' erwartet", game_id, year, month, line_index)
                    line_index += 1
                for player_index in range(4):
                    line = lines[line_index].strip()
                    # Index des Spielers prüfen
                    if line[:3] != f"({player_index})":
                        raise BSWParserError("Spieler-Index erwartet", game_id, year, month, line_index)
                    j = line.find(" ")
                    if j == -1:
                        raise BSWParserError("Leerzeichen erwartet", game_id, year, month, line_index)
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
                        raise BSWParserError("Spieler-Index erwartet", game_id, year, month, line_index)
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
                    return bsw_log
                raise BSWParserError("'Schupfen:' erwartet", game_id, year, month, line_index)
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
                    raise BSWParserError("Spieler-Index erwartet", game_id, year, month, line_index)
                j = line.find(" gibt: ")
                if j == -1:
                    raise BSWParserError("' gibt:' erwartet", game_id, year, month, line_index)
                # Anzahl der Tauschkarten prüfen
                s = line[j + 7:].rstrip(" -").split(" - ")
                j = len(s)
                if j != 3:
                    raise BSWParserError("Drei Tauschkarten erwartet", game_id, year, month, line_index)
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
                        raise BSWParserError("Spieler-Index erwartet", game_id, year, month, line_index)
                    player_index = int(s[1])
                    # Bomben-Besitzer übernehmen
                    log_entry.bomb_owners[player_index] = True
                line_index += 1

            # Es folgt die Trennzeile "---------------Rundenverlauf------------------".

            separator = "---------------Rundenverlauf------------------"
            line = lines[line_index].strip()
            if line != separator:
                raise BSWParserError(f"Separator 'Rundenverlauf' erwartet", game_id, year, month, line_index)
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
                        raise BSWParserError("Leerzeichen erwartet", game_id, year, month, line_index)
                    # Aktion auswerten (Karten gespielt oder gepasst?)
                    action = line[j + 1:].rstrip(".")  # 201205/1150668.tch endet in dieser Zeile, sodass der Punkt fehlt
                    cards = action.replace("10", "Z") if action != "passt" else ""
                    # Spielzug übernehmen
                    log_entry.history.append((player_index, cards))
                    line_index += 1

                elif line.startswith("Wunsch:"):  # Wunsch geäußert (z.B. "Wunsch:2")
                    # Wunsch ermitteln
                    wish = line[7:]
                    if wish not in ["2", "3", "4", "5", "6", "7", "8", "9", "10", "B", "D", "K", "A"]:  # 0 == "ohne Wunsch" wird nicht geloggt
                        raise BSWParserError("Kartenwert als Wunsch erwartet", game_id, year, month, line_index)
                    # Wunsch übernehmen
                    log_entry.wish_value = 14 if wish == "A" else 13 if wish == "K" else 12 if wish == "D" else 11 if wish == "B" else int(wish)
                    line_index += 1

                elif line.startswith("Tichu: "):  # Tichu angesagt (z.B. "Tichu: (3)Andreavorn")
                    # Index des Spielers ermitteln
                    s = line[7:]
                    if s[:3] not in ["(0)", "(1)", "(2)", "(3)"]:
                        raise BSWParserError("Spieler-Index erwartet", game_id, year, month, line_index)
                    player_index = int(s[1])
                    # Tichu-Ansage übernehmen
                    if log_entry.tichu_positions[player_index] == -3:  # es kommt vor, dass mehrmals direkt hintereinander Tichu angesagt wurde (Spieler zu hektisch geklickt?)
                        log_entry.tichu_positions[player_index] = len(log_entry.history)
                    line_index += 1

                elif line.startswith("Drache an: "):  # Drache verschenkt (z.B. "Drache an: (1)charliexyz")
                    # Index des Spielers ermitteln, der den Drachen bekommt
                    s = line[11:]
                    if s[:3] not in ["(0)", "(1)", "(2)", "(3)"]:
                        raise BSWParserError("Spieler-Index erwartet", game_id, year, month, line_index)
                    player_index = int(s[1])
                    # Empfänger des Drachens übernehmen
                    log_entry.dragon_recipient = player_index
                    line_index += 1

                elif line.startswith("Ergebnis: "):  # z.B. "Ergebnis: 40 - 60"
                    # Score ermitteln
                    values = line[10:].split(" - ")
                    if len(values) != 2:
                        raise BSWParserError("Zwei Werte getrennt mit ' - ' erwartet", game_id, year, month, line_index)
                    try:
                        score = int(values[0]), int(values[1])
                    except ValueError:
                        raise BSWParserError("Zwei Integer erwartet", game_id, year, month, line_index)
                    # Score übernehmen
                    log_entry.score = score
                    line_index += 1
                    break  # While-Schleife für Rundenverlauf verlassen

                else:
                    raise BSWParserError("Spielzug erwartet", game_id, year, month, line_index)

            # Rundenverlauf Ende

        except IndexError as e:
            if line_index >= num_lines:
                # Abruptes Ende der Logdatei, d.h., die Runde wurde nicht zu Ende gespielt.
                # Das ist normal und wird nicht als Fehler betrachtet.
                return bsw_log
            else: # Runde wurde zu Ende gespielt, der Fehler liegt woanders
                raise e

        # Runde ist beendet.

        # Ausschnitt der Logdatei für Debug-Zwecke übernehmen
        log_entry.content = "\n".join(lines[log_entry.line_index:line_index])

        # Runde in die Rückgabeliste hinzufügen
        bsw_log.append(log_entry)

        # Leerzeilen überspringen
        while line_index < num_lines and lines[line_index].strip() == "":
            line_index += 1

    return bsw_log