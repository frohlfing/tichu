import asyncio
import config
import json
import signal
import sys
from aiohttp.web_ws import WebSocketResponse
from aiohttp import web, WSMsgType, WSCloseCode, WSMessage
from json import JSONDecodeError
from src.common.logger import logger
from src.game_factory import GameFactory


def shutdown(*_args):
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    if tasks:
        if len(tasks) == 1:
            logger.info('Cancelling outstanding task...')
        else:
            logger.info(f'Cancelling {len(tasks)} outstanding tasks...')
        for task in tasks:
            task.cancel()


async def websocket_handler(request: web.Request) -> WebSocketResponse | None:
    """
    Verarbeitet eingehende WebSocket-Verbindungen mit aiohttp.
    """
    # WebSocketResponse-Objekt erstellen
    ws = web.WebSocketResponse()

    # Vorbereitung der WebSocket-Verbindung (Handshake)
    await ws.prepare(request)

    # Zugriff auf die GameFactory über den App-Kontext
    factory: GameFactory = request.app['game_factory']

    # Zugriff auf die Query-Parameter über das request-Objekt
    params = request.query
    remote_addr = request.remote # Client-Adresse für Logging
    logger.info(f"WebSocket connection established from {remote_addr}")
    logger.debug(f"Request Parameters: {params}")

    # --- Hier könntest du Logik hinzufügen, um den Spieler anhand der Params zu identifizieren/registrieren ---
    # player_id = params.get('player_id') or str(uuid.uuid4()) # Beispiel
    # await factory.register_player(player_id, ws) # Beispielhafte Registrierung

    try:
        # Asynchron über eingehende Nachrichten iterieren
        msg: WSMessage
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                logger.debug(f"Received TEXT from {remote_addr}: {msg.data}")
                try:
                    # Nachricht als JSON parsen
                    data = json.loads(msg.data)
                    logger.debug(f"Parsed JSON data: {data}")

                    # --- Hier deine Logik zur Verarbeitung der Nachricht 'data' ---
                    # Beispiel: Verwende die factory, um die Aktion zu verarbeiten
                    # response_data = await factory.handle_action(player_id, data)

                    # ---- Dein bisheriger Beispiel-Code ----
                    # Sendet eine Nachricht über die Websocket an den Benutzer
                    response_data = "Pong" # Platzhalter - ersetze dies durch deine echte Antwort
                    # ---- Ende Beispiel-Code ----

                    # Sende die Antwort als JSON zurück
                    if response_data is not None:
                        await ws.send_json(response_data)
                        logger.debug(f"Sending JSON to {remote_addr}: {response_data}")

                except JSONDecodeError:
                    logger.error(f"Invalid JSON received from {remote_addr}: {msg.data}")
                    await ws.send_json({"error": "Invalid JSON format"})
                except Exception as e:
                    logger.exception(f"Error processing message from {remote_addr}: {e}")
                    # Sende eine generische Fehlermeldung an den Client
                    try:
                        await ws.send_json({"error": "Error processing message"})
                    except Exception as send_e:
                        logger.error(f"Failed to send error message to {remote_addr}: {send_e}")

            elif msg.type == WSMsgType.BINARY:
                logger.warning(f"Received unexpected BINARY data from {remote_addr}")
                # Ignorieren oder behandeln, falls binäre Nachrichten erwartet werden

            elif msg.type == WSMsgType.ERROR:
                logger.error(f'WebSocket connection closed with exception {ws.exception()} for {remote_addr}')

            elif msg.type == WSMsgType.CLOSE:
                 logger.info(f"WebSocket CLOSE message received from {remote_addr}")
                 # Client hat die Schließung initiiert

    except asyncio.CancelledError:
        logger.info(f"WebSocket handler for {remote_addr} cancelled.")
        raise # Wichtig, damit der Abbruch weitergereicht wird
    except Exception as e:
        # Fängt unerwartete Fehler während der Verbindung ab
        logger.exception(f"Unexpected error in WebSocket handler for {remote_addr}: {e}")
    finally:
        # Wird immer ausgeführt, wenn die Verbindung endet (normal, Fehler, Abbruch)
        logger.info(f"WebSocket connection closing for {remote_addr}")
        # --- Hier Aufräumarbeiten durchführen ---
        # Beispiel: Spieler aus dem Spiel entfernen
        # await factory.unregister_player(player_id, ws)

        # Sicherstellen, dass der WebSocket serverseitig geschlossen ist
        # Ist nicht unbedingt nötig wenn der Loop normal endet, aber sicher ist sicher
        if not ws.closed:
             await ws.close(code=WSCloseCode.GOING_AWAY, message=b'Server shutdown or client disconnect')
        logger.info(f"WebSocket connection definitively closed for {remote_addr}")

    # Wichtig: Das WebSocketResponse-Objekt zurückgeben
    return ws


async def main():
    # aiohttp Anwendung erstellen
    app = web.Application()

    # GameFactory Instanz erstellen und im App-Kontext speichern, damit Handler darauf zugreifen können
    factory = GameFactory()
    app['game_factory'] = factory

    # Route für den WebSocket-Endpunkt hinzufügen (z.B. /ws)
    app.router.add_get('/ws', websocket_handler) # Passe '/ws' an, falls ein anderer Pfad benötigt wird

    # --- Plattformspezifisches Signal Handling ---
    if sys.platform == 'win32':
        # Unter Windows: Verwende signal.signal für SIGINT (Strg+C)
        # SIGTERM ist hier nicht relevant/zuverlässig
        signal.signal(signal.SIGINT, shutdown)
        logger.debug("Using signal.signal for SIGINT on Windows.")
    else:
        # Unter POSIX (Linux, macOS, RPi): Verwende loop.add_signal_handler
        # SIGINT: Interrupt from keyboard (CTRL+C), SIGTERM: Termination signal
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, shutdown, sig)
        logger.debug("Using loop.add_signal_handler for SIGINT and SIGTERM on POSIX.")

    # Server mit AppRunner und TCPSite starten (mehr Kontrolle über Start/Stop)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, config.HOST, config.PORT)

    try:
        await site.start()
        logger.info(f"aiohttp server started on http://{config.HOST}:{config.PORT}")
        logger.info(f"WebSocket available at ws://{config.HOST}:{config.PORT}/ws") # Pfad angepasst
        # Läuft "ewig" bzw. bis ein Signal empfangen wird
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        logger.debug('Interrupt signal received (e.g., CTRL-C)')
        # Der finally Block wird für das Cleanup sorgen
    finally:
        logger.info('Shutting down server...')
        # Korrektes Herunterfahren des Servers
        await site.stop() # Stoppt das Lauschen auf neue Verbindungen
        await runner.cleanup() # Räumt die App und Verbindungen auf
        logger.info('Server stopped.')


if __name__ == "__main__":
    # Stelle sicher, dass aiohttp installiert ist: pip install aiohttp
    try:
       asyncio.run(main(), debug=config.DEBUG)
    except KeyboardInterrupt:
       # Wird normalerweise durch den Signal-Handler abgefangen,
       # aber sicher ist sicher - falls etwas schiefgeht.
       logger.info("KeyboardInterrupt caught in __main__")
