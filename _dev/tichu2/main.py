import config
import logging
from logging.handlers import RotatingFileHandler
from passlib.hash import bcrypt
from tichu.agents import RandomAgent, HeuristicAgent
from tichu.arena import Arena
from web.database import init_flask_db

# Logging
# https://docs.python.org/3.7/library/logging.html#logging.info
# https://www.pylenin.com/blogs/python-logging-guide/
# logging.debug('This is a debug message!')
# logging.info('This is a info!')
# logging.warning('This is a warning!')
# logging.error('This is a error message!')
# logging.critical('This is a critical error message!')
# Bsp.:
# logging.info(f'Test A: {a}')
# logging.info('Test B: %s', 44)
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)  # Create a logger exclusively for the own modules
logger.propagate = config.LOG_SHELL  # Disable propagate to avoid logging to the console.
logger.setLevel(config.LOG_LEVEL)  # To override the default severity of logging
handler = RotatingFileHandler(config.LOG_PATH + '/app.log', maxBytes=1024 * 1024)  # Use FileHandler() to log to a file
handler.setFormatter(logging.Formatter('%(asctime)s APP %(levelname)-8s %(message)s (%(module)s, line %(lineno)d)'))
logger.addHandler(handler)

# Database
db = init_flask_db()

# WebSocket
# https://websocket-client.readthedocs.io/en/latest/core.html#websocket._core.create_connection
path = '/raum1'
username = 'wsclient'
url = ('wss://' if config.SSL_CRT else 'ws://') + config.HOST + ':' + str(config.WS_PORT)
if username:
    auth = username + ':' + bcrypt.hash(config.SECRET_KEY + username)
    cookie = 'WS-Auth=' + auth + '; path=/' + ('; secure' if config.SSL_CRT else '')
else:
    cookie = 'WS-Auth=; path=/; Max-Age=-99999999;'
# ws = WebSocket(sslopt={'cert_reqs': ssl.CERT_NONE}, enable_multithread=False)
# ws.connect(url=url + path, cookie=cookie, timeout=config.WS_TIMEOUT)


# -------------------------------------------------------------------
# Spiel eröffnen
# -------------------------------------------------------------------

# heuristic_agent = HeuristicAgent()
# random_agent = RandomAgent()

agents = [
    RandomAgent(), # HeuristicAgent(),
    RandomAgent(),
    RandomAgent(),
    RandomAgent(),
]


# Agenten spielen lassen
# episodes: Anzahl Episoden, die gespielt werden sollen. Eine Episode endet, wenn ein Team mind. 1000 Punkte erreicht.
def play(episodes=10, verbose=False):
    print('Los gehts...')
    # logger.debug('Los gehts')

    # Wettkampf durchführen
    arena = Arena(agents=agents, max_episodes=episodes, verbose=verbose)
    wins, lost, draws = arena.play()

    # Ergebnis auswerten
    print(f'Anzahl Worker: {config.ARENA_WORKER}')
    print(f'Anzahl Episoden: {arena.episodes}')
    print(f'Anzahl Runden: {arena.rounds}')
    print(f'Ranking Team A ({agents[0].name}, {agents[2].name}): {wins} - {wins * 100 / episodes:4.1f} %')
    print(f'Ranking Team B ({agents[1].name}, {agents[3].name}): {lost} - {lost * 100 / episodes:4.1f} %')
    print(f'Unentschieden: {draws} - {draws * 100 / episodes:4.1f} %')
    print(f'Gesamtzeit: {arena.seconds:5.3f} s')
    print(f'Zeit/Episode: {arena.seconds / arena.episodes:5.3f} s')
    print(f'Zeit/Runde: {arena.seconds * 1000 / arena.rounds:5.3f} ms')
    print(f'Runden/Episode: {arena.rounds / arena.episodes:2.1f}')
    print(f'Runden/Episode: {arena.rounds / arena.episodes:2.1f}')
    print(f'Stiche/Runde: {arena.tricks / arena.rounds:2.1f}')


if __name__ == '__main__':
    play(10, verbose=True)

# Interpreter-Options, um Asserts zu ignorieren:
# -O
