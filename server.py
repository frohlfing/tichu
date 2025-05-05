#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Haupt-Server-Skript für die Tichu Webanwendung.

Startet einen aiohttp-Server, der einen WebSocket-Endpunkt bereitstellt,
über den Clients (Spieler) mit dem Spiel interagieren können.
Verwaltet den Server-Lebenszyklus und Signal-Handling für sauberes Beenden.
"""

import asyncio
import config
import json
import os
import signal
import sys
from aiohttp import web, WSMsgType, WSCloseCode, WSMessage
from src.common.logger import logger  # Eigenes Logger-Modul
from src.game_engine2 import GameEngine  # Spiel-Logik-Klasse
from src.game_factory import GameFactory  # Verwaltung der Spiele
from src.players.client import Client  # Spieler-Repräsentation (Mensch)
from typing import Optional


async def websocket_handler(request: web.Request) -> web.WebSocketResponse | None:
    """
    Behandelt eingehende WebSocket-Verbindungen.

    Aufgaben des Händlers:
    - Verbindung aufbauen.
    - Die Verbindungsanfrage an factory.handle_connection_request übergeben.
    - Bei Erfolg dei Nachrichtenschleife starten.
    - Eingehende Nachrichten (die Antworten auf Anfragen sind) an den Client weiterleiten.
    - Eingehende Nachrichten (die proaktive Aktionen sind) an die Engine weiterleiten.
    - Die Factory über den Verbindungsabbruch informieren.

    :param request: Das aiohttp Request-Objekt, das die initiale HTTP-Anfrage enthält.
    :type request: web.Request
    :return: Das aiohttp WebSocketResponse-Objekt, das die Verbindung repräsentiert.
    :rtype: web.WebSocketResponse
    """
    ws = web.WebSocketResponse()
    try:
        # prepare() führt den WebSocket-Handshake durch.
        # Kann Exceptions werfen, z.B. bei Handshake-Fehlern.
        await ws.prepare(request)
    except Exception as e:
        # Loggen des Fehlers, wenn der Handshake fehlschlägt.
        logger.exception(f"WebSocket Handshake fehlgeschlagen für {request.remote}: {e}")
        return ws  # Rückgabe des ws-Objekts ist notwendig, auch wenn prepare fehlschlägt.

    # Zugriff auf die zentrale GameFactory über den App-Kontext.
    factory: GameFactory = request.app['game_factory']
    # Query-Parameter aus der Verbindungs-URL extrahieren.
    params = request.query  # z.B. ?playerName=Frank&tableName=Tisch1[&playerId=UUID...]
    # Client-Adresse für Logging. request.remote ist hier verfügbar.
    remote_addr = request.remote
    logger.info(f"WebSocket Verbindung hergestellt von {remote_addr} mit Parametern: {params}")

    client: Optional[Client] = None
    engine: Optional[GameEngine] = None

    try:
        # Die Factory verarbeitet die Logik für Beitritt/Reconnect.
        client, engine = await factory.handle_connection_request(ws, dict(params), remote_addr)

        # Wenn die Factory None zurückgibt, wurde die Verbindung abgelehnt.
        if client is None or engine is None:
            logger.warning(f"Verbindung von {remote_addr} wurde von der Factory abgelehnt oder konnte nicht zugeordnet werden.")
            # Die Factory sollte ws bereits geschlossen haben, aber zur Sicherheit prüfen.
            if not ws.closed:
                await ws.close(code=WSCloseCode.ABNORMAL_CLOSURE, message="Verbindung abgelehnt".encode('utf-8'))
            return ws  # Handler beenden.

        # Erfolgreich verbunden und zugeordnet.
        logger.info(f"Handler: Client {client.player_name} ({client.player_id}) erfolgreich Tisch '{engine.table_name}' zugeordnet.")

        # Haupt-Nachrichtenschleife: Warten auf und Verarbeiten von Client-Nachrichten.
        msg: WSMessage
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                # Ignoriere Nachrichten, wenn der Client intern bereits als getrennt markiert ist.
                if not client.is_connected:
                    logger.warning(f"Handler: Nachricht von {client.player_name} empfangen, obwohl intern als disconnected markiert.")
                    break  # Schleife verlassen -> finally wird ausgeführt.
                try:
                    # Versuche, die Textnachricht als JSON zu parsen.
                    data = json.loads(msg.data)
                    logger.debug(f"Empfangen TEXT von {client.player_name}: {data}") # Log nach erfolgreichem Parsen
                    # Leite die geparsten Daten zur Verarbeitung an die GameEngine weiter.
                    await engine.handle_player_message(client, data)
                except json.JSONDecodeError:
                    # Fehler beim Parsen von JSON. Informiere Client.
                    logger.exception(f"Ungültiges JSON von {client.player_name}: {msg.data}")
                    try:
                        await client.notify("error", {"message": "Ungültiges JSON Format"})
                    except Exception as e:
                        logger.exception(f"Fehler beim Senden der Fehlermeldung ab {client.player_name}: {e}")
                except Exception as send_e:
                    logger.exception(f"Fehler bei Verarbeitung der Nachricht von {client.player_name}: {send_e}")
                    try:
                        # Sende generische Fehlermeldung an Client.
                        await client.notify("error", {"message": "Fehler bei Verarbeitung Ihrer Anfrage."})
                    except Exception as send_e:
                        # Fehler beim Senden der Fehlermeldung loggen.
                        logger.exception(f"Senden der Fehlermeldung an {client.player_name} fehlgeschlagen: {send_e}")

            elif msg.type == WSMsgType.BINARY:
                # Binäre Nachrichten werden aktuell nicht erwartet.
                logger.warning(f"Empfangen unerwartete BINARY Daten von {client.player_name or remote_addr}")
                # Ignorieren oder spezifische Logik hinzufügen, falls benötigt.

            elif msg.type == WSMsgType.ERROR:
                # aiohttp meldet einen internen WebSocket-Fehler.
                logger.error(f'WebSocket Fehler für {client.player_name or "unbekannt"}: {ws.exception()}')
                break  # Schleife verlassen -> finally wird ausgeführt.

            elif msg.type == WSMsgType.CLOSE:
                # Der Client hat die Verbindung aktiv geschlossen (normaler Vorgang).
                logger.info(f"WebSocket CLOSE Nachricht von {client.player_name or 'unbekannt'} empfangen.")
                break  # Schleife verlassen -> finally wird ausgeführt.

    except asyncio.CancelledError:
        # Der Server wird heruntergefahren (z.B. durch Signal).
        client_name_log = client.player_name if client else remote_addr
        logger.info(f"WebSocket Handler für {client_name_log} abgebrochen (Server Shutdown).")
        raise  # Wichtig: CancelledError weitergeben für sauberes Beenden.
    except Exception as e:
        # Fängt unerwartete Fehler während der Verbindung oder im Handler ab.
        client_name_log = client.player_name if client else "unbekannt"
        logger.exception(f"Unerwarteter Fehler im WebSocket Handler für {client_name_log} von {remote_addr}: {e}")
    finally:
        # Dieser Block wird immer ausgeführt, wenn der Handler endet
        # (durch normalen Close, Fehler, CancelledError, etc.).
        client_name_log = client.player_name if client else 'N/A'
        client_id_log = client.player_id if client else 'N/A'
        table_name_log = engine.table_name if engine else 'N/A'
        logger.info(f"WebSocket Verbindung schließt für {client_name_log} ({client_id_log}) von {remote_addr}, Tisch: '{table_name_log}'")

        # Informiere die Factory über den Disconnect, damit der Timer gestartet werden kann.
        # Dies geschieht nur, wenn Client und Engine erfolgreich initialisiert wurden.
        if client and engine:
            # Ruft die synchrone Methode in der Factory auf.
            factory.notify_player_disconnect(engine.table_name, client.player_id, client.player_name)
        # else: # Optional: Loggen, wenn Client/Engine nicht vorhanden waren
        #    if not client: logger.debug(f"Kein Client-Objekt im finally-Block für {remote_addr} vorhanden.")
        #    if not engine: logger.debug(f"Keine Engine-Referenz im finally-Block für {remote_addr} vorhanden.")

        # Sicherstellen, dass die WebSocket-Verbindung serverseitig geschlossen ist.
        if not ws.closed:
            logger.debug(f"Stelle sicher, dass WebSocket für {remote_addr} im finally Block geschlossen wird.")
            try:
                await ws.close(code=WSCloseCode.GOING_AWAY, message="Verbindung wird serverseitig beendet".encode('utf-8'))
            except Exception as close_e:
                logger.warning(f"Fehler beim expliziten Schließen des WebSockets für {remote_addr}: {close_e}")
        logger.info(f"WebSocket Verbindung definitiv geschlossen für {remote_addr}")

    return ws


async def main():
    """
    Haupt-Einstiegspunkt zum Starten des aiohttp Servers.

    Erstellt die aiohttp-Anwendung, initialisiert die GameFactory,
    richtet Routen und Signal-Handler ein und startet den Server.
    Hält den Server am Laufen, bis ein Shutdown-Signal empfangen wird.
    """
    # aiohttp Anwendung erstellen.
    app = web.Application()

    # GameFactory Instanz erstellen und im App-Kontext speichern.
    # Dadurch ist sie für Handler über request.app['game_factory'] zugänglich.
    factory = GameFactory()
    app['game_factory'] = factory

    # Route für den WebSocket-Endpunkt '/ws' hinzufügen und mit dem Handler verknüpfen.
    app.router.add_get('/ws', websocket_handler)

    # --- Plattformspezifisches Signal Handling ---
    # Notwendig, um auf Strg+C (SIGINT) und Terminate-Signale (SIGTERM) zu reagieren
    # und einen geordneten Shutdown einzuleiten.
    if sys.platform == 'win32':
        # Unter Windows wird signal.signal verwendet, da loop.add_signal_handler nicht unterstützt wird.
        # Nur SIGINT (Strg+C) wird zuverlässig unterstützt.
        signal.signal(signal.SIGINT, shutdown) # Registriert die shutdown Funktion als Handler
        logger.debug("Signal-Handler: Verwende signal.signal für SIGINT unter Windows.")
    else:
        # Unter POSIX-Systemen (Linux, macOS) wird loop.add_signal_handler bevorzugt.
        # Es integriert sich besser in die asyncio Event-Schleife.
        try:
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                # Registriert die shutdown Funktion für SIGINT und SIGTERM.
                loop.add_signal_handler(sig, shutdown, sig) # Übergibt Signalnummer an shutdown
            logger.debug("Signal-Handler: Verwende loop.add_signal_handler für SIGINT und SIGTERM unter POSIX.")
        except NotImplementedError:
            # Fallback für seltene Fälle, wo add_signal_handler nicht verfügbar ist.
            logger.warning("Signal-Handler: loop.add_signal_handler nicht implementiert, falle zurück auf signal.signal für SIGINT.")
            signal.signal(signal.SIGINT, shutdown)

    # Server mit AppRunner und TCPSite starten für mehr Kontrolle.
    runner = web.AppRunner(app)
    await runner.setup()
    # Server an Host und Port aus der Konfiguration binden.
    site = web.TCPSite(runner, config.HOST, config.PORT)

    try:
        # Starte den Server und beginne, auf Verbindungen zu lauschen.
        await site.start()
        logger.info(f"aiohttp Server gestartet auf http://{config.HOST}:{config.PORT}")
        logger.info(f"WebSocket verfügbar unter ws://{config.HOST}:{config.PORT}/ws")
        # Hält den Haupt-Task am Laufen, bis ein Ereignis (z.B. CancelledError durch shutdown) eintritt.
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        # Wird ausgelöst, wenn shutdown() die Tasks abbricht.
        logger.info("Haupt-Task abgebrochen, beginne Shutdown-Sequenz.")
    finally:
        # Wird immer ausgeführt, auch bei Fehlern oder Abbruch.
        logger.info("Fahre Server herunter...")
        # Führe zuerst den Shutdown der Factory aus (bricht Timer ab, räumt Engines auf).
        await factory.shutdown()
        # Stoppe dann den aiohttp Listener (nimmt keine neuen Verbindungen mehr an).
        await site.stop()
        # Räume die aiohttp AppRunner Ressourcen auf.
        await runner.cleanup()
        logger.info("Server erfolgreich heruntergefahren.")


def shutdown(*_args):
    """
    Leitet den Server-Shutdown ein, indem laufende asyncio-Tasks abgebrochen werden.

    Diese Funktion wird durch die Signal-Handler (SIGINT/SIGTERM) aufgerufen.
    Das Abbrechen der Tasks führt dazu, dass `asyncio.Event().wait()` in `main`
    eine `CancelledError` auslöst, was den `finally`-Block für das
    geordnete Herunterfahren aktiviert.

    :param _args: Akzeptiert variable Argumente (z.B. Signalnummer), die aber nicht verwendet werden.
    """
    logger.info("Shutdown-Signal empfangen.")
    # Finde alle laufenden Tasks außer dem aktuellen Task (dem shutdown-Handler selbst).
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    if tasks:
        count = len(tasks)
        logger.info(f'Breche {count} laufende Task{"s" if count > 1 else ""} ab...')
        for task in tasks:
            task.cancel() # Sendet ein CancelledError an den Task.
    else:
        logger.info("Keine laufenden Tasks zum Abbrechen gefunden.")


if __name__ == "__main__":
    # Stellt sicher, dass das Skript nur ausgeführt wird, wenn es direkt gestartet wird.
    # Prüfe, ob aiohttp installiert ist (optional, aber gute Praxis).
    logger.info(f"Starte Tichu Server (PID: {os.getpid()})...") # os importieren
    try:
       asyncio.run(main(), debug=config.DEBUG)
    except KeyboardInterrupt:
       # Fängt Strg+C ab, falls die Signal-Handler aus irgendeinem Grund nicht greifen
       # (sollte unter Windows mit signal.signal passieren).
       logger.info("KeyboardInterrupt im __main__ abgefangen.")
    except Exception as e_top:
        # Fängt alle anderen unerwarteten Fehler beim Start ab.
        logger.exception(f"Unerwarteter Fehler auf Top-Level: {e_top}")
        sys.exit(1) # Beenden mit Fehlercode
    finally:
        logger.info("Server-Prozess beendet.")