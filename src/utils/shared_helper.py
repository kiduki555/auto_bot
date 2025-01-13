from typing import List, Dict, Any, Optional, Union
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from .logger import Logger


class SharedHelper:
    """
    Shared utility functions for trading operations
    """
    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger or Logger('SharedHelper')

    def validate_ohlcv_data(
        self,
        data: pd.DataFrame,
        required_columns: List[str] = ['open', 'high', 'low', 'close', 'volume']
    ) -> bool:
        """
        Validate OHLCV data structure
        
        Args:
            data: DataFrame with OHLCV data
            required_columns: List of required column names
            
        Returns:
            bool: Whether data is valid
        """
        try:
            # Check if all required columns exist
            if not all(col in data.columns for col in required_columns):
                self.logger.log_error(
                    f"Missing required columns. Expected: {required_columns}"
                )
                return False

            # Check for missing values
            if data[required_columns].isnull().any().any():
                self.logger.log_error("Data contains missing values")
                return False

            # Validate price relationships
            if not all(data['high'] >= data['low']) or \
               not all(data['high'] >= data['close']) or \
               not all(data['high'] >= data['open']) or \
               not all(data['low'] <= data['close']) or \
               not all(data['low'] <= data['open']):
                self.logger.log_error("Invalid price relationships in data")
                return False

            # Validate volume
            if not all(data['volume'] >= 0):
                self.logger.log_error("Negative volume values found")
                return False

            return True

        except Exception as e:
            self.logger.log_error(f"Error validating OHLCV data: {str(e)}")
            return False

    def resample_ohlcv(
        self,
        data: pd.DataFrame,
        timeframe: str
    ) -> pd.DataFrame:
        """
        Resample OHLCV data to a different timeframe
        
        Args:
            data: DataFrame with OHLCV data
            timeframe: Target timeframe (e.g., '1H', '4H', '1D')
            
        Returns:
            Resampled DataFrame
        """
        try:
            # Ensure data is sorted by index
            data = data.sort_index()

            # Define resampling rules
            ohlc_dict = {
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }

            # Resample data
            resampled = data.resample(timeframe).agg(ohlc_dict)

            # Remove rows with missing values
            resampled = resampled.dropna()

            return resampled

        except Exception as e:
            self.logger.log_error(f"Error resampling OHLCV data: {str(e)}")
            return pd.DataFrame()

    def calculate_vwap(
        self,
        data: pd.DataFrame,
        window: Optional[int] = None
    ) -> pd.Series:
        """
        Calculate Volume Weighted Average Price
        
        Args:
            data: DataFrame with OHLCV data
            window: Rolling window size (optional)
            
        Returns:
            Series with VWAP values
        """
        try:
            # Calculate typical price
            typical_price = (data['high'] + data['low'] + data['close']) / 3
            
            # Calculate VWAP
            if window:
                # Rolling VWAP
                vwap = (
                    (typical_price * data['volume']).rolling(window=window).sum() /
                    data['volume'].rolling(window=window).sum()
                )
            else:
                # Regular VWAP
                vwap = (
                    (typical_price * data['volume']).cumsum() /
                    data['volume'].cumsum()
                )
            
            return vwap

        except Exception as e:
            self.logger.log_error(f"Error calculating VWAP: {str(e)}")
            return pd.Series()

    def calculate_pivot_points(
        self,
        data: pd.DataFrame,
        method: str = 'standard'
    ) -> pd.DataFrame:
        """
        Calculate pivot points and support/resistance levels
        
        Args:
            data: DataFrame with OHLCV data
            method: Pivot point calculation method ('standard', 'fibonacci', 'woodie')
            
        Returns:
            DataFrame with pivot points and levels
        """
        try:
            high = data['high'].shift(1)
            low = data['low'].shift(1)
            close = data['close'].shift(1)
            
            if method == 'standard':
                pivot = (high + low + close) / 3
                r1 = 2 * pivot - low
                s1 = 2 * pivot - high
                r2 = pivot + (high - low)
                s2 = pivot - (high - low)
                r3 = high + 2 * (pivot - low)
                s3 = low - 2 * (high - pivot)
                
            elif method == 'fibonacci':
                pivot = (high + low + close) / 3
                r1 = pivot + 0.382 * (high - low)
                s1 = pivot - 0.382 * (high - low)
                r2 = pivot + 0.618 * (high - low)
                s2 = pivot - 0.618 * (high - low)
                r3 = pivot + (high - low)
                s3 = pivot - (high - low)
                
            elif method == 'woodie':
                pivot = (high + low + 2 * close) / 4
                r1 = 2 * pivot - low
                s1 = 2 * pivot - high
                r2 = pivot + (high - low)
                s2 = pivot - (high - low)
                r3 = r1 + (high - low)
                s3 = s1 - (high - low)
                
            else:
                raise ValueError(f"Unsupported pivot point method: {method}")
            
            return pd.DataFrame({
                'pivot': pivot,
                'r1': r1, 's1': s1,
                'r2': r2, 's2': s2,
                'r3': r3, 's3': s3
            })

        except Exception as e:
            self.logger.log_error(f"Error calculating pivot points: {str(e)}")
            return pd.DataFrame()

    def detect_divergence(
        self,
        prices: pd.Series,
        indicator: pd.Series,
        window: int = 20
    ) -> pd.Series:
        """
        Detect regular and hidden divergences
        
        Args:
            prices: Series of price values
            indicator: Series of indicator values
            window: Lookback window for divergence detection
            
        Returns:
            Series with divergence signals (1: bullish, -1: bearish, 0: none)
        """
        try:
            divergence = pd.Series(0, index=prices.index)
            
            for i in range(window, len(prices)):
                price_window = prices[i-window:i+1]
                ind_window = indicator[i-window:i+1]
                
                # Find local extrema
                price_min_idx = price_window.idxmin()
                price_max_idx = price_window.idxmax()
                ind_min_idx = ind_window.idxmin()
                ind_max_idx = ind_window.idxmax()
                
                # Regular bullish divergence
                if (price_min_idx == price_window.index[-1] and
                    ind_min_idx != ind_window.index[-1] and
                    ind_window[ind_min_idx] > ind_window.iloc[-1]):
                    divergence.iloc[-1] = 1
                
                # Regular bearish divergence
                elif (price_max_idx == price_window.index[-1] and
                      ind_max_idx != ind_window.index[-1] and
                      ind_window[ind_max_idx] < ind_window.iloc[-1]):
                    divergence.iloc[-1] = -1
                
                # Hidden bullish divergence
                elif (price_min_idx != price_window.index[-1] and
                      ind_min_idx == ind_window.index[-1] and
                      price_window.iloc[-1] > price_window[price_min_idx]):
                    divergence.iloc[-1] = 1
                
                # Hidden bearish divergence
                elif (price_max_idx != price_window.index[-1] and
                      ind_max_idx == ind_window.index[-1] and
                      price_window.iloc[-1] < price_window[price_max_idx]):
                    divergence.iloc[-1] = -1
            
            return divergence

        except Exception as e:
            self.logger.log_error(f"Error detecting divergence: {str(e)}")
            return pd.Series()

    def calculate_risk_metrics(
        self,
        returns: pd.Series,
        risk_free_rate: float = 0.0
    ) -> Dict[str, float]:
        """
        Calculate various risk metrics
        
        Args:
            returns: Series of period returns
            risk_free_rate: Risk-free rate (annualized)
            
        Returns:
            Dictionary of risk metrics
        """
        try:
            # Convert to numpy array for calculations
            returns_arr = returns.dropna().values
            
            # Basic metrics
            total_return = (1 + returns_arr).prod() - 1
            avg_return = returns_arr.mean()
            std_dev = returns_arr.std()
            
            # Sharpe Ratio
            excess_returns = returns_arr - risk_free_rate/252  # Daily risk-free rate
            sharpe_ratio = np.sqrt(252) * excess_returns.mean() / std_dev
            
            # Sortino Ratio
            downside_returns = returns_arr[returns_arr < 0]
            downside_std = downside_returns.std()
            sortino_ratio = (
                np.sqrt(252) * excess_returns.mean() / downside_std
                if len(downside_returns) > 0 else 0
            )
            
            # Maximum Drawdown
            cum_returns = (1 + returns_arr).cumprod()
            rolling_max = np.maximum.accumulate(cum_returns)
            drawdowns = (rolling_max - cum_returns) / rolling_max
            max_drawdown = drawdowns.max()
            
            # Calmar Ratio
            calmar_ratio = (
                -total_return / max_drawdown
                if max_drawdown != 0 else 0
            )
            
            return {
                'total_return': total_return,
                'avg_return': avg_return,
                'std_dev': std_dev,
                'sharpe_ratio': sharpe_ratio,
                'sortino_ratio': sortino_ratio,
                'max_drawdown': max_drawdown,
                'calmar_ratio': calmar_ratio
            }

        except Exception as e:
            self.logger.log_error(f"Error calculating risk metrics: {str(e)}")
            return {}
