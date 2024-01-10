import websockets
import asyncio
import json
import time

class WebsocketServer:
    def __init__ (self, queue):
        self.queue = queue
        self.host = "localhost"
        self.port = 7799
        self.stockdata = {"type": "courses"}
        self.stats = {"type": "stats"}
        self.buys = {"type": "buys", "data": {}}
        self.sells = {"type": "sells", "data": {}}
        self.clients = set()
        self.dispatch = False

    async def run(self):
        print("websocket server started 🚀")
        await self.open_websocket()

    async def open_websocket (self):
        async with websockets.serve(self.handle_websocket, self.host, self.port):
            await asyncio.gather(
                asyncio.Future(),
                self.handle_queue_message(),
            )

    async def handle_websocket (self, websocket, path):
        print("connect 🤝")
        self.clients.add(websocket)
        #receiver_task = asyncio.create_task(self.receive_messages(websocket))
        
        try:
            for client in self.clients:
                await client.send(json.dumps(self.stockdata))
        except websockets.exceptions.ConnectionClosed or websockets.exceptions.ConnectionClosedError or websockets.exceptions.ConnectionClosedOK:
            try:
                print("disconnect 😞")
                self.clients.remove(websocket)
            except:
                pass
        
        while True:
            try:
                if self.dispatch:
                    for client in self.clients:
                        await client.send(json.dumps(self.stockdata))
                        await client.send(json.dumps(self.stats))
                        await client.send(json.dumps(self.buys))
                        await client.send(json.dumps(self.sells))
                    self.dispatch = False
                else:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                break
            except websockets.exceptions.ConnectionClosed or websockets.exceptions.ConnectionClosedError or websockets.exceptions.ConnectionClosedOK:
                try:
                    print("disconnect 😞")
                    self.clients.remove(websocket)
                    break
                except:
                    break
            except Exception as e:
                websocket.close()
                print(f"ws Error: {e}")
    
    async def receive_messages (self, websocket):
        async for message in websocket:
            print(json.loads(message))

    async def handle_queue_message (self):
        while True:
            if self.queue.qsize() > 0:
                data = json.loads(await self.queue.get())
                if data["type"] == "stocks":
                    self.stockdata[data["data"]["name"]] = data
                elif data["type"] == "courses":
                    for e in data:
                        if e != "type":
                            self.stockdata[e] = {}
                elif data["type"] == "stats":
                    self.stats = data
                elif data["type"] == "buy":
                    self.buys["data"].setdefault(data["data"]["name"], []).append(data["data"])
                elif data["type"] == "sell":
                    self.sells["data"].setdefault(data["data"]["name"], []).append(data["data"])    
                elif data["type"] == "dispatch":
                    self.dispatch = True
            else:
                await asyncio.sleep(1)

    # async def test_queue (self):
    #     while True:
    #         await self.queue.put(json.dumps({"type": "stocks", "data": {}}))
    #         await asyncio.sleep(3)