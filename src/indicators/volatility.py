from typing import Dict, Any
import pandas as pd
import numpy as np
from .base_indicator import BaseIndicator


class ATRIndicator(BaseIndicator):
    """Average True Range indicator"""
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Initialize ATR indicator
        
        Args:
            params: Dictionary with parameters:
                - period: ATR period (default: 14)
        """
        super().__init__(params)
        self.period = self.params.get('period', 14)
        
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate ATR values"""
        if not self.validate_data(data):
            raise ValueError("Invalid data format")
            
        data = data.copy()
        
        # Calculate True Range
        data['tr1'] = abs(data['high'] - data['low'])
        data['tr2'] = abs(data['high'] - data['close'].shift(1))
        data['tr3'] = abs(data['low'] - data['close'].shift(1))
        data['tr'] = data[['tr1', 'tr2', 'tr3']].max(axis=1)
        
        # Calculate ATR
        data[f'atr_{self.period}'] = data['tr'].rolling(
            window=self.period
        ).mean()
        
        # Clean up temporary columns
        data = data.drop(['tr1', 'tr2', 'tr3', 'tr'], axis=1)
        
        return data


class BollingerBands(BaseIndicator):
    """Bollinger Bands indicator"""
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Initialize Bollinger Bands indicator
        
        Args:
            params: Dictionary with parameters:
                - period: MA period (default: 20)
                - std_dev: Number of standard deviations (default: 2)
                - column: Column to calculate BB for (default: 'close')
        """
        super().__init__(params)
        self.period = self.params.get('period', 20)
        self.std_dev = self.params.get('std_dev', 2)
        self.column = self.params.get('column', 'close')
        
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate Bollinger Bands values"""
        if not self.validate_data(data):
            raise ValueError("Invalid data format")
            
        data = data.copy()
        
        # Calculate middle band (SMA)
        data['bb_middle'] = data[self.column].rolling(
            window=self.period
        ).mean()
        
        # Calculate standard deviation
        rolling_std = data[self.column].rolling(window=self.period).std()
        
        # Calculate upper and lower bands
        data['bb_upper'] = data['bb_middle'] + (rolling_std * self.std_dev)
        data['bb_lower'] = data['bb_middle'] - (rolling_std * self.std_dev)
        
        # Calculate bandwidth and %B
        data['bb_bandwidth'] = (
            data['bb_upper'] - data['bb_lower']
        ) / data['bb_middle']
        data['bb_percent'] = (
            data[self.column] - data['bb_lower']
        ) / (data['bb_upper'] - data['bb_lower'])
        
        return data


class KeltnerChannels(BaseIndicator):
    """Keltner Channels indicator"""
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Initialize Keltner Channels indicator
        
        Args:
            params: Dictionary with parameters:
                - period: EMA period (default: 20)
                - atr_period: ATR period (default: 10)
                - multiplier: ATR multiplier (default: 2)
        """
        super().__init__(params)
        self.period = self.params.get('period', 20)
        self.atr_period = self.params.get('atr_period', 10)
        self.multiplier = self.params.get('multiplier', 2)
        
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate Keltner Channels values"""
        if not self.validate_data(data):
            raise ValueError("Invalid data format")
            
        data = data.copy()
        
        # Calculate middle line (EMA)
        data['kc_middle'] = data['close'].ewm(
            span=self.period,
            adjust=False
        ).mean()
        
        # Calculate ATR
        data['tr1'] = abs(data['high'] - data['low'])
        data['tr2'] = abs(data['high'] - data['close'].shift(1))
        data['tr3'] = abs(data['low'] - data['close'].shift(1))
        data['tr'] = data[['tr1', 'tr2', 'tr3']].max(axis=1)
        data['atr'] = data['tr'].rolling(window=self.atr_period).mean()
        
        # Calculate upper and lower channels
        data['kc_upper'] = (
            data['kc_middle'] + (data['atr'] * self.multiplier)
        )
        data['kc_lower'] = (
            data['kc_middle'] - (data['atr'] * self.multiplier)
        )
        
        # Clean up temporary columns
        data = data.drop(['tr1', 'tr2', 'tr3', 'tr', 'atr'], axis=1)
        
        return data
