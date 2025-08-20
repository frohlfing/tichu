# scripts/build_timeseries_db.py

import sqlite3
import os
import pandas as pd
from src import config
from src.lib.bsw.database import update_elo, get_k_factor
from tqdm import tqdm
from typing import Dict, Any

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
    dst_conn = sqlite3.connect(TIMESERIES_DATABASE)
    dst_cursor = dst_conn.cursor()

    # Tabellen und Indezies erstellen
    dst_cursor.execute("""
            CREATE TABLE IF NOT EXISTS timeseries (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id   INTEGER NOT NULL,
                game_id     INTEGER NOT NULL,
                num_games   INTEGER NOT NULL,  -- Anzahl Partien des Spielers
                elo_v1      REAL NOT NULL,     -- z.B. k_dyn, divisor=400
                elo_v2      REAL NOT NULL,     -- z.B. k_dyn, divisor=200
                elo_v3      REAL NOT NULL,     -- z.B. k_dyn, divisor=600
                elo_v4      REAL NOT NULL,     -- z.B. fester k=20
                win_rate    REAL NOT NULL,     -- Anzahl Partien gewonnen / Anzahl Partien gesamt
                final       INTEGER NOT NULL   -- 1 == letzter Eintrag des Spielers, 0 == nicht final
            )
        """)
    dst_cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_timeseries_player_id_game_id ON timeseries (player_id, game_id);")
    dst_cursor.execute("CREATE INDEX IF NOT EXISTS idx_timeseries_game_id ON timeseries (game_id);")
    dst_cursor.execute("CREATE INDEX IF NOT EXISTS idx_timeseries_final ON timeseries (final);")
    dst_conn.commit()

    # Read-Only-Verbindung zur Tichu-Datenbank herstellen
    src_conn = sqlite3.connect(f'file:{TICHU_DATABASE}?mode=ro', uri=True)
    src_conn.row_factory = sqlite3.Row

    try:
        # --- 1. Lade alle Spieler und Partien für die Elo-Berechnung ---
        print("Lade Partien für die chronologische Verarbeitung...")

        games_query = """
            SELECT
                g.id, g.total_score_20, g.total_score_31, g.winner_team,
                gp.player_id, gp.player_index
            FROM games g
            JOIN games_players gp ON g.id = gp.game_id
            WHERE g.error_code = 0 AND g.player_changed = 0
            ORDER BY g.log_year, g.log_month, g.id
        """
        all_games_df = pd.read_sql_query(games_query, src_conn)

        # --- 2. Initialisiere Spieler-Statistiken im Speicher ---
        print("Initialisiere Spieler-Statistiken...")
        player_ids = pd.read_sql_query("SELECT id FROM players", src_conn)['id']

        player_stats: Dict[int, Dict[str, Any]] = {
            pid: {
                'elo_v1': 1500.0, 'max_elo_v1': 1500.0,
                'elo_v2': 1500.0, 'max_elo_v2': 1500.0,
                'elo_v3': 1500.0, 'max_elo_v3': 1500.0,
                'elo_v4': 1500.0, 'max_elo_v4': 1500.0,
                'games_played': 0,
                'games_won': 0,
                'total_score_diff': 0  # Wir brauchen diesen Wert, um den laufenden Durchschnitt zu berechnen
            } for pid in player_ids
        }

        # --- 3. Iteriere chronologisch und berechne die Zeitreihe ---
        game_groups = all_games_df.groupby('id')
        timeseries_data_to_insert = []
        loop_counter = 0
        for game_id, game_df in tqdm(game_groups, desc="Erstelle Zeitreihe"):
            if len(game_df) != 4: continue

            game_df = game_df.sort_values('player_index')
            player_ids = game_df['player_id'].tolist()
            score = (game_df.iloc[0]['total_score_20'], game_df.iloc[0]['total_score_31'])

            # Hole aktuelle Stats
            ratings_v1 = tuple(player_stats[pid]['elo_v1'] for pid in player_ids)
            # ... (hole ratings für v2, v3, v4) ...
            games_played = tuple(player_stats[pid]['games_played'] for pid in player_ids)

            # Berechne neue Elos
            k_factors_v1 = tuple(get_k_factor(gp, player_stats[pid]['max_elo_v1']) for gp, pid in zip(games_played, player_ids))
            new_ratings_v1 = update_elo(ratings_v1, score, k_factors_v1)
            # ... (berechne neue ratings für v2, v3, v4 mit anderen Parametern in update_elo) ...
            new_ratings_v4 = update_elo(tuple(player_stats[pid]['elo_v4'] for pid in player_ids), score, k=(20.0,) * 4)

            # Aktualisiere In-Memory-Stats und sammle Daten für den INSERT
            for i, pid in enumerate(player_ids):
                stats = player_stats[pid]

                # Update Elos
                stats['elo_v1'] = new_ratings_v1[i]
                stats['max_elo_v1'] = max(stats['max_elo_v1'], new_ratings_v1[i])
                stats['elo_v4'] = new_ratings_v4[i]
                # ...

                # Update laufende Statistiken
                stats['games_played'] += 1
                winner_team = game_df.iloc[0]['winner_team']
                player_team = 20 if i in [0, 2] else 31
                if winner_team == player_team:
                    stats['games_won'] += 1

                # ... (total_score_diff updaten, indem man aus rounds JOINt, oder vereinfacht hier)

                # Berechne kumulative Metriken für diesen Zeitpunkt
                cumulative_win_rate = stats['games_won'] / stats['games_played'] if stats['games_played'] > 0 else 0.0
                # cumulative_avg_score_diff = ...

                timeseries_data_to_insert.append((
                    game_id, pid, stats['games_played'],
                    stats['elo_v1'], 1500.0, 1500.0, stats['elo_v4'],  # Platzhalter für v2, v3
                    cumulative_win_rate, 0.0  # Platzhalter für avg_score_diff
                ))

        # --- 4. Schreibe die gesammelten Zeitreihen-Daten in die neue DB ---
        print(f"\nSchreibe {len(timeseries_data_to_insert)} Zeitreihen-Datenpunkte in die Analyse-DB...")
        dst_cursor.executemany("""
            INSERT INTO timeseries (
                player_id,
                game_id,
                num_games,
                elo_v1,
                elo_v2,
                elo_v3,
                elo_v4,
                win_rate,
                final
            ) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                timeseries_data_to_insert
        )

        loop_counter += 1
        if loop_counter % 1000 == 0:
            dst_conn.commit()

    finally:
        dst_conn.commit()
        src_conn.close()
        dst_conn.close()

    print(f"Analyse-DB '{TIMESERIES_DATABASE}' erfolgreich erstellt.")


if __name__ == "__main__":
    build_timeseries_data()