#!/usr/bin/env python

"""
Dieses Modul implementiert den Webserver für Tichu.

**Start des Servers**:
   ```
   python server.py
   ```
"""

import argparse
import asyncio
import config
import json
import os
import signal
import sys
from aiohttp import WSMsgType, WSCloseCode, WSMessage
from aiohttp.web import Application, AppRunner, Request, WebSocketResponse, TCPSite
from src.common.git_utils import get_release
from src.common.logger import logger
from src.game_factory import GameFactory
from src.players.client import Client

async def websocket_handler(request: Request) -> WebSocketResponse | None:
    """
    Behandelt eingehende WebSocket-Verbindungen.

    :param request: Das aiohttp Request-Objekt, das die initiale HTTP-Anfrage enthält.
    :return: Das aiohttp WebSocketResponse-Objekt, das die Verbindung repräsentiert.
    """
    factory: GameFactory = request.app['game_factory']

    # --- 1) WebSocket-Handshake durchführen. ---
    ws = WebSocketResponse()
    try:
        await ws.prepare(request)
    except Exception as e:
        logger.exception(f"WebSocket Handshake fehlgeschlagen für {request.remote}: {e}")
        return ws

    # --- 2) Query-String auslesen. ---
    params = request.query  # z.B. ?player_name=Frank&table_name=Tisch1 oder ?session_id=UUID
    remote_addr = request.remote if request.remote else "Unbekannt"  # Client-Adresse
    logger.debug(f"WebSocket Verbindung hergestellt von {remote_addr} mit Parametern: {params}")

    # --- 3) Referenz auf die Game-Engine holen, Client anlegen und der Engine zuordnen. ---
    session_id = params.get("session_id")
    if session_id:
        engine = factory.get_engine_by_session(session_id)
        client = engine.get_player_by_session(session_id) if engine else None
        if isinstance(client, Client) and not client.is_connected:
            client.set_websocket(ws)
        else:
            error_message = "Query-Parameter 'session_id' fehlerhaft."
            logger.warning(f"Verbindung von {remote_addr} abgelehnt. {error_message}")
            await ws.close(code=WSCloseCode.POLICY_VIOLATION, message=error_message.encode('utf-8'))
            return ws
        logger.info(f"Client {client.name} (Session {client.session_id}) erfolgreich wiederverbunden.")
    else:
        try:
            engine = factory.get_or_create_engine(params.get("table_name"))
            client = Client(params.get("player_name"), websocket=ws) if engine else None
        except ValueError:
            error_message = "Query-Parameter 'player_name' oder 'table_name' fehlerhaft."
            logger.warning(f"Verbindung von {remote_addr} abgelehnt. {error_message}")
            await ws.close(code=WSCloseCode.POLICY_VIOLATION, message=error_message.encode('utf-8'))
            return ws
        if not await engine.join_client(client):
            error_message = f"Kein freier Platz am Tisch '{engine.table_name}'."
            logger.warning(f"Verbindung von {remote_addr} abgelehnt. {error_message}")
            await ws.close(code=WSCloseCode.POLICY_VIOLATION, message=error_message.encode('utf-8'))
            return ws
        logger.info(f"Client {client.name} (Session {client.session_id}) erfolgreich am Tisch '{engine.table_name}' mit Sitzplatz {client.index} zugeordnet.")

    # --- 4) Bestätigung an den Client senden. ---
    try:
        await client.on_notify("joined", {
            "player_name": client.name,
            "table_name": engine.table_name,
            "player_index": client.index,
            "session_id": client.session_id,
        })
    except Exception as e:
        logger.warning(f"Senden der Beitrittsbestätigung an {client.name} fehlgeschlagen: {e}.")
        return ws

    # --- 5) So lange Nachrichten von der WebSocket verarbeiten, bis die Verbindung abbricht oder der Client absichtlich geht. ---
    try:
        msg: WSMessage
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:

                # Ignoriere Nachrichten, wenn der Client intern bereits als getrennt markiert ist.
                if not client.is_connected:
                    logger.warning(f"Websocket-Nachricht von {client.name} empfangen, obwohl intern als disconnected markiert.")
                    break  # Schleife verlassen -> finally wird ausgeführt.

                try:
                    # Nachricht laden
                    data = json.loads(msg.data)
                    logger.debug(f"Empfangen TEXT von {client.name}: {data}")
                    if not isinstance(data, dict):
                        logger.warning(f"Handler: Ungültiges Nachrichtenformat (kein dict) von {client.name}: {data}")
                        await client.on_notify("error", {"message": "Ungültiges Nachrichtenformat."})
                        continue
                    msg_type = data.get("type")  # Nachrichtentyp
                    payload = data.get("payload", {})  # Die Nutzdaten

                    # Nachricht weiterdelegieren
                    if msg_type == "leave":  # Client verlässt den Tisch
                        break # aus der Message-Loop springen

                    elif msg_type == "ping":  # Verbindungstest
                        logger.info(f"{client.name}: ping")
                        await client.on_notify("pong", payload)

                    elif msg_type == "interrupt":  # explizite Interrupt-Anfrage
                        await engine.on_interrupt(client, payload.get("reason"))

                    elif msg_type == "response":  # Antwort auf eine vorherige Anfrage (die mittels _ask() gestellt wurde)
                        await client.on_websocket_response(payload.get("action"), payload.get("data", {}))

                    else:
                        logger.error(f"Message-Type '{msg_type}' nicht erwartet")
                        await client.on_notify("error", {"message": "Invalide Daten."})

                except json.JSONDecodeError:
                    logger.exception(f"Ungültiges JSON von {client.name}: {msg.data}")
                    await client.on_notify("error", {"message": "Ungültiges JSON-Format"})

                except Exception as send_e:
                    logger.exception(f"Fehler bei Verarbeitung der Nachricht von {client.name}: {send_e}")
                    await client.on_notify("error", {"message": "Fehler bei der Verarbeitung der Anfrage."})

            elif msg.type == WSMsgType.BINARY:
                logger.warning(f"Empfangen unerwartete Binary-Daten von {client.name}")

            elif msg.type == WSMsgType.ERROR:
                logger.error(f'WebSocket-Fehler für {client.name}: {ws.exception()}')
                break

            elif msg.type == WSMsgType.CLOSE:  # der Client hat die Verbindung aktiv geschlossen (normaler Vorgang)
                logger.debuf(f"WebSocket-CLOSE Nachricht von {client.name} empfangen.")
                break
                
    except asyncio.CancelledError:  # der Server wird heruntergefahren (z.B. durch Signal)
        client_name_log = client.name if client else remote_addr
        logger.debug(f"WebSocket Handler für {client_name_log} abgebrochen (Server Shutdown).")
        raise  # Wichtig: CancelledError weitergeben für sauberes Beenden.
    except Exception as e:  # fängt unerwartete Fehler während der Verbindung oder im Handler ab
        logger.exception(f"Unerwarteter Fehler in der Nachrichtenschleife für {client.name} von {remote_addr}: {e}")

    # --- 6) Bei Verbindungsabbruch etwas warten, vielleicht schlüpft der Client erneut in sein altes Ich. Ansonsten WebSocket-Verbindung serverseitig schließen. ---
    if not client.is_connected:
        # Verbindungsabbruch
        logger.info(f"{engine.table_name}, Spieler {client.name}: Verbindungsabbruch. Starte Kick-Out-Timer...")
        await asyncio.sleep(config.KICK_OUT_TIME)
        if client.is_connected:
            logger.info(f"{engine.table_name}, Spieler {client.name}: Kick-Out-Zeit abgelaufen. Der Spieler hat sich inzwischen wieder verbunden.")
            return ws  # keine weiteren Aufräumarbeiten erforderlich
        else:
            logger.info(f"{engine.table_name}, Spieler {client.name}: Kick-Out-Zeit abgelaufen. Der Spieler hat sich nicht wieder verbunden.")
    elif not ws.closed:
        # Client will gehen
        try:
            await ws.close(code=WSCloseCode.GOING_AWAY, message="Verbindung wird serverseitig beendet".encode('utf-8'))
        except Exception as close_e:
            logger.exception(f"Fehler beim expliziten Schließen des WebSockets für {remote_addr}: {close_e}")

    # --- 7) Wenn es noch menschliche Mitspieler gibt, einen Fallback-Agent einsetzen, ansonst Tisch schließen. ---
    client_exists = any(isinstance(p, Client) for p in engine.players if p.index != client.index)
    if client_exists:
        try:
            await engine.leave_client(client)  # der Fallback-Agent spielt jetzt weiter
        except ValueError as e:
            logger.error(f"Fehler beim Entfernen des Clients {client.name} aus {engine.table_name}: {e}")
    else:
        await factory.remove_engine(engine.table_name)

    logger.debug(f"{engine.table_name}, Spieler {client.name}: WebSocket geschlossen.")
    return ws


async def main(args: argparse.Namespace):
    """
    Haupt-Einstiegspunkt zum Starten des aiohttp Servers.

    Erstellt die aiohttp-Anwendung, initialisiert die GameFactory,
    richtet Routen und Signal-Handler ein und startet den Server.
    Hält den Server am Laufen, bis ein Shutdown-Signal empfangen wird.
    """
    # aiohttp Anwendung erstellen.
    app = Application()

    # GameFactory-Instanz erstellen und im App-Kontext speichern, damit der Handler darauf zugreifen kann
    factory = GameFactory()
    app['game_factory'] = factory  #

    # Route für den WebSocket-Endpunkt '/ws' hinzufügen und mit dem Handler verknüpfen.
    app.router.add_get('/ws', websocket_handler)

    # Plattformspezifisches Signal-Handling
    # Notwendig, um auf Strg+C (SIGINT) und Terminate-Signale (SIGTERM) zu reagieren und einen geordneten Shutdown einzuleiten.
    if sys.platform == 'win32':
        # Unter Windows wird signal.signal verwendet, da loop.add_signal_handler nicht unterstützt wird.
        # Nur SIGINT (Strg+C) wird zuverlässig unterstützt.
        signal.signal(signal.SIGINT, shutdown) # Registriert die Shutdown-Funktion als Handler
        logger.debug("Signal-Handler: Verwende signal.signal für SIGINT unter Windows.")
    else:
        # Unter POSIX-Systemen (Linux, macOS) wird loop.add_signal_handler bevorzugt. Es integriert sich besser in die asyncio Event-Schleife.
        try:
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                # Registriert die Shutdown-Funktion für SIGINT und SIGTERM.
                loop.add_signal_handler(sig, shutdown, sig) # Übergibt Signalnummer an shutdown
            logger.debug("Signal-Handler: Verwende loop.add_signal_handler für SIGINT und SIGTERM unter POSIX.")
        except NotImplementedError:
            # Fallback für seltene Fälle, wo add_signal_handler nicht verfügbar ist.
            logger.warning("Signal-Handler: loop.add_signal_handler nicht implementiert, falle zurück auf signal.signal für SIGINT.")
            signal.signal(signal.SIGINT, shutdown)

    # Server starten (mit AppRunner und TCPSite, das bietet mehr Kontrolle)
    runner = AppRunner(app)
    await runner.setup()
    site = TCPSite(runner, args.host, args.port)  # Server an Host und Port aus der Konfiguration binden
    try:
        await site.start()  # startet den Server
        logger.debug(f"aiohttp Server gestartet auf http://{args.host}:{args.port}")
        logger.debug(f"WebSocket verfügbar unter ws://{args.host}:{args.port}/ws")
        await asyncio.Event().wait()  # hält den Haupt-Task am Laufen, bis ein Ereignis (z.B. CancelledError durch shutdown) eintritt
    except asyncio.CancelledError:  # wird ausgelöst, wenn shutdown() die Tasks abbricht.
        logger.debug("Haupt-Task abgebrochen, beginne Shutdown-Sequenz.")
    finally:
        logger.debug("Fahre Server herunter...")
        await factory.cleanup()
        await site.stop()  # aiohttp Listener stoppen (nimmt keine neuen Verbindungen mehr an)
        await runner.cleanup()  # aiohttp AppRunner Ressourcen aufräumen
        logger.debug("Server erfolgreich heruntergefahren.")


def shutdown(*_args):
    """
    Bricht laufende asyncio-Tasks ab und löst dadurch ein `CancelledError` aus.

    Diese Funktion wird durch die Signal-Handler (SIGINT/SIGTERM) aufgerufen.
    """
    logger.info("Shutdown-Signal empfangen.")
    # alle laufenden Tasks außer dem aktuellen Task (dem shutdown-Handler) abbrechen
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    if tasks:
        count = len(tasks)
        logger.info(f'Breche {count} laufende Task{"s" if count > 1 else ""} ab...')
        for task in tasks:
            task.cancel() # Sendet ein CancelledError an den Task.


if __name__ == "__main__":
    print(f"Tichu Server {get_release()}")

    # Argumente parsen
    parser = argparse.ArgumentParser(description="Stellt einen Webserver inkl. WebSocket bereit")
    parser.add_argument("-s", "--host", default=config.HOST, help=f"Hostname oder IP-Adresse (Default: {config.HOST})")
    parser.add_argument("-p", "--port", type=int, default=config.PORT, help=f"Port (Default: {config.PORT})")

    # Main-Routine starten
    logger.info(f"Starte Server-Prozess (PID: {os.getpid()})...")
    try:
       asyncio.run(main(parser.parse_args()), debug=config.DEBUG)
    except Exception as e_top:
        logger.exception(f"Unerwarteter Fehler auf Top-Level: {e_top}")
        sys.exit(1) # Beenden mit Fehlercode
    finally:
        logger.debug("Server-Prozess beendet.")
