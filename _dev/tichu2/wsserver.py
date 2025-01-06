import asyncio
import config
import json
from logging.handlers import RotatingFileHandler
import logging
import signal
import ssl
import sys
import traceback
import websockets
from http.cookies import SimpleCookie
from passlib.hash import bcrypt


# Logging
# https://docs.python.org/3.7/library/logging.html#logging.info
# https://www.pylenin.com/blogs/python-logging-guide/
logging.basicConfig(level=logging.ERROR)
websocket_logger = logging.getLogger('websockets.server')  # see https://websockets.readthedocs.io/en/3.4/api.html
websocket_logger.propagate = config.LOG_SHELL  # Disable propagate to avoid logging to the console.
websocket_logger.setLevel(logging.WARNING)  # To override the default severity of logging
handler = RotatingFileHandler(config.LOG_PATH + '/ws.log', maxBytes=1024 * 1024)  # Use FileHandler() to log to a file
handler.setFormatter(logging.Formatter('%(asctime)s WS %(levelname)-8s %(message)s (%(module)s, line %(lineno)d)'))
websocket_logger.addHandler(handler)
logger = logging.getLogger(__name__)  # Create a logger exclusively for the own modules
logger.propagate = config.LOG_SHELL  # Disable propagate to avoid logging to the console.
logger.setLevel(config.LOG_LEVEL)  # To override the default severity of logging
logger.addHandler(handler)


# Error Handling
def handle_exception(exc_type, exc_value, exc_traceback):
    logger.critical('Uncaught exception: %s\nType: %s\nTraceback:\n%s', exc_value, exc_type, ''.join(traceback.format_tb(exc_traceback)))
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


sys.excepthook = handle_exception


# Abbruch-Routine (Control-C)
async def shutdown(sig: str = None):
    """
    Breche ausstehende Tasks ab
    :param sig: Name of the POSIX Signal
    """
    if sig:
        logger.debug(f'Received {sig}')
    pending = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    if pending:
        if len(pending) == 1:
            logger.debug('Cancelling outstanding task...')
        else:
            logger.debug(f'Cancelling {len(pending)} outstanding tasks...')
        for task in pending:
            task.cancel()
    loop = asyncio.get_event_loop()
    loop.stop()


# Authentifizierung
# https://stackoverflow.com/questions/4361173/http-headers-in-websockets-client-api
def authenticate(websocket: websockets.WebSocketServerProtocol) -> str:
    """
    Determine if current user is authenticated.
    Der Authentication Key (Cookie "WS-Auth") muss wie folgt aufgebaut sein:
        auth = username + ':' + bcrypt.hash(SECRET_KEY + username)
        Hinweis: Ein Doppelpunkt wird nicht in bcrypt verwendet, ist also als Trennzeichen geeignet.
        https://stackoverflow.com/questions/5881169/what-column-type-length-should-i-use-for-storing-a-bcrypt-hashed-password-in-a-d
    :param websocket:
    :return: Username, if user is authenticated
    """
    data = websocket.request_headers.get('Cookie')  # Read cookie "WS-Auth" from request header
    if data:
        cookie = SimpleCookie()
        cookie.load(data)
        auth = cookie.get('WS-Auth')
        if auth and auth.value.find(':') != -1:
            username, key = auth.value.split(':')
            if bcrypt.verify(config.SECRET_KEY + username, key):
                return username
    return ''


# Connection list
connected = {}


async def send(path: str, address: str, message):
    """
    Sende eine private Nachricht.
    :param path:
    :param address: host + ':' + port
    :param message:
    """
    addr = address.rsplit(':', 1)
    addr = (addr[0], int(addr[1])) if len(addr) == 2 and addr[1].isnumeric() else ()
    # noinspection PyUnresolvedReferences
    fs = [to.send(message) for to in connected[path] if to.remote_address == addr and to.state is websockets.protocol.State.OPEN]
    if fs:  # asyncio.wait doesn't accept an empty list
        await asyncio.wait(fs)


async def broadcast(path: str, ws: websockets.WebSocketServerProtocol, message):
    """
    Sende eine öffentliche Nachricht an alle Teilnehmer.
    :param path:
    :param ws: Sender
    :param message:
    """
    # noinspection PyUnresolvedReferences
    fs = [to.send(message) for to in connected[path] if to != ws and to.state is websockets.protocol.State.OPEN]
    if fs:  # asyncio.wait doesn't accept an empty list
        await asyncio.wait(fs)


# WebSocket-Handler
# https://websockets.readthedocs.io
async def websocket_handler(ws: websockets.WebSocketServerProtocol, path: str):
    """
    Bearbeite eingehende WebSocket-Verbindungen.
    :param ws: WebSocketServerProtocol
    :param path: Request URI
    """
    address = f'{ws.remote_address[0]}:{ws.remote_address[1]}'

    # Zugriffskontrolle
    username = authenticate(ws)
    if not username:
        if not config.ANONYMOUS:  # kein anonymer Zugriff erlaubt?
            logger.info('%s: Invalid authentication', address)
            ws.fail_connection(1008, 'Invalid authentication')
            return
        username = 'anonymous'
    if hasattr(websockets.WebSocketServerProtocol, 'username'):
        raise Exception('Property "username" for WebSocket not expected, seems to be new for WebSockets!')
    ws.username = username

    # Verbindung merken
    connected.setdefault(path, set()).add(ws)
    logger.info('%s: Enter (path: %s, user: %s)', address, path, username)
    dic = [{'address': f'{c.remote_address[0]}:{c.remote_address[1]}', 'username': c.username} for c in connected[path]]
    await send(path, address, json.dumps({'event': 'WELCOME', 'address': address, 'connected': dic}))
    await broadcast(path, ws, json.dumps({'event': 'ENTER', 'address': address, 'username': username}))

    # Message-Loop
    try:
        async for message in ws:
            data = json.loads(message)
            if 'to' in data:
                await send(path, data['to'], message)
            else:
                await broadcast(path, ws, message)
    except asyncio.CancelledError:
        logger.debug('CancelledError')
    except websockets.ConnectionClosed:
        if ws.open:
            logger.info('Server closed connection')
            await ws.close()

    # Verbindung vergessen
    connected[path].remove(ws)
    if not connected[path]:
        del connected[path]
    logger.info('%s: Exit', address)
    await broadcast(path, ws, json.dumps({'event': 'EXIT', 'address': address}))


# WebSocket-Server starten
def run():
    # POSIX Signal-Handler einrichten
    # SIGHUP - Hangup detected on controlling terminal or death of controlling process
    # SIGQUIT - Quit from keyboard (via ^\)
    # SIGTERM - Termination signal
    # SIGINT - Interrupt program
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGHUP, signal.SIGQUIT, signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(sig.name)))

    # WebSocket starten
    ssl_context = None
    if config.SSL_CRT:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(certfile=config.SSL_CRT, keyfile=config.SSL_KEY)
    try:
        # https://websockets.readthedocs.io/en/7.0/api.html
        start_server = websockets.serve(
            websocket_handler,
            config.HOST,
            config.WS_PORT,
            ssl=ssl_context,
            ping_interval=config.PING_INTERVAL,
            ping_timeout=config.PING_TIMEOUT)
        loop.run_until_complete(start_server)
        logger.info('Process started.')
        loop.run_forever()
    except asyncio.CancelledError:
        logger.debug('CancelledError')
    finally:
        loop.close()
        logger.info('Process stopped.')


if __name__ == '__main__':
    run()
