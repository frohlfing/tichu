import asyncio
import weakref
import uuid
from aiohttp import web
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple, Type

# Vorwärtsdeklarationen für Typ-Annotationen, da sich Klassen gegenseitig referenzieren
class GameEngine: pass
class Player: pass
class Client: pass
class Agent: pass
class GameFactory: pass

# --- Datenklassen für Spielstatus ---





# --- Anpassungen in main ---
async def main():
    factory = GameFactory()
    app = web.Application()
    app['game_factory'] = factory
    app.router.add_get('/ws', websocket_handler)

    # --- Plattformspezifisches Signal Handling ---
    # (Wie gehabt)
    if sys.platform == 'win32':
        signal.signal(signal.SIGINT, lambda s, f: shutdown(factory)) # Factory an shutdown übergeben
        logger.debug("Using signal.signal for SIGINT on Windows.")
    else:
        try:
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                 # Wir brauchen eine Lambda-Funktion, um die Factory zu übergeben
                loop.add_signal_handler(sig, lambda s=sig: shutdown(factory, s))
            logger.debug("Using loop.add_signal_handler for SIGINT and SIGTERM on POSIX.")
        except NotImplementedError:
             logger.warning("loop.add_signal_handler not fully implemented, falling back to signal.signal for SIGINT.")
             signal.signal(signal.SIGINT, lambda s, f: shutdown(factory))

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, config.HOST, config.PORT)

    try:
        await site.start()
        logger.info(f"aiohttp server started on http://{config.HOST}:{config.PORT}")
        logger.info(f"WebSocket available at ws://{config.HOST}:{config.PORT}/ws")
        await asyncio.Event().wait() # Läuft bis shutdown() aktiv wird
    except asyncio.CancelledError:
        logger.debug('Main task cancelled, initiating shutdown sequence.')
    finally:
        logger.info('Shutting down server...')
        # Hier die Factory bitten, alle Spiele zu beenden
        await factory.shutdown()
        # Dann den aiohttp Server stoppen
        await site.stop()
        await runner.cleanup()
        logger.info('Server stopped.')

# --- Anpassung der shutdown Funktion ---
def shutdown(factory: GameFactory, *_args):
    """Initiates server shutdown: stops factory games and cancels tasks."""
    logger.info("Shutdown signal received.")
    # Zuerst Factory bitten, Spiele zu beenden (wird im main finally gemacht)
    # Hier primär Tasks canceln
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    if tasks:
        logger.info(f'Cancelling {len(tasks)} outstanding task{"s" if len(tasks) > 1 else ""}...')
        for task in tasks:
            task.cancel()
    else:
        logger.info('No outstanding tasks to cancel.')
    # Wichtig: Das asyncio.Event().wait() im main muss beendet werden.
    # Das Canceln der Tasks sollte das auslösen, wenn main selbst gecancelt wird.

# (Rest bleibt gleich, z.B. __main__ Block)