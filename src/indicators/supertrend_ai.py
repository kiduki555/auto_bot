from typing import List, Dict, Optional, Union
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from ta.volatility import average_true_range


class SupertrendAI:
    """
    AI-enhanced Supertrend indicator implementation
    """
    def __init__(
        self,
        period: int = 10,
        multiplier: float = 3.0,
        clusters: int = 3,
        lookback: int = 100
    ):
        self.period = period
        self.multiplier = multiplier
        self.clusters = clusters
        self.lookback = lookback

    def calculate_supertrend(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series
    ) -> pd.DataFrame:
        """
        Calculate Supertrend indicator
        
        Args:
            high: Series of high prices
            low: Series of low prices
            close: Series of closing prices
            
        Returns:
            DataFrame with Supertrend values and trend direction
        """
        # Calculate ATR
        atr = average_true_range(high, low, close, window=self.period)

        # Calculate basic upper and lower bands
        basic_upper = (high + low) / 2 + (self.multiplier * atr)
        basic_lower = (high + low) / 2 - (self.multiplier * atr)

        # Initialize final bands and trend
        final_upper = pd.Series(index=close.index, dtype=float)
        final_lower = pd.Series(index=close.index, dtype=float)
        supertrend = pd.Series(index=close.index, dtype=float)
        trend = pd.Series(index=close.index, dtype=int)

        for i in range(len(close)):
            if i < self.period:
                final_upper.iloc[i] = basic_upper.iloc[i]
                final_lower.iloc[i] = basic_lower.iloc[i]
                supertrend.iloc[i] = (final_upper.iloc[i] + final_lower.iloc[i]) / 2
                trend.iloc[i] = 1 if close.iloc[i] > supertrend.iloc[i] else -1
                continue

            # Update upper band
            if (basic_upper.iloc[i] < final_upper.iloc[i-1] or 
                close.iloc[i-1] > final_upper.iloc[i-1]):
                final_upper.iloc[i] = basic_upper.iloc[i]
            else:
                final_upper.iloc[i] = final_upper.iloc[i-1]

            # Update lower band
            if (basic_lower.iloc[i] > final_lower.iloc[i-1] or 
                close.iloc[i-1] < final_lower.iloc[i-1]):
                final_lower.iloc[i] = basic_lower.iloc[i]
            else:
                final_lower.iloc[i] = final_lower.iloc[i-1]

            # Update supertrend and trend
            if (trend.iloc[i-1] == 1 and close.iloc[i] < final_upper.iloc[i]):
                trend.iloc[i] = -1
            elif (trend.iloc[i-1] == -1 and close.iloc[i] > final_lower.iloc[i]):
                trend.iloc[i] = 1
            else:
                trend.iloc[i] = trend.iloc[i-1]

            supertrend.iloc[i] = (
                final_upper.iloc[i] if trend.iloc[i] == -1
                else final_lower.iloc[i]
            )

        return pd.DataFrame({
            'supertrend': supertrend,
            'upper_band': final_upper,
            'lower_band': final_lower,
            'trend': trend
        })

    def identify_key_levels(
        self,
        prices: Union[List[float], pd.Series],
        n_clusters: Optional[int] = None
    ) -> np.ndarray:
        """
        Identify key price levels using K-means clustering
        
        Args:
            prices: List or Series of price values
            n_clusters: Number of clusters to use (optional)
            
        Returns:
            Array of key price levels
        """
        if isinstance(prices, list):
            prices = pd.Series(prices)

        # Prepare data for clustering
        X = prices.values.reshape(-1, 1)
        
        # Use specified or default number of clusters
        k = n_clusters if n_clusters is not None else self.clusters
        
        # Perform K-means clustering
        kmeans = KMeans(n_clusters=k, random_state=42)
        kmeans.fit(X)
        
        # Get cluster centers (key levels)
        key_levels = np.sort(kmeans.cluster_centers_.flatten())
        
        return key_levels

    def calculate_performance(
        self,
        supertrend: pd.DataFrame,
        close: pd.Series
    ) -> Dict[str, float]:
        """
        Calculate strategy performance metrics
        
        Args:
            supertrend: DataFrame with Supertrend values
            close: Series of closing prices
            
        Returns:
            Dictionary of performance metrics
        """
        # Calculate returns based on trend signals
        returns = pd.Series(index=close.index)
        returns[1:] = np.log(close[1:] / close[:-1].values)
        strategy_returns = returns * supertrend['trend'].shift(1)
        
        # Calculate metrics
        total_return = strategy_returns.sum()
        sharpe_ratio = np.sqrt(252) * (
            strategy_returns.mean() / strategy_returns.std()
        ) if len(strategy_returns) > 0 else 0
        
        # Calculate maximum drawdown
        cum_returns = strategy_returns.cumsum()
        rolling_max = cum_returns.expanding().max()
        drawdowns = rolling_max - cum_returns
        max_drawdown = drawdowns.max()
        
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': len(strategy_returns[strategy_returns > 0]) / len(strategy_returns)
        }

    def get_signal(
        self,
        high_prices: List[float],
        low_prices: List[float],
        close_prices: List[float],
        current_position: int
    ) -> Optional[str]:
        """
        Generate trading signal based on Supertrend AI
        
        Args:
            high_prices: List of high prices
            low_prices: List of low prices
            close_prices: List of closing prices
            current_position: Current position (-1 for short, 0 for none, 1 for long)
            
        Returns:
            'buy', 'sell', or None
        """
        # Convert price data to pandas Series
        high = pd.Series(high_prices)
        low = pd.Series(low_prices)
        close = pd.Series(close_prices)
        
        # Calculate Supertrend
        supertrend = self.calculate_supertrend(high, low, close)
        
        # Get key levels
        key_levels = self.identify_key_levels(
            close[-self.lookback:] if len(close) > self.lookback else close
        )
        
        current_price = close.iloc[-1]
        current_trend = supertrend['trend'].iloc[-1]
        
        # Find nearest key levels
        nearest_resistance = min(
            [level for level in key_levels if level > current_price],
            default=current_price * 1.01
        )
        nearest_support = max(
            [level for level in key_levels if level < current_price],
            default=current_price * 0.99
        )
        
        # Generate signals based on trend and key levels
        if (current_trend == 1 and
            current_price > nearest_support and
            current_position <= 0):
            return 'buy'
        
        elif (current_trend == -1 and
              current_price < nearest_resistance and
              current_position >= 0):
            return 'sell'
        
        return None
