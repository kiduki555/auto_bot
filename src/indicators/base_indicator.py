from typing import Dict, Any
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod


class BaseIndicator(ABC):
    """Base class for all technical indicators"""
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Initialize indicator with parameters
        
        Args:
            params: Dictionary of indicator parameters
        """
        self.params = params or {}
        
    @abstractmethod
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate indicator values
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with indicator values
        """
        pass
        
    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate input data
        
        Args:
            data: DataFrame to validate
            
        Returns:
            bool: Whether data is valid
        """
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        return all(col in data.columns for col in required_columns)
