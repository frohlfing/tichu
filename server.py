import asyncio
import config
import json
import signal
from json import JSONDecodeError
from src.common.logger import logger
from src.game_factory import GameFactory
from urllib.parse import urlparse, parse_qs
from websockets import ConnectionClosed
from websockets.asyncio.server import serve, ServerConnection


def shutdown(*_args):
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    if tasks:
        if len(tasks) == 1:
            logger.info('Cancelling outstanding task...')
        else:
            logger.info(f'Cancelling {len(tasks)} outstanding tasks...')
        for task in tasks:
            task.cancel()


async def websocket_handler(websocket: ServerConnection, factory: GameFactory) -> None:
    # Wird von der Websocket aufgerufen, wenn eine neue Verbindung aufgebaut wurde
    query = urlparse(websocket.request.path).query
    params = parse_qs(query)
    logger.debug(f"Request Parameters: {params}")

    while True:
        try:
            # auf eine Nachricht warten
            message = await websocket.recv()
            try:
                data = json.loads(message)
            except JSONDecodeError:
                logger.error(f"Invalid Json: {message}")
                continue
            logger.debug(f"Received: {data}")

            # Sendet eine Nachricht über die Websocket an den Benutzer
            data = "Pong"
            try:
                await websocket.send(json.dumps(data))
            except TypeError as e:
                logger.error(f"The data could not be serialized: {e}")
            logger.debug(f"Sending: {data}")

        except ConnectionClosed:
            logger.debug(f"Connection closed.")
            break


async def main():
    # POSIX Signal-Handler einrichten
    signal.signal(signal.SIGINT, shutdown)  # Interrupt from keyboard (CTRL + C)
    signal.signal(signal.SIGTERM, shutdown)  # Termination signal

    factory = GameFactory()

    server = await serve(lambda ws: websocket_handler(ws, factory), config.HOST, config.PORT)
    logger.info(f"WebSocket server started at ws://{config.HOST}:{config.PORT}")

    try:
        await server.wait_closed()
        # await asyncio.gather(
        #     benchmark(),
        #     server.wait_closed(),
        # )
    except asyncio.CancelledError:
        logger.debug('Interrupt CTRL-C')
        pass
    finally:
        logger.info('Process stopped.')


if __name__ == "__main__":
    asyncio.run(main(), debug=config.DEBUG)
