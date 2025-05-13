#!/usr/bin/env python

import argparse
import asyncio
import config
from datetime import datetime
import json
import sys
from aiohttp import WSMsgType, ClientSession, ClientWebSocketResponse, ClientConnectorError

from src.common.git_utils import get_git_tag
from src.common.logger import logger
from src.lib.errors import ClientDisconnectedError
from typing import Optional

# Tichu-Session
session: Optional[str] = None  # todo aus session-Datei laden

async def receive_messages(ws: ClientWebSocketResponse):
    """ Lauscht kontinuierlich auf Nachrichten vom Server und gibt sie aus. """
    global session

    logger.debug("Starte Empfangs-Task...")

    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            try:
                data = json.loads(msg.data)
                logger.debug(f"Empfangen: {json.dumps(data)}")

                msg_type, payload = data.get("type"), data.get("payload", {})
                if msg_type == "joined":
                     session = payload.get("session")
                     print(f"Session: {session}")
                elif msg_type == "action":
                    action = payload.get("action")
                    payload = payload.get("payload")
                    print(f"{action}: {json.dumps(payload)}")

            except json.JSONDecodeError:
                logger.exception(f"Kein JSON empfangen: {msg.data}")

            except Exception as e:
                logger.exception(f"Fehler beim Verarbeiten der empfangenen Nachricht: {e}")

        elif msg.type == WSMsgType.CLOSED:
            logger.debug("Verbindung vom Server geschlossen.")
            break

        elif msg.type == WSMsgType.ERROR:
            logger.error(f"WebSocket Fehler empfangen: {ws.exception()}")
            break

    logger.debug("Empfangs-Task beendet.")


async def main(args: argparse.Namespace):
    # URL zusammenbauen
    global session
    if session:
        url = f"ws://{args.host}:{args.port}/ws?session={session}"
    else:
        url = f"ws://{args.host}:{args.port}/ws?name={args.name}&table={args.table}"

    messages = [
        {"type": "bye"},
        {"type": "ping", "payload": {"timestamp": "<timestamp>"}},
        {"type": "interrupt", "payload": {"reason": "tichu"}},
        {"type": "interrupt", "payload": {"reason": "bomb"}},
        {"type": "request", "payload": {"action": "start"}},
        {"type": "request", "payload": {"action": "play", "data": {"cards": "Dr S9"}}},
    ]

    async with ClientSession() as http:
        try:
            # mit der Websocket verbinden
            logger.debug(f"Verbinde mit {url}...")
            async with http.ws_connect(url) as ws:
                logger.debug("Verbindung erfolgreich hergestellt!")
                # todo session-Datei löschen

                # Empfangs-Task im Hintergrund starten
                receive_task = asyncio.create_task(receive_messages(ws))

                print("Nummer der Nachricht oder JSON eingeben:")
                for i, msg in enumerate(messages):
                    print(f"   {i}:\t{json.dumps(msg)}")
                print("disc\tVerbindungsabbruch simulieren ")
                print("quit\tText-Client beenden")

                while True:
                    # asynchrone Eingabeaufforderung (verhindert Blockieren)
                    print("Test Client> ")
                    cmd = await asyncio.to_thread(sys.stdin.readline)

                    # Eingabedaten auswerten
                    cmd = cmd.strip()
                    if not cmd:
                        continue
                    if cmd.lower() == 'disc':
                        raise ClientDisconnectedError("Verbindungsabbruch simuliert")
                    if cmd.lower() == 'quit':
                        break
                    if cmd.strip().isdigit():
                        msg: dict = messages[int(cmd)]
                        if msg.get("type") == "ping":
                            msg["payload"]["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    else:
                        try:
                            msg = json.loads(cmd)
                        except json.JSONDecodeError:
                            print("Ungültiges JSON. Gib valides JSON ein.")

                    # WebSocket-Nachricht an den Server senden
                    try:
                        logger.debug(f"Sende: {json.dumps(msg)}")
                        await ws.send_json(msg)
                    except Exception as e:
                        logger.exception(f"Fehler beim Senden: {e}")

                # Warte, bis der Server die Verbindung schließt oder ein Fehler auftritt
                if not receive_task.done():
                    receive_task.cancel()
                    print("Warte auf Ende der Verbindung")
                    await receive_task

        except KeyboardInterrupt:  # Strg+C
            logger.debug("KeyboardInterrupt")
        except (ClientConnectorError, ClientDisconnectedError) as e:
            print(f"Verbindungsfehler: {e}")
            # todo session-Datei speichern
        except Exception as e:
            print(f"Unerwarteter Fehler im Client: {e}")
            import traceback
            traceback.print_exc()
        # finally:
        #     pass


if __name__ == "__main__":
    print(f"Tichu WebSocket-Client {get_git_tag().strip("v")}")

    # Argumente parsen
    parser = argparse.ArgumentParser(description="Verbindet sich zu Testzwecke mit dem Tichu Server")
    parser.add_argument("-s", "--host", default=config.HOST, help=f"Server Hostname oder IP-Adresse (Default: {config.HOST})")
    parser.add_argument("-p", "--port", type=int, default=config.PORT, help=f"Server Port (Default: {config.PORT})")
    parser.add_argument("-n", "--name", default="Anton", help="Name des Spielers (Default: Anton)")
    parser.add_argument("-t", "--table", default="Test", help="Name des Tisches (Default: Test)")

    # Main-Routine starten
    logger.debug(f"Starte Tichu WebSocket-Client...")
    try:
        asyncio.run(main(parser.parse_args()), debug=config.DEBUG)
    except Exception as e_top:
        logger.exception(f"Unerwarteter Fehler auf Top-Level: {e_top}")
        sys.exit(1)  # Beenden mit Fehlercode
    finally:
        logger.debug("Test-Client beendet.")


# todo Client wird bei der Eingabe von "quit" noch nicht sauber beendet:
# quit
# Warte auf Ende der Verbindung
# 2025-05-12 00:11:24,412 INFO     Test-Client beendet. (ws-test-client, line 154)
# Traceback (most recent call last):
#   File "C:\Users\frank\Source\PyCharm\tichu\ws-test-client.py", line 149, in <module>
#     asyncio.run(main(), debug=config.DEBUG)
#     ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "C:\Users\frank\AppData\Local\Programs\Python\Python313\Lib\asyncio\runners.py", line 195, in run
#     return runner.run(main)
#            ~~~~~~~~~~^^^^^^
#   File "C:\Users\frank\AppData\Local\Programs\Python\Python313\Lib\asyncio\runners.py", line 118, in run
#     return self._loop.run_until_complete(task)
#            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^
#   File "C:\Users\frank\AppData\Local\Programs\Python\Python313\Lib\asyncio\base_events.py", line 719, in run_until_complete
#     return future.result()
#            ~~~~~~~~~~~~~^^
#   File "C:\Users\frank\Source\PyCharm\tichu\ws-test-client.py", line 131, in main
#     await receive_task
#   File "C:\Users\frank\Source\PyCharm\tichu\ws-test-client.py", line 23, in receive_messages
#     async for msg in ws:
#     ...<26 lines>...
#             break
#   File "C:\Users\frank\Source\PyCharm\tichu\.venv\Lib\site-packages\aiohttp\client_ws.py", line 414, in __anext__
#     msg = await self.receive()
#           ^^^^^^^^^^^^^^^^^^^^
#   File "C:\Users\frank\Source\PyCharm\tichu\.venv\Lib\site-packages\aiohttp\client_ws.py", line 336, in receive
#     msg = await self._reader.read()
#           ^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "aiohttp\\_websocket\\reader_c.py", line 118, in read
#   File "aiohttp\\_websocket\\reader_c.py", line 115, in aiohttp._websocket.reader_c.WebSocketDataQueue.read
# asyncio.exceptions.CancelledError
#
# Process finished with exit code 1
