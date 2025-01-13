from typing import List, Optional, Dict
import pandas as pd
from ta.momentum import stoch, stoch_signal, rsi
from ta.trend import macd, macd_signal


class StochRSIMACDStrategy:
    """
    Combined Stochastic RSI and MACD trading strategy
    """
    def __init__(
        self,
        rsi_period: int = 14,
        stoch_period: int = 14,
        stoch_smooth_k: int = 3,
        stoch_smooth_d: int = 3,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        oversold: float = 20,
        overbought: float = 80
    ):
        self.rsi_period = rsi_period
        self.stoch_period = stoch_period
        self.stoch_smooth_k = stoch_smooth_k
        self.stoch_smooth_d = stoch_smooth_d
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.oversold = oversold
        self.overbought = overbought

    def calculate_indicators(
        self,
        prices: List[float]
    ) -> Dict[str, List[float]]:
        """Calculate all required indicators"""
        price_series = pd.Series(prices)
        
        # Calculate RSI
        rsi_values = rsi(
            price_series,
            window=self.rsi_period
        )
        
        # Calculate Stochastic
        stoch_k = stoch(
            high=price_series,
            low=price_series,
            close=price_series,
            window=self.stoch_period,
            smooth_window=self.stoch_smooth_k
        )
        
        stoch_d = stoch_signal(
            high=price_series,
            low=price_series,
            close=price_series,
            window=self.stoch_period,
            smooth_window=self.stoch_smooth_d
        )
        
        # Calculate MACD
        macd_line = macd(
            price_series,
            window_fast=self.macd_fast,
            window_slow=self.macd_slow
        )
        
        macd_signal_line = macd_signal(
            price_series,
            window_fast=self.macd_fast,
            window_slow=self.macd_slow,
            window_sign=self.macd_signal
        )

        return {
            'rsi': rsi_values.tolist(),
            'stoch_k': stoch_k.tolist(),
            'stoch_d': stoch_d.tolist(),
            'macd': macd_line.tolist(),
            'macd_signal': macd_signal_line.tolist()
        }

    def get_signal(
        self,
        prices: List[float],
        current_position: int
    ) -> Optional[str]:
        """
        Generate trading signal based on Stochastic RSI and MACD
        
        Args:
            prices: List of closing prices
            current_position: Current position (-1 for short, 0 for none, 1 for long)
            
        Returns:
            'buy', 'sell', or None
        """
        indicators = self.calculate_indicators(prices)
        
        if not all(indicators.values()):
            return None

        current_idx = -1
        
        stoch_k = indicators['stoch_k'][current_idx]
        stoch_d = indicators['stoch_d'][current_idx]
        rsi_value = indicators['rsi'][current_idx]
        macd_line = indicators['macd'][current_idx]
        macd_signal_line = indicators['macd_signal'][current_idx]

        # Buy conditions:
        # 1. Stochastic K and D lines are below oversold level
        # 2. RSI is below oversold level
        # 3. MACD line crosses above signal line
        if (stoch_k < self.oversold and 
            stoch_d < self.oversold and
            rsi_value < self.oversold and
            macd_line > macd_signal_line and
            current_position <= 0):
            return 'buy'

        # Sell conditions:
        # 1. Stochastic K and D lines are above overbought level
        # 2. RSI is above overbought level
        # 3. MACD line crosses below signal line
        elif (stoch_k > self.overbought and 
              stoch_d > self.overbought and
              rsi_value > self.overbought and
              macd_line < macd_signal_line and
              current_position >= 0):
            return 'sell'

        return None
