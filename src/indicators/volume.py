from typing import Dict, Any
import pandas as pd
import numpy as np
from .base_indicator import BaseIndicator


class OBVIndicator(BaseIndicator):
    """On Balance Volume indicator"""
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate OBV values"""
        if not self.validate_data(data):
            raise ValueError("Invalid data format")
            
        data = data.copy()
        
        # Calculate price changes
        price_change = data['close'].diff()
        
        # Calculate OBV
        data['obv'] = (
            data['volume'] * np.where(price_change > 0, 1,
            np.where(price_change < 0, -1, 0))
        ).cumsum()
        
        return data


class VWAPIndicator(BaseIndicator):
    """Volume Weighted Average Price indicator"""
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Initialize VWAP indicator
        
        Args:
            params: Dictionary with parameters:
                - anchor: VWAP anchor point ('D' for daily) (default: 'D')
        """
        super().__init__(params)
        self.anchor = self.params.get('anchor', 'D')
        
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate VWAP values"""
        if not self.validate_data(data):
            raise ValueError("Invalid data format")
            
        data = data.copy()
        
        # Calculate typical price
        data['typical_price'] = (
            data['high'] + data['low'] + data['close']
        ) / 3
        
        # Calculate VWAP components
        data['vwap_cum_vol'] = data.groupby(
            pd.Grouper(freq=self.anchor)
        )['volume'].cumsum()
        data['vwap_cum_vol_price'] = data.groupby(
            pd.Grouper(freq=self.anchor)
        ).apply(
            lambda x: (x['typical_price'] * x['volume']).cumsum()
        )
        
        # Calculate VWAP
        data['vwap'] = (
            data['vwap_cum_vol_price'] / data['vwap_cum_vol']
        )
        
        # Clean up temporary columns
        data = data.drop(
            ['typical_price', 'vwap_cum_vol', 'vwap_cum_vol_price'],
            axis=1
        )
        
        return data


class AccumulationDistribution(BaseIndicator):
    """Accumulation/Distribution indicator"""
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate A/D values"""
        if not self.validate_data(data):
            raise ValueError("Invalid data format")
            
        data = data.copy()
        
        # Calculate money flow multiplier
        data['mf_multiplier'] = (
            ((data['close'] - data['low']) -
             (data['high'] - data['close'])) /
            (data['high'] - data['low'])
        )
        
        # Calculate money flow volume
        data['mf_volume'] = data['mf_multiplier'] * data['volume']
        
        # Calculate A/D line
        data['ad_line'] = data['mf_volume'].cumsum()
        
        # Clean up temporary columns
        data = data.drop(['mf_multiplier', 'mf_volume'], axis=1)
        
        return data


class ChaikinMoneyFlow(BaseIndicator):
    """Chaikin Money Flow indicator"""
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Initialize CMF indicator
        
        Args:
            params: Dictionary with parameters:
                - period: CMF period (default: 20)
        """
        super().__init__(params)
        self.period = self.params.get('period', 20)
        
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate CMF values"""
        if not self.validate_data(data):
            raise ValueError("Invalid data format")
            
        data = data.copy()
        
        # Calculate money flow multiplier
        data['mf_multiplier'] = (
            ((data['close'] - data['low']) -
             (data['high'] - data['close'])) /
            (data['high'] - data['low'])
        )
        
        # Calculate money flow volume
        data['mf_volume'] = data['mf_multiplier'] * data['volume']
        
        # Calculate CMF
        data[f'cmf_{self.period}'] = (
            data['mf_volume'].rolling(window=self.period).sum() /
            data['volume'].rolling(window=self.period).sum()
        )
        
        # Clean up temporary columns
        data = data.drop(['mf_multiplier', 'mf_volume'], axis=1)
        
        return data
