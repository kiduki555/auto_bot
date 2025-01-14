from typing import Dict, List, Optional, Any
from datetime import datetime
from src.utils.logger import Logger


class TradeManager:
    """
    Manages all trading operations including position tracking and risk management
    """
    def __init__(
        self,
        symbol: str,
        initial_balance: float,
        risk_per_trade: float = 0.02,
        max_position_size: float = 1.0
    ):
        self.symbol = symbol
        self.balance = initial_balance
        self.risk_per_trade = risk_per_trade
        self.max_position_size = max_position_size
        self.current_position = 0
        self.open_orders: List[Dict] = []
        self.trade_history: List[Dict] = []
        self.logger = Logger(symbol)

    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float
    ) -> float:
        """Calculate appropriate position size based on risk parameters"""
        risk_amount = self.balance * self.risk_per_trade
        price_risk = abs(entry_price - stop_loss)
        
        if price_risk == 0:
            return 0
            
        position_size = risk_amount / price_risk
        return min(position_size, self.max_position_size)

    def open_position(
        self,
        side: str,
        entry_price: float,
        position_size: float,
        stop_loss: float,
        take_profit: float
    ) -> bool:
        """
        Open a new trading position
        
        Args:
            side: 'long' or 'short'
            entry_price: Entry price for the position
            position_size: Size of the position
            stop_loss: Stop loss price
            take_profit: Take profit price
            
        Returns:
            bool: Whether the position was successfully opened
        """
        if self.current_position != 0:
            self.logger.log_warning(
                f"Cannot open {side} position - existing position active"
            )
            return False

        order = {
            'side': side,
            'entry_price': entry_price,
            'position_size': position_size,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'entry_time': datetime.now(),
            'status': 'open'
        }

        self.open_orders.append(order)
        self.current_position = position_size if side == 'long' else -position_size
        
        self.logger.log_trade(
            f"Opened {side} position",
            entry_price,
            position_size,
            take_profit,
            stop_loss
        )
        
        return True

    def close_position(
        self,
        exit_price: float,
        reason: str = 'manual'
    ) -> Optional[Dict]:
        """
        Close an existing position
        
        Args:
            exit_price: Price at which to close the position
            reason: Reason for closing ('tp', 'sl', or 'manual')
            
        Returns:
            Dict containing trade details if successful, None otherwise
        """
        if not self.open_orders:
            self.logger.log_warning("No open position to close")
            return None

        current_order = self.open_orders[-1]
        
        if current_order['status'] != 'open':
            return None

        profit_loss = (
            (exit_price - current_order['entry_price'])
            * current_order['position_size']
            if current_order['side'] == 'long'
            else (current_order['entry_price'] - exit_price)
            * current_order['position_size']
        )

        trade_record = {
            **current_order,
            'exit_price': exit_price,
            'exit_time': datetime.now(),
            'profit_loss': profit_loss,
            'close_reason': reason,
            'status': 'closed'
        }

        self.trade_history.append(trade_record)
        self.balance += profit_loss
        self.current_position = 0
        self.open_orders[-1] = trade_record

        self.logger.log_trade(
            f"Closed position ({reason})",
            exit_price,
            profit_loss=profit_loss
        )

        return trade_record

    def check_stop_loss(self, current_price: float) -> bool:
        """Check if stop loss has been hit"""
        if not self.open_orders:
            return False

        current_order = self.open_orders[-1]
        
        if current_order['status'] != 'open':
            return False

        if (current_order['side'] == 'long' and 
            current_price <= current_order['stop_loss']):
            self.close_position(current_price, 'sl')
            return True

        if (current_order['side'] == 'short' and 
            current_price >= current_order['stop_loss']):
            self.close_position(current_price, 'sl')
            return True

        return False

    def check_take_profit(self, current_price: float) -> bool:
        """Check if take profit has been hit"""
        if not self.open_orders:
            return False

        current_order = self.open_orders[-1]
        
        if current_order['status'] != 'open':
            return False

        if (current_order['side'] == 'long' and 
            current_price >= current_order['take_profit']):
            self.close_position(current_price, 'tp')
            return True

        if (current_order['side'] == 'short' and 
            current_price <= current_order['take_profit']):
            self.close_position(current_price, 'tp')
            return True

        return False

    def get_position_status(self) -> Dict[str, Any]:
        """Get current position status"""
        if not self.open_orders or self.open_orders[-1]['status'] != 'open':
            return {
                'has_position': False,
                'side': None,
                'entry_price': None,
                'current_size': 0,
                'stop_loss': None,
                'take_profit': None
            }

        current_order = self.open_orders[-1]
        return {
            'has_position': True,
            'side': current_order['side'],
            'entry_price': current_order['entry_price'],
            'current_size': current_order['position_size'],
            'stop_loss': current_order['stop_loss'],
            'take_profit': current_order['take_profit']
        }
