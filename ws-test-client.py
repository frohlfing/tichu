import config
import asyncio
import json
import websockets


async def test_connection():
    uri = f"ws://{config.HOST}:{config.PORT}/?world=my_world&nickname=Tiger&canonical_chair=-1"
    async with websockets.connect(uri) as websocket:
        print("Connected")
        try:
            c = 0
            while True:
                data = ["Ping", c]
                await websocket.send(json.dumps(data))
                print(f"Send: {data}")
                #response = await websocket.recv()
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1)
                    print(f"Received: {response}")
                except asyncio.TimeoutError:
                    pass
                await asyncio.sleep(3)
                c += 1
        except websockets.exceptions.ConnectionClosedOK:
            print('Connection closed by the server')
        except asyncio.CancelledError:
            print('CancelledError')
            pass
        finally:
            print('Process stopped.')


if __name__ == "__main__":
    asyncio.run(test_connection())
