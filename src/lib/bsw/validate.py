"""
Validieren der geparsten Brettspielwelt-Logs.
"""

__all__ = "BSWRoundErrorCode", "BSWGameErrorCode", "BSWDataset", "validate_bswlog",

import enum
from dataclasses import dataclass, field
from src.lib.bsw.parse import BSWLog
from src.lib.cards import validate_cards, parse_card, sum_card_points, is_wish_in, Cards, CARD_DRA
from src.lib.combinations import get_trick_combination, CombinationType, build_action_space, build_combinations
from typing import List, Tuple, Optional


class BSWRoundErrorCode(enum.IntEnum):
    """
    Fehlercodes für Logs der Brettspielwelt.
    """
    NO_ERROR = 0
    """Kein Fehler"""

    # Karten

    INVALID_CARD_LABEL = 10
    """Unbekanntes Kartenlabel."""

    INVALID_CARD_COUNT = 11
    """Anzahl der Karten ist fehlerhaft."""

    DUPLICATE_CARD = 12
    """Karten mehrmals vorhanden."""

    CARD_NOT_IN_HAND = 13
    """Karte gehört nicht zu den Handkarten."""

    CARD_ALREADY_PLAYED = 14
    """Karte bereits gespielt."""

    # Spielzüge

    PASS_NOT_POSSIBLE = 20
    """Passen nicht möglich."""

    WISH_NOT_FOLLOWED = 21
    """Wunsch nicht beachtet."""

    COMBINATION_NOT_PLAYABLE = 22
    """Kombination nicht spielbar."""

    SMALLER_OF_AMBIGUOUS_RANK = 23
    """Es wurde der kleinere Rang bei einem mehrdeutigen Rang gewählt."""

    PLAYER_NOT_ON_TURN = 24
    """Der Spieler ist nicht am Zug."""

    HISTORY_TOO_SHORT = 25
    """Es fehlen Einträge in der Historie."""

    HISTORY_TOO_LONG = 26
    """Karten ausgespielt, obwohl die Runde vorbei ist (wurde korrigiert)."""

    # Drache verschenken

    DRAGON_NOT_GIVEN = 30
    """Drache hat den Stich nicht gewonnen, wurde aber nicht verschenkt."""

    DRAGON_GIVEN_TO_OWN_TEAM = 31
    """Drache an eigenes Team verschenkt."""

    DRAGON_GIVEN_WITHOUT_BEAT = 32
    "Drache verschenkt, aber niemand hat durch den Drachen ein Stich gewonnen."

    # Wunsch

    WISH_WITHOUT_MAHJONG = 40
    """Wunsch geäußert, aber kein Mahjong gespielt."""

    # Tichu-Ansage

    ANNOUNCEMENT_NOT_POSSIBLE = 50
    """Tichu-Ansage an der geloggten Position nicht möglich (wurde korrigiert)."""

    # Rundenergebnis

    SCORE_NOT_POSSIBLE = 60
    """Rechenfehler! Geloggtes Rundenergebnis ist nicht möglich (wurde korrigiert)."""

    SCORE_MISMATCH = 61
    """Geloggtes Rundenergebnis stimmt nicht mit dem berechneten Ergebnis überein (wurde korrigiert)."""


class BSWGameErrorCode(enum.IntEnum):
    """
    Fehlercodes für Logs der Brettspielwelt.
    """
    NO_ERROR = 0
    """Kein Fehler"""

    # Endergebnis

    GAME_NOT_FINISHED  = 70
    """Partie nicht zu Ende gespielt."""

    GAME_OVERPLAYED  = 71
    """Ein oder mehrere Runden gespielt, obwohl die Partie bereits entschieden war."""

    # Runden

    ROUND_FAILED = 80
    """Mindestens eine Runde ist fehlerhaft."""

    # Spieler

    PLAYER_CHANGED  = 90
    """Mindestens ein Spieler hat während der Partie gewechselt."""


@dataclass
class BSWDataset:
    """
    Datencontainer für eine validierte Runde.

    :ivar game_id: ID der Partie.
    :ivar round_index: Index der Runde innerhalb der Partie.
    :ivar player_names: Die Namen der 4 Spieler dieser Runde.
    :ivar start_hands: Handkarten der Spieler vor dem Schupfen (zuerst die 8 Grand-Tichu-Karten, danach die restlichen).
    :ivar schupf_hands: Abgegebene Tauschkarten der Spieler (an rechten Gegner, Partner, linken Gegner).
    :ivar tichu_positions: Position in der Historie, an der Tichu angesagt wurde (-3 == kein Tichu, -2 == großes Tichu, -1 == Ansage vor oder während des Schupfens).
    :ivar wish_value: Der gewünschte Kartenwert (2 bis 14, 0 == ohne Wunsch, -1 == kein Mahjong gespielt).
    :ivar dragon_recipient: Index des Spielers, der den Drachen bekommen hat (-1 == Drache wurde nicht verschenkt).
    :ivar winner_index: Index des Spielers, der zuerst in der aktuellen Runde fertig wurde (-1 == kein Spieler).
    :ivar loser_index: Index des Spielers, der in der aktuellen Runde als letztes übrig blieb (-1 == kein Spieler).
    :ivar is_double_victory: Gibt an, ob die Runde durch einen Doppelsieg beendet wurde.
    :ivar score: Rundenergebnis (Team20, Team31).
    :ivar history: Spielzüge. Jeder Spielzug ist ein Tuple: Spieler-Index + Karten + Spieler-Index, der den Stich nach dem Zug kassiert (-1 == Stich nicht kassiert).
    :ivar year: Jahr der Logdatei.
    :ivar month: Monat der Logdatei.
    :ivar error_code: Fehlercode.
    :ivar error_content: Im Fehlerfall der betroffene Abschnitt aus der Logdatei, sonst None.
    """
    game_id: int = -1
    round_index: int = -1
    player_names: List[str] = field(default_factory=lambda: ["", "", "", ""])
    start_hands: List[Cards] = field(default_factory=lambda: [[], [], [], []])
    schupf_hands: List[Cards] = field(default_factory=lambda: [[], [], [], []])
    tichu_positions: List[int] = field(default_factory=lambda: [-3, -3, -3, -3])
    wish_value: int = 0
    dragon_recipient: int = -1
    winner_index: int = -1,
    loser_index: int = -1,
    is_double_victory: bool = False,
    score: Tuple[int, int] = (0, 0)
    history: List[Tuple[int, Cards, int]] = field(default_factory=list)
    year: int = -1
    month: int = -1
    error_code: BSWRoundErrorCode = BSWRoundErrorCode.NO_ERROR
    error_content: Optional[str] = None


def _can_score_be_ok(score: Tuple[int, int], announcements: List[int]) -> bool:
    """
    Prüft, ob der Score plausibel ist.

    :param score: Rundenergebnis (Team20, Team31)
    :param announcements: Tichu-Ansagen pro Spieler (0 == keine Ansage, 1 == einfaches Tichu, 2 == großes Tichu).
    :return: True, wenn der Score plausibel ist, sonst False.
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


def _schupf(start_hands: List[List[str]], schupf_hands: List[List[str]]) -> List[List[str]]:
    """
    Ermittelt die Handkarten nach dem Schupfen.

    :param start_hands: Handkarten der vier Spieler vor dem Schupfen.
    :param schupf_hands: Die abgegebenen Tauschkarten der vier Spieler (an rechten Gegner, Partner, linken Gegner).
    :return: Die neuen Handkarten der vier Spieler nach dem Schupfen.
    """
    hands = []
    for player_index in range(4):  # Geber
        # Tauschkarten abgeben.
        start_card_labels = start_hands[player_index]
        given_card_labels = schupf_hands[player_index]
        remaining_card_labels = [label for label in start_card_labels if label not in given_card_labels]
        # Tauscharten aufnehmen.
        received_card_labels = [
            schupf_hands[(player_index + 1) % 4][2],
            schupf_hands[(player_index + 2) % 4][1],
            schupf_hands[(player_index + 3) % 4][0],
        ]
        hands.append(remaining_card_labels + received_card_labels)
    return hands


def validate_bswlog(bw_log: BSWLog) -> Tuple[List[BSWDataset], BSWGameErrorCode]:
    """
    Validiert die geparsten Runden einer Partie auf Plausibilität.

    Der erste zutreffende Fehler wird dokumentiert.

    :param bw_log: Die geparsten Logdatei (eine Partie).
    :return: Die validierten Rundendaten der Partie und der Fehlercode der Partie.
    """
    datasets = []
    for log_entry in bw_log:
        error_code = BSWRoundErrorCode.NO_ERROR

        # Karten aufsplitten
        grand_hands: List[List[str]] = []
        start_hands: List[List[str]] = []
        schupf_hands: List[List[str]] = []
        for player_index in range(4):
            grand_hands.append(log_entry.grand_tichu_hands[player_index].split(" "))
            start_hands.append(log_entry.start_hands[player_index].split(" "))
            schupf_hands.append(log_entry.schupf_hands[player_index].split(" "))

        # Handkarten prüfen
        for player_index in range(4):
            grand_card_labels = grand_hands[player_index]
            start_card_labels = start_hands[player_index]
            schupf_card_labels = schupf_hands[player_index]

            # Grand-Hand-Karten
            if not validate_cards(log_entry.grand_tichu_hands[player_index]):  # Kartenlabel
                error_code = BSWRoundErrorCode.INVALID_CARD_LABEL
                break
            elif len(grand_card_labels) != 8:  # Anzahl
                error_code = BSWRoundErrorCode.INVALID_CARD_COUNT
                break
            elif len(set(grand_card_labels)) != 8:  # Duplikate
                error_code = BSWRoundErrorCode.DUPLICATE_CARD
                break
            elif any(label not in start_card_labels for label in grand_card_labels):  # sind Handkarten?
                error_code = BSWRoundErrorCode.CARD_NOT_IN_HAND
                break

            # Startkarten
            elif not validate_cards(log_entry.start_hands[player_index]):  # Kartenlabel
                error_code = BSWRoundErrorCode.INVALID_CARD_LABEL
                break
            elif len(start_card_labels) != 14:  # Anzahl
                error_code = BSWRoundErrorCode.INVALID_CARD_COUNT
                break
            elif len(set(start_card_labels)) != 14:  # Duplikate
                error_code = BSWRoundErrorCode.DUPLICATE_CARD
                break

            # Tauschkarten
            elif not validate_cards(log_entry.schupf_hands[player_index]):  # Kartenlabel
                error_code = BSWRoundErrorCode.INVALID_CARD_LABEL
                break
            elif len(schupf_card_labels) != 3:  # Anzahl
                error_code = BSWRoundErrorCode.INVALID_CARD_COUNT
                break
            elif len(set(schupf_card_labels)) != 3:  # Duplikate
                error_code = BSWRoundErrorCode.DUPLICATE_CARD
                break
            elif any(label not in start_card_labels for label in schupf_card_labels):  # sind Handkarten?
                error_code = BSWRoundErrorCode.CARD_NOT_IN_HAND
                break

        # Sind alle Karten verteilt und keine mehrfach vergeben?
        if error_code == BSWRoundErrorCode.NO_ERROR:
            if len(set(start_hands[0] + start_hands[1] + start_hands[2] + start_hands[3])) != 56:
                error_code = BSWRoundErrorCode.DUPLICATE_CARD

        # Handkarten nach dem Schupfen ermitteln
        hands = _schupf(start_hands, schupf_hands)
        num_hand_cards = [14, 14, 14, 14]

        # Kombinationsmöglichkeiten berechnen
        combinations = []
        for player_index in range(4):
            card_labels = hands[player_index]
            combinations.append(build_combinations([parse_card(label) for label in card_labels]))

        # Startspieler ermitteln
        current_turn_index = -1
        for player_index in range(4):
            if "Ma" in hands[player_index]:
                current_turn_index = player_index
                break

        # Historie bereinigen:
        # Leider wird nicht geloggt, wer den Stich kassiert. Stattdessen "passt" der Spieler in dem Moment des Kassierens :-(
        # Daher baue ich eine neue Historie auf, die festhält, wer den Stich kassiert, ohne überflüssiges Passen.
        history = []

        trick_owner_index = -1
        trick_combination = CombinationType.PASS, 0, 0
        trick_points = 0
        points = [0, 0, 0, 0]
        played_card_labels = []
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
        for player_index, card_str in log_entry.history:  # card_str ist z.B. "B2 S2 R2" für Karten ausgespielt oder "" für passen
            if is_round_over:
                # Runde ist vorbei, aber es gibt noch weitere Einträge in der Historie
                if card_str == "":
                    continue  # Passen am Ende der Runde ignoriere ich
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
                    # tichu_positions anpassen, da dieser Eintrag übersprungen wird
                    for i in range(4):
                        if tichu_positions[i] >= len(history):
                            tichu_positions[i] -= 1
                    continue # nächsten Eintrag in der Historie lesen

                # Spieler hat gepasst

                # Spielzug in die Historie schreiben
                history.append((player_index, [], -1))

                # Im Anspiel gepasst?
                if trick_owner_index == -1:
                    error_code = BSWRoundErrorCode.PASS_NOT_POSSIBLE
                    break

                # Wunsch beachtet?
                if wish_value > 0:
                    action_space = build_action_space(combinations[player_index], trick_combination, wish_value)
                    if action_space[0][1][0] != CombinationType.PASS:  # Wunsch wurde nicht beachtet!
                        error_code = BSWRoundErrorCode.WISH_NOT_FOLLOWED
                        break

                # Prüfen, ob der Spieler dran war
                if player_index != current_turn_index:
                    if error_code == BSWRoundErrorCode.NO_ERROR:
                        error_code = BSWRoundErrorCode.PLAYER_NOT_ON_TURN
                    break
            else:
                # Spieler hat Karten gespielt

                # Die erste Position für jeden Spieler merken
                if first_pos[player_index] == -1:
                    first_pos[player_index] = len(history)

                # Karten prüfen
                card_labels = card_str.split(" ")
                if not validate_cards(card_str):  # Kartenlabel bekannt?
                    if error_code == BSWRoundErrorCode.NO_ERROR:
                        error_code = BSWRoundErrorCode.INVALID_CARD_LABEL
                    history.append((player_index, [], -1))
                    break

                # Spielzug in die Historie schreiben
                cards = [parse_card(label) for label in card_labels]
                history.append((player_index, cards, -1))

                if len(card_labels) != len(set(card_labels)):  # Duplikate?
                    if error_code == BSWRoundErrorCode.NO_ERROR:
                        error_code = BSWRoundErrorCode.DUPLICATE_CARD
                    break
                elif any(label not in hands[player_index] for label in card_labels):  # gehören die Karten zur Hand?
                    if error_code == BSWRoundErrorCode.NO_ERROR:
                        error_code = BSWRoundErrorCode.CARD_NOT_IN_HAND
                    break
                elif any(label in played_card_labels for label in card_labels):  # bereits gespielt?
                    if error_code == BSWRoundErrorCode.NO_ERROR:
                        error_code = BSWRoundErrorCode.CARD_ALREADY_PLAYED
                    break

                # Gespielte Karten merken
                played_card_labels += card_labels

                # Kombination prüfen
                combination = get_trick_combination(cards, trick_combination[2], shift_phoenix=True)
                action_space = build_action_space(combinations[player_index], trick_combination, wish_value)
                if not any(set(cards) == set(playable_cards) for playable_cards, _playable_combination in action_space):
                    if error_code == BSWRoundErrorCode.NO_ERROR:
                        if wish_value > 0 and is_wish_in(wish_value, action_space[0][0]):
                            error_code = BSWRoundErrorCode.WISH_NOT_FOLLOWED  # Wunsch wurde nicht beachtet
                        elif is_trick_rank_ambiguous:
                            error_code = BSWRoundErrorCode.SMALLER_OF_AMBIGUOUS_RANK  # es wurde der kleinere Rang bei einem mehrdeutigen Stich angenommen
                        else:
                            error_code = BSWRoundErrorCode.COMBINATION_NOT_PLAYABLE
                    break

                # Wenn kein Anspiel ist, kann das Zugrecht durch eine Bombe erobert werden
                if trick_owner_index != -1 and combination[0] == CombinationType.BOMB:
                    current_turn_index = player_index

                # Prüfen, ob der Spieler dran war
                if player_index != current_turn_index:
                    if error_code == BSWRoundErrorCode.NO_ERROR:
                        error_code = BSWRoundErrorCode.PLAYER_NOT_ON_TURN
                    break

                # Handkarten aktualisieren
                hands[player_index] = [label for label in hands[player_index] if label not in card_labels]
                num_hand_cards[player_index] -= len(card_labels)
                combinations[player_index] = build_combinations([parse_card(label) for label in hands[player_index]])

                # Stich aktualisieren
                trick_points += sum_card_points(cards)
                trick_combination = combination
                trick_owner_index = player_index
                # Der Rang ist nicht eindeutig, wenn beim Fullhouse der Phönix in der Mitte liegt oder bei der Straße am Ende.
                is_trick_rank_ambiguous = (
                    (combination[0] == CombinationType.FULLHOUSE and cards[2][0] == 16) or
                    (combination[0] == CombinationType.STREET and cards[0][0] == 16)
                )

                # Wunsch erfüllt?
                if wish_value > 0 and is_wish_in(wish_value, cards):
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

                # Falls ein Mahjong ausgespielt wurde, kann der Spieler sich einen Kartenwert wünschen.
                if 'Ma' in card_labels:
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
            if error_code == BSWRoundErrorCode.NO_ERROR:
                error_code = BSWRoundErrorCode.HISTORY_TOO_SHORT
        elif history_too_long:
            if error_code == BSWRoundErrorCode.NO_ERROR:
                error_code = BSWRoundErrorCode.HISTORY_TOO_LONG

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
            cards = history[-1][1]
            if not (len(cards) == 1 and cards[0] == CARD_DRA and is_double_victory):  # Ausnahme: Drache im letzten Stich führt zum Doppelsieg (dann wird der Drache nicht verschenkt, weil egal)
                if error_code == BSWRoundErrorCode.NO_ERROR:
                    error_code = BSWRoundErrorCode.DRAGON_NOT_GIVEN
        elif dragon_giver != -1 and log_entry.dragon_recipient not in [(dragon_giver + 1) % 4, (dragon_giver + 3) % 4]:
            # Drache hat Stich gewonnen, wurde aber an das eigene Team verschenkt
            if error_code == BSWRoundErrorCode.NO_ERROR:
                error_code = BSWRoundErrorCode.DRAGON_GIVEN_TO_OWN_TEAM
        elif dragon_giver == -1 and log_entry.dragon_recipient != -1:
            # Drache hat keinen Stich gewonnen, wurde aber verschenkt
            if error_code == BSWRoundErrorCode.NO_ERROR:
                error_code = BSWRoundErrorCode.DRAGON_GIVEN_WITHOUT_BEAT

        # Falls der Mahjong gespielt wurde, aber kein Wunsch geäußert wurde (was legitim ist), 0 für "ohne Wunsch" eintragen.
        wish_value = log_entry.wish_value
        if wish_value == -1:
            if "Ma" in played_card_labels:
                log_entry.wish_value = 0
            else:
                error_code = BSWRoundErrorCode.WISH_WITHOUT_MAHJONG

        # Position der Tichu-Ansage prüfen und korrigieren
        for player_index in range(4):
            if tichu_positions[player_index] - first_pos[player_index] > 1:
                if error_code == BSWRoundErrorCode.NO_ERROR:
                    error_code = BSWRoundErrorCode.ANNOUNCEMENT_NOT_POSSIBLE
                tichu_positions[player_index] = first_pos[player_index]

        # Endwertung der Runde
        if is_double_victory:
            # Doppelsieg! Das Gewinnerteam kriegt 200 Punkte. Die Gegner nichts.
            points = [0, 0, 0, 0]
            points[winner_index] = 200
        elif loser_index >= 0:
            # a) Der letzte Spieler gibt seine Handkarten an das gegnerische Team.
            leftover_points = 100 - sum_card_points([parse_card(label) for label in played_card_labels])
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
            if error_code == BSWRoundErrorCode.NO_ERROR:
                # Wer hat Tichu angesagt?
                announcements = [0, 0, 0, 0]
                for player_index in range(4):
                    if log_entry.tichu_positions[player_index] != -3:
                        announcements[player_index] = 2 if log_entry.tichu_positions[player_index] == -2 else 1
                if not _can_score_be_ok(log_entry.score, announcements):
                    error_code = BSWRoundErrorCode.SCORE_NOT_POSSIBLE
                else:
                    error_code = BSWRoundErrorCode.SCORE_MISMATCH

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
            player_names.append(name)

        # Startkarten so sortieren, dass erst die Grand-Tichu-Karten aufgelistet sind
        sorted_start_hands: List[Cards] = [[], [], [], []]
        if error_code != BSWRoundErrorCode.INVALID_CARD_LABEL:
            for player_index in range(4):
                grand_card_labels = grand_hands[player_index]
                start_card_labels = start_hands[player_index]
                remaining_card_labels = [label for label in start_card_labels if label not in grand_card_labels]
                sorted_grand_cards = sorted([parse_card(label) for label in grand_card_labels], reverse=True)
                sorted_remaining_cards = sorted([parse_card(label) for label in remaining_card_labels], reverse=True)
                sorted_start_hands[player_index] = sorted_grand_cards + sorted_remaining_cards

        # Labels der Schupfkarten umwandeln
        given_schupf_hands: List[Cards] = [[], [], [], []]
        if error_code != BSWRoundErrorCode.INVALID_CARD_LABEL:
            for player_index in range(4):
                schupf_card_labels = schupf_hands[player_index]
                given_schupf_hands[player_index] = [parse_card(label) for label in schupf_card_labels]

        datasets.append(BSWDataset(
            game_id=log_entry.game_id,
            round_index=log_entry.round_index,
            player_names=player_names,
            start_hands=sorted_start_hands,
            schupf_hands=given_schupf_hands,
            tichu_positions=tichu_positions,
            wish_value=wish_value,
            dragon_recipient=log_entry.dragon_recipient,
            winner_index=winner_index,
            loser_index=loser_index,
            is_double_victory=is_double_victory,
            score=score,
            history=history,
            year=log_entry.year,
            month=log_entry.month,
            error_code=error_code,
            error_content=log_entry.content if error_code != BSWRoundErrorCode.NO_ERROR else None,
        ))

    # Fehlercode für die Partie ermitteln
    total_score = (sum(dataset.score[0] for dataset in datasets),
                   sum(dataset.score[1] for dataset in datasets))
    if total_score[0] < 1000 and total_score[1] < 1000:
        game_error_code = BSWGameErrorCode.GAME_NOT_FINISHED
    elif total_score[0] - datasets[-1].score[0] >= 1000 or total_score[1] - datasets[-1].score[1] >= 1000:
        game_error_code = BSWGameErrorCode.GAME_OVERPLAYED
    elif any(dataset.error_code != BSWRoundErrorCode.NO_ERROR for dataset in datasets):
        game_error_code = BSWGameErrorCode.ROUND_FAILED
    elif any(dataset.player_names != datasets[0].player_names for dataset in datasets):
        game_error_code = BSWGameErrorCode.PLAYER_CHANGED
    else:
        game_error_code = BSWGameErrorCode.NO_ERROR

    return datasets, game_error_code