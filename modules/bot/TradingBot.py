import time
import json
import sys
import os
import asyncio
import random
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
from api.TradingAPI import TradingAPI
from api.TradingAPI import Resolution
from api.TradingAPI import Position
import numpy as np

def display_json(json_string):
    """Pretty prints the json data."""
    data = json.loads(json_string)
    pretty_data = json.dumps(data, indent=4)
    print(pretty_data)
    
class ScalpingStrategy:
    def __init__(self, queue = None, max_open_positions=2):
        self.api = TradingAPI()
        self.queue = queue
        self.max_open_positions = max_open_positions
        self.gcapital = 10000.0
        self.acapital = 0.0
        self.margin = 0.0
        self.guv = 0.0

    async def run (self, epics):
        print("Running Scalping Strategy...")
        await self.api.run()
        await self.init_send_all_epics_to_websocket(epics)
        
        for pos in json.loads(await self.api.all_positions())["positions"]:
            await self.api.close_position(pos['position']['dealId'])

        await self.request_new_data()
        await self.send_queue_stats()
        await self.queue.put(json.dumps({"type": "dispatch"})) if self.queue else None
        
        hashmap = {}
        
        for epic in epics:
            hashmap[epic] = 0
        
        while True:
            before_time = time.time()

            for epic in epics:
                print("Epic:", epic)
                try:
                    buy_condition, sell_condition = await self.analyze_market(epic)

                    if buy_condition:
                        if hashmap[epic] < self.max_open_positions:
                            await self.execute_scalp(epic)
                            hashmap[epic] += 1
                    elif sell_condition:
                        if hashmap[epic] > 0:
                            hashmap[epic] = 0
                            await self.execute_sell(epic)
                        
                            print("Position will be closed... 📉")

                    await self.request_new_data()
                    await self.send_data_to_queue(epic)
                    await self.send_queue_stats()
                    await self.queue.put(json.dumps({"type": "dispatch"})) if self.queue else None

                    print()
                    print("Analyzing market... 📈")
                    print()
            
                except Exception as e:
                    print("Error:", e)

            after_time = time.time()
            tot_time = after_time - before_time
            sleep_time = max(60 - tot_time, 0)

            if (sleep_time >= 6):
                slices = sleep_time / 6
                for _ in range(6):
                    await self.request_new_data()
                    await self.send_queue_stats()
                    await self.queue.put(json.dumps({"type": "dispatch"})) if self.queue else None
                    await asyncio.sleep(slices)
            else:
                # Sleep for a short duration before analyzing the market again
                await self.request_new_data()
                await self.send_queue_stats()
                await self.queue.put(json.dumps({"type": "dispatch"})) if self.queue else None
                await asyncio.sleep(sleep_time)
    
    async def send_queue_stats (self):
        await self.queue.put(json.dumps({"type": "stats", "data": {"gcapital": self.gcapital, "acapital": self.acapital, "margin": self.margin, "guv": self.guv}})) if self.queue else None

    async def request_new_data(self):
        for account in json.loads(await self.api.get_all_accounts())["accounts"]:
            self.gcapital = account["balance"]["deposit"]
            self.acapital = account["balance"]["balance"]
            self.margin =  self.acapital - account["balance"]["available"]
            self.guv = account["balance"]["profitLoss"]
            break
        
    
    async def get_price_data(self, epic, resolution=Resolution.MINUTE, num_periods=10):
        # Fetch historical price data
        historical_data = json.loads(await self.api.get_market_history(epic, resolution, num_periods))

        # Extract closing prices from the historical data
        prices = [float(data['closePrice']['bid']) for data in historical_data['prices']]
        return prices

    async def analyze_market(self, epic, resolution=Resolution.MINUTE, num_periods=10):
        # Analyze the market using a simple moving average (SMA)
        prices = await self.get_price_data(epic, resolution, num_periods)
        if len(prices) < num_periods:
            return False # Not enough data for analysis

        # Calculate SMA
        sma = np.mean(prices)

        out = await self.api.get_market_details(epic)
        data = json.loads(out)
        
        current_price = float(data['snapshot']['bid'])

        # Buy if the current price is above the SMA,
        # Sell if the current price is below the SMA
        print("Current Price:", current_price)
        print("SMA:", sma)

        return current_price > sma, current_price < sma
    
    async def execute_scalp(self, epic):
        # Execute a scalp trade
        out = await self.api.get_market_details(epic)
        data = json.loads(out)
        
        current_price = float(data['snapshot']['bid'])
        
        normal_pos = random.uniform(0.69, 4.20)
        min_pos = json.loads(await self.api.get_market_details(epic))["dealingRules"]["minDealSize"]["value"]
        #lowest_stop = float(data['dealingRules']['maxStopOrProfitDistance']['value'])
        #lowest_stop = current_price - 0.01
        #min_takeprofit = json.loads(await self.api.get_market_details(epic))["dealingRules"]["minStopOrProfitDistance"]["value"]
        
        #print("Buying:", lowest_stop)
        
        if normal_pos < min_pos:
            normal_pos = min_pos
        
        current_price_multiplyer = json.loads(await self.api.get_market_details("ETHUSD"))["dealingRules"]["minStopOrProfitDistance"]["value"]

        order_result = json.loads(await self.api.open_positions(Position.BUY, epic, normal_pos, stop_level = (1.00-current_price_multiplyer) * float(current_price), profit_level = (current_price_multiplyer+1.00) * float(current_price)))

        await self.queue.put(json.dumps({"type": "buy", "data": {"name": epic, "timestamp": time.time(), "price": float(current_price), "unit": normal_pos}})) if self.queue else None
        
        print("Order Result: "+str(order_result))
        
    async def execute_sell(self, epic):
        """Execute a sell trade."""
        order_result = json.loads(await self.api.all_positions())
        print("Selling:", epic)
        
        out = await self.api.get_market_details(epic)
        data = json.loads(out)
        
        current_price = float(data['snapshot']['bid'])
        for position in order_result['positions']:
            if position['market']['epic'] == epic:
                unit = position['position']['size']
                delete = await self.api.close_position(position['position']['dealId'])
                print("Order Result:", delete)

                await self.queue.put(json.dumps({"type": "sell", "data": {"name": epic, "timestamp": time.time(), "price": float(current_price), "unit": unit}})) if self.queue else None
                
    async def send_data_to_queue(self, epic):             
        data = {
            "type": "stocks",
            "timestamp": time.time(),
            "data": {
                "name": epic,
                "highest": 0,
                "lowest": 0,
                "prices": {
                }
            }
        }
        
        ups = json.loads(await self.api.get_market_history(epic, Resolution.MINUTE, 35))
        
        highest = 0
        lowest = 0

        for r, ups in zip(range(35), ups['prices']):
            open_bid = float(ups['openPrice']['bid'])
            high_bid = float(ups['highPrice']['bid'])
            low_bid = float(ups['lowPrice']['bid'])
            close_bid = float(ups['closePrice']['bid'])
            
            open_ask = float(ups['openPrice']['ask'])
            high_ask = float(ups['highPrice']['ask'])
            low_ask = float(ups['lowPrice']['ask'])
            close_ask = float(ups['closePrice']['ask'])
            
            real_open = (open_bid + open_ask) / 2
            real_high = (high_bid + high_ask) / 2
            real_low = (low_bid + low_ask) / 2
            real_close = (close_bid + close_ask) / 2
            
            highest = real_high if real_high > highest else highest
            lowest = real_low if real_low < lowest or lowest == 0 else lowest
            
            data["data"]["prices"][abs(r - 34)] = {
                "open": real_open,
                "close": real_close,
                "high": real_high,
                "low": real_low
            }
        
        data["data"]["highest"] = highest
        data["data"]["lowest"] = lowest

        await self.queue.put(json.dumps(data)) if self.queue else None
    
    async def init_send_all_epics_to_websocket(self, epics):
        data = {"type": "courses"}

        for e in epics:
            data[e] = {}
        
        await self.queue.put(json.dumps(data)) if self.queue else None

if __name__ == "__main__":
    bot = ScalpingStrategy()
    asyncio.run(bot.run(["ETHUSD", "USDJPY", "BTCUSD", "META", "AAPL", "DE40", 
                                            "TSLA", "MSFT", "FORD", "J225", "GBPUSD", "SILVER", "EURUSD",
                                            "OIL_CRUDE", "US100", "COIN"]))  # You can add more epics here if you want to (this is for testing purposes, if the whole bot (+ interface, WS) is running on the server, it will use the epics from main.py)