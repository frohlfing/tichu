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
from src.lib.errors import ErrorCode
from src.players.peer import Peer


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
        logger.exception(f"[{request.remote}] WebSocket-Handshake fehlgeschlagen: {e}")
        return ws

    # --- 2) Query-String auslesen. ---
    params = request.query  # z.B. ?player_name=Frank&table_name=Tisch1 oder ?session_id=UUID
    remote_addr = request.remote if request.remote else "Unbekannt"  # Client-Adresse
    logger.debug(f"[{remote_addr}] Client verbunden: session_id='{params.get('session_id')}', player_name='{params.get('player_name')}', table_name='{params.get('table_name')}'.")

    # --- 3) Referenz auf die Game-Engine holen, Peer anlegen und der Engine zuordnen. ---
    session_id = params.get("session_id")
    if session_id:
        engine = factory.get_engine_by_session(session_id)
        peer = engine.get_peer_by_session(session_id) if engine else None
        if not peer or not await engine.rejoin_client(peer, websocket=ws):
            error_message = "Session unbekannt."
            logger.warning(f"[{remote_addr}] Verbindung abgelehnt: {error_message} ")
            await ws.close(code=WSCloseCode.POLICY_VIOLATION, message=error_message.encode('utf-8'))
            return ws
        logger.info(f"[{remote_addr}] '{peer.name}' erfolgreich wiederverbunden.")
    else:
        try:
            engine = factory.get_or_create_engine(params.get("table_name"))
            peer = Peer(params.get("player_name"), websocket=ws)
        except ValueError:
            error_message = "Query-Parameter 'player_name' oder 'table_name' fehlerhaft."
            logger.warning(f"[{remote_addr}] Verbindung abgelehnt: {error_message}")
            await ws.close(code=WSCloseCode.POLICY_VIOLATION, message=error_message.encode('utf-8'))
            return ws
        if not await engine.join_client(peer):
            message = f"Kein freier Platz am Tisch '{engine.table_name}'."
            logger.warning(f"[{remote_addr}] Verbindung abgelehnt: {message}")
            await ws.close(code=WSCloseCode.OK, message=message.encode('utf-8'))
            return ws
        logger.info(f"[{remote_addr}] '{peer.name}' am Tisch '{engine.table_name}' beigetreten.")

    # 4) So lange Nachrichten von der WebSocket verarbeiten, bis die Verbindung abbricht oder der Client absichtlich geht.
    try:
        msg: WSMessage
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    if not isinstance(data, dict):
                        logger.warning(f"[{remote_addr}] Ungültiges Nachrichtenformat empfangen: {msg.data}")
                        await peer.error("Ungültiges Nachrichtenformat", ErrorCode.INVALID_MESSAGE, context=msg.data)
                        continue
                    msg_type = data.get("type")  # Nachrichtentyp
                    payload = data.get("payload", {})  # die Nutzdaten
                    logger.debug(f"[{remote_addr}] Nachricht '{msg_type}' empfangen.")
                    if msg_type == "leave":  # der Client verlässt den Tisch.
                        break # aus der Message-Loop springen

                    elif msg_type == "swap_players":  # der Client möchte die Plätze zweier Spieler vertauschen).
                        if not await engine.swap_players(payload.get("player_index_1"), payload.get("player_index_2")):
                            await peer.error("Die Spieler konnten nicht vertauscht werden.", ErrorCode.INVALID_MESSAGE, context=payload)

                    elif msg_type == "start_game":
                        if not await engine.start_game():
                            await peer.error("Es konnte keine neue Partie gestartet werden. Es läuft bereits eine.", ErrorCode.INVALID_MESSAGE, context=payload)

                    elif msg_type == "announce":  # proaktive Tichu-Ansage vom Client
                        if not await engine.set_announcement(peer.priv.player_index):
                            await peer.error("Tichu-Ansage abgelehnt.", ErrorCode.INVALID_ANNOUNCE)

                    elif msg_type == "bomb":  # proaktiver Bombenwurf vom Client
                        await peer.client_bomb(payload.get("cards"))

                    elif msg_type == "response":  # Antwort auf eine vorherige Anfrage
                        await peer.client_response(payload.get("request_id"), payload.get("response_data", {}))

                    else:  # Nachrichtentyp unbekannt
                        logger.error(f"[{remote_addr}] Message-Type '{msg_type}' unbekannt.")
                        await peer.error("Message-Type unbekannt.", ErrorCode.INVALID_MESSAGE, context=msg.data)

                except json.JSONDecodeError:
                    logger.exception(f"[{remote_addr}] Ungültiges JSON: {msg.data}")
                    await peer.error("Ungültiges JSON-Format.", ErrorCode.INVALID_MESSAGE, context=msg.data)

                except Exception as send_e:
                    logger.exception(f"[{remote_addr}] Unerwarteter Fehler. Verarbeitung der Nachricht fehlgeschlagen: {send_e}")
                    await peer.error("Fehler bei der Verarbeitung der Nachricht.", ErrorCode.UNKNOWN_ERROR, context=msg.data)

            elif msg.type == WSMsgType.BINARY:
                logger.warning(f"[{remote_addr}] Unerwartete Binary-Daten empfangen.")

            elif msg.type == WSMsgType.ERROR:
                logger.error(f"[{remote_addr}] WebSocket-Fehler: {ws.exception()}.")
                break

            elif msg.type == WSMsgType.CLOSE:  # der Client hat die Verbindung aktiv geschlossen (normaler Vorgang)
                logger.debug(f"[{remote_addr}] '{peer.name}' hat die Verbindung geschlossen.")
                break
                
    except asyncio.CancelledError:  # der Server wird heruntergefahren (z.B. durch Signal)
        logger.debug(f"[{remote_addr}] Server Shutdown. WebSocket-Handler abgebrochen.")
        raise  # Wichtig: CancelledError weitergeben für sauberes Beenden.
    except Exception as e:  # fängt unerwartete Fehler während der Verbindung oder im Handler ab
        logger.exception(f"[{remote_addr}] Unerwarteter Fehler. WebSocket-Handler abgebrochen: {e}")

    # 5) Bei Verbindungsabbruch etwas warten, vielleicht schlüpft der Client erneut in sein altes Ich. Ansonsten WebSocket-Verbindung serverseitig schließen.
    if ws.closed:  # not peer.is_connected:
        # Verbindungsabbruch
        logger.info(f"[{remote_addr}] Verbindungsabbruch für Spieler '{peer.name}'. Starte Kick-Out-Timer...")
        #await asyncio.sleep(config.KICK_OUT_TIME)
        if await peer.wait_for_reconnect(config.KICK_OUT_TIME):
            logger.info(f"[{remote_addr}] Kick-Out-Timer gestoppt. Spieler '{peer.name}' hat sich wieder verbunden.")
            return ws  # keine weiteren Aufräumarbeiten erforderlich
        else:
            logger.info(f"[{remote_addr}] Kick-Out-Zeit abgelaufen. Spieler '{peer.name}' hat sich nicht wieder verbunden.")
    else:
        # Client will gehen
        try:
            await ws.close(code=WSCloseCode.GOING_AWAY, message="Verbindung wird serverseitig beendet".encode('utf-8'))
        except Exception as close_e:
            logger.exception(f"[{remote_addr}] Unerwarteter Fehler. Verbindung serverseitig unsauber beendet: {close_e}")

    # 6) Wenn es noch menschliche Mitspieler gibt, einen Fallback-Agent einsetzen, ansonst Tisch schließen.
    client_exists = any(isinstance(p, Peer) for p in engine.players if p.session_id != peer.session_id)
    if client_exists:
        if not await engine.leave_client(peer):  # der Fallback-Agent spielt jetzt weiter
            logger.error(f"[{remote_addr}] '{peer.name}' am Tisch `{engine.table_name}` nicht gefunden, verlässt ihn aber.")
    else:
        await factory.remove_engine(engine.table_name)
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

    # Route für das Frontend hinzufügen
    app.router.add_static('/', path=os.path.join(config.BASE_PATH, "web"), name='web_root')

    # Plattformspezifisches Signal-Handling
    # Notwendig, um auf Strg+C (SIGINT) und Terminate-Signale (SIGTERM) zu reagieren und einen geordneten Shutdown einzuleiten.
    if sys.platform == 'win32':
        # Unter Windows wird signal.signal verwendet, da loop.add_signal_handler nicht unterstützt wird.
        # Nur SIGINT (Strg+C) wird zuverlässig unterstützt.
        signal.signal(signal.SIGINT, shutdown) # Registriert die Shutdown-Funktion als Handler
        #logger.debug("Verwende signal.signal für SIGINT unter Windows.")
    else:
        # Unter POSIX-Systemen (Linux, macOS) wird loop.add_signal_handler bevorzugt. Es integriert sich besser in die asyncio Event-Schleife.
        try:
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                # Registriert die Shutdown-Funktion für SIGINT und SIGTERM.
                loop.add_signal_handler(sig, shutdown, sig) # Übergibt Signalnummer an shutdown
            #logger.debug("Verwende loop.add_signal_handler für SIGINT und SIGTERM unter POSIX.")
        except NotImplementedError:
            # Fallback für seltene Fälle, wo add_signal_handler nicht verfügbar ist.
            logger.warning("loop.add_signal_handler nicht implementiert, verwende signal.signal().")
            signal.signal(signal.SIGINT, shutdown)

    # Server starten (mit AppRunner und TCPSite, das bietet mehr Kontrolle)
    runner = AppRunner(app)
    await runner.setup()
    site = TCPSite(runner, args.host, args.port)  # Server an Host und Port aus der Konfiguration binden
    try:
        await site.start()  # startet den Server
        logger.debug(f"Web-App verfügbar unter http://{args.host}:{args.port}/index.html")
        logger.debug(f"WebSocket verfügbar unter ws://{args.host}:{args.port}/ws/")
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
