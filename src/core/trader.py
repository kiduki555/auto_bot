from typing import Dict, Any
from src.exchanges.exchange import BinanceExchange
from src.strategies.base_strategy import Strategy
import logging
import os
import pandas as pd

class Trader:
    def __init__(self, exchange: BinanceExchange, strategy: Strategy, config: Dict[str, Any]):
        self.exchange = exchange
        self.strategy = strategy
        self.config = config
        self.logger = logging.getLogger(__name__)

    def execute_trade(self, symbol: str, side: str, quantity: float, stop_loss: float = None, take_profit: float = None):
        """Execute a trade on Binance using the exchange methods"""
        try:
            order = self.exchange.place_futures_order(symbol=symbol, side=side, quantity=quantity)
            self.logger.info(f"Executed {side} order: {order}")

            # Set stop loss and take profit if provided
            if stop_loss is not None:
                self.set_stop_loss(symbol, order['orderId'], stop_loss)
            if take_profit is not None:
                self.set_take_profit(symbol, order['orderId'], take_profit)

        except Exception as e:
            self.logger.error(f"Error executing trade: {str(e)}")

    def set_stop_loss(self, symbol: str, order_id: str, stop_loss: float):
        """Set a stop loss order"""
        try:
            self.exchange.place_futures_order(symbol=symbol, side='sell', quantity=1, stopPrice=stop_loss, order_type='STOP_MARKET')
            self.logger.info(f"Stop loss set for order {order_id} at {stop_loss}")
        except Exception as e:
            self.logger.error(f"Error setting stop loss: {str(e)}")

    def set_take_profit(self, symbol: str, order_id: str, take_profit: float):
        """Set a take profit order"""
        try:
            self.exchange.place_futures_order(symbol=symbol, side='sell', quantity=1, price=take_profit, order_type='LIMIT')
            self.logger.info(f"Take profit set for order {order_id} at {take_profit}")
        except Exception as e:
            self.logger.error(f"Error setting take profit: {str(e)}")

    def cancel_order(self, symbol: str, order_id: str):
        """Cancel an existing order"""
        try:
            self.exchange.cancel_order(symbol=symbol, order_id=order_id)
            self.logger.info(f"Order {order_id} canceled.")
        except Exception as e:
            self.logger.error(f"Error canceling order: {str(e)}")

