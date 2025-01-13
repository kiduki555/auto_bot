from typing import Dict, Any, Tuple
import pandas as pd
from ..base_strategy import BaseStrategy
from ...indicators.volume import VWAPIndicator
from ...indicators.momentum import RSIIndicator
from ...indicators.volatility import ATRIndicator


class VWAPBounceStrategy(BaseStrategy):
    """
    VWAP Bounce trading strategy
    
    Entry Rules:
    - Long: Price bounces up from VWAP with RSI oversold
    - Short: Price bounces down from VWAP with RSI overbought
    
    Exit Rules:
    - Take profit at R:R ratio
    - Stop loss based on ATR
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Initialize strategy
        
        Args:
            params: Dictionary with parameters:
                - rsi_period: RSI period (default: 14)
                - rsi_overbought: RSI overbought level (default: 70)
                - rsi_oversold: RSI oversold level (default: 30)
                - atr_period: ATR period (default: 14)
                - atr_multiplier: ATR multiplier for stop loss (default: 2)
                - vwap_deviation: VWAP deviation for signal (default: 0.1)
                - risk_reward_ratio: Risk/Reward ratio (default: 2)
                - risk_per_trade: Risk per trade in % (default: 1)
        """
        super().__init__(params)
        
        # Strategy parameters
        self.rsi_period = self.params.get('rsi_period', 14)
        self.rsi_overbought = self.params.get('rsi_overbought', 70)
        self.rsi_oversold = self.params.get('rsi_oversold', 30)
        self.atr_period = self.params.get('atr_period', 14)
        self.atr_multiplier = self.params.get('atr_multiplier', 2)
        self.vwap_deviation = self.params.get('vwap_deviation', 0.1)
        self.risk_reward_ratio = self.params.get('risk_reward_ratio', 2)
        self.risk_per_trade = self.params.get('risk_per_trade', 1)
        
        # Initialize indicators
        self.vwap = VWAPIndicator()
        self.rsi = RSIIndicator(params={'period': self.rsi_period})
        self.atr = ATRIndicator(params={'period': self.atr_period})
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals"""
        if not self.validate_data(data):
            raise ValueError("Invalid data format")
            
        # Calculate indicators
        data = self.vwap.calculate(data)
        data = self.rsi.calculate(data)
        data = self.atr.calculate(data)
        
        # Initialize signal column
        data['signal'] = 0
        
        # Calculate VWAP deviation percentage
        data['vwap_dev'] = (data['close'] - data['vwap']) / data['vwap'] * 100
        
        for i in range(1, len(data)):
            # Long signal conditions
            if (data['vwap_dev'].iloc[i-1] <= -self.vwap_deviation and
                data['vwap_dev'].iloc[i] > -self.vwap_deviation and
                data['rsi'].iloc[i] < self.rsi_oversold):
                
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
                    signal_type='LONG (VWAP Bounce)',
                    price=data['close'].iloc[i],
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )
                
            # Short signal conditions
            elif (data['vwap_dev'].iloc[i-1] >= self.vwap_deviation and
                  data['vwap_dev'].iloc[i] < self.vwap_deviation and
                  data['rsi'].iloc[i] > self.rsi_overbought):
                
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
                    signal_type='SHORT (VWAP Bounce)',
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
