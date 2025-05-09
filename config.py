import logging
from dotenv import load_dotenv
from os import getenv
from os.path import dirname

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


def str_to_loglevel(env_value: str):
    log_levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
    }
    return log_levels.get(env_value.upper(), logging.NOTSET)


#Versionsnummer
# 1. Ziffer: Major Release - vollständige Neuentwicklung; nicht abwärtskompatibel
# 2. Ziffer: Minor Release - wird erhöht, wenn der Funktionsempfang geändert wurde
# 3. Ziffer: Patch Level - wird erhöht bei Fehlerbereinigung
VERSION = '0.0.0'

# asyncio im Debug-Mode starten
DEBUG = _to_bool(getenv("DEBUG"))

# Log Level und maximale Anzahl Log-Dateien (pro Tag wird eine neue Datei angelegt; ältere Dateien werden automatisch gelöscht)
LOG_LEVEL = str_to_loglevel(getenv("LOG_LEVEL", "WARNING"))
LOG_COUNT = int(getenv("LOG_COUNT", 5))

# Ordner
BASE_PATH = getenv("BASE_PATH", dirname(__file__))
DATA_PATH = getenv("DATA_PATH", f'{BASE_PATH}/data')

# WebSocket-Host und Port
HOST = getenv("HOST", "localhost")
PORT = int(getenv("PORT", 8080))

# Wer das nicht kennt, darf nicht mitspielen
SECRET_KEY = getenv("SECRET_KEY", "secret")

# Wartezeit nach einem Verbindungsabbruch bis zum Rauswurf in Sekunden
KICK_OUT_TIME = int(getenv("KICK_OUT_TIME", 15))

# Maximale Wartezeit für Anfragen an den Client in Sekunden (0 == unbegrenzt)
DEFAULT_REQUEST_TIMEOUT = 0

# Anzahl Prozesse für die Arena
ARENA_WORKER = int(getenv("ARENA_WORKER", 1))

# gewünschte Gewinnquote WIN / (WIN + LOST)
# wenn erreicht, bricht die Arena den Wettkampf ab (sofern early_stopping gesetzt ist)
ARENA_WIN_RATE = 0.6

# Denkzeit des Agenten (von/bis) in Sekunden
AGENT_THINKING_TIME = _to_array(getenv("AGENT_THINKING_TIME", [0.5, 3.0]), lambda item: float(item))

# Maximale Anzahl mögliche Partitionen, die pro Hand berechnet werden
PARTITIONS_MAXLEN = 2000

# Mindestwert für die Güte bei der Tichu-Ansage (kleines, großes)
HEURISTIC_TICHU_QUALITY = [0.6, 0.7]
