from typing import Optional
from dotenv import load_dotenv
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
import os
import json
import base64
import aiohttp
import asyncio
from enum import Enum

load_dotenv()

URL = "https://demo-api-capital.backend-capital.com"
EMAIL = os.getenv('EMAIL')
API_KEY = os.getenv('API_KEY')
PASSWORD = os.getenv('PASSWORD')

class Resolution(Enum):
    MINUTE = "MINUTE"
    MINUTE_5 = "MINUTE_5"
    MINUTE_15 = "MINUTE_15"
    MINUTE_30 = "MINUTE_30"
    HOUR = "HOUR"
    HOUR_4 = "HOUR_4"
    DAY = "DAY"
    WEEK = "WEEK"
    
class Position(Enum):
    BUY = "BUY"
    SELL = "SELL"
    
class Types(Enum):
    LIMIT = "LIMIT"
    STOP = "STOP"

def display_json(json_string):
    """Pretty prints json data."""
    data = json.loads(json_string)
    pretty_data = json.dumps(data, indent=4)
    print(pretty_data)

def pkcs1_to_pem(pkcs1) -> bytes:
    """Converts the pkcs1 key to pem."""
    decoded_key = base64.b64decode(pkcs1)
    public_key = serialization.load_der_public_key(decoded_key)
    pem_key = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return pem_key

def extract_security_token_and_cst(session: str) -> tuple[str, str]:
    """Extracts the currentAccountId and clientId from the session."""
    data = json.loads(session)
    current_account_id = data['currentAccountId']
    client_id = data['clientId']
    return current_account_id, client_id

class TradingAPI:
    def __init__(self, queue = None) -> None:
        self.queue = queue

        self.API_KEY = API_KEY
        self.URL = URL
        self.PASSWORD = PASSWORD
        self.EMAIL = EMAIL
        
        self.security_token, self.cst = None, None

    async def run(self):
        print("TradingAPI started.")
        self.security_token, self.cst = await self.create_session()

    async def get_encryption_key(self) -> Optional[str]:
        """Fetches the encryption key from the API."""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {'X-CAP-API-KEY': self.API_KEY}
                async with session.get(f"{self.URL}/api/v1/session/encryptionKey", headers = headers) as response:
                    data = await response.text()
                    return data
        except Exception as e:
            print(f"Failed to get encryption key: {e}")
            return None

    async def encrypt_password(self) -> str | None:
        """Encrypts the password."""
        data = json.loads(await self.get_encryption_key())
        encryption_key = data['encryptionKey']
        timestamp = data['timeStamp']
        try:
            input_data = (self.PASSWORD + "|" + str(timestamp)).encode('utf-8')
            input_data = base64.b64encode(input_data)
            pem_key = pkcs1_to_pem(encryption_key)
            public_key = serialization.load_pem_public_key(pem_key)
            cipher = public_key.encrypt(
                input_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            output = base64.b64encode(cipher)
            return output.decode('utf-8')
        except Exception as e:
            print(e)
            return None

    async def create_session(self) -> tuple[str | None, str | None]:
        """Creates a session with the API."""

        # TODO: encrypt password:
        """
        password = self.encrypt_password()
        payload = json.dumps({
            "identifier": password,
            "password": password,
            "encryptedPassword": True,
        })
        payload = json.dumps({
            "identifier": self.EMAIL,
            "password": self.PASSWORD,
            "encryptedPassword": False,
        })
        """

        payload = json.dumps({
            "identifier": self.EMAIL,
            "password": self.PASSWORD,
            "encryptedPassword": False,
        })

        headers = {
            'X-CAP-API-KEY': self.API_KEY,
            'Content-Type': 'application/json'
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.URL}/api/v1/session", data = payload, headers = headers) as response:
                if response.status == 200:
                    cst = response.headers.get("CST")
                    x_security_token = response.headers.get('X-SECURITY-TOKEN')
                    return x_security_token, cst
                else:
                    return None, None

    async def session_details(self):
        """Fetches the session details."""
        headers = {
            'X-SECURITY-TOKEN': self.security_token,
            'CST': self.cst,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.URL}/api/v1/session", headers = headers) as response:
                data = await response.text()
                return data

    async def get_all_top_level_market(self):
        """Fetches all top level markets."""
        headers = {
            'X-SECURITY-TOKEN': self.security_token,
            'CST': self.cst,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.URL}/api/v1/marketnavigation", headers = headers) as response:
                data = await response.text()
                return data

    async def search_market(self, search_term: str = "", epics: str = ""):
        """Searches for a market."""
        headers = {
            'X-SECURITY-TOKEN': self.security_token,
            'CST': self.cst,
        }
        url = "/api/v1/markets?"

        if search_term != "":
            url += f"searchTerm={search_term}&"
        if epics != "":
            url += f"epics={epics}&"

        async with aiohttp.ClientSession() as session:
            async with session.get(self.URL + url, headers = headers) as response:
                data = await response.text()
                return data

    async def get_all_sub_markets(self, market_id: str, limit: int = 500):
        """Fetches all sub markets."""
        headers = {
            'X-SECURITY-TOKEN': self.security_token,
            'CST': self.cst,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.URL}/api/v1/marketnavigation/{market_id}?limit={limit}", headers = headers) as response:
                data = await response.text()
                return data

    async def get_market_details(self, epic: str):
        """Fetches the market details."""
        headers = {
            'X-SECURITY-TOKEN': self.security_token,
            'CST': self.cst,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.URL}/api/v1/markets/{epic}", headers = headers) as response:
                data = await response.text()
                return data

    async def get_market_history(self, epic: str, resolution=Resolution.MINUTE, max: int = 10, from_date: str = "",
                           to_date: str = ""):
        """
        Fetches the market history.
        :param epic: The epic of the market.
        :param resolution: The resolution of the market history (default: Resolution.MINUTE) see Resolution class.
        :param max: The maximum number of the values in answer. Default = 10, max = 1000
        :param from_date: The start date of the market history (default: "")  Date format: YYYY-MM-DDTHH:MM:SS　(e.g. 2022-04-01T01:01:00)
        :param to_date: The end date of the market history (default: "") Date format: YYYY-MM-DDTHH:MM:SS　(e.g. 2022-04-01T01:01:00)
        :return: The market history as json string.
        """
        headers = {
            'X-SECURITY-TOKEN': self.security_token,
            'CST': self.cst,
        }
        url = f"/api/v1/prices/{epic}?resolution={resolution.value}&max={max}&"

        if from_date != "":
            url += f"from={from_date}&"
        if to_date != "":
            url += f"to={to_date}&"

        async with aiohttp.ClientSession() as session:
            async with session.get(self.URL + url, headers = headers) as response:
                data = await response.text()
                return data

    async def get_sentiment_for_multiple_markets(self, marketIds: str = ""):
        """Fetches the sentiment for multiple markets."""
        headers = {
            'X-SECURITY-TOKEN': self.security_token,
            'CST': self.cst,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.URL}/api/v1/clientsentiment" + "" if marketIds == "" else f"?marketIds={marketIds}", headers = headers) as response:
                data = await response.text()
                return data

    async def get_sentiment_for_single_market(self, marketId: str):
        """Fetches the sentiment for a single market."""
        headers = {
            'X-SECURITY-TOKEN': self.security_token,
            'CST': self.cst,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.URL}/api/v1/clientsentiment/{marketId}", headers = headers) as response:
                data = await response.text()
                return data
    
    async def get_trade_info(self, dealReference: str):
        """Fetches the trade info for a single market."""
        headers = {
            'X-SECURITY-TOKEN': self.security_token,
            'CST': self.cst,
            'Content-Type': 'application/json'
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.URL}/api/v1/trade/{dealReference}", headers = headers) as response:
                data = await response.text()
                return data
    
    async def all_positions(self):
        """Fetches all positions."""
        headers = {
            'X-SECURITY-TOKEN': self.security_token,
            'CST': self.cst
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.URL}/api/v1/positions", headers = headers) as response:
                data = await response.text()
                return data
    
    async def open_positions(self, direction:Position, epic:str, size:int, guaranteed_stop:bool = None, trailing_stop:bool = None, stop_level = -1,stop_distance = -1, stop_amount = -1, profit_level = -1, profit_distance=-1,profit_ammount = -1):
        """Opens a position."""
        payload = {
            "direction": direction.value,   # buy or sell
            "epic": epic,                   # the epic of the market
            "size": size,                   # how much you want to buy
        }

        headers = {
            'X-SECURITY-TOKEN': self.security_token,
            'CST': self.cst,
            'Content-Type': 'application/json'
        }
        
        if guaranteed_stop != None:
            payload["guaranteedStop"] = guaranteed_stop
        if trailing_stop != None:
            payload["trailingStop"] = trailing_stop
        if stop_level != -1:            # Stop level is only needed if you have a guaranteed stop it is the absolute value of the stop level
            payload["stopLevel"] = stop_level 
        if stop_distance != -1:         # Stop distance is only needed if you have a trailing stop it is the distance to the buy point its a less value than the buy value but doesn't stop if the price goes down
            payload["stopDistance"] = stop_distance
        if stop_amount != -1:           # Stop amount is only needed if you have a stop level it is the absolute value of the stop level
            payload["stopAmount"] = stop_amount
        if profit_level != -1:          # Profit level is only needed if stopLevel is true it is the distance to the stop level
            payload["profitLevel"] = profit_level
        if profit_distance != -1:       # Price distance to the buy point in the profit level
            payload["profitDistance"] = profit_distance
        if profit_ammount != -1:        # Distance from the buy point to the profit level
            payload["profitAmount"] = profit_ammount
            
        display_json(json.dumps(payload))
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.URL}/api/v1/positions", data = json.dumps(payload), headers = headers) as response:
                data = await response.text()
                return data
            
    async def set_demo_capital(self, capital:float):
        """Sets the demo capital."""
        headers = {
            'X-SECURITY-TOKEN': self.security_token,
            'CST': self.cst,
            'Content-Type': 'application/json'
        }
        payload = {
            "amount": capital
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.URL}/api/v1/accounts/topUp", data = json.dumps(payload), headers = headers) as response:
                data = await response.text()
                return data
    
    async def get_single_position(self, dealReference:str):
        """Fetches a single position."""
        headers = {
            'X-SECURITY-TOKEN': self.security_token,
            'CST': self.cst
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.URL}/api/v1/positions/{dealReference}", headers = headers) as response:
                data = await response.text()
                return data
    
    async def update_position(self, deal_id:str, guaranteed_stop:bool = None, trailingStop:bool = None, stop_level = -1,stop_distance = -1, stop_amount = -1, profit_level = -1, profit_distance=-1,profit_ammount = -1):
        """Updates a position."""
        headers = {
            'X-SECURITY-TOKEN': self.security_token,
            'CST': self.cst,
            'Content-Type': 'application/json'
        }
        payload = {}

        if stop_level != None:          # Stop level is only needed if you have a guaranteed stop it is the absolute value of the stop level
            payload["stopLevel"] = stop_level 
        if stop_distance != -1:         # Stop distance is only needed if you have a trailing stop it is the distance to the buy point its a less value than the buy value but doesn't stop if the price goes down
            payload["stopDistance"] = stop_distance
        if stop_amount != -1:           # Stop amount is only needed if you have a stop level it is the absolute value of the stop level
            payload["stopAmount"] = stop_amount
        if profit_level != -1:          # Profit level is only needed if stopLevel is true it is the distance to the stop level
            payload["profitLevel"] = profit_level
        if profit_distance != -1:       # Price distance to the buy point in the profit level
            payload["profitDistance"] = profit_distance
        if profit_ammount != -1:        # Distance from the buy point to the profit level
            payload["profitAmount"] = profit_ammount
        if guaranteed_stop != None:
            payload["guaranteedStop"] = guaranteed_stop
        if trailingStop != None:
            payload["trailingStop"] = trailingStop    
            
        
        
        
        async with aiohttp.ClientSession() as session:
            async with session.put(f"{self.URL}/api/v1/positions/{deal_id}", data = json.dumps(payload), headers = headers) as response:
                data = await response.text()
                return data
    
    async def close_position(self, deal_id:str):
        """Closes a position."""
        headers = {
            'X-SECURITY-TOKEN': self.security_token,
            'CST': self.cst
        }
        async with aiohttp.ClientSession() as session:
            async with session.delete(f"{self.URL}/api/v1/positions/{deal_id}", headers = headers) as response:
                data = await response.text()
                return data 
    
    async def get_all_working_orders(self):
        """Fetches all working orders."""
        headers = {
            'X-SECURITY-TOKEN': self.security_token,
            'CST': self.cst
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.URL}/api/v1/workingorders/", headers = headers) as response:
                data = await response.text()
                return data
    
    async def create_order(self, direction:Position, epic:str, size:int, level:int, type:Types ,good_till_date:str = "", guaranteed_stop:bool = None,trailing_stop = None, stop_level:int = -1, stop_distance = -1, stop_amount = -1, profit_level = -1, profit_distance = -1, profit_amount = -1):
        """Creates an order."""
        headers = {
            'X-SECURITY-TOKEN': self.security_token,
            'CST': self.cst,
            'Content-Type': 'application/json'
        }
        payload = {
            "direction": direction.value,       # buy or sell
            "epic": epic,                       # the epic of the market
            "size": size,                       # how much you want to buy
            "level": level,                     # the level you want to buy at
            "type": type.value,                 # the type of the order
        }
        
        if stop_level != -1:            # Stop level is only needed if you have a guaranteed stop it is the absolute value of the stop level
            payload["stopLevel"] = stop_level
        if stop_distance != -1:         # Stop distance is only needed if you have a trailing stop it is the distance to the buy point its a less value than the buy value but doesn't stop if the price goes down
            payload["stopDistance"] = stop_distance
        if stop_amount != -1:           # Stop amount is only needed if you have a stop level it is the absolute value of the stop level
            payload["stopAmount"] = stop_amount
        if profit_level != -1:          # Profit level is only needed if stopLevel is true it is the distance to the stop level
            payload["profitLevel"] = profit_level
        if profit_distance != -1:
            payload["profitDistance"] = profit_distance
        if profit_amount != -1:
            payload["profitAmount"] = profit_amount
        if guaranteed_stop != None:
            payload["guaranteedStop"] = guaranteed_stop
        if trailing_stop != None:
            payload["trailingStop"] = trailing_stop
        if good_till_date != "":
            payload["goodTillDate"] = good_till_date
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.URL}/api/v1/workingorders/", data = json.dumps(payload), headers = headers) as response:
                data = await response.text()
                return data
            
    async def get_all_accounts(self):
        """Fetches all accounts."""
        headers = {
            'X-SECURITY-TOKEN': self.security_token,
            'CST': self.cst
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.URL}/api/v1/accounts", headers = headers) as response:
                data = await response.text()
                return data
    
    async def update_order(self, deal_id:str,level:int = -1, good_till_date:str = "", guaranteed_stop:bool = None,trailing_stop = None, stop_level:int = -1, stop_distance = -1, stop_amount = -1, profit_level = -1, profit_distance = -1, profit_amount = -1):
        """Updates an order."""
        headers = {
            'X-SECURITY-TOKEN': self.security_token,
            'CST': self.cst,
            'Content-Type': 'application/json'
        }
        payload = {}

        if good_till_date != "":
            payload["goodTillDate"] = good_till_date
        if guaranteed_stop != None:
            payload["guaranteedStop"] = guaranteed_stop
        if trailing_stop != None:
            payload["trailingStop"] = trailing_stop
        if stop_level != -1:            # Stop level is only needed if you have a guaranteed stop it is the absolute value of the stop level
            payload["stopLevel"] = stop_level
        if stop_distance != -1:         # Stop distance is only needed if you have a trailing stop it is the distance to the buy point its a less value than the buy value but doesn't stop if the price goes down
            payload["stopDistance"] = stop_distance
        if stop_amount != -1:           # Stop amount is only needed if you have a stop level it is the absolute value of the stop level
            payload["stopAmount"] = stop_amount
        if profit_level != -1:          # Profit level is only needed if stopLevel is true it is the distance to the stop level
            payload["profitLevel"] = profit_level
        if profit_distance != -1:
            payload["profitDistance"] = profit_distance
        if profit_amount != -1:
            payload["profitAmount"] = profit_amount
        
        async with aiohttp.ClientSession() as session:
            async with session.put(f"{self.URL}/api/v1/workingorders/{deal_id}", data = json.dumps(payload), headers = headers) as response:
                data = await response.text()
                return data
    
    async def close_order(self, deal_id:str):
        """Closes an order."""
        headers = {
            'X-SECURITY-TOKEN': self.security_token,
            'CST': self.cst
        }

        async with aiohttp.ClientSession() as session:
            async with session.delete(f"{self.URL}/api/v1/workingorders/{deal_id}", headers = headers) as response:
                data = await response.text()
                return data        
        
async def test():
    print("Starting...")
    trading_handler = TradingAPI()
    await trading_handler.run()

    print("Session details:")
    display_json(await trading_handler.session_details())

    print("All top level markets:")
    display_json(await trading_handler.get_all_top_level_market())

    print("Search for 'Tesla':")
    display_json(await trading_handler.search_market("Tesla", ""))

    print("All sub markets of Shares:")
    display_json(await trading_handler.get_all_sub_markets("hierarchy_v1.shares"))

    print("All sub markets of Populare Shares:")
    display_json(await trading_handler.get_all_sub_markets("hierarchy_v1.shares.popular_shares"))

    print("tesla market details:")
    display_json(await trading_handler.get_market_details("TSLA"))

    print("tesla market history:")
    display_json(await trading_handler.get_market_history("TSLA", Resolution.MINUTE_15, 10))

    print("Sentiment for apple market:")
    display_json(await trading_handler.get_sentiment_for_single_market("TSLA"))
    
    print("Order Tesla:")
    display_json(await trading_handler.open_positions(Position.BUY, "TSLequityA", 0.1))
    
    print("All positions:")
    display_json(await trading_handler.all_positions())
    
    print("Get single position:")
    display_json(await trading_handler.get_single_position("00513301-0055-311e-0000-0000808f1d3a"))
    
    print("Update position:")
    display_json(await trading_handler.update_position("00513301-0055-311e-0000-0000808f1d3a", stop_level = 700))
    
    print("Close position:")
    display_json(await trading_handler.close_position("00513301-0055-311e-0000-0000808f1d3a"))
    
    print("All working orders:")
    display_json(await trading_handler.get_all_working_orders())
    
    print("Create order:")
    display_json(await trading_handler.create_order(Position.BUY, "TSLA", 0.1, 256.97, Types.STOP, stop_level = 253.22))
    
    print("Update order:")
    display_json(await trading_handler.update_order("00513301-0055-311e-0000-0000808f1d3a", stop_level = 253.22))
    
    print("Close order:")
    display_json(await trading_handler.close_order("00513301-0055-311e-0000-0000808f1d63"))

    print("Finished.")
    
async def main():
    api = TradingAPI()
    await api.run()
    display_json(await api.all_positions())

if __name__ == "__main__":
    # api = TradingAPI()
    # api.run()
    # display_json(await api.get_market_details("TSLA"))
    # print("AAA")
    # display_json(await api.all_positions())
    # data = json.loads(await api.all_positions())
    # for position in data['positions']:
    #     print(position['market']['epic'])
    #     print(position['position']['dealId'])
    asyncio.run(main())