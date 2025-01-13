from typing import Dict, Any
import pandas as pd
import numpy as np
from .base_indicator import BaseIndicator


class EMAIndicator(BaseIndicator):
    """Exponential Moving Average indicator"""
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Initialize EMA indicator
        
        Args:
            params: Dictionary with parameters:
                - period: EMA period (default: 20)
                - column: Column to calculate EMA for (default: 'close')
        """
        super().__init__(params)
        self.period = self.params.get('period', 20)
        self.column = self.params.get('column', 'close')
        
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate EMA values"""
        if not self.validate_data(data):
            raise ValueError("Invalid data format")
            
        data = data.copy()
        data[f'ema_{self.period}'] = data[self.column].ewm(
            span=self.period,
            adjust=False
        ).mean()
        return data


class SMAIndicator(BaseIndicator):
    """Simple Moving Average indicator"""
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Initialize SMA indicator
        
        Args:
            params: Dictionary with parameters:
                - period: SMA period (default: 20)
                - column: Column to calculate SMA for (default: 'close')
        """
        super().__init__(params)
        self.period = self.params.get('period', 20)
        self.column = self.params.get('column', 'close')
        
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate SMA values"""
        if not self.validate_data(data):
            raise ValueError("Invalid data format")
            
        data = data.copy()
        data[f'sma_{self.period}'] = data[self.column].rolling(
            window=self.period
        ).mean()
        return data


class WMAIndicator(BaseIndicator):
    """Weighted Moving Average indicator"""
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Initialize WMA indicator
        
        Args:
            params: Dictionary with parameters:
                - period: WMA period (default: 20)
                - column: Column to calculate WMA for (default: 'close')
        """
        super().__init__(params)
        self.period = self.params.get('period', 20)
        self.column = self.params.get('column', 'close')
        
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate WMA values"""
        if not self.validate_data(data):
            raise ValueError("Invalid data format")
            
        data = data.copy()
        weights = np.arange(1, self.period + 1)
        data[f'wma_{self.period}'] = data[self.column].rolling(
            window=self.period
        ).apply(lambda x: np.dot(x, weights) / weights.sum())
        return data


class HMAIndicator(BaseIndicator):
    """Hull Moving Average indicator"""
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Initialize HMA indicator
        
        Args:
            params: Dictionary with parameters:
                - period: HMA period (default: 20)
                - column: Column to calculate HMA for (default: 'close')
        """
        super().__init__(params)
        self.period = self.params.get('period', 20)
        self.column = self.params.get('column', 'close')
        
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate HMA values"""
        if not self.validate_data(data):
            raise ValueError("Invalid data format")
            
        data = data.copy()
        
        # Calculate WMAs
        period_half = int(self.period / 2)
        sqrt_period = int(np.sqrt(self.period))
        
        # WMA with period/2
        weights1 = np.arange(1, period_half + 1)
        wma1 = data[self.column].rolling(window=period_half).apply(
            lambda x: np.dot(x, weights1) / weights1.sum()
        )
        
        # WMA with period
        weights2 = np.arange(1, self.period + 1)
        wma2 = data[self.column].rolling(window=self.period).apply(
            lambda x: np.dot(x, weights2) / weights2.sum()
        )
        
        # Calculate 2 * WMA(n/2) - WMA(n)
        raw_hma = 2 * wma1 - wma2
        
        # Calculate final HMA
        weights3 = np.arange(1, sqrt_period + 1)
        data[f'hma_{self.period}'] = raw_hma.rolling(window=sqrt_period).apply(
            lambda x: np.dot(x, weights3) / weights3.sum()
        )
        
        return data
