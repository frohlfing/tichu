# scripts/analyze_premature_tichu.py

import sqlite3
import os
from tqdm import tqdm

# Passe diese Importe an die Struktur deines Projekts an
from src import config
from src.lib.bsw.database import deserialize_history

DB_PATH = os.path.join(config.DATA_PATH, "bsw", "bsw.sqlite")


def analyze_premature_tichu_calls():
    """
    Durchläuft die Datenbank, um zu analysieren, wie oft ein Spieler Tichu ansagt,
    aber direkt danach passt, obwohl er auch hätte spielen können.
    """
    if not os.path.exists(DB_PATH):
        print(f"Fehler: Datenbank nicht gefunden unter {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    # Verwende row_factory, um auf Spalten per Namen zugreifen zu können (lesbarer)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("Analysiere Tichu-Ansagen... (dies kann einige Minuten dauern)")

    # 1. Finde alle Runden, in denen mindestens ein "kleines" Tichu angesagt wurde.
    #    tichu_pos >= 0 bedeutet, es wurde während des Spiels angesagt.
    query = """
        SELECT id, history, tichu_pos_0, tichu_pos_1, tichu_pos_2, tichu_pos_3
        FROM rounds
        WHERE tichu_pos_0 >= 0 OR tichu_pos_1 >= 0 OR tichu_pos_2 >= 0 OR tichu_pos_3 >= 0
    """

    cursor.execute("SELECT COUNT(*) FROM rounds WHERE tichu_pos_0 >= 0 OR tichu_pos_1 >= 0 OR tichu_pos_2 >= 0 OR tichu_pos_3 >= 0")
    total_rounds_with_tichu = cursor.fetchone()[0]

    if total_rounds_with_tichu == 0:
        print("Keine Runden mit Tichu-Ansagen in der Datenbank gefunden.")
        conn.close()
        return

    cursor.execute(query)

    premature_pass_count = 0
    total_tichu_calls_analyzed = 0

    progress_bar = tqdm(cursor, total=total_rounds_with_tichu, desc="Analysiere Runden", unit=" Runde")

    for row in progress_bar:
        history = deserialize_history(row['history'])
        tichu_positions = [row['tichu_pos_0'], row['tichu_pos_1'], row['tichu_pos_2'], row['tichu_pos_3']]

        for player_idx in range(4):
            tichu_pos = tichu_positions[player_idx]

            # Interessiert uns nur "kleines" Tichu, das während des Spiels angesagt wurde
            if tichu_pos < 0:
                continue

            total_tichu_calls_analyzed += 1

            # Finde den Zug direkt nach der Tichu-Ansage.
            # `tichu_pos` ist der Index in der History, AN dem die Ansage gemacht wurde.
            # Hat der Spieler dann auch Karten ausgespielt?
            turn_player_index, turn_cards, collector_index = history[tichu_pos]
            if turn_player_index != player_idx or not turn_cards:
                # Der Spieler hat nach seiner Tichu-Ansage keine Karten ausgespielt.
                # Anfängerfehler!
                premature_pass_count += 1

    conn.close()

    print("\n--- Analyse-Ergebnis ---")
    print(f"Runden mit Tichu-Ansage gefunden: {total_rounds_with_tichu}")
    print(f"Individuelle 'kleine' Tichu-Ansagen analysiert: {total_tichu_calls_analyzed}")
    print(f"Fälle von 'Tichu angesagt und direkt gepasst': {premature_pass_count}")

    if total_tichu_calls_analyzed > 0:
        percentage = (premature_pass_count / total_tichu_calls_analyzed) * 100
        print(f"Anteil der 'nervösen Tichus': {percentage:.2f}%")


if __name__ == "__main__":
    analyze_premature_tichu_calls()