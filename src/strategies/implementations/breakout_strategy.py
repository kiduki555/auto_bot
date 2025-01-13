from typing import List, Optional, Dict
import numpy as np
import pandas as pd


class BreakoutStrategy:
    """
    Volume-based breakout trading strategy
    """
    def __init__(
        self,
        lookback_period: int = 20,
        volume_threshold: float = 2.0
    ):
        self.lookback_period = lookback_period
        self.volume_threshold = volume_threshold

    def calculate_indicators(
        self,
        prices: List[float],
        volumes: List[float]
    ) -> Dict[str, float]:
        """Calculate price and volume indicators"""
        if len(prices) < self.lookback_period or len(volumes) < self.lookback_period:
            return {}

        # Calculate price levels
        price_window = prices[-self.lookback_period:]
        max_price = max(price_window[:-1])  # Exclude current price
        min_price = min(price_window[:-1])  # Exclude current price
        
        # Calculate volume levels
        volume_window = volumes[-self.lookback_period:]
        max_volume = max(volume_window[:-1])  # Exclude current volume
        avg_volume = np.mean(volume_window[:-1])  # Average volume excluding current

        return {
            'max_price': max_price,
            'min_price': min_price,
            'max_volume': max_volume,
            'avg_volume': avg_volume
        }

    def get_signal(
        self,
        prices: List[float],
        volumes: List[float],
        current_position: int
    ) -> Optional[str]:
        """
        Generate trading signal based on price and volume breakouts
        
        Args:
            prices: List of closing prices
            volumes: List of trading volumes
            current_position: Current position (-1 for short, 0 for none, 1 for long)
            
        Returns:
            'buy', 'sell', or None
        """
        if len(prices) < self.lookback_period or len(volumes) < self.lookback_period:
            return None

        indicators = self.calculate_indicators(prices, volumes)
        if not indicators:
            return None

        current_price = prices[-1]
        current_volume = volumes[-1]

        # Check for bullish breakout
        if (current_price > indicators['max_price'] and
            current_volume > self.volume_threshold * indicators['avg_volume'] and
            current_position <= 0):
            return 'buy'

        # Check for bearish breakout
        elif (current_price < indicators['min_price'] and
              current_volume > self.volume_threshold * indicators['avg_volume'] and
              current_position >= 0):
            return 'sell'

        return None


class CandlePatternStrategy:
    """
    Candlestick pattern recognition strategy
    """
    def __init__(
        self,
        wick_multiplier: float = 10.0
    ):
        self.wick_multiplier = wick_multiplier

    def get_signal(
        self,
        opens: List[float],
        highs: List[float],
        lows: List[float],
        closes: List[float],
        current_position: int
    ) -> Optional[str]:
        """
        Generate trading signal based on candlestick patterns
        
        Args:
            opens: List of opening prices
            highs: List of high prices
            lows: List of low prices
            closes: List of closing prices
            current_position: Current position (-1 for short, 0 for none, 1 for long)
            
        Returns:
            'buy', 'sell', or None
        """
        if len(closes) < 5:  # Need at least 5 candles
            return None

        current_idx = -1
        
        # Check for bullish reversal pattern
        # 3 red candles followed by a green candle with a long wick
        if (closes[current_idx-4] > closes[current_idx-3] > closes[current_idx-2] and
            closes[current_idx-1] > opens[current_idx-1] and
            (highs[current_idx-1] - closes[current_idx-1] +
             opens[current_idx-1] - lows[current_idx-1]) >
            self.wick_multiplier * (closes[current_idx-1] - opens[current_idx-1]) and
            closes[current_idx] > closes[current_idx-1] and
            current_position <= 0):
            return 'buy'

        # Check for bearish reversal pattern
        # 3 green candles followed by a red candle with a long wick
        elif (closes[current_idx-4] < closes[current_idx-3] < closes[current_idx-2] and
              closes[current_idx-1] < opens[current_idx-1] and
              (highs[current_idx-1] - opens[current_idx-1] +
               closes[current_idx-1] - lows[current_idx-1]) >
              self.wick_multiplier * (opens[current_idx-1] - closes[current_idx-1]) and
              closes[current_idx] < closes[current_idx-1] and
              current_position >= 0):
            return 'sell'

        return None
