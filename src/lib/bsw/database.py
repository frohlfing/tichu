"""
Verwaltet eine SQLite-Datenbank mit den von der Brettspielwelt importierten Spieldaten.
"""

__all__ = "deserialize_cards", "deserialize_history", "BSWDatabase",

import os
import sqlite3
from src.lib.bsw.download import logfiles, count_logfiles
from src.lib.bsw.parse import parse_logfile
from src.lib.bsw.validate import BSWRoundErrorCode, BSWGameErrorCode, BSWDataset, validate_bswlog
from tqdm import tqdm
from typing import List, Tuple, Generator, Optional


def serialize_cards(cards: str) -> str:
    """
    Serialisiert die Karten zu einem String.
    
    :param cards: Kartenlabels mit Leerzeichen getrennt.
    :return: Kartenlabels ohne Leerzeichen.
    """
    return "".join(cards.split(" "))


def deserialize_cards(s: str) -> str:
    """
    Deserialisiert die Karten.
    
    :param s: Kartenlabels ohne Leerzeichen.
    :return: Kartenlabels mit Leerzeichen getrennt.
    """
    return " ".join([s[i:i + 2] for i in range(0, len(s), 2)])


def serialize_history(history: List[Tuple[int, str, int]]) -> str:
    """
    Serialisiert die Historie.
    
    :param history: Die Historie als Liste.
    :return: Historie als String, z.B "3:R6R3Ph|2|3:R6R3Ph;0|2;3".
    """
    turns = []
    for player_index, cards, trick_collector_index in history:
        turn = f"{player_index}"
        if cards:
            turn += f":{serialize_cards(cards)}"
        if trick_collector_index != -1:
            turn += f";{trick_collector_index}"
        turns.append(turn)
    return "|".join(turns)


def deserialize_history(s) -> List[Tuple[int, str, int]]:
    """
    Serialisiert die Historie.

    :param s: Historie als String, z.B "3:R6R3Ph|2|3:R6R3Ph;0|2;3".
    :return: Die Historie als Liste.
    """
    history = []
    for turn in s.split("|"):
        parts = turn.split(";")
        trick_collector_index = int(parts[1]) if len(parts) == 2 else -1
        parts = parts[0].split(":")
        cards = deserialize_cards(parts[1]) if len(parts) == 2 else ""
        player_index = int(parts[0])
        history.append((player_index, cards, trick_collector_index))
    return history


class BSWDatabase:
    """
    Brettspielwelt-Datenbank.
    """

    def __init__(self, database: str):
        """
        Initialisiert die Datenbank.

        :param database: Die SQLite-Datenbankdatei.
        """
        self._database = database
        """Die SQLite-Datenbankdatei."""

        self._conn: Optional[sqlite3.Connection] = None
        """Die Datenbankverbindung."""

    def __del__(self):
        """
        Bereinigt Ressourcen.
        """
        self.close()

    def open(self):
        """
        Stellt eine Verbindung mit der SQLite-Datenbank her.

        Falls die DB nicht existiert, wird sie erstellt und Tabellen eingerichtet.
        """
        if self._conn:
            return

        # Datenbankverbindung herstellen
        db_exists = os.path.exists(self._database)
        if not db_exists:
            os.makedirs(os.path.dirname(self._database))
        self._conn = sqlite3.connect(self._database)

        # Tabellen einrichten
        if not db_exists:
            self._create_tables()

    def close(self):
        """
        Schließt die Datenbankverbindung, sofern sie offen ist.
        """
        if self._conn:
            self._conn.close()
            self._conn = None

    def cursor(self) -> sqlite3.Cursor:
        """
        Gibt einen Datenbank-Cursor zurück, mit dem man SQL-Statements ausführen kann.

        :return: Datenbank-Cursor.
        """
        return self._conn.cursor()

    def commit(self):
        """
        Übernimmt alle ausstehenden Transaktionen.
        """
        self._conn.commit()

    def rollback(self):
        """
        Führt ein Rollback zum Anfang einer ausstehenden Transaktion durch.
        """
        self._conn.rollback()

    def import_logfiles(self, path: str, y1: int, m1: int, y2: int, m2: int):
        """
        Importiert die vom Spiele-Portal "Brettspielwelt" heruntergeladenen Logdateien.

        :param path: Das Verzeichnis, in dem die Zip-Archive liegen.
        :param y1: ab Jahr
        :param m1: ab Monat
        :param y2: bis Jahr (einschließlich)
        :param m2: bis Monat (einschließlich)
        """
        # Verbindung zur Datenbank herstellen und Tabellen einrichten
        self.open()
        cursor = self.cursor()

        # Aktualisierung starten
        log_file_counter = 0
        try:
            progress_bar = tqdm(
                logfiles(path, y1, m1, y2, m2),
                total=count_logfiles(path, y1, m1, y2, m2),
                desc="Verarbeite Log-Dateien",
                unit=" Datei")
            logfiles_total = 0
            games_fails = 0
            games_empty = 0
            for game_id, year, month, content in progress_bar:
                # Logdateien zählen
                logfiles_total += 1

                # Parsen
                bsw_log = parse_logfile(game_id, year, month, content)
                if len(bsw_log) == 0:
                    games_empty += 1

                # Validieren
                datasets, game_error_code = validate_bswlog(bsw_log)

                # Fehlerhafte Partien zählen
                if game_error_code != BSWGameErrorCode.NO_ERROR:
                    games_fails += 1

                # Endergebnis der Partie berechnen
                total_score = (sum(dataset.score[0] for dataset in datasets),
                               sum(dataset.score[1] for dataset in datasets))

                # Datenbank aktualisieren
                for dataset in datasets:
                    # Tabelle für die Spieler aktualisieren und Spieler-IDs ermitteln
                    player_ids = []
                    for player_index in range(4):
                        player_ids.append(self._save_player(cursor, dataset.player_names[player_index]))

                    # Partie speichern
                    if dataset.round_index == 0:
                        self._save_game(cursor, dataset.game_id, player_ids, total_score, dataset.year, dataset.month, game_error_code)

                    # Runde speichern
                    self._save_round(cursor, dataset, player_ids)

                # Transaktion alle 1000 Dateien committen
                log_file_counter += 1
                if log_file_counter % 1000 == 0:
                    progress_bar.set_postfix_str(f"Commit DB...")
                    self.commit()

                # Fortschritt aktualisieren
                progress_bar.set_postfix({
                    "Logdateien": logfiles_total,
                    "Leere": games_empty,
                    "Fehler": games_fails,
                    "Datei": f"{year:04d}{month:02d}/{game_id}.tch"
                })

            # Indizes erst am Ende einrichten, damit der Import schneller durchläuft.
            self._create_indexes()

        # Alle verbleibenden Änderungen speichern und Datenbank schließen.
        finally:
            self.commit()
            self.close()

    def datasets(self) -> Generator[BSWDataset]:
        """
        Liefert die in der DB gespeicherten Partien aus.

        :return: Ein Generator, der die Datensätze der Datenbank liefert.
        """
        self.open()
        cursor = self.cursor()
        try:
            cursor.execute("""
                SELECT r.game_id, r.round_index, 
                   g.player_id_0, g.player_id_1, g.player_id_2, g.player_id_3, 
                   p0.name AS player_name_0, p1.name AS player_name_1, p2.name AS player_name_2, p3.name AS player_name_3, 
                   hand_cards_0, hand_cards_1, hand_cards_2, hand_cards_3,
                   schupf_cards_0, schupf_cards_1, schupf_cards_2, schupf_cards_3, 
                   tichu_pos_0, tichu_pos_1, tichu_pos_2, tichu_pos_3, 
                   r.wish_value, r.dragon_recipient, r.winner_index, r.loser_index, r.is_double_victory,
                   r.score_20, r.score_31, g.score_20 AS total_score_20, g.score_31 AS total_score_31, 
                   r.history,
                   g.log_year, g.log_month
                FROM games AS g
                INNER JOIN rounds AS r ON g.id = r.game_id
                INNER JOIN players AS p0 ON g.player_id_0 = p0.id 
                INNER JOIN players AS p1 ON g.player_id_1 = p1.id 
                INNER JOIN players AS p2 ON g.player_id_2 = p2.id 
                INNER JOIN players AS p3 ON g.player_id_3 = p3.id 
                WHERE g.error_code = 0 
            """)
            columns = [desc[0] for desc in cursor.description]
            for row in cursor:
                ds = dict(zip(columns, row))
                yield BSWDataset(
                    game_id=ds["game_id"],
                    round_index=ds["round_index"],
                    player_names=[ds["player_name_0"], ds["player_name_1"], ds["player_name_2"], ds["player_name_3"]],
                    start_hands=[deserialize_cards(ds[f"hand_cards_{player_index}"]) for player_index in range(4)],
                    given_schupf_cards=[deserialize_cards(ds[f"schupf_cards_{player_index}"]) for player_index in range(4)],
                    tichu_positions=[ds["tichu_pos_0"], ds["tichu_pos_1"], ds["tichu_pos_2"], ds["tichu_pos_3"]],
                    wish_value=ds["wish_value"],
                    dragon_recipient=ds["dragon_recipient"],
                    winner_index=ds["winner_index"],
                    loser_index=ds["loser_index"],
                    is_double_victory=ds["is_double_victory"],
                    score=(ds["score_20"],ds["score_31"]),
                    history=deserialize_history(ds["history"]),
                    year=ds["log_year"],
                    month=ds["log_month"],
                )
        finally:
            self.close()

    def count(self):
        """
        Zählt die in der DB gespeicherten Partien.
        """
        self.open()
        cursor = self.cursor()
        try:
            cursor.execute("SELECT count(*) FROM games ORDER BY id")
            result = cursor.fetchone()
            total = result[0] if result else 0
        finally:
            self.close()
        return total

    def _create_tables(self):
        """
        Erstellt die Tabellen in der SQLite-Datenbank, falls sie nicht existieren.
        """
        self.open()
        cursor = self._conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id              INTEGER PRIMARY KEY,  -- ID der Partie
                player_id_0     INTEGER NOT NULL,     -- ID des Spielers zu Beginn der Partie an Position 0
                player_id_1     INTEGER NOT NULL,     -- ID des Spielers zu Beginn der Partie an Position 1
                player_id_2     INTEGER NOT NULL,     -- ID des Spielers zu Beginn der Partie an Position 2
                player_id_3     INTEGER NOT NULL,     -- ID des Spielers zu Beginn der Partie an Position 3
                score_20        INTEGER NOT NULL,     -- Endergebnis Team 20  # todo kann raus, wenn der Replay-Simulator auf das gleiche Ergebnis kommt
                score_31        INTEGER NOT NULL,     -- Endergebnis Team 31  # todo 
                log_year        INTEGER NOT NULL,     -- Jahr der Logdatei
                log_month       INTEGER NOT NULL,     -- Monat der Logdatei
                error_code      INTEGER NOT NULL      -- Fehlercode der ersten fehlerhaften Runde (0 == kein Fehler)
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rounds (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,  -- ID der Runde
                game_id           INTEGER NOT NULL,   -- ID der Partie
                round_index       INTEGER NOT NULL,   -- Index der Runde innerhalb der Partie (0, 1, 2, ...)
                player_id_0       INTEGER NOT NULL,   -- ID des Spielers an Position 0  # todo kann raus, falls ich nur Spiele betrachte, wo kein Spielerwechsel statt fand
                player_id_1       INTEGER NOT NULL,   -- ID des Spielers an Position 1  # todo 
                player_id_2       INTEGER NOT NULL,   -- ID des Spielers an Position 2  # todo 
                player_id_3       INTEGER NOT NULL,   -- ID des Spielers an Position 3  # todo 
                hand_cards_0      TEXT    NOT NULL,   -- Handkarten von Spieler 0 vor dem Schupfen (ohne Leerzeichen) 
                hand_cards_1      TEXT    NOT NULL,   -- Handkarten von Spieler 1 vor dem Schupfen (ohne Leerzeichen)
                hand_cards_2      TEXT    NOT NULL,   -- Handkarten von Spieler 2 vor dem Schupfen (ohne Leerzeichen)
                hand_cards_3      TEXT    NOT NULL,   -- Handkarten von Spieler 3 vor dem Schupfen (ohne Leerzeichen)
                schupf_cards_0    TEXT    NOT NULL,   -- Abgegebene Tauschkarten von Spieler 0 (ohne Leerzeichen)
                schupf_cards_1    TEXT    NOT NULL,   -- Abgegebene Tauschkarten von Spieler 1 (ohne Leerzeichen)
                schupf_cards_2    TEXT    NOT NULL,   -- Abgegebene Tauschkarten von Spieler 2 (ohne Leerzeichen)
                schupf_cards_3    TEXT    NOT NULL,   -- Abgegebene Tauschkarten von Spieler 3 (ohne Leerzeichen)
                tichu_pos_0       INTEGER NOT NULL,   -- Tichu-Ansage-Position Spieler 0 (-3…-1, ≥0 = Zug-Index)
                tichu_pos_1       INTEGER NOT NULL,   -- Tichu-Ansage-Position Spieler 1
                tichu_pos_2       INTEGER NOT NULL,   -- Tichu-Ansage-Position Spieler 2
                tichu_pos_3       INTEGER NOT NULL,   -- Tichu-Ansage-Position Spieler 3
                wish_value        INTEGER NOT NULL,   -- Gewünschter Kartenwert (2–14, 0 = ohne Wunsch, -1 = kein Mahjong)
                dragon_recipient  INTEGER NOT NULL,   -- Index des Spielers, der den Drachen erhielt (-1 = niemand)
                winner_index      INTEGER NOT NULL,   -- Index des Spielers, der als Erster ausspielt (-1 = niemand)  # todo kann raus, wenn der Replay-Simulator funktioniert
                loser_index       INTEGER NOT NULL,   -- Index des Spielers, der als Letzter übrig bleibt (-1 = niemand)  # todo
                is_double_victory INTEGER NOT NULL,   -- 1 == Doppelsieg, 0 == normales Ende # todo
                score_20          INTEGER NOT NULL,   -- Rundenergebnis Team 20  # todo kann raus, wenn der Replay-Simulator auf das gleiche Ergebnis kommt
                score_31          INTEGER NOT NULL,   -- Rundenergebnis Team 31  # todo
                history           TEXT    NOT NULL,   -- Spielzüge [(Spieler, Karten, Stichnehmer), …], z.B 3:R6R3Ph|2|3:R6R3Ph;0|2;3
                error_code        INTEGER NOT NULL,   -- Fehlercode (Enum-Wert)
                error_content     TEXT                -- Betroffener Log-Abschnitt (NULL, wenn kein Fehler)
            );
        """)

        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_rounds_game_id_round_index ON rounds (game_id, round_index);")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,  -- ID des Spielers
                name TEXT    NOT NULL  -- Name des Spielers
            );
        """)

        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_players_name ON players (name);")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS errors (
                code        INTEGER PRIMARY KEY,
                name        TEXT NOT NULL,
                description TEXT NOT NULL
            );
        """)
        self._insert_error_codes(cursor)

        self._conn.commit()

    def _create_indexes(self):
        """
        Erstellt Indizes für die Tabellen in der SQLite-Datenbank zur Beschleunigung typischer Abfragen.
        """
        self.open()
        cursor = self.cursor()

        # games
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_player_id_0        ON games (player_id_0);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_player_id_1        ON games (player_id_1);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_player_id_2        ON games (player_id_2);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_player_id_3        ON games (player_id_3);")
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

        self.commit()

    @staticmethod
    def _insert_error_codes(cursor: sqlite3.Cursor):
        """
        Füllt die Mapping-Tabelle mit Fehlercodes.

        :param cursor: Datenbank-Cursor
        """
        descriptions = {
            0: "Kein Fehler",
            10: "Unbekanntes Kartenlabel",
            11: "Anzahl der Karten ist fehlerhaft",
            12: "Karten mehrmals vorhanden",
            13: "Karte gehört nicht zu den Handkarten",
            14: "Karte bereits gespielt",
            20: "Passen nicht möglich",
            21: "Wunsch nicht beachtet",
            22: "Kombination nicht spielbar",
            23: "Es wurde der kleinere Rang bei einem mehrdeutigen Rang gewählt",
            24: "Der Spieler ist nicht am Zug",
            25: "Es fehlen Einträge in der Historie",
            26: "Karten ausgespielt, obwohl die Runde vorbei ist (wurde korrigiert)",
            30: "Drache hat den Stich nicht gewonnen, wurde aber nicht verschenkt",
            31: "Drache an eigenes Team verschenkt",
            32: "Drache verschenkt, aber niemand hat durch den Drachen ein Stich gewonnen",
            40: "Wunsch geäußert, aber kein Mahjong gespielt",
            50: "Tichu-Ansage an der geloggten Position nicht möglich (wurde korrigiert)",
            60: "Rechenfehler! Geloggtes Rundenergebnis ist nicht möglich (wurde korrigiert)",
            61: "Geloggtes Rundenergebnis stimmt nicht mit dem berechneten Ergebnis überein (wurde korrigiert)",
            70: "Partie nicht zu Ende gespielt",
            71: "Ein oder mehrere Runden gespielt, obwohl die Partie bereits entschieden war",
            80: "Mindestens eine Runde ist fehlerhaft",
            90: "Mindestens ein Spieler hat während der Partie gewechselt",
        }

        for code in BSWRoundErrorCode:
            cursor.execute("SELECT code FROM errors WHERE code = ?", (code.value,))
            result = cursor.fetchone()
            if result:
                cursor.execute("UPDATE errors SET name=?, description=? WHERE code = ?", (code.name, descriptions[code.value], code.value))
            else:
                cursor.execute("INSERT INTO errors (code, name, description) VALUES (?, ?, ?)", (code.value, code.name, descriptions[code.value]))

    @staticmethod
    def _save_player(cursor: sqlite3.Cursor, player_name: str) -> int:
        """
        Speichert den Spieler.

        Die Änderung muss mit commit() übernommen werden.

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

    @staticmethod
    def _save_game(cursor: sqlite3.Cursor, game_id: int, player_ids: List[int], score: Tuple[int, int], year: int, month: int, error_code: BSWGameErrorCode) -> int:
        """
        Speichert eine Partie in der Datenbank.

        :param cursor: Datenbank-Cursor.
        :param game_id: ID der Partie.
        :param player_ids: Die IDs der 4 Spieler, die zu Beginn der Partie mitgespielt haben.
        :param score: Endergebnis der Partie (Team20, Team31).
        :param year: Jahr der Logdatei.
        :param month: Monat der Logdatei.
        :param error_code: Fehlercode der Partie (0 == kein Fehler).
        """
        cursor.execute("SELECT id FROM games WHERE id = ?", (game_id,))
        result = cursor.fetchone()
        if result:
            cursor.execute("""
                UPDATE games SET
                    player_id_0=?, player_id_1=?, player_id_2=?, player_id_3=?,
                    score_20=?, score_31=?,
                    log_year=?, log_month=?,
                    error_code=?
                WHERE id = ?
                """,(
                   player_ids[0], player_ids[1], player_ids[2], player_ids[3],
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
                    score_20, score_31, 
                    log_year, log_month, 
                    error_code
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,(
                    game_id,
                    player_ids[0], player_ids[1], player_ids[2], player_ids[3],
                    score[0], score[1],
                    year, month,
                    error_code.value
                )
            )
        return game_id

    @staticmethod
    def _save_round(cursor: sqlite3.Cursor, ds: BSWDataset, player_ids: List[int]) -> int:
        """
        Speichert die Runde in der Datenbank.

        :param cursor: Datenbank-Cursor.
        :param ds: Rundendaten.
        :param player_ids: Die IDs der 4 Spieler.
        :return: Die Runden-ID.
        """
        # Karten und Historie serialisieren

        hands_str = [serialize_cards(ds.start_hands[player_index]) for player_index in range(4)]
        schupf_str = [serialize_cards(ds.given_schupf_cards[player_index]) for player_index in range(4)]
        history_str = serialize_history(ds.history)

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
