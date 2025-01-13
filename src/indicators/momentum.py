from typing import Dict, Any
import pandas as pd
import numpy as np
from .base_indicator import BaseIndicator


class RSIIndicator(BaseIndicator):
    """Relative Strength Index indicator"""
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Initialize RSI indicator
        
        Args:
            params: Dictionary with parameters:
                - period: RSI period (default: 14)
                - column: Column to calculate RSI for (default: 'close')
        """
        super().__init__(params)
        self.period = self.params.get('period', 14)
        self.column = self.params.get('column', 'close')
        
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate RSI values"""
        if not self.validate_data(data):
            raise ValueError("Invalid data format")
            
        data = data.copy()
        
        # Calculate price changes
        delta = data[self.column].diff()
        
        # Separate gains and losses
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        
        # Calculate RS and RSI
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs))
        
        return data


class StochasticIndicator(BaseIndicator):
    """Stochastic Oscillator indicator"""
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Initialize Stochastic indicator
        
        Args:
            params: Dictionary with parameters:
                - k_period: %K period (default: 14)
                - d_period: %D period (default: 3)
                - smooth_k: %K smoothing period (default: 3)
        """
        super().__init__(params)
        self.k_period = self.params.get('k_period', 14)
        self.d_period = self.params.get('d_period', 3)
        self.smooth_k = self.params.get('smooth_k', 3)
        
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate Stochastic Oscillator values"""
        if not self.validate_data(data):
            raise ValueError("Invalid data format")
            
        data = data.copy()
        
        # Calculate %K
        low_min = data['low'].rolling(window=self.k_period).min()
        high_max = data['high'].rolling(window=self.k_period).max()
        
        k = 100 * ((data['close'] - low_min) / (high_max - low_min))
        
        # Apply smoothing to %K if specified
        if self.smooth_k > 1:
            k = k.rolling(window=self.smooth_k).mean()
            
        # Calculate %D
        d = k.rolling(window=self.d_period).mean()
        
        data['stoch_k'] = k
        data['stoch_d'] = d
        
        return data


class MACDIndicator(BaseIndicator):
    """Moving Average Convergence Divergence indicator"""
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Initialize MACD indicator
        
        Args:
            params: Dictionary with parameters:
                - fast_period: Fast EMA period (default: 12)
                - slow_period: Slow EMA period (default: 26)
                - signal_period: Signal line period (default: 9)
                - column: Column to calculate MACD for (default: 'close')
        """
        super().__init__(params)
        self.fast_period = self.params.get('fast_period', 12)
        self.slow_period = self.params.get('slow_period', 26)
        self.signal_period = self.params.get('signal_period', 9)
        self.column = self.params.get('column', 'close')
        
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate MACD values"""
        if not self.validate_data(data):
            raise ValueError("Invalid data format")
            
        data = data.copy()
        
        # Calculate fast and slow EMAs
        fast_ema = data[self.column].ewm(
            span=self.fast_period,
            adjust=False
        ).mean()
        slow_ema = data[self.column].ewm(
            span=self.slow_period,
            adjust=False
        ).mean()
        
        # Calculate MACD line
        data['macd_line'] = fast_ema - slow_ema
        
        # Calculate signal line
        data['macd_signal'] = data['macd_line'].ewm(
            span=self.signal_period,
            adjust=False
        ).mean()
        
        # Calculate MACD histogram
        data['macd_hist'] = data['macd_line'] - data['macd_signal']
        
        return data


class ADXIndicator(BaseIndicator):
    """Average Directional Index indicator"""
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Initialize ADX indicator
        
        Args:
            params: Dictionary with parameters:
                - period: ADX period (default: 14)
        """
        super().__init__(params)
        self.period = self.params.get('period', 14)
        
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate ADX values"""
        if not self.validate_data(data):
            raise ValueError("Invalid data format")
            
        data = data.copy()
        
        # Calculate True Range
        data['tr1'] = abs(data['high'] - data['low'])
        data['tr2'] = abs(data['high'] - data['close'].shift(1))
        data['tr3'] = abs(data['low'] - data['close'].shift(1))
        data['tr'] = data[['tr1', 'tr2', 'tr3']].max(axis=1)
        
        # Calculate directional movement
        data['up_move'] = data['high'] - data['high'].shift(1)
        data['down_move'] = data['low'].shift(1) - data['low']
        
        data['plus_dm'] = np.where(
            (data['up_move'] > data['down_move']) & (data['up_move'] > 0),
            data['up_move'],
            0
        )
        data['minus_dm'] = np.where(
            (data['down_move'] > data['up_move']) & (data['down_move'] > 0),
            data['down_move'],
            0
        )
        
        # Calculate smoothed values
        data['tr_' + str(self.period)] = data['tr'].rolling(
            window=self.period
        ).mean()
        data['plus_di_' + str(self.period)] = 100 * (
            data['plus_dm'].rolling(window=self.period).mean() /
            data['tr_' + str(self.period)]
        )
        data['minus_di_' + str(self.period)] = 100 * (
            data['minus_dm'].rolling(window=self.period).mean() /
            data['tr_' + str(self.period)]
        )
        
        # Calculate ADX
        data['dx'] = 100 * abs(
            data['plus_di_' + str(self.period)] -
            data['minus_di_' + str(self.period)]
        ) / (
            data['plus_di_' + str(self.period)] +
            data['minus_di_' + str(self.period)]
        )
        data['adx_' + str(self.period)] = data['dx'].rolling(
            window=self.period
        ).mean()
        
        # Clean up temporary columns
        data = data.drop(['tr1', 'tr2', 'tr3', 'tr', 'up_move', 'down_move',
                         'plus_dm', 'minus_dm', 'dx'], axis=1)
        
        return data
