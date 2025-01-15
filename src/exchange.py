from binance.client import Client
import os

class BinanceExchange:
    def __init__(self):
        self.client = Client(
            os.getenv('BINANCE_API_KEY'),
            os.getenv('BINANCE_API_SECRET')
        )

    def get_historical_data(self, symbol: str, interval: str, limit: int = 100):
        """Fetch historical data from Binance"""
        klines = self.client.get_historical_klines(symbol, interval, limit=limit)
        # Convert to DataFrame or any other format as needed
        return klines

    def place_order(self, symbol: str, side: str, quantity: float):
        """Place an order on Binance"""
        if side.lower() == 'buy':
            return self.client.order_market_buy(symbol=symbol, quantity=quantity)
        elif side.lower() == 'sell':
            return self.client.order_market_sell(symbol=symbol, quantity=quantity)
        else:
            raise ValueError("Invalid order side. Use 'buy' or 'sell'.") 