from typing import List, Optional
import pandas as pd
from ta.trend import ema_indicator


class EMAStrategy:
    """
    EMA Crossover trading strategy implementation
    """
    def __init__(
        self,
        short_period: int = 20,
        long_period: int = 50
    ):
        self.short_period = short_period
        self.long_period = long_period

    def calculate_ema(
        self,
        prices: List[float],
        period: int
    ) -> List[float]:
        """Calculate EMA for given period"""
        return ema_indicator(
            pd.Series(prices),
            window=period
        ).tolist()

    def get_signal(
        self,
        prices: List[float],
        current_position: int
    ) -> Optional[str]:
        """
        Generate trading signal based on EMA crossover
        
        Args:
            prices: List of closing prices
            current_position: Current position (-1 for short, 0 for none, 1 for long)
            
        Returns:
            'buy', 'sell', or None
        """
        ema_short = self.calculate_ema(prices, self.short_period)
        ema_long = self.calculate_ema(prices, self.long_period)

        if len(ema_short) < 2 or len(ema_long) < 2:
            return None

        # Check for crossover
        current_idx = -1
        prev_idx = -2

        # Golden Cross (Short EMA crosses above Long EMA)
        if (ema_short[prev_idx] <= ema_long[prev_idx] and 
            ema_short[current_idx] > ema_long[current_idx] and
            current_position <= 0):
            return 'buy'
        
        # Death Cross (Short EMA crosses below Long EMA)
        elif (ema_short[prev_idx] >= ema_long[prev_idx] and 
              ema_short[current_idx] < ema_long[current_idx] and
              current_position >= 0):
            return 'sell'

        return None


class TripleEMAStrategy:
    """
    Triple EMA trading strategy implementation
    """
    def __init__(
        self,
        fast_period: int = 3,
        medium_period: int = 6,
        slow_period: int = 9
    ):
        self.fast_period = fast_period
        self.medium_period = medium_period
        self.slow_period = slow_period

    def calculate_emas(
        self,
        prices: List[float]
    ) -> tuple[List[float], List[float], List[float]]:
        """Calculate three EMAs"""
        ema_fast = ema_indicator(
            pd.Series(prices),
            window=self.fast_period
        ).tolist()
        
        ema_medium = ema_indicator(
            pd.Series(prices),
            window=self.medium_period
        ).tolist()
        
        ema_slow = ema_indicator(
            pd.Series(prices),
            window=self.slow_period
        ).tolist()

        return ema_fast, ema_medium, ema_slow

    def get_signal(
        self,
        prices: List[float],
        current_position: int
    ) -> Optional[str]:
        """
        Generate trading signal based on Triple EMA alignment
        
        Args:
            prices: List of closing prices
            current_position: Current position (-1 for short, 0 for none, 1 for long)
            
        Returns:
            'buy', 'sell', or None
        """
        ema_fast, ema_medium, ema_slow = self.calculate_emas(prices)

        if len(ema_fast) < 2 or len(ema_medium) < 2 or len(ema_slow) < 2:
            return None

        # Check EMA alignment
        if (ema_fast[-1] > ema_medium[-1] > ema_slow[-1] and
            current_position <= 0):
            return 'buy'
        
        elif (ema_fast[-1] < ema_medium[-1] < ema_slow[-1] and
              current_position >= 0):
            return 'sell'

        return None
