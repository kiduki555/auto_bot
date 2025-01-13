from typing import Dict, Any, Tuple
import pandas as pd
from ..base_strategy import BaseStrategy
from ...indicators.momentum import MACDIndicator
from ...indicators.volatility import ATRIndicator


class MACDCrossoverStrategy(BaseStrategy):
    """
    MACD Crossover trading strategy
    
    Entry Rules:
    - Long: MACD line crosses above signal line
    - Short: MACD line crosses below signal line
    
    Exit Rules:
    - Take profit at R:R ratio
    - Stop loss based on ATR
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Initialize strategy
        
        Args:
            params: Dictionary with parameters:
                - fast_period: Fast EMA period (default: 12)
                - slow_period: Slow EMA period (default: 26)
                - signal_period: Signal line period (default: 9)
                - atr_period: ATR period (default: 14)
                - atr_multiplier: ATR multiplier for stop loss (default: 2)
                - risk_reward_ratio: Risk/Reward ratio (default: 2)
                - risk_per_trade: Risk per trade in % (default: 1)
        """
        super().__init__(params)
        
        # Strategy parameters
        self.fast_period = self.params.get('fast_period', 12)
        self.slow_period = self.params.get('slow_period', 26)
        self.signal_period = self.params.get('signal_period', 9)
        self.atr_period = self.params.get('atr_period', 14)
        self.atr_multiplier = self.params.get('atr_multiplier', 2)
        self.risk_reward_ratio = self.params.get('risk_reward_ratio', 2)
        self.risk_per_trade = self.params.get('risk_per_trade', 1)
        
        # Initialize indicators
        self.macd = MACDIndicator(params={
            'fast_period': self.fast_period,
            'slow_period': self.slow_period,
            'signal_period': self.signal_period
        })
        self.atr = ATRIndicator(params={
            'period': self.atr_period
        })
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals"""
        if not self.validate_data(data):
            raise ValueError("Invalid data format")
            
        # Calculate indicators
        data = self.macd.calculate(data)
        data = self.atr.calculate(data)
        
        # Initialize signal column
        data['signal'] = 0
        
        # Generate signals
        for i in range(1, len(data)):
            # Long signal
            if (data['macd_line'].iloc[i-1] <= data['macd_signal'].iloc[i-1] and
                data['macd_line'].iloc[i] > data['macd_signal'].iloc[i]):
                data.loc[data.index[i], 'signal'] = 1
                
                # Calculate exit points
                stop_loss, take_profit = self.calculate_exit_points(
                    entry_price=data['close'].iloc[i],
                    side='long',
                    risk_reward_ratio=self.risk_reward_ratio
                )
                
                # Log signal
                self.log_signal(
                    timestamp=data.index[i],
                    signal_type='LONG',
                    price=data['close'].iloc[i],
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )
                
            # Short signal
            elif (data['macd_line'].iloc[i-1] >= data['macd_signal'].iloc[i-1] and
                  data['macd_line'].iloc[i] < data['macd_signal'].iloc[i]):
                data.loc[data.index[i], 'signal'] = -1
                
                # Calculate exit points
                stop_loss, take_profit = self.calculate_exit_points(
                    entry_price=data['close'].iloc[i],
                    side='short',
                    risk_reward_ratio=self.risk_reward_ratio
                )
                
                # Log signal
                self.log_signal(
                    timestamp=data.index[i],
                    signal_type='SHORT',
                    price=data['close'].iloc[i],
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )
                
        return data
        
    def calculate_position_size(
        self,
        capital: float,
        entry_price: float,
        stop_loss: float
    ) -> float:
        """Calculate position size based on risk"""
        risk_amount = capital * (self.risk_per_trade / 100)
        price_risk = abs(entry_price - stop_loss)
        
        if price_risk == 0:
            return 0
            
        position_size = risk_amount / price_risk
        return position_size
        
    def calculate_exit_points(
        self,
        entry_price: float,
        side: str,
        risk_reward_ratio: float = None
    ) -> Tuple[float, float]:
        """Calculate stop loss and take profit levels"""
        if risk_reward_ratio is None:
            risk_reward_ratio = self.risk_reward_ratio
            
        atr_value = self.atr_multiplier * self.atr_period
        
        if side == 'long':
            stop_loss = entry_price - atr_value
            take_profit = entry_price + (atr_value * risk_reward_ratio)
        else:  # short
            stop_loss = entry_price + atr_value
            take_profit = entry_price - (atr_value * risk_reward_ratio)
            
        return stop_loss, take_profit
