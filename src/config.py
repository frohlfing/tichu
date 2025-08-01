"""
Dieses Modul stellt zentrale Konfigurationsvariablen bereit.

Die Standardwerte können mit den Umgebungsvariablen der `.env`-Datei überschieben werden.
"""

import logging
import os
from dotenv import load_dotenv

# Lade die Umgebungsvariablen aus der .env-Datei
load_dotenv()


def _to_bool(env_value: str|None) -> bool:
    if env_value is None:
        return False
    return env_value.lower() in ("true", "yes", "on", "1")


def _to_array(env_value: str|list|None, method: callable) -> list:
    # wandelt ein Eintrag wie z.B. "[0.5, 3.0]" in eine Liste um
    if env_value is None:
        return []
    if type(env_value) == list:
        return env_value
    arr = []
    for item in env_value.lstrip("[").rstrip("]").split(","):
        arr.append(method(item))
    return arr


def str_to_loglevel(env_value: str) -> int:
    log_levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
    }
    return log_levels.get(env_value.upper(), logging.NOTSET)


VERSION = '0.0.0'
"""
Versionsnummer:
 1. Ziffer: Major Release - vollständige Neuentwicklung; nicht abwärtskompatibel.
 2. Ziffer: Minor Release - wird erhöht, wenn der Funktionsempfang geändert wurde.
 3. Ziffer: Patch Level - wird erhöht bei Fehlerbereinigung.
"""

DEBUG = _to_bool(os.getenv("DEBUG"))
"""
asyncio im Debug-Mode starten.
"""

LOG_LEVEL = str_to_loglevel(os.getenv("LOG_LEVEL", "WARNING"))
"""
Log Level .
"""

LOG_COUNT = int(os.getenv("LOG_COUNT", 5))
"""
Maximale Anzahl Log-Dateien (pro Tag wird eine neue Datei angelegt; ältere Dateien werden automatisch gelöscht).
"""

BASE_PATH = os.path.abspath(os.getenv("BASE_PATH", os.path.join(os.path.dirname(__file__), "..")))
"""
Projektverzeichnis.
"""

DATA_PATH = os.path.abspath(os.getenv("DATA_PATH", f'{BASE_PATH}/data'))
"""
Datenverzeichnis.
"""

HOST = os.getenv("HOST", "localhost")
"""
WebSocket-Host.
"""

PORT = int(os.getenv("PORT", 8765))
"""
WebSocket-Port.
"""

SECRET_KEY = os.getenv("SECRET_KEY", "secret")
"""
Wer das nicht kennt, darf nicht mitspielen.
"""

KICK_OUT_TIME = int(os.getenv("KICK_OUT_TIME", 15))
"""
Wartezeit nach einem Verbindungsabbruch bis zum Rauswurf in Sekunden.
"""

DEFAULT_REQUEST_TIMEOUT = 99999999
"""
Maximale Wartezeit für Anfragen an den Client in Sekunden (None == unbegrenzt).
"""

ARENA_WORKER = int(os.getenv("ARENA_WORKER", 1))
"""
Anzahl Prozesse für die Arena.
"""

ARENA_WIN_RATE = 0.6
"""
Gewünschte Gewinnquote WIN / (WIN + LOST).
Wenn erreicht, bricht die Arena den Wettkampf ab (sofern early_stopping gesetzt ist).
"""

AGENT_THINKING_TIME = _to_array(os.getenv("AGENT_THINKING_TIME", [500, 1500]), lambda item: int(item))
"""
Denkzeit des Agenten (von/bis) in ms.
"""

BREAK_TIME_AFTER_ROUND = 1000
"""
Pause in ms nach einer Runde, wenn Clients mitspielen.
"""

PARTITIONS_MAXLEN = 2000
"""
Maximale Anzahl mögliche Partitionen, die pro Hand berechnet werden.
"""

HEURISTIC_TICHU_QUALITY = [0.6, 0.7]
"""
Mindestwert für die Güte bei der Tichu-Ansage (kleines, großes).
"""
