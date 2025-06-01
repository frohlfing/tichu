#!/usr/bin/env python

"""
Dieses Modul implementiert einen WebSocket-Client für den Tichu-Server zu Test-Zwecken.

**Start des Clients**:
   ```
   python wsclient.py
   ```
"""

import argparse
import asyncio
import config
from datetime import datetime
import json
import os
import pickle
import sys
from aiohttp import WSMsgType, ClientSession, ClientWebSocketResponse, ClientConnectorError
from src.common.git_utils import get_release
from src.common.logger import logger
from src.lib.errors import ClientDisconnectedError, ErrorCode
from typing import Optional

# Request-ID der letzten Server-Anfrage
last_request_id: Optional[str] = None


def get_session_filename() -> str: # NEU
    """Gibt den vollständigen Pfad zur Session-Datei zurück."""
    return os.path.join(config.DATA_PATH, "session_wsclient.pkl")


def save_session_id(session_id: Optional[str]):
    """Speichert die session_id in der Pickle-Datei."""
    file = get_session_filename()
    try:
        os.makedirs(config.DATA_PATH, exist_ok=True)
        if session_id:
            with open(file, 'wb') as fp:
                # noinspection PyTypeChecker
                pickle.dump(session_id, fp)
        elif os.path.exists(file):
            os.remove(file)
    except IOError as e:
        print(f"Fehler beim Speichern der Session-ID in {file}: {e}")


def load_session_id() -> Optional[str]:
    """Lädt die session_id aus der Pickle-Datei."""
    session_id = None
    file = get_session_filename()
    if os.path.exists(file):
        try:
            with open(file, 'rb') as fp:
                session_id = pickle.load(fp)
        except Exception as e: # Breitere Exception-Palette für Pickle
            print(f"Fehler beim Laden der Session-ID aus {file}: {e}")
    return session_id


async def receive_messages(ws: ClientWebSocketResponse):
    """ Lauscht kontinuierlich auf Nachrichten vom Server und gibt sie aus. """
    global last_request_id

    logger.debug("Starte Empfangs-Task...")

    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            try:
                data = json.loads(msg.data)
                logger.debug(f"Empfangen: {json.dumps(data)}")

                msg_type = data.get("type")
                payload = data.get("payload", {})

                if msg_type == "request":  # Server fordert eine Entscheidung
                    last_request_id = payload.get("request_id", "")
                    action_to_perform = payload.get("action")
                    _public_state = payload.get("public_state", {})
                    _private_state = payload.get("private_state", {})
                    print(f"--- SERVER ANFRAGE ---")
                    print(f"  Aktion angefordert: {action_to_perform}")
                    print(f"  Request ID: {last_request_id}")
                    print(f"  Tipp: Antworte mit: {{\"type\": \"response\", \"payload\": {{\"request_id\": \"{last_request_id}\", \"response_data\": {{...deine Daten...}}}}}}")

                elif msg_type == "notification":  # Server informiert über ein Spielereignis
                    event = payload.get("event")
                    context = payload.get("context", {})
                    print(f"--- SERVER BENACHRICHTIGUNG ---")
                    print(f"  Event: {event}")
                    print(f"  Context: {json.dumps(context)}")
                    if event == "player_joined" and "session_id" in context:
                        session_id = payload.get("session_id")
                        public_state: dict = payload.get("public_state", {})
                        private_state: dict = payload.get("private_state", {})
                        print(f"  Session ID: {session_id}")
                        print(f"  Tischname: {public_state.get('table_name', 'N/A')}, Spieler: {public_state.get('player_names', [])}")
                        print(f"  Dein Spieler-Index: {private_state.get("player_index", "N/A")}")
                        print(f"  Deine Handkarten: {private_state.get('hand_cards', 'N/A')}")
                        # neue Session-ID speichern
                        save_session_id(session_id)

                elif msg_type == "error":  # Fehlermeldung vom Server
                    error_message = payload.get("message")
                    error_code = payload.get("code")
                    error_context = payload.get("context", {})
                    print(f"--- SERVER FEHLER (ERROR) ---")
                    print(f"  Fehlercode: {error_code}")
                    print(f"  Nachricht: {error_message}")
                    if error_context:
                        print(f"  Context: {json.dumps(error_context)}")
                    if error_code in (ErrorCode.SESSION_EXPIRED, ErrorCode.SESSION_NOT_FOUND):
                        save_session_id(None)
                        print(f"Session gelöscht")

                elif msg_type == "pong":  # Antwort vom Server auf eine ping-Nachricht
                    timestamp = payload.get("timestamp")
                    print(f"--- PONG ---")
                    print(f"  Timestamp: {timestamp}")

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
    global last_request_id

    # URL zusammenbauen
    if args.session_id:
        url = f"ws://{args.host}:{args.port}/ws?session_id={args.session_id}"
    else:
        url = f"ws://{args.host}:{args.port}/ws?player_name={args.name}&table_name={args.table}"

    example_messages = [
        # Proaktive Nachrichten vom Spieler
        {"type": "leave"},
        {"type": "ping", "payload": {"timestamp": "<timestamp>"}},
        {"type": "lobby_action", "payload": {"action": "assign_team", "data": [3,0,2,1]}},
        {"type": "lobby_action", "payload": {"action": "start_game"}},
        {"type": "announce"},
        {"type": "bomb", "payload": {"cards": [(2,1), (2,2), (2,3), (2,4)]}},


        # Antworten von Server-Anfragen
        # announce_grand_tichu
        {"type": "response", "payload": {"request_id": "<request_id>", "response_data": {"announced": False}}},
        {"type": "response", "payload": {"request_id": "<request_id>", "response_data": {"announced": True}}},
        # schupf
        {"type": "response", "payload": {"request_id": "<request_id>", "response_data": {"to_opponent_right": (2,1), "to_partner": (2,2), "to_opponent_left": (2,3)}}},
        # play
        {"type": "response", "payload": {"request_id": "<request_id>", "response_data": {"cards": [(2,1),(9,3)]}}},
        # wish
        {"type": "response", "payload": {"request_id": "<request_id>", "response_data": {"wish_value": 8}}},
        # give_dragon_away
        {"type": "response", "payload": {"request_id": "<request_id>", "response_data": {"player_index": 2}}},
    ]

    async with ClientSession() as http:
        try:
            # mit der Websocket verbinden
            logger.debug(f"Verbinde mit {url}...")
            async with http.ws_connect(url) as ws:
                logger.debug("Verbindung erfolgreich hergestellt!")

                receive_task = asyncio.create_task(receive_messages(ws))

                print("Nummer der Nachricht oder JSON eingeben:")
                for i, msg_template in enumerate(example_messages):
                    print(f"   {i}:\t{json.dumps(msg_template)}")
                print("disc\tVerbindungsabbruch simulieren ")
                print("quit\tText-Client beenden")

                while True:
                    # asynchrone Eingabeaufforderung (verhindert Blockieren)
                    print("Test Client> ", end="")
                    cmd = await asyncio.to_thread(sys.stdin.readline)

                    # Eingabedaten auswerten
                    cmd = cmd.strip()
                    if not cmd:
                        continue
                    if cmd.lower() == 'disc':
                        raise ClientDisconnectedError("Verbindungsabbruch simuliert")
                    if cmd.lower() == 'quit':
                        save_session_id(None)  # Session löschen
                        break

                    if cmd.strip().isdigit():
                        try:
                            msg_index = int(cmd)
                            if msg_index < 0 or msg_index >= len(example_messages):
                                print(f"Ungültige Nummer. Bitte zwischen 0 und {len(example_messages) - 1} wählen.")
                                continue

                            msg_to_send: dict = example_messages[msg_index].copy()  # Kopie, damit wir Payload ändern können
                            if msg_to_send is None:
                                continue
                            if "payload" not in msg_to_send:
                                msg_to_send["payload"] = {}

                            elif msg_to_send.get("type") == "ping":
                                msg_to_send["payload"]["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

                            elif msg_to_send.get("type") == "response":
                                if last_request_id:
                                    msg_to_send["payload"]["request_id"] = last_request_id
                                else:
                                    print("Keine aktive request_id für die Response-Nachricht vorhanden.")
                                    continue

                        except ValueError:
                            print("Ungültige Eingabe für Nummer.")
                            continue
                    else:
                        try:
                            msg_to_send  = json.loads(cmd)
                        except json.JSONDecodeError:
                            print("Ungültiges JSON. Gib valides JSON oder eine Nummer ein.")
                            continue

                    # WebSocket-Nachricht an den Server senden
                    if msg_to_send:
                        try:
                            logger.debug(f"Sende: {json.dumps(msg_to_send)}")
                            await ws.send_json(msg_to_send)
                        except Exception as e:
                            logger.exception(f"Fehler beim Senden: {e}")
                            if ws.closed:
                                print("Verbindung ist geschlossen. Senden nicht möglich.")
                                break  # Schleife verlassen, da keine Kommunikation mehr möglich

                # Warte, bis der Server die Verbindung schließt oder ein Fehler auftritt
                if not receive_task.done():
                    receive_task.cancel()
                    try:
                        print("Warte auf Ende des Empfangs-Tasks...")
                        await asyncio.wait_for(receive_task, timeout=2.0)  # kurzer Timeout
                    except asyncio.CancelledError:
                        logger.debug("Empfangs-Task erfolgreich abgebrochen.")
                    except asyncio.TimeoutError:
                        logger.warning("Timeout beim Warten auf Abbruch des Empfangs-Tasks.")
        except KeyboardInterrupt:  # Strg+C
            logger.debug("KeyboardInterrupt")
        except (ClientConnectorError, ClientDisconnectedError) as e:
            print(f"Verbindungsfehler: {e}")
        except Exception as e:
            print(f"Unerwarteter Fehler im Client: {e}")
            import traceback
            traceback.print_exc()
        finally:
            pass


if __name__ == "__main__":
    print(f"Tichu WebSocket-Client {get_release()}")

    sid = load_session_id()

    # Argumente parsen
    parser = argparse.ArgumentParser(description="Verbindet sich zu Testzwecke mit dem Tichu Server")
    parser.add_argument("-i", "--host", default=config.HOST, help=f"Server Hostname oder IP-Adresse (Default: {config.HOST})")
    parser.add_argument("-p", "--port", type=int, default=config.PORT, help=f"Server Port (Default: {config.PORT})")
    parser.add_argument("-n", "--name", default="Anton", help="Name des Spielers (Default: Anton)")
    parser.add_argument("-t", "--table", default="Test", help="Name des Tisches (Default: Test)")
    parser.add_argument("-s", "--session_id", default=sid, help="Session-ID (Default: Letzte gespeicherte Session-ID)")

    # Main-Routine starten
    logger.debug(f"Starte Tichu WebSocket-Client...")
    try:
        asyncio.run(main(parser.parse_args()), debug=config.DEBUG)
    except Exception as e_top:
        logger.exception(f"Unerwarteter Fehler auf Top-Level: {e_top}")
        sys.exit(1)  # Beenden mit Fehlercode
    finally:
        logger.debug("Test-Client beendet.")
