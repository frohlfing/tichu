# scripts/analyze_premature_tichu.py

import os
import sqlite3
from src import config
from tqdm import tqdm

DB_PATH = os.path.join(config.DATA_PATH, "bsw", "bsw.sqlite")


def fix():
    """
    Befüllt die Spalten `score_cum_20` und `score_cum_31` in der `rounds`-Tabelle
    mit den kumulativen Scores, ohne Pandas zu verwenden.
    """
    if not os.path.exists(DB_PATH):
        print(f"Fehler: Datenbank nicht gefunden unter {DB_PATH}")
        return

    print(f"Öffne Datenbank: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Für Zugriff auf Spalten per Namen

    read_cursor = conn.cursor()
    write_cursor = conn.cursor()

    read_cursor.execute("SELECT COUNT(*) FROM rounds")
    total_rounds = read_cursor.fetchone()[0]

    try:
        read_cursor.execute("""
            SELECT id, game_id, score_20, score_31 
            FROM rounds 
            ORDER BY game_id, round_index
        """)

        # Berechne die kumulativen Werte
        game_id = -1
        cumulative_score_20 = 0
        cumulative_score_31 = 0
        loop_counter = 0
        progress_bar = tqdm(read_cursor, total=total_rounds, desc="Berechne kumulative Scores", unit=" Runde")
        for row in progress_bar:
            if game_id != row['game_id']:
                game_id = row['game_id']
                cumulative_score_20 = 0
                cumulative_score_31 = 0

            write_cursor.execute("UPDATE rounds SET score_cum_20 = ?, score_cum_31 = ? WHERE id = ?", (
                cumulative_score_20,
                cumulative_score_31,
                row['id']
            ))

            # Transaktion alle 1000 Dateien committen
            loop_counter += 1
            if loop_counter % 1000 == 0:
                conn.commit()

            # Aktualisiere die laufende Summe für die *nächste* Runde in dieser Partie
            cumulative_score_20 += row['score_20']
            cumulative_score_31 += row['score_31']

    finally:
        conn.commit()
        conn.close()


if __name__ == "__main__":
    fix()
