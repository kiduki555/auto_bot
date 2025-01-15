from typing import List, Dict, Optional
import pandas as pd

class FutureTrendStrategy:
    """
    Future Trend trading strategy implementation
    """
    def __init__(self, period: int = 25):
        self.period = period

    def calculate_volume_delta(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate volume deltas and totals"""
        delta1 = data['volume'].rolling(window=self.period).sum().iloc[-1]
        delta2 = data['volume'].rolling(window=self.period * 2).sum().iloc[-1] - delta1
        delta3 = data['volume'].rolling(window=self.period * 3).sum().iloc[-1] - delta1 - delta2

        total1 = data['volume'].rolling(window=self.period).sum().iloc[-1]
        total2 = data['volume'].rolling(window=self.period * 2).sum().iloc[-1] - total1
        total3 = data['volume'].rolling(window=self.period * 3).sum().iloc[-1] - total1 - total2

        return {
            'delta1': delta1,
            'delta2': delta2,
            'delta3': delta3,
            'total1': total1,
            'total2': total2,
            'total3': total3
        }

    def get_signal(self, data: pd.DataFrame, current_position: int) -> Optional[str]:
        """
        Generate trading signal based on future trend
        
        Args:
            data: DataFrame with OHLCV data
            current_position: Current position (-1 for short, 0 for none, 1 for long)
            
        Returns:
            'buy', 'sell', or None
        """
        if len(data) < self.period * 3:
            return None

        volume_data = self.calculate_volume_delta(data)

        # Determine the signal based on volume deltas
        if volume_data['delta1'] > 0 and current_position <= 0:
            return 'buy'
        elif volume_data['delta1'] < 0 and current_position >= 0:
            return 'sell'

        return None

    def get_strategy_name(self) -> str:
        return "Future Trend Strategy"  