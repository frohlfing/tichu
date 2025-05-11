#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ein einfacher Kommandozeilen-WebSocket-Client für den Tichu-Server.

Ermöglicht interaktive Eingabe oder das automatische Abspielen von Testszenarien.
Verwendet aiohttp für die WebSocket-Kommunikation.
"""

import asyncio
import aiohttp
import json
import sys
import argparse
import uuid
from typing import Optional, Dict, Any

# Globale Variable für die aktive WebSocket-Verbindung
ws_connection: Optional[aiohttp.ClientWebSocketResponse] = None
# Eigene Player ID für Reconnects
my_player_id: Optional[str] = None
# Flag für interaktiven Modus
interactive_mode = True
# Dictionary für vordefinierte Testfälle
test_cases: Dict[str, list] = {}


async def receive_messages(ws: aiohttp.ClientWebSocketResponse):
    """ Lauscht kontinuierlich auf Nachrichten vom Server und gibt sie aus. """
    global my_player_id
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            try:
                data = json.loads(msg.data)
                print(f"<<< Empfangen: {json.dumps(data, indent=2, ensure_ascii=False)}")
                # Speichere die Player ID, wenn wir dem Tisch beitreten
                if data.get("type") == "joined_table":
                     payload = data.get("payload", {})
                     received_id = payload.get("playerId")
                     if received_id:
                          my_player_id = received_id
                          print(f"--- Meine Player ID ist jetzt: {my_player_id} ---")
                # TODO: Hier könnte man auf spezifische Nachrichten reagieren
                #       z.B. auf "request_action" im automatischen Modus antworten
            except json.JSONDecodeError:
                print(f"<<< Empfangen (kein JSON): {msg.data}")
            except Exception as e:
                 print(f"<<< Fehler beim Verarbeiten der empfangenen Nachricht: {e}")
                 print(f"    Nachricht war: {msg.data}")
        elif msg.type == aiohttp.WSMsgType.CLOSED:
            print("<<< Verbindung vom Server geschlossen.")
            break
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print(f"<<< WebSocket Fehler empfangen: {ws.exception()}")
            break
    print("--- Empfangs-Task beendet. ---")


async def send_message(ws: aiohttp.ClientWebSocketResponse, message_data: Dict[str, Any]):
    """ Sendet eine Nachricht als JSON an den Server. """
    try:
        print(f">>> Sende: {json.dumps(message_data, ensure_ascii=False)}")
        await ws.send_json(message_data)
    except Exception as e:
        print(f"!!! Fehler beim Senden: {e}")


async def run_test_case(ws: aiohttp.ClientWebSocketResponse, case_name: str):
    """ Spielt einen vordefinierten Testfall ab. """
    if case_name not in test_cases:
        print(f"!!! Fehler: Testfall '{case_name}' nicht gefunden.")
        return

    print(f"--- Starte Testfall: {case_name} ---")
    steps = test_cases[case_name]
    for step in steps:
        action = step.get("action")
        payload = step.get("payload", {})
        delay = step.get("delay", 0.5) # Standard-Verzögerung zwischen Schritten

        await asyncio.sleep(delay) # Warte kurz

        if action == "send":
            await send_message(ws, {"action": payload.get("message_action"), "payload": payload.get("message_payload", {})})
        elif action == "wait_for_type": # Beispiel für Warten auf Nachricht
            # TODO: Implementiere Logik zum Warten auf eine bestimmte Nachricht
            #       Das ist komplexer, da receive_messages parallel läuft.
            #       Man bräuchte Events oder Queues für die Synchronisation.
            #       Vorerst nur eine Pause.
            wait_time = payload.get("timeout", 5)
            print(f"--- Warte {wait_time}s (Platzhalter für Warten auf Typ '{payload.get('message_type')}') ---")
            await asyncio.sleep(wait_time)
        elif action == "disconnect":
             print(f"--- Trenne Verbindung (Testfall) ---")
             await ws.close()
             break # Testfall beenden nach Disconnect
        else:
            print(f"--- Unbekannte Testfall-Aktion: {action} ---")

    print(f"--- Testfall '{case_name}' beendet. ---")


async def main_client(args):
    """ Hauptfunktion des Clients. """
    global ws_connection, interactive_mode, my_player_id

    # Parameter setzen
    server_url = f"ws://{args.host}:{args.port}/ws"
    player_name = args.name or f"TestClient_{str(uuid.uuid4())[:4]}"
    table_name = args.table
    interactive_mode = not args.non_interactive
    test_case_name = args.testcase
    # Versuche, eine gespeicherte Player ID zu laden (für Reconnect-Tests)
    # TODO: ID persistent speichern/laden (z.B. in einer Datei)
    # my_player_id = load_player_id()

    # URL mit Parametern bauen
    connect_params = f"playerName={player_name}&tableName={table_name}"
    if my_player_id:
        connect_params += f"&playerId={my_player_id}"
    full_url = f"{server_url}?{connect_params}"

    print(f"Verbinde mit {server_url}...")
    print(f"Parameter: Name={player_name}, Tisch={table_name}, ID={my_player_id or '(Neu)'}")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.ws_connect(full_url) as ws:
                print("+++ Verbindung erfolgreich hergestellt! +++")
                ws_connection = ws

                # Starte den Empfangs-Task im Hintergrund
                receive_task = asyncio.create_task(receive_messages(ws))

                print("--- Interaktiver Modus ---")
                print("Gib JSON-Nachrichten ein (z.B. {\"action\":\"start_game\"}) oder 'quit' zum Beenden.")
                while True:
                    try:
                        # Asynchrone Eingabeaufforderung (verhindert Blockieren)
                        loop = asyncio.get_running_loop()
                        user_input = await loop.run_in_executor(None, sys.stdin.readline)
                        user_input = user_input.strip()

                        if not user_input: continue
                        if user_input.lower() == 'quit': break
                        if user_input.lower() == 'disconnect': # Test für Trennung
                             print("--- Trenne Verbindung (manuell) ---")
                             await ws.close()
                             break

                        # Versuche Eingabe als JSON zu parsen
                        try:
                            message_data = json.loads(user_input)
                            if isinstance(message_data, dict):
                                # Erwarte Struktur {"action": ..., "payload": ...} oder setze Defaults
                                action = message_data.get("action")
                                payload = message_data.get("payload", {})
                                if action:
                                     await send_message(ws, {"action": action, "payload": payload})
                                else:
                                     print("!!! Fehler: Nachricht muss ein 'action'-Feld enthalten.")
                            else:
                                print("!!! Fehler: JSON muss ein Objekt sein (z.B. {\"action\":...}).")
                        except json.JSONDecodeError:
                            print("!!! Fehler: Ungültiges JSON. Gib valides JSON ein oder 'quit'.")
                        except Exception as e:
                             print(f"!!! Fehler beim Verarbeiten der Eingabe: {e}")

                    except (EOFError, KeyboardInterrupt):
                        break # Beende bei Strg+D / Strg+C

                # Nach dem Loop (interaktiv/testcase) oder wenn nur gelauscht wurde:
                # Warte, bis der Server die Verbindung schließt oder ein Fehler auftritt
                if not receive_task.done():
                     print("--- Warte auf Ende der Verbindung oder Strg+C ---")
                     await receive_task

        except aiohttp.ClientConnectorError as e:
            print(f"!!! Verbindungsfehler: {e}")
        except Exception as e:
            print(f"!!! Unerwarteter Fehler im Client: {e}")
            import traceback
            traceback.print_exc()
        finally:
            ws_connection = None
            # TODO: Player ID speichern für nächsten Lauf?
            # save_player_id(my_player_id)
            print("--- Client beendet. ---")


# --- Definition der Testfälle ---
def define_test_cases():
    global test_cases
    test_cases = {
        "connect_start": [
            {"action": "wait", "delay": 1}, # Warte kurz nach Verbindung
            {"action": "send", "payload": {"message_action": "start_game", "message_payload": {}}, "delay": 1},
            {"action": "wait", "delay": 8}, # Warte auf künstliches Spielende
            {"action": "send", "payload": {"message_action": "ping", "message_payload": {"data": "test"}}, "delay": 1},
        ],
        "join_full": [ # Annahme: Tisch 'voll' ist schon von 4 anderen Clients belegt
            {"action": "wait", "delay": 1}, # Versuch zu verbinden, sollte fehlschlagen
        ],
        "reconnect_ok": [ # Annahme: Client war vorher verbunden, wurde disconnected, Timer läuft
            {"action": "wait", "delay": 1}, # Verbindet sich wieder
            {"action": "send", "payload": {"message_action": "ping", "message_payload": {"data": "reconnected"}}, "delay": 1},
        ],
        "reconnect_fail_ki": [ # Annahme: Client war vorher verbunden, Timeout ist abgelaufen, KI ist drin
             {"action": "wait", "delay": 1}, # Versuch zu verbinden, sollte fehlschlagen/neuen Slot bekommen?
        ],
        # Füge hier weitere Testfälle hinzu...
        "play_invalid_json": [
            {"action": "wait", "delay": 1},
            {"action": "send_raw", "payload": {"raw_message": "[1, 2, 3]"}}, # Raw senden (andere send_message Variante nötig)
            {"action": "wait", "delay": 2},
            {"action": "send_raw", "payload": {"raw_message": "kein json"}},
        ],

    }

# --- Argument Parser ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tichu WebSocket Test Client")
    parser.add_argument("--host", default="localhost", help="Server Hostname/IP")
    parser.add_argument("--port", type=int, default=8080, help="Server Port")
    parser.add_argument("--table", default="TestTisch1", help="Name des Tisches")
    parser.add_argument("--name", help="Name des Spielers (optional, wird sonst generiert)")
    parser.add_argument("--testcase", help="Name des auszuführenden Testfalls (überschreibt interaktiv)")
    parser.add_argument("--non-interactive", action="store_true", help="Nicht interaktiv, nur verbinden und lauschen (wenn kein Testfall angegeben)")
    args = parser.parse_args()

    # Definiere die Testfälle
    define_test_cases()

    # Starte den Client
    try:
        asyncio.run(main_client(args))
    except KeyboardInterrupt:
        print("\nClient durch Benutzer abgebrochen.")





