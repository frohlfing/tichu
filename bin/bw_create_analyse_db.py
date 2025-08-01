#!/usr/bin/env python

"""
Dieses Modul importiert die vom Spiele-Portal "Brettspielwelt" heruntergeladenen Logdateien in eine SQLite-Analyse-Datenbank.
"""

import argparse
import os
import sqlite3
from datetime import datetime
from src import config
from src.lib.cards import parse_card
from src.lib.bw import BWLogEntry, BWReplayError, bw_logfiles, bw_count_logfiles, parse_bw_logfile, replay_play
from typing import List
from tqdm import tqdm


def create_tables(conn: sqlite3.Connection):
    """
    Erstellt die Tabellen in der SQLite-Datenbank, falls sie nicht existieren.
    """
    cursor = conn.cursor()

    # Tabelle für durchgespielte Runden
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rounds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,   -- ID der Runde
        game_id INTEGER NOT NULL,               -- ID der Partie
        aborted INTEGER NOT NULL,               -- 1 wenn die Partie abgebrochen wurde, sonst 0
        round_index INTEGER NOT NULL,           -- Die Nummer der Runde innerhalb der Partie (0, 1, 2...).
        player_0_id INTEGER NOT NULL,           -- Spieler mit Index 0
        player_1_id INTEGER NOT NULL,           -- Spieler mit Index 1
        player_2_id INTEGER NOT NULL,           -- Spieler mit Index 2
        player_3_id INTEGER NOT NULL,           -- Spieler mit Index 3
        tichu_0 INTEGER NOT NULL,               -- Tichu-Ansagen des Spielers 0 (0 == keine Ansage, 1 == einfaches Tichu, 2 == großes Tichu).
        tichu_1 INTEGER NOT NULL,               -- Tichu-Ansagen des Spielers 1 (0 == keine Ansage, 1 == einfaches Tichu, 2 == großes Tichu).
        tichu_2 INTEGER NOT NULL,               -- Tichu-Ansagen des Spielers 2 (0 == keine Ansage, 1 == einfaches Tichu, 2 == großes Tichu).
        tichu_3 INTEGER NOT NULL,               -- Tichu-Ansagen des Spielers 3 (0 == keine Ansage, 1 == einfaches Tichu, 2 == großes Tichu).
        tichu_successful_0 INTEGER NOT NULL,    -- 1 wenn Spieler 0 das Tichu gewonnen hat, sonst 0
        tichu_successful_1 INTEGER NOT NULL,    -- 1 wenn Spieler 1 das Tichu gewonnen hat, sonst 0
        tichu_successful_2 INTEGER NOT NULL,    -- 1 wenn Spieler 2 das Tichu gewonnen hat, sonst 0
        tichu_successful_3 INTEGER NOT NULL,    -- 1 wenn Spieler 3 das Tichu gewonnen hat, sonst 0
        early_tichu_0 INTEGER NOT NULL,         -- 1 wenn Spieler 0 vor dem Ausspielen ein einfaches Tichu angesagt hat, sonst 0
        early_tichu_1 INTEGER NOT NULL,         -- 1 wenn Spieler 1 vor dem Ausspielen ein einfaches Tichu angesagt hat, sonst 0
        early_tichu_2 INTEGER NOT NULL,         -- 1 wenn Spieler 2 vor dem Ausspielen ein einfaches Tichu angesagt hat, sonst 0
        early_tichu_3 INTEGER NOT NULL,         -- 1 wenn Spieler 3 vor dem Ausspielen ein einfaches Tichu angesagt hat, sonst 0
        schupf_0_right_opp INTEGER NOT NULL,    -- Wert der Schupfkarte vom Spieler 0 für rechten Gegner
        schupf_0_partner INTEGER NOT NULL,      -- Wert der Schupfkarte vom Spieler 0 für Partner
        schupf_0_left_opp INTEGER NOT NULL,     -- Wert der Schupfkarte vom Spieler 0 für linken Gegner
        schupf_1_right_opp INTEGER NOT NULL,    -- Wert der Schupfkarte vom Spieler 1 für rechten Gegner
        schupf_1_partner INTEGER NOT NULL,      -- Wert der Schupfkarte vom Spieler 1 für Partner
        schupf_1_left_opp INTEGER NOT NULL,     -- Wert der Schupfkarte vom Spieler 1 für linken Gegner
        schupf_2_right_opp INTEGER NOT NULL,    -- Wert der Schupfkarte vom Spieler 2 für rechten Gegner
        schupf_2_partner INTEGER NOT NULL,      -- Wert der Schupfkarte vom Spieler 2 für Partner
        schupf_2_left_opp INTEGER NOT NULL,     -- Wert der Schupfkarte vom Spieler 2 für linken Gegner
        schupf_3_right_opp INTEGER NOT NULL,    -- Wert der Schupfkarte vom Spieler 3 für rechten Gegner
        schupf_3_partner INTEGER NOT NULL,      -- Wert der Schupfkarte vom Spieler 3 für Partner
        schupf_3_left_opp INTEGER NOT NULL,     -- Wert der Schupfkarte vom Spieler 3 für linken Gegner
        is_even_odd_rule_20 INTEGER NOT NULL,   -- 1 wenn Team 20 nach der Regel "rechts gerade, links ungerade" (oder umgekehrt) geschupft hat, sonst 0.
        is_even_odd_rule_31 INTEGER NOT NULL,   -- 1 wenn Team 31 nach der Regel "rechts gerade, links ungerade" (oder umgekehrt) geschupft hat, sonst 0.
        wish_value INTEGER NOT NULL,            -- Gewünschter Kartenwert (2 bis 14; -1 == kein Mahjong gespielt, 0 == kein Wunsch geäußert).
        dragon_recipient INTEGER NOT NULL       -- Index des Spielers, der den Drachen bekommen hat (-1 == Drache wurde bis zum Schluss nicht verschenkt).
        is_double_victory INTEGER NOT NULL,     -- 1 wenn die Runde mit einem Doppelsieg beendet wurde, sonst 0.
        min_points INTEGER NOT NULL,            -- Kleinste Punktzahl, die ein Spieler während der Runde hatte.
        max_points INTEGER NOT NULL,            -- Höchste Punktzahl, die ein Spieler in der Runde erzielt.
        avg_points REAL NOT NULL,               -- Durchschnittliche Punktzahl, die ein Spieler während der Runde hatte.
        stdef_points REAL NOT NULL,             -- Standardabweichung der Punktzahl, die ein Spieler während der Runde hatte.
        score_20 INTEGER NOT NULL,              -- Rundenergebnis für Team 20 (Erzielte Punkte inkl. Bonus am Ende der Runde für Spieler 0 und 2).
        score_31 INTEGER NOT NULL,              -- Rundenergebnis für Team 31 (Erzielte Punkte inkl. Bonus am Ende der Runde für Spieler 3 und 1).
        score_diff INTEGER NOT NULL,            -- Ergebnisdifferenz der Runde (score_20 - score_31). Die Haupt-Zielvariable für das Value-Netz.
        total_score_20 INTEGER NOT NULL,        -- Punktestand der Partie für Team 20 (diese und vorherige Runden zusammengezählt).
        total_score_31 INTEGER NOT NULL,        -- Punktestand der Partie für Team 31 (diese und vorherige Runden zusammengezählt).
        num_tricks INTEGER NOT NULL,            -- Anzahl der Stiche in der Runde.
        num_turns INTEGER NOT NULL,             -- Anzahl der Spielzüge in der Runde.
        min_turns_per_trick INTEGER NOT NULL,   -- Kleinste Anzahl Spielzüge pro Stich.
        max_turns_per_trick INTEGER NOT NULL,   -- Höchste Anzahl Spielzüge pro Stich.
        avg_turns_per_trick REAL NOT NULL,      -- Durchschnittliche Anzahl Spielzüge pro Stich.
        stdef_turns_per_trick REAL NOT NULL,    -- Standardabweichung der Anzahl Spielzüge pro Stich.
        log_year INTEGER NOT NULL,              -- Jahr des Logfiles
        log_month INTEGER NOT NULL              -- Monat des Logfiles
    """)

    # Tabelle für Spieler
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,  -- ID des Spielers
        name TEXT NOT NULL, -- Eindeutiger Name des Spielers.
        num_games INTEGER NOT NULL, -- Anzahl Partien, in der der Spieler beteiligt war.
        num_aborted_games INTEGER NOT NULL, -- Anzahl der abgebrochenen Partien, in der der Spieler beteiligt war.
        num_completed_games INTEGER NOT NULL, -- Anzahl der Partien, die der Spieler durchgespielt hat.
        num_rounds INTEGER NOT NULL, -- Anzahl der Runden, die der Spieler gespielt hat.
        game_win_rate REAL NOT NULL, -- Gewinnrate des Spielers (auf die Partie bezogen, inkl. abgebrochenen).
        completed_game_win_rate REAL NOT NULL, -- Gewinnrate des Spielers (auf die durchgespielte Partie bezogen).
        round_win_rate REAL NOT NULL, -- Gewinnrate des Spielers (auf die Runde bezogen).
        avg_score_diff REAL NOT NULL, -- Durchschnittliche Ergebnisdifferenz einer Runde dieses Spielers.
        num_grand_tichus REAL NOT NULL -- Anzahl der Grand-Tichu-Ansagen.
        num_grand_tichus_successes REAL NOT NULL -- Anzahl der erfolgreichen Grand-Tichus.
        normal_tichu_success_rate REAL NOT NULL -- Erfolgsrate-Rate bei einer Grand-Tichu-Ansage.
        num_normal_tichus REAL NOT NULL -- Anzahl der einfachen Tichu-Ansagen.
        num_normal_tichus_successes REAL NOT NULL -- Anzahl der erfolgreichen einfachen Tichus.
        tichu_success_rate REAL NOT NULL -- Erfolgsrate-Rate bei einer einfachen Tichu-Ansage.
    )
    """)

    conn.commit()


def create_indexes(conn: sqlite3.Connection):
    """
    Erstellt Indizes für die Tabellen in der SQLite-Datenbank, falls sie nicht existieren.
    """
    cursor = conn.cursor()

    # rounds
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_game_id ON rounds (game_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_aborted ON games (aborted)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_player_0_id ON rounds (player_0_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_player_1_id ON rounds (player_1_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_player_2_id ON rounds (player_2_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_player_3_id ON rounds (player_3_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_tichu_0 ON rounds (tichu_0)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_tichu_1 ON rounds (tichu_1)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_tichu_2 ON rounds (tichu_2)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_tichu_3 ON rounds (tichu_3)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_schupf_0_right_opp ON rounds (schupf_0_right_opp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_schupf_0_partner ON rounds (schupf_0_partner)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_schupf_0_left_opp ON rounds (schupf_0_left_opp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_schupf_1_right_opp ON rounds (schupf_1_right_opp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_schupf_1_partner ON rounds (schupf_1_partner)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_schupf_1_left_opp ON rounds (schupf_1_left_opp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_schupf_2_right_opp ON rounds (schupf_2_right_opp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_schupf_2_partner ON rounds (schupf_2_partner)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_schupf_2_left_opp ON rounds (schupf_2_left_opp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_schupf_3_right_opp ON rounds (schupf_3_right_opp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_schupf_3_partner ON rounds (schupf_3_partner)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_schupf_3_left_opp ON rounds (schupf_3_left_opp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_is_even_odd_rule_20 ON rounds (is_even_odd_rule_20)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_is_even_odd_rule_31 ON rounds (is_even_odd_rule_31)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_wish_value ON rounds (wish_value)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_dragon_recipient ON rounds (dragon_recipient)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_is_double_victory ON rounds (is_double_victory)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_min_points ON rounds (min_points)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_max_points ON rounds (max_points)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_avg_points ON rounds (avg_points)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_stdef_points ON rounds (stdef_points)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_score_20 ON rounds (score_20)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_score_31 ON rounds (score_31)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_score_diff ON rounds (score_diff)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_num_tricks ON rounds (num_tricks)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_num_turns ON rounds (num_turns)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_min_turns_per_trick ON rounds (min_turns_per_trick)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_max_turns_per_trick ON rounds (max_turns_per_trick)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_avg_turns_per_trick ON rounds (avg_turns_per_trick)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_stdef_turns_per_trick ON rounds (stdef_turns_per_trick)")
    conn.commit()

    # players
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_num_games ON players (num_games)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_num_aborted_games ON players (num_aborted_games)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_num_completed_games ON players (num_completed_games)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_num_rounds ON players (num_rounds)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_win_rate ON players (game_win_rate)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_completed_game_win_rate ON players (completed_game_win_rate)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_round_win_rate ON players (round_win_rate)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_avg_score_diff ON players (avg_score_diff)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_num_grand_tichus ON players (num_grand_tichus)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_num_grand_tichus_successes ON players (num_grand_tichus_successes)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_num_normal_tichu_success_rate ON players (normal_tichu_success_rate)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_num_normal_tichus ON players (num_normal_tichus)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_num_normal_tichus_successes ON players (num_normal_tichus_successes)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_tichu_success_rate ON players (tichu_success_rate)")
    conn.commit()


def process_and_insert_data(cursor: sqlite3.Cursor, all_rounds_data: List[BWLogEntry]):
    """
    Verarbeitet die geparsten Daten einer Log-Datei und fügt sie in die DB ein.
    """
    if not all_rounds_data:
        return

    # --- 1. Aggregierte Daten für die `games`-Tabelle sammeln ---
    game_data = all_rounds_data[0] # Nimm Daten aus der ersten Runde als Referenz
    game_id = game_data.game_id
    num_rounds = len(all_rounds_data)

    # Berechne Gesamtscore (Annahme: letzter Eintrag in score_history ist der Endstand)
    # Dies muss evtl. angepasst werden, je nachdem wie dein Parser den Endstand liefert.
    # Hier nehmen wir an, der Endstand ist die Summe der Runden-Scores.
    total_score_team20 = sum(r.score_entry[0] for r in all_rounds_data)
    total_score_team31 = sum(r.score_entry[1] for r in all_rounds_data)

    # --- Replay-Simulator verwenden, um Metriken zu extrahieren ---
    total_tricks = 0
    total_moves = 0

    for round_data in all_rounds_data:
        # Hier könnten wir den Replay-Simulator laufen lassen, wenn wir
        # detaillierte Zug-Statistiken bräuchten. Für die DB-Metriken
        # können wir oft einfachere Berechnungen auf den Rohdaten machen.
        # Beispiel:
        # num_turns_in_round = len(round_data.history)
        # num_tricks_in_round = ... (müsste man aus der History ableiten)
        # Wir lassen das für den Moment einfacher und nehmen an, die Metriken
        # sind bereits im BWRoundData-Objekt oder werden hier berechnet.

        # --- 2. Daten für die `rounds`-Tabelle vorbereiten und einfügen ---
        # Tichu-Infos serialisieren (Beispiel, muss an dein Datenmodell angepasst werden)
        # tichu_json = json.dumps([...])

        # Dummy-Werte für Tricks/Moves, da wir den Simulator hier nicht voll laufen lassen
        # um den Import zu beschleunigen.
        num_turns = len(round_data.history)

        cursor.execute(
            "INSERT OR REPLACE INTO rounds (game_id, round_index, wish_value, dragon_recipient, is_double_victory, score_20, score_31, score_diff, num_tricks, num_turns) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                round_data.game_id,
                round_data.round_index,
                None, # tichu_announcements
                -1, # wish_value
                -1, #dragon_recipient
                False, # is_double_victory
                round_data.score_entry[0],
                round_data.score_entry[1],
                round_data.score_entry[0] - round_data.score_entry[1],
                0, #num_tricks
                num_turns,
            )
        )
        round_id = cursor.lastrowid

        total_moves += num_turns

        # --- 3. Daten für die `schupf_actions`-Tabelle vorbereiten und einfügen ---
        for giver_index, schupf_tuple in enumerate(round_data.given_schupf_cards):
            recipients = [(giver_index + 1) % 4, (giver_index + 2) % 4, (giver_index + 3) % 4]
            for i, card_str in enumerate(schupf_tuple):
                if card_str:
                    card_rank, card_suit = parse_card(card_str)
                    recipient_index = recipients[i]
                    cursor.execute(
                        "INSERT INTO schupf_actions (round_id, giver_index, recipient_index, card_rank, card_suit) VALUES (?, ?, ?, ?, ?)",
                        (round_id, giver_index, recipient_index, card_rank, card_suit.value)
                    )
            pass # Schupf-Logik erstmal weggelassen zur Vereinfachung des Beispiels

    # Füge die aggregierten Game-Daten ein
    cursor.execute(
        "INSERT OR REPLACE INTO games (id, player_name_0, player_name_1, player_name_2, player_name_3, score_20, score_31, num_rounds, avg_tricks_per_round, avg_turns_per_round, log_year, log_month) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            game_id,
            game_data.player_names[0], game_data.player_names[1], game_data.player_names[2], game_data.player_names[3],
            total_score_team20, total_score_team31,
            num_rounds,
            0.0, # avg_tricks_per_round
            total_moves / num_rounds if num_rounds > 0 else 0.0, # avg_turns_per_round
            game_data.year,
            game_data.month
        )
    )


def save_dirty_logfile(game_id, year, month, content):
    """Speichert Log-Dateien, die nicht geparst werden konnten."""
    file_path = os.path.join(config.DATA_PATH, f"bw/dirty/{year:04d}{month:02d}-{game_id}.tch")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        f.write(content)


def run_bw_parser(args: argparse.Namespace):
    """Testdurchlauf für den BW-Parser"""

    # Argumente auswerten
    y1, m1 = map(int, args.ym1.split("-"))
    y2, m2 = map(int, args.ym2.split("-"))
    path = args.path # Pfad zu den heruntergeladenen Log-Archiven

    print(f"Testdurchlauf für den BW-Parser von {y1:04d}-{m1:02d} bis {y2:04d}-{m2:02d}")

    # Fortschrittsbalken
    progress_bar = tqdm(
        bw_logfiles(path, y1, m1, y2, m2),
        total=bw_count_logfiles(path, y1, m1, y2, m2),
        desc="Verarbeite Log-Dateien",
        unit=" Datei"
    )

    c = 0
    fails = 0
    for game_id, year, month, content in progress_bar:
        c += 1
        all_rounds_data: List[BWLogEntry] = parse_bw_logfile(game_id, year, month, content)
        if all_rounds_data is None:
            save_dirty_logfile(game_id, year, month, content)
            return

        for round_data in all_rounds_data:
            if round_data.parser_error:
                if round_data.parser_error not in error_counters:
                    error_counters[round_data.parser_error] = 0
                error_counters[round_data.parser_error] += 1

        try:
            #all_rounds_data = [all_rounds_data[5]]
            for _action in replay_play(all_rounds_data):
                pass
            progress_bar.set_postfix({
                "Partien": c,
                "Fehler": fails,
                "Fehlerrate": f"{fails/c:.2%}"
            })
        except BWReplayError as e:
            error = str(e)
            if error not in error_counters:
                error_counters[error] = 0
            error_counters[error] += 1
            #print(e)
            save_dirty_logfile(game_id, year, month, content)
            fails += 1

    print("fertig")
    print(error_counters)





def run_replay_play(args: argparse.Namespace):
    """Testdurchlauf für den Replay-Round-Simulator"""

    # Argumente auswerten
    y1, m1 = map(int, args.ym1.split("-"))
    y2, m2 = map(int, args.ym2.split("-"))
    path = args.path # Pfad zu den heruntergeladenen Log-Archiven

    print(f"Testdurchlauf für den Replay-Round-Simulator von {y1:04d}-{m1:02d} bis {y2:04d}-{m2:02d}")

    # Fortschrittsbalken
    progress_bar = tqdm(
        bw_logfiles(path, y1, m1, y2, m2),
        total=bw_count_logfiles(path, y1, m1, y2, m2),
        desc="Verarbeite Log-Dateien",
        unit=" Datei"
    )

    error_counters = {}

    c = 0
    fails = 0
    for game_id, year, month, content in progress_bar:
        # if game_id not in [2067904]: continue

        all_rounds_data: List[BWLogEntry] = parse_bw_logfile(game_id, year, month, content)
        if all_rounds_data is None:
            print("Parserfehler!")
            save_dirty_logfile(game_id, year, month, content)
            return

        for round_data in all_rounds_data:
            if round_data.parser_error:
                if round_data.parser_error not in error_counters:
                    error_counters[round_data.parser_error] = 0
                error_counters[round_data.parser_error] += 1

        c += 1
        try:
            #all_rounds_data = [all_rounds_data[5]]
            for _action in replay_play(all_rounds_data):
                pass
            progress_bar.set_postfix({
                "Partien": c,
                "Fehler": fails,
                "Fehlerrate": f"{fails/c:.2%}"
            })
        except BWReplayError as e:
            error = str(e)
            if error not in error_counters:
                error_counters[error] = 0
            error_counters[error] += 1
            #print(e)
            save_dirty_logfile(game_id, year, month, content)
            fails += 1

    print("fertig")
    print(error_counters)


def main(args: argparse.Namespace):
    """Main-Routine"""
    # Argumente auswerten
    y1, m1 = map(int, args.ym1.split("-"))
    y2, m2 = map(int, args.ym2.split("-"))
    path = args.path  # Pfad zu den heruntergeladenen Log-Archiven
    db_file = os.path.join(config.DATA_PATH, "bw", "bw_analysis.sqlite")

    # Import starten
    print(f"Importiere Log-Dateien von {y1:04d}-{m1:02d} bis {y2:04d}-{m2:02d}")
    print(f"Datenbank-Datei: {db_file}")

    # Verbindung zur Datenbank herstellen und Tabellen einrichten
    os.makedirs(os.path.dirname(db_file), exist_ok=True)
    conn = sqlite3.connect(db_file)
    create_tables(conn)
    cursor = conn.cursor()

    # Fortschrittsbalken
    progress_bar = tqdm(
        bw_logfiles(path, y1, m1, y2, m2),
        total=bw_count_logfiles(path, y1, m1, y2, m2),
        desc="Verarbeite Log-Dateien",
        unit=" Datei"
    )

    log_file_counter = 0
    try:
        for game_id, year, month, content in progress_bar:
            # Log-Datei parsen
            all_rounds_data: List[BWLogEntry] = parse_bw_logfile(game_id, year, month, content)
            if all_rounds_data is None:
                print("Parserfehler!")
                save_dirty_logfile(game_id, year, month, content)
                continue

            # Daten verarbeiten und in DB einfügen
            process_and_insert_data(cursor, all_rounds_data)

            # Transaktion alle 1000 Dateien committen, um die Performance zu verbessern
            log_file_counter += 1
            if log_file_counter % 1000 == 0:
                conn.commit()
                progress_bar.set_postfix_str(f"Committing to DB...")

    except KeyboardInterrupt:
        print("\nImport durch Benutzer abgebrochen.")
    except Exception as e:
        print(f"\nEin Fehler ist aufgetreten: {e}")
    finally:
        # Sicherstellen, dass alle verbleibenden Änderungen gespeichert werden
        print("Speichere finale Änderungen in der Datenbank...")
        conn.commit()
        conn.close()
        print("Datenbankverbindung geschlossen. Import beendet.")


if __name__ == "__main__":
    print(f"BW Analyse DB Creator")

    # Argumente parsen
    today_ = datetime.today().strftime("%Y-%m")
    path_ = os.path.join(config.DATA_PATH, "bw/tichulog")
    parser = argparse.ArgumentParser(description="Importiert BSW Tichu Logs in eine SQLite-Analyse-Datenbank.")
    parser.add_argument("--ym1", default="2007-01", help="Start-Datum im Format YYYY-MM")
    parser.add_argument("--ym2", default=today_, help="End-Datum im Format YYYY-MM")
    parser.add_argument("--path", default=path_, help="Pfad zu den heruntergeladenen Log-Archiven")

    # Main-Routine starten
    run_bw_parser(parser.parse_args())
    run_replay_play(parser.parse_args())
    #main(parser.parse_args())
