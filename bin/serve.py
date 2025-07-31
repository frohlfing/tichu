#!/usr/bin/env python

"""
Dieses Skript startet den Webserver.

**Start des Servers**:
   ```
   python server.py
   ```
"""

import argparse
import asyncio
import os
import signal
import sys
from aiohttp.web import Application, AppRunner, TCPSite
from src import config
from src.common.git_utils import get_release
from src.common.logger import logger
from src.game_factory import GameFactory
from src.ws_handler import websocket_handler


def handle_exception(_loop: asyncio.AbstractEventLoop, context: dict):
    """
    Exception-Handler für asyncio-Transportschicht (_ProactorBasePipeTransport auf Windows).

    :param _loop: Asyncio Event Loop
    :param context: Ergänzende Informationen zum Fehler
    :return:
    """
    message = context.get("message")
    exception = context.get("exception")
    if isinstance(exception, ConnectionResetError):
        logger.warning(f"Verbindung durch Client abrupt zurückgesetzt: {message}")
    else:
        logger.error(f"Nicht abgefangener Fehler im asyncio-Loop: {message}", exc_info=exception)


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

    # Setze den benutzerdefinierten Exception-Handler
    loop = asyncio.get_running_loop()
    loop.set_exception_handler(handle_exception)

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
            #loop = asyncio.get_running_loop()
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
    except asyncio.CancelledError:  # wird ausgelöst, wenn shutdown() die Tasks abbricht
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

    Diese Funktion wird durch die Signal-Händler (SIGINT/SIGTERM) aufgerufen.
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
        if config.DEBUG:
            import traceback
            traceback.print_exc()
        sys.exit(1) # Beenden mit Fehlercode
    finally:
        logger.debug("Server-Prozess beendet.")
