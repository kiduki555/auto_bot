from typing import Dict, Any, Optional, Tuple
import pandas as pd
from abc import ABC, abstractmethod
from src.utils.logger import Logger


class BaseStrategy(ABC):
    """Base class for all trading strategies"""
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Initialize strategy with parameters
        
        Args:
            params: Dictionary of strategy parameters
        """
        self.params = params or {}
        self.logger = Logger(self.__class__.__name__)
        
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals
        
        Args:
            data: DataFrame with OHLCV and indicator data
            
        Returns:
            DataFrame with signals added
        """
        pass
        
    @abstractmethod
    def calculate_position_size(
        self,
        capital: float,
        entry_price: float,
        stop_loss: float
    ) -> float:
        """
        Calculate position size based on risk management rules
        
        Args:
            capital: Available capital
            entry_price: Entry price
            stop_loss: Stop loss price
            
        Returns:
            Position size
        """
        pass
        
    @abstractmethod
    def calculate_exit_points(
        self,
        entry_price: float,
        side: str,
        risk_reward_ratio: float = 2.0
    ) -> Tuple[float, float]:
        """
        Calculate stop loss and take profit levels
        
        Args:
            entry_price: Entry price
            side: Trade side ('long' or 'short')
            risk_reward_ratio: Risk/Reward ratio
            
        Returns:
            Tuple of (stop_loss, take_profit)
        """
        pass
        
    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate input data
        
        Args:
            data: DataFrame to validate
            
        Returns:
            bool: Whether data is valid
        """
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        return all(col in data.columns for col in required_columns)
        
    def log_signal(
        self,
        timestamp: pd.Timestamp,
        signal_type: str,
        price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> None:
        """
        Log trading signal
        
        Args:
            timestamp: Signal timestamp
            signal_type: Type of signal
            price: Signal price
            stop_loss: Stop loss price
            take_profit: Take profit price
        """
        message = (
            f"Signal: {signal_type} at {price:.8f} "
            f"[{timestamp}]"
        )
        if stop_loss:
            message += f" SL: {stop_loss:.8f}"
        if take_profit:
            message += f" TP: {take_profit:.8f}"
            
        self.logger.log_info(message)
