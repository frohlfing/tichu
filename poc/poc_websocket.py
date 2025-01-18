import asyncio
import config
import json
from json import JSONDecodeError
from src.common.logger import logger
from typing import Any
from websockets import ConnectionClosed
from websockets.asyncio.server import serve, ServerConnection


# noinspection DuplicatedCode
class Client:
    def __init__(self, websocket: ServerConnection) -> None:
        self._websocket = websocket
        self._queue = asyncio.Queue()

    async def message_loop(self) -> None:
        # Wartet auf Websocket-Nachrichten und legt diese in die Queue
        while True:
            try:
                message = await self._websocket.recv()
                try:
                    data = json.loads(message)
                except JSONDecodeError:
                    logger.error(f"Invalid Json: {message}")
                    continue
                logger.debug(f"Received: {data}")
                await self._queue.put(data)
            except ConnectionClosed:
                logger.debug(f"Connection closed.")
                break

    async def send(self, data: Any) -> None:
        # Sendet eine Nachricht über die Websocket an den Benutzer
        try:
            message = json.dumps(data)
        except TypeError as e:
            logger.error(f"The data could not be serialized: {e}")
            return
        try:
            await self._websocket.send(message)
            logger.debug(f"Send: {data}")
        except ConnectionClosed:
            logger.warning(f"Connection closed, message could not be sent: {message}")

    async def compute_action(self) -> Any:
        logger.debug(f"Queue.length: {self._queue.qsize()}")
        while not self._queue.empty():
            await self._queue.get()
        data = await self._queue.get()
        return data


async def run_engine(client):
    while True:
        data = await client.compute_action()
        if data is None:
            continue
        response = ["Pong", data[1]]
        await client.send(response)

        # Simuliere Berechnungen
        await asyncio.sleep(4)


async def websocket_handler(websocket: ServerConnection) -> None:
    client = Client(websocket)
    asyncio.create_task(run_engine(client))
    await client.message_loop()


async def main():
    server = await serve(websocket_handler, config.HOST, config.PORT)
    logger.info(f"WebSocket server started at ws://{config.HOST}:{config.PORT}")
    await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main(), debug=config.DEBUG)
