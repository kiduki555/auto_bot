from typing import Dict, Optional
import pandas as pd

class AdaptiveSuperTrendStrategy:
    """
    Adaptive SuperTrend trading strategy implementation
    """
    def __init__(self, atr_length: int = 10, factor: float = 3.0, training_data_period: int = 100,
                 highvol: float = 0.75, midvol: float = 0.5, lowvol: float = 0.25):
        self.atr_length = atr_length
        self.factor = factor
        self.training_data_period = training_data_period
        self.highvol = highvol
        self.midvol = midvol
        self.lowvol = lowvol

    def calculate_atr(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Average True Range (ATR)"""
        high = data['high']
        low = data['low']
        close = data['close']
        tr = pd.concat([high - low, 
                        (high - close.shift()).abs(), 
                        (low - close.shift()).abs()], axis=1).max(axis=1)
        return tr.rolling(window=self.atr_length).mean()

    def calculate_volatility_clusters(self, volatility: pd.Series) -> Dict[str, float]:
        """Calculate volatility clusters based on ATR"""
        upper = volatility.rolling(window=self.training_data_period).max().iloc[-1]
        lower = volatility.rolling(window=self.training_data_period).min().iloc[-1]

        high_volatility = lower + (upper - lower) * self.highvol
        medium_volatility = lower + (upper - lower) * self.midvol
        low_volatility = lower + (upper - lower) * self.lowvol

        return {
            'high_volatility': high_volatility,
            'medium_volatility': medium_volatility,
            'low_volatility': low_volatility
        }

    def calculate_supertrend(self, data: pd.DataFrame, assigned_centroid: float) -> pd.Series:
        """Calculate SuperTrend based on assigned centroid"""
        hl2 = (data['high'] + data['low']) / 2
        atr = self.calculate_atr(data)
        upper_band = hl2 + (self.factor * atr)
        lower_band = hl2 - (self.factor * atr)

        supertrend = pd.Series(index=data.index, dtype=float)
        direction = pd.Series(index=data.index, dtype=int)

        for i in range(1, len(data)):
            if data['close'][i] > upper_band[i - 1]:
                supertrend[i] = lower_band[i]
                direction[i] = -1
            elif data['close'][i] < lower_band[i - 1]:
                supertrend[i] = upper_band[i]
                direction[i] = 1
            else:
                supertrend[i] = supertrend[i - 1]
                direction[i] = direction[i - 1]

        return supertrend, direction

    def get_signal(self, data: pd.DataFrame, current_position: int) -> Optional[str]:
        """
        Generate trading signal based on Adaptive SuperTrend
        
        Args:
            data: DataFrame with OHLCV data
            current_position: Current position (-1 for short, 0 for none, 1 for long)
            
        Returns:
            'buy', 'sell', or None
        """
        if len(data) < self.training_data_period:
            return None

        volatility = self.calculate_atr(data)
        clusters = self.calculate_volatility_clusters(volatility)

        # Assign centroid based on current volatility
        assigned_centroid = clusters['high_volatility'] if volatility.iloc[-1] > clusters['high_volatility'] else \
                            clusters['medium_volatility'] if volatility.iloc[-1] > clusters['medium_volatility'] else \
                            clusters['low_volatility']

        supertrend, direction = self.calculate_supertrend(data, assigned_centroid)

        # Determine the signal based on direction
        if direction.iloc[-1] == -1 and current_position <= 0:
            return 'buy'
        elif direction.iloc[-1] == 1 and current_position >= 0:
            return 'sell'

        return None

    def get_strategy_name(self) -> str:
        return "Adaptive SuperTrend Strategy" 