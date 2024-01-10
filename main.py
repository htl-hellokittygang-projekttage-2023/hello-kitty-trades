import asyncio
from modules.bot import ScalpingStrategy
from modules.websocket import WebsocketServer

async def main():
    message_queue = asyncio.Queue()

    bot = ScalpingStrategy(message_queue)
    ws = WebsocketServer(message_queue)

    bot_task = asyncio.create_task(bot.run(["ETHUSD", "USDJPY", "BTCUSD", "META", "AAPL", "DE40", 
                                            "TSLA", "MSFT", "FORD", "J225", "GBPUSD", "SILVER", "EURUSD", 
                                            "OIL_CRUDE", "US100", "COIN"])) # Add more epics here as you wish
    ws_task = asyncio.create_task(ws.run())

    await asyncio.gather(bot_task, ws_task)

if __name__ == "__main__":
    asyncio.run(main())
