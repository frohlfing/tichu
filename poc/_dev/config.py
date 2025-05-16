import logging
from os.path import dirname

VERSION = "1.0.0"
BASE_PATH = dirname(__file__)
DATA_PATH = f"{BASE_PATH}/data"
LOCALE = "de"  # de, en
# TIMEZONE = 'Europe/Berlin'  # Europe/Berlin, UTC  - wird noch nicht verwendet
DEBUG = True  # Erweiterte Ausgabe, insbesondere für Webserver: interaktiver Debugger und Reloader

# Logging
LOG_PATH = f"{BASE_PATH}/logs"
LOG_LEVEL = logging.DEBUG   # CRITICAL, ERROR, WARNING, INFO, DEBUG
LOG_SHELL = False           # Wenn True, werden alle Log-Einträge zusätzlich in die Console geschrieben.

# Database
# https://docs.sqlalchemy.org/en/13/core/engines.html
# DATABASE = mysql+pymysql://root:@localhost/tichu
# DATABASE = mssql+pymssql://nextccportal_migration:!O$terD3T3W3!@PE-MICCE01:1433/nextccportal
DATABASE = f"sqlite:///{BASE_PATH}/data/app.sqlite"
# DATABASE = sqlite:///:memory:

# SMTP Server
MAIL_HOST = "mail.your-server.de"
MAIL_PORT = 587
MAIL_USERNAME = "webmaster@frank-rohlfing.de"
MAIL_PASSWORD = "9eEi4kfX5UPvI5tY"
MAIL_TLS = True
MAIL_SSL = False
# MAIL_FROM = "Frank's Webmailer <webmailer@frank-rohlfing.de>"
MAIL_FROM = ("Frank's Webmailer", 'webmailer@frank-rohlfing.de')
MAIL_TO = "mail@frank-rohlfing.de"

# Webserver
# HOST:
# Set this to "0.0.0.0" to have the server available externally as well.
# - Falls hier eine IP-Adresse eingetragen ist, wirft Flask folgende Warnung:
#   UserWarning: The session cookie domain is an IP address. This may not work as intended in some browsers.
# - Falls localhost eingetragen ist:
#   UserWarning: "localhost" is not a valid cookie domain, it must contain a ".".
HOST = 'localhost.localdomain'  # FQDN, e.g. localhost.localdomain (wird auch für die WebSocket benötigt)
PORT = 5555
SECRET_KEY = '1234'         # os.urandom(16)
LIFETIME = 525600           # Session Lifetime in Minuten: 120 = 2 Stunden (default), 525600 = 365 Tage
MAX_CONTENT = 8             # MB - Don’t read more than this many bytes from the incoming request data.

# WebSocket
WS_PORT = 8765
ANONYMOUS = False           # Anonymer Zugriff erlauben?
AUTOCONNECT = 2000          # Delay in milliseconds for reconnection after connection loss (0 never means).
WS_TIMEOUT = 10             # Timeout in seconds for receiving a message in blocking mode
PING_INTERVAL = 20          # The Ping is sent every these seconds. It helps keeping the connection open (default: 20).
PING_TIMEOUT = None         # If the Pong isn’t received within these seconds, the connection is closed (default: 20; None = disable this behavior).

# SSL-Zertifikat
#
# Zertifikat erstellen:
#   https://blog.miguelgrinberg.com/post/running-your-flask-application-over-https
#   openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
#
# Zertifikat vertrauenswürdig machen:
#   https://www.filoo.de/faq/content/7/82/de/wie-fuege-ich-ein-selbst_signiertes-zertifikat-zum-browser-hinzu.html
#
SSL_CRT = None  # f'{BASE_PATH}/ssl/cert.pem'  # SSL certification file. If no certificate is specified, only an unencrypted connection is possible.
SSL_KEY = None  # f'{BASE_PATH}/ssl/key.pem'   # SSL private key file

PASSWORD_LENGTH = 6         # Minimum length of user password
# RATE_LIMIT = 0            # Maximum number of API requests per minute a new user can make (0 == no rate limit)

# GPU
MIXED_PRECISION = False     # Nvidia GPUs with compute capability of at least 7.0 run quickly with mixed_float16.

# --------------
# Heuristik
# --------------

PARTITIONS_MAXLEN = 2000    # Maximale Anzahl mögliche Partitionen, die pro Hand berechnet werden
TICHU_QUALITY = (0.6, 0.7)  # Mindestwert für die Güte bei der Tichu-Ansage (kleines, großes)

# --------------
# alpha-zero
# --------------

# NNET
EPOCHS = 10                 # Anzahl Trainings-Epochen
BATCH_SIZE = 16             # Datensätze pro Trainingsschritt (bzw. Validierungs- oder Testschritt)
TRAIN_STEPS = 100           # BATCH_SIZE * TRAIN_STEPS = Anzahl Trainingsdaten pro Epoche
VAL_STEPS = 10              # BATCH_SIZE * VAL_STEPS = Anzahl Validierungsdaten pro Epoche
TEST_STEPS = 10             # BATCH_SIZE * TEST_STEPS = Anzahl Testdaten pro Epoche
SQL_RATE = 0.01             # Anteil Datensätze an, die pro Epoche neu aus der Datenbank abgefragt werden

ACTIVATION = "relu"         # Aktivierungsfunktion (z.B. relu, sigmoid oder tanh)
OPTIMIZER = "adam"          # Optimierer (z.B. rmsprop, adam oder sgd)
LR = 0.001                  # Lernrate für Optimierer (Keras Standardwert für Adam ist 0.001, für SGD ist 0.01)
L2 = 0.01                   # L2-Regularisierungsfaktor  (Keras Standardwert ist 0.01)
DROPOUT = 0.1               # Dropout-Factor
LAYERS = 5                  # Anzahl der Convolution Layers
FILTERS = 512               # Anzahl der Filter pro Convolution Layer
KERNEL_SIZE = 3             # Höhe und Breite eines Convolution Windows
DENSE_UNITS = (1024, 512)   # Größen der Dense-Layer
PATIENCE_STOPPING = -5      # Anzahl Epochen, in welche Loss kleiner werden muss. Ansonsten wird das Training abgebrochen
PATIENCE_REDUCE = 3         # Anzahl Epochen, in welche Loss kleiner werden muss. Ansonsten wird die Lernrate verkleinert.
REDUCE_FACTOR = 1.          # Faktor, mit der die Lernrate während des Trainings verkleinert wird (0 < f < 1)

# MCTS
SIMS = 25                   # Anzahl der MCTS-Simulationen (mind. 2) (25)
CPUCT = 1.                  # Konstante für Polynomial Upper Confidence Tree (Faktor für die Neugierde) (1.)

# Training
ITERATIONS = 1              # Anzahl der Iterationen für ein Training (1000)
SELFPLAY = 10               # Anzahl Selfplay-Spiele pro Iteration für das Sammeln der Trainingsdaten (100)
HISTORY = 20                # Maximale Anzahl Iterationen, dessen Selfplay-Ergebnisse gespeichert werden (20)
COMPARISONS = 40            # Anzahl Vergleichsspiele pro Iteration zur Bewertung, ob das neu trainierte Netz akzeptiert wird (40)
WIN_RATE = 0.6              # Gewinnquote WIN / (WIN + LOST); wenn erreicht, wird das neue Netz akzeptiert (0.6)
TAU = 1.                    # Neugierde während der Erkundungsphase im Selfplay (0 = immer beste Aktion bis inf = zufällige Aktion)
EXPLORING = 15              # Länge der Erkundungsphase (Anzahl der Züge). Danach werden nur noch die besten Aktionen gewählt.
ARENA_WORKER = 1            # Anzahl Prozesse für die Arena
