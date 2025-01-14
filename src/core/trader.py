from typing import Dict, Any
from src.exchanges.exchange import BinanceExchange
from src.strategies.base_strategy import Strategy
from src.strategies.implementations.adaptive_supertrend_strategy import AdaptiveSuperTrendStrategy
from src.strategies.implementations.future_trend_strategy import FutureTrendStrategy
import logging
from binance.client import Client
import os
import pandas as pd

class Trader:
    def __init__(self, exchange: BinanceExchange, strategy: Strategy, config: Dict[str, Any]):
        self.exchange = exchange
        self.strategy = strategy
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Binance API 클라이언트 초기화
        if os.getenv('USE_TESTNET', 'false').lower() == 'true':
            self.binance_client = Client(
                os.getenv('BINANCE_TESTNET_API_KEY'),
                os.getenv('BINANCE_TESTNET_API_SECRET')
            )
        else:
            self.binance_client = Client(
                os.getenv('BINANCE_API_KEY'),
                os.getenv('BINANCE_API_SECRET')
            )

    def execute_trade(self, symbol: str, side: str, quantity: float):
        """Execute a trade on Binance"""
        try:
            if side.lower() == 'buy':
                order = self.binance_client.order_market_buy(
                    symbol=symbol,
                    quantity=quantity
                )
            elif side.lower() == 'sell':
                order = self.binance_client.order_market_sell(
                    symbol=symbol,
                    quantity=quantity
                )
            self.logger.info(f"Executed {side} order: {order}")
        except Exception as e:
            self.logger.error(f"Error executing trade: {str(e)}")

    def execute_trades(self, symbol: str):
        signals = pd.DataFrame()
        last_signal = signals.iloc[-1]