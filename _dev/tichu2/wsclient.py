import config
import json
from passlib.hash import bcrypt
import ssl
from select import select
from sys import stdin
from time import time
from websocket import WebSocket, WebSocketConnectionClosedException, WebSocketTimeoutException  # , create_connection

path = '/raum1'
username = 'wsclient'


# WebSocket Client starten
def run():

    url = ('wss://' if config.SSL_CRT else 'ws://') + config.HOST + ':' + str(config.WS_PORT)

    if username:
        auth = username + ':' + bcrypt.hash(config.SECRET_KEY + username)
        cookie = 'WS-Auth=' + auth + '; path=/' + ('; secure' if config.SSL_CRT else '')
    else:
        cookie = 'WS-Auth=; path=/; Max-Age=-99999999;'

    # Verbindung aufbauen
    # https://websocket-client.readthedocs.io/en/latest/core.html#websocket._core.create_connection
    # ws = create_connection(
    #     url=url + path,
    #     timeout=config.WS_TIMEOUT,
    #     sslopt={'cert_reqs': ssl.CERT_NONE},
    #     # sslopt={'ssl_version': ssl.PROTOCOL_TLS_SERVER, 'certfile': config.SSL_CRT, 'keyfile': config.SSL_KEY},
    #     cookie=cookie,
    # )
    ws = WebSocket(sslopt={'cert_reqs': ssl.CERT_NONE}, enable_multithread=False)
    ws.connect(url=url + path, cookie=cookie, timeout=config.WS_TIMEOUT)

    time_start = time()
    try:
        # Auf die WELCOME-Message warten
        data = json.loads(ws.recv())
        if 'event' not in data or data['event'] != 'WELCOME':
            raise Exception('Message not expected: ' + json.dumps(data))
        address = data['address']
        connected = data['connected']

        # Auswahl-Menü anzeigen
        print('Options:')
        print('0: Exit')
        for i, dic in enumerate(connected):
            print(f'{i + 1}: Send message to {dic["address"]} ({dic["username"]})')
        print('*: Send a Broadcast message')

        # noinspection PyArgumentList
        ws.settimeout(0.001)  # bei ws.recv() nur noch 1ms warten
        while True:
            # Auf Eingabe warten und Nachricht senden
            # j = input('> ')
            i, o, e = select([stdin], [], [], 0.1)  # 100 ms warten
            if i:
                j = stdin.readline().strip()
                if j == '0':
                    break
                message = {'event': 'CHAT', 'address': address, 'text': 'Hallo'}
                if j.isnumeric() and int(j) - 1 < len(connected):
                    message['to'] = connected[int(j) - 1]['address']
                ws.send(json.dumps(message))

            # Daten empfangen?
            try:
                print(ws.recv())
            except WebSocketTimeoutException:
                pass

    except WebSocketConnectionClosedException:
        print('WebSocketConnectionClosedException')
    except WebSocketTimeoutException:
        print('WebSocketTimeoutException')

    print(f'{(time() - time_start) * 1000:5.3f} ms')


if __name__ == '__main__':
    run()
