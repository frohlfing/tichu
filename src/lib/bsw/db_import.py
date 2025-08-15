"""
Importieren der validierten Tichu-Logdateien in die Datenbank.
"""

__all__ = "import_logfiles",

from src.lib.bsw.database import TichuDatabase, ETLErrorCode
from src.lib.bsw.download import logfiles, count_logfiles
from src.lib.bsw.parse import parse_logfile
from src.lib.bsw.validate import validate_bswlog
from tqdm import tqdm


def import_logfiles(database: str, path: str, y1: int, m1: int, y2: int, m2: int):
    """
    Importiert die vom Spiele-Portal "Brettspielwelt" heruntergeladenen Logdateien.

    Hierbei wird ein Fortschrittsbalken angezeigt.

    :param database: Die SQLite-Datenbankdatei.
    :param path: Das Verzeichnis, in dem die Zip-Archive liegen.
    :param y1: ab Jahr
    :param m1: ab Monat
    :param y2: bis Jahr (einschließlich)
    :param m2: bis Monat (einschließlich)
    """
    # Verbindung zur Datenbank herstellen und Tabellen einrichten
    db = TichuDatabase(database)
    db.open()

    # Aktualisierung starten
    log_file_counter = 0
    try:
        progress_bar = tqdm(logfiles(path, y1, m1, y2, m2), total=count_logfiles(path, y1, m1, y2, m2), unit=" Datei", desc="Importiere Log-Dateien")
        logfiles_total = 0
        games_fails = 0
        games_empty = 0
        for game_id, year, month, content in progress_bar:
            # Logdateien zählen
            logfiles_total += 1

            # Parsen
            bsw_log = parse_logfile(game_id, year, month, content)
            if len(bsw_log) > 0:
                # Validieren
                game = validate_bswlog(bsw_log)

                # Fehlerhafte Partien zählen
                if game.error_code != ETLErrorCode.NO_ERROR:
                    games_fails += 1

                # Datenbank aktualisieren
                db.save_game(game)
            else:
                games_empty += 1

            # Transaktion alle 1000 Dateien committen
            log_file_counter += 1
            if log_file_counter % 1000 == 0:
                progress_bar.set_postfix_str(f"Commit DB...")
                db.commit()

            # Fortschritt aktualisieren
            progress_bar.set_postfix({
                "Logdateien": logfiles_total,
                "Leere": games_empty,
                "Fehler": games_fails,
                "Datei": f"{year:04d}{month:02d}/{game_id}.tch"
            })

        # Indizes erst am Ende einrichten, damit der Import schneller durchläuft.
        db.create_indexes()

    # Alle verbleibenden Änderungen speichern und Datenbank schließen.
    finally:
        db.commit()
        db.close()