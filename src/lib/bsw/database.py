"""
Brettspielwelt-Datenbank
"""

__all__ = "update_database", "datasets", "count_datasets",

import os
import sqlite3
from src.lib.bsw.download import logfiles, count_logfiles
from src.lib.bsw.parse import parse_logfile
from src.lib.bsw.validate import BSWErrorCode, BSWRoundData, validate_bswlog
from tqdm import tqdm
from typing import List, Tuple, Generator


def _create_tables(conn: sqlite3.Connection):
    """
    Erstellt die Tabellen in der SQLite-Datenbank, falls sie nicht existieren.
    """
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS games (
        id                INTEGER PRIMARY KEY,  -- ID der Partie
        player_id_0       INTEGER NOT NULL,     -- ID des Spielers an Position 0
        player_id_1       INTEGER NOT NULL,     -- ID des Spielers an Position 1
        player_id_2       INTEGER NOT NULL,     -- ID des Spielers an Position 2
        player_id_3       INTEGER NOT NULL,     -- ID des Spielers an Position 3
        player_changed    INTEGER NOT NULL,     -- 1 == Spielerwechsel, 0 == kein Spielerwechsel
        score_20          INTEGER NOT NULL,     -- Endergebnis Team 20  # todo kann raus, wenn der Replay-Simulator auf das gleiche Ergebnis kommt
        score_31          INTEGER NOT NULL,     -- Endergebnis Team 31  # todo 
        log_year          INTEGER NOT NULL,     -- Jahr der Logdatei
        log_month         INTEGER NOT NULL,     -- Monat der Logdatei
        error_code        INTEGER NOT NULL      -- Fehlercode der ersten fehlerhaften Runde (0 == kein Fehler)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rounds (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,  -- ID der Runde
        game_id           INTEGER NOT NULL,     -- ID der Partie
        round_index       INTEGER NOT NULL,     -- Index der Runde innerhalb der Partie (0, 1, 2, ...)
        player_id_0       INTEGER NOT NULL,     -- ID des Spielers an Position 0  # todo kann raus, falls ich nur Spiele betrachte, wo kein Spielerwechsel statt fand
        player_id_1       INTEGER NOT NULL,     -- ID des Spielers an Position 1  # todo 
        player_id_2       INTEGER NOT NULL,     -- ID des Spielers an Position 2  # todo 
        player_id_3       INTEGER NOT NULL,     -- ID des Spielers an Position 3  # todo 
        hand_cards_0      TEXT    NOT NULL,     -- Handkarten von Spieler 0 vor dem Schupfen (ohne Leerzeichen) 
        hand_cards_1      TEXT    NOT NULL,     -- Handkarten von Spieler 1 vor dem Schupfen (ohne Leerzeichen)
        hand_cards_2      TEXT    NOT NULL,     -- Handkarten von Spieler 2 vor dem Schupfen (ohne Leerzeichen)
        hand_cards_3      TEXT    NOT NULL,     -- Handkarten von Spieler 3 vor dem Schupfen (ohne Leerzeichen)
        schupf_cards_0    TEXT    NOT NULL,     -- Abgegebene Tauschkarten von Spieler 0 (ohne Leerzeichen)
        schupf_cards_1    TEXT    NOT NULL,     -- Abgegebene Tauschkarten von Spieler 1 (ohne Leerzeichen)
        schupf_cards_2    TEXT    NOT NULL,     -- Abgegebene Tauschkarten von Spieler 2 (ohne Leerzeichen)
        schupf_cards_3    TEXT    NOT NULL,     -- Abgegebene Tauschkarten von Spieler 3 (ohne Leerzeichen)
        tichu_pos_0       INTEGER NOT NULL,     -- Tichu-Ansage-Position Spieler 0 (-3…-1, ≥0 = Zug-Index)
        tichu_pos_1       INTEGER NOT NULL,     -- Tichu-Ansage-Position Spieler 1
        tichu_pos_2       INTEGER NOT NULL,     -- Tichu-Ansage-Position Spieler 2
        tichu_pos_3       INTEGER NOT NULL,     -- Tichu-Ansage-Position Spieler 3
        wish_value        INTEGER NOT NULL,     -- Gewünschter Kartenwert (2–14, 0 = ohne Wunsch, -1 = kein Mahjong)
        dragon_recipient  INTEGER NOT NULL,     -- Index des Spielers, der den Drachen erhielt (-1 = niemand)
        winner_index      INTEGER NOT NULL,     -- Index des Spielers, der als Erster ausspielt (-1 = niemand)  # todo kann raus, wenn der Replay-Simulator funktioniert
        loser_index       INTEGER NOT NULL,     -- Index des Spielers, der als Letzter übrig bleibt (-1 = niemand)  # todo
        is_double_victory INTEGER NOT NULL,     -- 1 == Doppelsieg, 0 == normales Ende # todo
        score_20          INTEGER NOT NULL,     -- Rundenergebnis Team 20  # todo kann raus, wenn der Replay-Simulator auf das gleiche Ergebnis kommt
        score_31          INTEGER NOT NULL,     -- Rundenergebnis Team 31  # todo
        history           TEXT    NOT NULL,     -- Spielzüge [(Spieler, Karten, Stichnehmer), …], z.B 3:R6R3Ph|2|3:R6R3Ph;0|2;3
        error_code        INTEGER NOT NULL,     -- Fehlercode (Enum-Wert)
        error_content     TEXT                  -- Betroffener Log-Abschnitt (NULL, wenn kein Fehler)
    );
    """)

    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_rounds_game_id_round_index ON rounds (game_id, round_index);")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS players (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,  -- ID des Spielers
        name              TEXT    NOT NULL      -- Name des Spielers
    );
    """)

    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_players_name ON players (name);")

    conn.commit()


def _create_indexes(conn: sqlite3.Connection):
    """
    Erstellt Indizes für die Tabellen in der SQLite-Datenbank zur Beschleunigung typischer Abfragen.
    """
    cursor = conn.cursor()

    # games
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_player_id_0        ON games (player_id_0);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_player_id_1        ON games (player_id_1);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_player_id_2        ON games (player_id_2);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_player_id_3        ON games (player_id_3);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_player_changed     ON games (player_changed);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_log_year_month     ON games (log_year, log_month);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_error_code         ON games (error_code);")

    # rounds
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_player_id_0       ON rounds (player_id_0);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_player_id_1       ON rounds (player_id_1);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_player_id_2       ON rounds (player_id_2);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_player_id_3       ON rounds (player_id_3);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_tichu_pos_0       ON rounds (tichu_pos_0);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_tichu_pos_1       ON rounds (tichu_pos_1);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_tichu_pos_2       ON rounds (tichu_pos_2);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_tichu_pos_3       ON rounds (tichu_pos_3);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_wish_value        ON rounds (wish_value);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_dragon_recipient  ON rounds (dragon_recipient);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_double_victory    ON rounds (is_double_victory);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_score_20          ON rounds (score_20);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_score_31          ON rounds (score_31);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_error_code        ON rounds (error_code);")

    conn.commit()


def _save_player(cursor: sqlite3.Cursor, player_name: str) -> int:
    """
    Speichert den Spieler in der Datenbank.

    :param cursor: Datenbank-Cursor
    :param player_name: Name des Spielers
    :return: ID des Spielers in der Datenbank.
    """
    cursor.execute("SELECT id FROM players WHERE name = ?", (player_name,))
    result = cursor.fetchone()
    if result:
        player_id = result[0]
    else:
        cursor.execute("INSERT INTO players (name) VALUES (?)", (player_name,))
        player_id = cursor.lastrowid
    return player_id


def _save_game(cursor: sqlite3.Cursor, game_id: int, player_ids: List[int], player_changed: bool, score: Tuple[int, int], year: int, month: int, error_code: BSWErrorCode) -> int:
    """
    Speichert eine Partie in der Datenbank.

    :param cursor: Datenbank-Cursor.
    :param game_id: ID der Partie.
    :param player_ids: Die IDs der 4 Spieler, die zu Beginn der Partie mitgespielt haben.
    :param player_changed: True, wenn Spielerwechsel während der Partie stattgefunden haben, sonst False.
    :param score: Endergebnis der Partie (Team20, Team31).
    :param year: Jahr der Logdatei.
    :param month: Monat der Logdatei.
    :param error_code: Fehlercode der ersten fehlerhaften Runde (0 == kein Fehler).
    """
    cursor.execute("SELECT id FROM games WHERE id = ?", (game_id,))
    result = cursor.fetchone()
    if result:
        cursor.execute("""
            UPDATE games SET
                player_id_0=?, player_id_1=?, player_id_2=?, player_id_3=?,
                player_changed=?,
                score_20=?, score_31=?,
                log_year=?, log_month=?,
                error_code=?
            WHERE id = ?
            """,(
               player_ids[0], player_ids[1], player_ids[2], player_ids[3],
               int(player_changed),
               score[0], score[1],
               year, month,
               error_code.value,
               game_id
            )
        )
    else:
        cursor.execute("""
            INSERT INTO games (
                id, 
                player_id_0, player_id_1, player_id_2, player_id_3,
                player_changed,
                score_20, score_31, 
                log_year, log_month, 
                error_code
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,(
                game_id,
                player_ids[0], player_ids[1], player_ids[2], player_ids[3],
                int(player_changed),
                score[0], score[1],
                year, month,
                error_code.value
            )
        )
    return game_id


def _save_round(cursor: sqlite3.Cursor, ds: BSWRoundData, player_ids: List[int]) -> int:
    """
    Speichert die Runde in der Datenbank.

    :param cursor: Datenbank-Cursor.
    :param ds: Rundendaten.
    :param player_ids: Die IDs der 4 Spieler.
    :return: Die Runden-ID.
    """
    # Karten serialisieren
    hands_str = ["".join(ds.start_hands[player_index].split(" ")) for player_index in range(4)]
    schupf_str = ["".join(ds.given_schupf_cards[player_index].split(" ")) for player_index in range(4)]

    # Spielzüge serialisieren (z.B 3:R6R3Ph|2|3:R6R3Ph;0|2;3)
    history = []
    for player_index, cards, trick_collector_index in ds.history:
        turn = f"{player_index}"
        if cards:
            turn += f":{"".join(cards.split(" "))}"
        if trick_collector_index != -1:
            turn += f";{trick_collector_index}"
        history.append(turn)
    history_str = "|".join(history)

    # Datensatz speichern
    cursor.execute("SELECT id FROM rounds WHERE game_id = ? AND round_index = ?", (ds.game_id, ds.round_index))
    result = cursor.fetchone()
    if result:
        round_id = result[0]
        cursor.execute("""
            UPDATE rounds SET
                player_id_0=?, player_id_1=?, player_id_2=?, player_id_3=?,
                hand_cards_0=?, hand_cards_1=?, hand_cards_2=?, hand_cards_3=?,
                schupf_cards_0=?, schupf_cards_1=?, schupf_cards_2=?, schupf_cards_3=?,
                tichu_pos_0=?, tichu_pos_1=?, tichu_pos_2=?, tichu_pos_3=?,
                wish_value=?, 
                dragon_recipient=?, 
                winner_index=?, 
                loser_index=?, 
                is_double_victory=?, 
                score_20=?, score_31=?, 
                history=?,
                error_code=?, error_content=?
            WHERE id = ?
            """, (
                player_ids[0], player_ids[1], player_ids[2], player_ids[3],
                hands_str[0], hands_str[1], hands_str[2], hands_str[3],
                schupf_str[0], schupf_str[1], schupf_str[2], schupf_str[3],
                ds.tichu_positions[0], ds.tichu_positions[1], ds.tichu_positions[2], ds.tichu_positions[3],
                ds.wish_value,
                ds.dragon_recipient,
                ds.winner_index,
                ds.loser_index,
                int(ds.is_double_victory),
                ds.score[0], ds.score[1],
                history_str,
                ds.error_code.value, ds.error_content,
                round_id
            )
        )
    else:
        cursor.execute("""
            INSERT INTO rounds (
                game_id, 
                round_index, 
                player_id_0, player_id_1, player_id_2, player_id_3,
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
                error_code, error_content
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ds.game_id,
                ds.round_index,
                player_ids[0], player_ids[1], player_ids[2], player_ids[3],
                hands_str[0], hands_str[1], hands_str[2], hands_str[3],
                schupf_str[0], schupf_str[1], schupf_str[2], schupf_str[3],
                ds.tichu_positions[0], ds.tichu_positions[1], ds.tichu_positions[2], ds.tichu_positions[3],
                ds.wish_value,
                ds.dragon_recipient,
                ds.winner_index,
                ds.loser_index,
                int(ds.is_double_victory),
                ds.score[0], ds.score[1],
                history_str,
                ds.error_code.value, ds.error_content
            )
        )
        round_id = cursor.lastrowid
    return round_id


def update_database(database: str, path: str, y1: int, m1: int, y2: int, m2: int):
    """
    Aktualisiert die SQLite-Datenbank mit den vom Spiele-Portal "Brettspielwelt" heruntergeladenen Logdateien.

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

    # Aktualisierung starten
    log_file_counter = 0
    try:
        progress_bar = tqdm(
            logfiles(path, y1, m1, y2, m2),
            total=count_logfiles(path, y1, m1, y2, m2),
            desc="Verarbeite Log-Dateien",
            unit=" Datei")
        games_total = 0
        games_fails = 0
        rounds_total = 0
        rounds_fails = 0
        error_summary = {}
        for game_id, year, month, content in progress_bar:
            # Logdatei parsen und validieren
            games_total += 1
            bw_log = parse_logfile(game_id, year, month, content)
            game_data = validate_bswlog(bw_log)

            # Runden-übergreifende Angaben für die Partie ermitteln
            player_changed = any(round_data.player_names != game_data[0].player_names for round_data in game_data)
            total_score = (sum(round_data.score[0] for round_data in game_data), sum(round_data.score[1] for round_data in game_data))
            game_error_code = BSWErrorCode.NO_ERROR
            if total_score[0] < 1000 and total_score[1] < 1000:
                game_error_code = BSWErrorCode.GAME_NOT_FINISHED
            else:
                last_score = game_data[-1].score
                if total_score[0] - last_score[0] >= 1000 or total_score[1] - last_score[1] >= 1000:
                    game_error_code = BSWErrorCode.GAME_OVERPLAYED
                else:
                    # den Fehlercode der ersten fehlerhaften Runde ermitteln
                    for round_data in game_data:
                        if round_data.error_code != BSWErrorCode.NO_ERROR:
                            game_error_code = round_data.error_code
                            break
            if game_error_code != BSWErrorCode.NO_ERROR:
                games_fails += 1

            # Datenbank aktualisieren
            for round_data in game_data:
                # Die fehlerhaften Runden zählen
                rounds_total += 1
                if round_data.error_code != BSWErrorCode.NO_ERROR:
                    if round_data.error_code not in error_summary:
                        error_summary[round_data.error_code] = 0
                    error_summary[round_data.error_code] += 1
                    rounds_fails += 1

                # Tabelle für die Spieler aktualisieren und Spieler-IDs ermitteln
                player_ids = []
                for player_index in range(4):
                    player_ids.append(_save_player(cursor, round_data.player_names[player_index]))

                # Partie speichern
                if round_data.round_index == 0:
                    _save_game(cursor, round_data.game_id, player_ids, player_changed, total_score, round_data.year, round_data.month, game_error_code)

                # Runde speichern
                _save_round(cursor, round_data, player_ids)

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


def datasets(database: str) -> Generator[dict]:
    """
    Liefert die in der DB gespeicherten Partien aus.

    :param database: Die SQLite-Datenbankdatei.
    :return: Ein Generator, der die Datensätze der Datenbank liefert.
    """
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM games ORDER BY id")
        columns = [desc[0] for desc in cursor.description]
        for row in cursor:
            ds = dict(zip(columns, row))
            yield ds
    finally:
        conn.close()


def count_datasets(database: str):
    """
    Zählt die in der DB gespeicherten Partien.

    :param database: Die SQLite-Datenbankdatei.
    """
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT count(*) FROM games ORDER BY id")
        result = cursor.fetchone()
        total = result[0] if result else 0
    finally:
        conn.close()
    return total