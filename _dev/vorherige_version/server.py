import asyncio
import config
import json
import signal
import websockets
from src.common.logger import logger
from src.game_factory import GameFactory
from src.player.agent import Agent
from src.player.client import Client
from src.player.random_agent import RandomAgent
from time import time
from urllib.parse import urlparse, parse_qs
from websockets import ConnectionClosed, WebSocketServerProtocol


default_agent = RandomAgent

async def websocket_handler(websocket: WebSocketServerProtocol, path: str, factory: GameFactory) -> None:
    # Wird von der Websocket aufgerufen, wenn eine neue Verbindung aufgebaut wurde

    query = urlparse(path).query
    params = parse_qs(query)

    # Referenz auf die Game-Engine holen

    if 'world' not in params or "nickname" not in params:
        logger.warning("Player rejected because necessary information is missing")
        return
    world_name = params['world'][0]
    nickname = params['nickname'][0]
    engine = factory.get_or_create_engine(world_name, [default_agent, default_agent, default_agent, default_agent])

    # Client anlegen

    try:
        canonical_chair = int(params.get('canonical_chair', [-1])[0])
        if canonical_chair < -1 or canonical_chair > 3:
            logger.warning("Player rejected because canonical_chair is invalid")
            return
    except ValueError:
        canonical_chair = -1

    client = None
    if canonical_chair == -1:
        # Sitzplatz suchen, der von der KI besetzt ist (diesen werden wir kapern)
        for chair in range(4):
            if isinstance(engine.get_player(chair), Agent):
                # Sitzplatz gefunden!
                client = Client(nickname, chair, engine, websocket)
                await engine.replace_player(client)
                break
    else:
        # der Benutzer möchte einen bestimmten Sitzplatz haben
        player = engine.get_player(canonical_chair)
        if isinstance(player, Client) and not player.websocket.open and player.nickname == nickname:
            # auf dem Platz sitz noch sein früheres Ich (er hatte einen Verbindungsabbruch)
            client = player
            client.websocket = websocket  # Websocket ersetzen und Client weiterverwenden
        elif isinstance(player, Agent):
            # der gewünschte Sitzplatz ist von einer KI besetzt, den können wir also nehmen
            client = Client(nickname, canonical_chair, engine, websocket)
            await engine.replace_player(client)

    if not client:
        message = f"{world_name}: Engine is full"
        try:
            await websocket.send(json.dumps({"type": "error", "message": message}))
            logger.debug(message)
        except ConnectionClosed:
            logger.warning(f"Connection closed, message could not be sent: {message}")
        return

    # solange Nachrichten von der Websocket verarbeiten, bis die Verbindung abbricht oder der Benutzer absichtlich geht
    try:
        await client.message_loop()
    except Exception as e:
        logger.error(f"{world_name}, Player {client.nickname}: Unhandled exception in the message loop: {e}")

    # bei Verbindungsabbruch etwas warten, vielleicht schlüpft der Benutzer erneut in sein altes Ich
    if not websocket.open:
        logger.debug(f"{world_name}, Player {client.nickname}: Kick timer started...")
        await asyncio.sleep(config.KICK_OUT_TIME)
        if client.websocket.id != websocket.id:
            logger.debug(f"{world_name}, Player {client.nickname}: Kick timeout expired, has since rejoined")
            return  # der Client wurde inzwischen innerhalb eines anderen Aufrufs des Websocket-Händlers übernommen
        logger.debug(f"{world_name}, Player {client.nickname}: Kick timeout expired, player did not rejoin")

    # Gibt es noch andere Benutzer?
    number_of_clients = sum(1 for chair in range(4) if isinstance(engine.get_player(chair), Client))
    if number_of_clients > 1:
        # ja, es gibt weitere Benutzer
        agent = default_agent(client.canonical_chair, engine)
        await engine.replace_player(agent)  # client in der Engine durch die KI ersetzen, andere wollen ja weiterspielen
    else:
        # es war der letzte Benutzer
        factory.remove_engine(engine)  # Engine entfernen


def shutdown(*_args):
    # Beendet den Server
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    if tasks:
        if len(tasks) == 1:
            logger.info('Cancelling outstanding task...')
        else:
            logger.info(f'Cancelling {len(tasks)} outstanding tasks...')
        for task in tasks:
            task.cancel()


# async def benchmark():
#     factory = GameFactory()
#     engine = factory.get_or_create_engine("Benchmark", [RandomAgent, RandomAgent, RandomAgent, RandomAgent])
#     game_counter: int = 0
#     start_time = time()
#     for game in range(1):
#         while not engine.is_game_over():
#             result = await engine.get_player(engine.current_chair).compute_action()
#             print(result)
#             if result:
#                 action, params = result
#                 await engine.change_state(action, params)
#         game_counter += 1
#     print(f"Anzahl Partien: {game_counter}")
#     duration = time() - start_time  # in Sekunden
#     print(f"Laufzeit: {duration:.3f} s.")
#     print(f"Durchschnittliche Zeit: {duration / game_counter:.3f} s.")
#     shutdown()


async def main():
    # Startet den Websocker-Server

    factory = GameFactory()

    server = await websockets.serve(lambda ws, path: websocket_handler(ws, path, factory), config.HOST, config.PORT)
    logger.info(f"WebSocket server started at ws://{config.HOST}:{config.PORT}")

    # POSIX Signal-Handler einrichten
    signal.signal(signal.SIGINT, shutdown)  # Interrupt from keyboard (CTRL + C)
    signal.signal(signal.SIGTERM, shutdown)  # Termination signal

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
