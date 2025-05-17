#!/usr/bin/env python

import argparse
import asyncio
import config
from datetime import datetime
import json
import sys
from aiohttp import WSMsgType, ClientSession, ClientWebSocketResponse, ClientConnectorError
from src.common.git_utils import get_release
from src.common.logger import logger
from src.lib.errors import ClientDisconnectedError
from typing import Optional

# Tichu-Session-ID
session_id: Optional[str] = None  # todo aus session-Datei laden

# Request-ID der letzten Server-Anfrage
last_request_id: Optional[str] = None

async def receive_messages(ws: ClientWebSocketResponse):
    """ Lauscht kontinuierlich auf Nachrichten vom Server und gibt sie aus. """
    global session_id, last_request_id

    logger.debug("Starte Empfangs-Task...")

    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            try:
                data = json.loads(msg.data)
                logger.debug(f"Empfangen: {json.dumps(data)}")

                msg_type = data.get("type")
                payload = data.get("payload", {})

                if msg_type == "joined_confirmation":  # Antwort vom Server auf die join-Nachricht
                    session_id = payload.get("session_id")
                    public_state: dict = payload.get("public_state", {})
                    private_state: dict = payload.get("private_state", {})
                    print(f"--- ERFOLGREICH BEIGETRETEN ---")
                    print(f"  Session ID: {session_id}")
                    print(f"  Dein Spieler-Index: {private_state.get("player_index", "N/A")}")
                    print(f"  Öffentlicher Spielstatus (Auszug): Tischname: {public_state.get('table_name', 'N/A')}, Spieler: {public_state.get('player_names', [])}")
                    print(f"  Privater Spielstatus (Auszug): Handkarten: {private_state.get('hand_cards', 'N/A')}")

                elif msg_type == "pong":  # Antwort vom Server auf die ping-Nachricht
                    timestamp = payload.get("timestamp")
                    print(f"--- PONG ---")
                    print(f"  Timestamp: {timestamp}")

                elif msg_type == "request":  # Proaktive Nachrichten vom Server
                    #public_state = payload.get("public_state", {})
                    #private_state = payload.get("private_state", {})
                    request_id = payload.get("request_id", "")
                    last_request_id = request_id
                    action = payload.get("action")
                    print(f"--- SERVER ANFRAGE ---")
                    print(f"  Aktion angefordert: {action}")
                    print(f"  Tipp: Antworte mit: {{\"type\": \"response\", \"payload\": {{\"request_id\": \"{request_id}\", \"data\": {{...deine Daten...}}}}}}")
                    print(f"  Request ID: {request_id}")

                elif msg_type == "notification":  # Benachrichtigung an alle Spieler
                    event = payload.get("event")
                    event_data = payload.get("data", {})
                    print(f"--- SERVER BENACHRICHTIGUNG ---")
                    print(f"  Event: {event}")
                    print(f"  Daten: {json.dumps(event_data)}")

                elif msg_type == "deal_cards":  # Proaktive Nachrichten vom Server
                    hand_cards = payload.get("hand_cards")
                    print(f"--- KARTEN ERHALTEN ({len(hand_cards)}) ---")
                    print(f"  Deine Handkarten: {hand_cards if hand_cards else 'Keine'}")

                elif msg_type == "schupf_cards_received":
                    received = payload.get("received_cards", {})
                    print(f"--- SCHUPF-KARTEN ERHALTEN ---")
                    print(f"  Vom rechten Gegner: {received.get('from_opponent_right', 'N/A')}")
                    print(f"  Vom Partner: {received.get('from_partner', 'N/A')}")
                    print(f"  Vom linken Gegner: {received.get('from_opponent_left', 'N/A')}")

                elif msg_type == "error":
                    error_message = payload.get("message")
                    error_code = payload.get("code")
                    error_details = payload.get("details", {})
                    original_request_id = payload.get("request_id")  # aus der Response-Nachricht
                    print(f"--- SERVER FEHLER (ERROR) ---")
                    print(f"  Fehlercode: {error_code}")
                    print(f"  Nachricht: {error_message}")
                    if original_request_id:
                        print(f"  Bezogen auf Request ID: {original_request_id}")
                    if error_details:
                        print(f"  Details: {json.dumps(error_details)}")

                else:
                    # Fallback für unbekannte Nachrichtentypen vom Server
                    print(f"--- UNBEKANNTE NACHRICHT VOM SERVER ---")
                    print(f"  Typ: {msg_type}")
                    print(f"  Payload: {json.dumps(payload)}")

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
    global session_id
    if session_id:
        url = f"ws://{args.host}:{args.port}/ws?session={session_id}"
    else:
        url = f"ws://{args.host}:{args.port}/ws?name={args.name}&table={args.table}"

    messages = [
        {"type": "leave"},
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
    print(f"Tichu WebSocket-Client {get_release()}")

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
