import asyncio
import json

import websockets

async def test_connection():
    uri = "ws://localhost:8080/?world=my_world&nickname=Tiger&canonical_chair=-1"
    async with websockets.connect(uri) as websocket:
        print("Connected")
        try:
            #await websocket.send("Hello Server!")
            await websocket.send(json.dumps({"type": "ACTION", "action": "START"}))
            await websocket.send(json.dumps({"type": "ACTION", "action": "GRAND", "parameters": {"decision": False}}))
            while True:
                response = await websocket.recv()
                print(f"Received from server: {response}")
        except websockets.exceptions.ConnectionClosedOK:
            print('Connection closed by the server')
        except asyncio.CancelledError:
            print('CancelledError')
            pass
        finally:
            print('Process stopped.')

if __name__ == "__main__":
    asyncio.run(test_connection())