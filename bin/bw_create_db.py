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
from src.lib.bw import bw_logfiles, bw_count_logfiles, BWLogEntry, BWErrorCode, BWParserError, parse_bw_logfile, validate_bw_log, BWReplayError, replay_play
from time import time
from typing import List
from tqdm import tqdm


def save_dirty_logfile(game_id, year, month, content):
    """Speichert Log-Dateien, die nicht geparst werden konnten."""
    file_path = os.path.join(config.DATA_PATH, f"bw/dirty/{year:04d}{month:02d}-{game_id}.tch")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        f.write(content)


def run_bw_validator(args: argparse.Namespace):
    """Testdurchlauf für den BW-Validator"""

    # Argumente auswerten
    y1, m1 = map(int, args.ym1.split("-"))
    y2, m2 = map(int, args.ym2.split("-"))
    path = args.path # Pfad zu den heruntergeladenen Log-Archiven

    print(f"Testdurchlauf für den BW-Validator von {y1:04d}-{m1:02d} bis {y2:04d}-{m2:02d}")

    # Fortschrittsbalken
    progress_bar = tqdm(
        bw_logfiles(path, y1, m1, y2, m2),
        total=bw_count_logfiles(path, y1, m1, y2, m2),
        desc="Verarbeite Log-Dateien",
        unit=" Datei"
    )

    c = 0
    rounds = 0
    fails = 0
    error_summary = {}
    time_start = time()
    for game_id, year, month, content in progress_bar:
        c += 1
        try:
            bw_log = parse_bw_logfile(game_id, year, month, content)
            rounds += len(bw_log)
            datasets = validate_bw_log(bw_log)
            if any(ds.error_code != BWErrorCode.NO_ERROR for ds in datasets):
                fails += 1
            for ds in datasets:
                if ds.error_code != BWErrorCode.NO_ERROR:
                    if ds.error_code not in error_summary:
                        error_summary[ds.error_code] = 0
                    error_summary[ds.error_code] += 1
        except BWParserError as e:
            print(e)
            save_dirty_logfile(game_id, year, month, content)
            fails += 1
            #exit(1)
        progress_bar.set_postfix({
            "Partien": c,
            "Fehlerhaft": fails,
            "Runden": rounds,
            "Datei": f"{year:04d}{month:02d}-{game_id}.tch"
        })

    duration = time() - time_start
    print("Vorgang beendet")
    print(f"Anzahl Partien: {c}")
    print(f"Gesamtzeit: {duration / 60:.0f} Minuten")
    print(f"Zeit pro Partie: {duration * 1000 / c:.3f} ms")
    for code, count in error_summary.items():
        print(f"{code.name}: {count} Fehler")


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
    run_bw_validator(parser.parse_args())
    #main(parser.parse_args())
