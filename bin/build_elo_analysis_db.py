#!/usr/bin/env python

import sqlite3
import os
from src import config
from src.lib.bsw.database import update_elo, get_k_factor
from tqdm import tqdm

# --- Konfiguration ---
TICHU_DATABASE = os.path.join(config.DATA_PATH, "bsw", "bsw.sqlite")
TIMESERIES_DATABASE = os.path.join(config.DATA_PATH, "bsw", "timeseries.sqlite")


def build_timeseries_data():
    """
    Liest die Tichu-Datenbank, berechnet die chronologische Entwicklung der Spieler-Stats
    und speichert sie in einer neuen Zeitreihen-DB.
    """
    if not os.path.exists(TICHU_DATABASE):
        print(f"Fehler: Datenbank nicht gefunden unter {TICHU_DATABASE}")
        return

    # Schreib-Verbindung zur neuen Analyse-DB herstellen
    write_conn = sqlite3.connect(TIMESERIES_DATABASE)
    write_conn.row_factory = sqlite3.Row
    write_cursor = write_conn.cursor()

    # Tabellen und Indezies erstellen
    write_cursor.execute("""
        CREATE TABLE IF NOT EXISTS timeseries (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id   INTEGER NOT NULL,
            game_id     INTEGER NOT NULL,
            num_games   INTEGER NOT NULL,  -- Anzahl Partien des Spielers (ohne diese Partie)
            win_rate    REAL NOT NULL,     -- Anzahl Partien gewonnen / Anzahl Partien gesamt
            elo_value   REAL NOT NULL,     -- Elo-Zahl
            elo_v2      REAL,              -- Elo-Zahl Version 2
            elo_v3      REAL,              -- Elo-Zahl Version 3
            elo_v4      REAL,              -- Elo-Zahl Version 4
            final       INTEGER NOT NULL   -- 1 == dies ist der letzte Eintrag des Spielers, 0 == nicht final
        )
    """)
    write_cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_timeseries_player_id_game_id ON timeseries (player_id, game_id);")
    write_cursor.execute("CREATE INDEX IF NOT EXISTS idx_timeseries_game_id ON timeseries (game_id);")
    write_cursor.execute("CREATE INDEX IF NOT EXISTS idx_timeseries_final ON timeseries (final);")
    write_conn.commit()

    # Read-Only-Verbindung zur Tichu-Datenbank herstellen
    read_conn = sqlite3.connect(f'file:{TICHU_DATABASE}?mode=ro', uri=True)
    read_conn.row_factory = sqlite3.Row
    read_cursor = read_conn.cursor()
    loop_cursor = read_conn.cursor()
    try:
        # Spielerstatistik
        player_stats = {}

        # Anzahl Partien ermitteln
        read_cursor.execute("SELECT count(*) FROM games WHERE error_code = 0 AND player_changed = 0")
        row = read_cursor.fetchone()
        total = row[0] if row else 0

        # Partien durchlaufen...
        loop_counter = 0
        loop_cursor.execute("SELECT id, winner_team FROM games WHERE error_code = 0 AND player_changed = 0 ORDER BY id")
        for loop_row in tqdm(loop_cursor, total=total, unit=" Spieler", desc="Aggregiere Daten für Spieler"):
            game_id = loop_row["id"]
            winner_team = loop_row["winner_team"]

            # Spieler der Partie durchlaufen und ihre Eol-Zahlen ermitteln
            player_ids = []
            elo_values = []
            k_factors = []
            wins = []
            read_cursor.execute("""
                SELECT pr.player_index, pr.player_id
                FROM players_rounds AS pr
                INNER JOIN rounds AS r ON pr.round_id = r.id
                WHERE r.game_id = ? AND r.round_index = 0
                ORDER BY pr.player_index
                """, (game_id,))
            for row in read_cursor.fetchall():
                player_id = row["player_id"]
                player_ids.append(player_id)
                if player_id not in player_stats:
                    player_stats[player_id] = {
                        "num_games": 0,
                        "num_wins": 0,
                        "elo_value": 1500.0,
                        "max_elo_value": 1500.0,
                    }
                stat = player_stats[player_id]
                elo_values.append(stat["elo_value"])
                k_factors.append(get_k_factor(stat["num_games"], stat["max_elo_value"]))
                if row["player_index"] in [2, 0]:
                    wins.append(winner_team == 20)
                else:
                    wins.append(winner_team == 31)

            # Neue Elo-Werte berechnen
            new_elo_values = update_elo(elo_values, k_factors, winner_team)

            # Neue Elo-Werte in DB speichern
            for player_index, player_id in enumerate(player_ids):
                stat = player_stats[player_id]
                stat["num_games"] = stat["num_games"] + 1
                if wins[player_index]:
                    stat["num_wins"] += 1
                stat["elo_value"] = new_elo_values[player_index]
                stat["max_elo_value"] = max(stat["max_elo_value"], stat["elo_value"])
                write_cursor.execute("""
                    INSERT INTO timeseries (
                        player_id,
                        game_id,
                        num_games,
                        win_rate,
                        elo_value,
                        final
                    ) 
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        player_id,
                        game_id,
                        stat["num_games"],
                        stat["num_wins"] / stat["num_games"],
                        stat["elo_value"],
                        0,
                    )
                )

            # Transaktion alle 1000 Dateien committen
            loop_counter += 1
            if loop_counter % 1000 == 0:
                write_conn.commit()

        # Final-Flag setzen
        write_cursor.execute("""
            UPDATE timeseries SET final = 1 WHERE id IN (
                SELECT MAX(id) AS id FROM timeseries GROUP BY player_id
            )   
        """)

    finally:
        write_conn.commit()
        read_conn.close()
        write_conn.close()

    print(f"Analyse-DB '{TIMESERIES_DATABASE}' erfolgreich erstellt.")

if __name__ == "__main__":
    build_timeseries_data()