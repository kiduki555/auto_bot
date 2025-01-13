from typing import Dict, Any, Tuple, List
import pandas as pd
import numpy as np
from ..base_strategy import BaseStrategy
from ...indicators.momentum import RSIIndicator
from ...indicators.volatility import ATRIndicator


class RSIDivergenceStrategy(BaseStrategy):
    """
    RSI Divergence trading strategy
    
    Entry Rules:
    - Long: Bullish divergence (price makes lower low but RSI makes higher low)
    - Short: Bearish divergence (price makes higher high but RSI makes lower high)
    
    Exit Rules:
    - Take profit at R:R ratio
    - Stop loss based on ATR
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Initialize strategy
        
        Args:
            params: Dictionary with parameters:
                - rsi_period: RSI period (default: 14)
                - atr_period: ATR period (default: 14)
                - atr_multiplier: ATR multiplier for stop loss (default: 2)
                - divergence_lookback: Bars to look back for divergence (default: 10)
                - risk_reward_ratio: Risk/Reward ratio (default: 2)
                - risk_per_trade: Risk per trade in % (default: 1)
        """
        super().__init__(params)
        
        # Strategy parameters
        self.rsi_period = self.params.get('rsi_period', 14)
        self.atr_period = self.params.get('atr_period', 14)
        self.atr_multiplier = self.params.get('atr_multiplier', 2)
        self.divergence_lookback = self.params.get('divergence_lookback', 10)
        self.risk_reward_ratio = self.params.get('risk_reward_ratio', 2)
        self.risk_per_trade = self.params.get('risk_per_trade', 1)
        
        # Initialize indicators
        self.rsi = RSIIndicator(params={'period': self.rsi_period})
        self.atr = ATRIndicator(params={'period': self.atr_period})
        
    def find_extrema(
        self,
        data: pd.Series,
        lookback: int
    ) -> Tuple[List[int], List[int]]:
        """
        Find local extrema in a series
        
        Args:
            data: Series to find extrema in
            lookback: Number of bars to look back
            
        Returns:
            Tuple of (peaks, troughs) indices
        """
        peaks = []
        troughs = []
        
        for i in range(lookback, len(data)-lookback):
            if all(data.iloc[i] > data.iloc[i-j] for j in range(1, lookback+1)) and \
               all(data.iloc[i] > data.iloc[i+j] for j in range(1, lookback+1)):
                peaks.append(i)
            if all(data.iloc[i] < data.iloc[i-j] for j in range(1, lookback+1)) and \
               all(data.iloc[i] < data.iloc[i+j] for j in range(1, lookback+1)):
                troughs.append(i)
                
        return peaks, troughs
        
    def check_divergence(
        self,
        price: pd.Series,
        rsi: pd.Series,
        idx1: int,
        idx2: int
    ) -> str:
        """
        Check for divergence between price and RSI
        
        Args:
            price: Price series
            rsi: RSI series
            idx1: First point index
            idx2: Second point index
            
        Returns:
            String indicating divergence type ('bullish', 'bearish', or None)
        """
        price_diff = price.iloc[idx2] - price.iloc[idx1]
        rsi_diff = rsi.iloc[idx2] - rsi.iloc[idx1]
        
        # Bullish divergence
        if price_diff < 0 and rsi_diff > 0:
            return 'bullish'
        # Bearish divergence
        elif price_diff > 0 and rsi_diff < 0:
            return 'bearish'
        else:
            return None
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals"""
        if not self.validate_data(data):
            raise ValueError("Invalid data format")
            
        # Calculate indicators
        data = self.rsi.calculate(data)
        data = self.atr.calculate(data)
        
        # Initialize signal column
        data['signal'] = 0
        
        # Find extrema in price and RSI
        price_peaks, price_troughs = self.find_extrema(
            data['close'],
            self.divergence_lookback
        )
        rsi_peaks, rsi_troughs = self.find_extrema(
            data['rsi'],
            self.divergence_lookback
        )
        
        # Check for divergences
        for i in range(len(data)):
            # Skip if not enough lookback data
            if i < self.divergence_lookback:
                continue
                
            # Check recent price and RSI movements
            recent_price_peaks = [p for p in price_peaks if p < i][-2:]
            recent_price_troughs = [t for t in price_troughs if t < i][-2:]
            recent_rsi_peaks = [p for p in rsi_peaks if p < i][-2:]
            recent_rsi_troughs = [t for t in rsi_troughs if t < i][-2:]
            
            # Check for bullish divergence
            if len(recent_price_troughs) >= 2 and len(recent_rsi_troughs) >= 2:
                div_type = self.check_divergence(
                    data['close'],
                    data['rsi'],
                    recent_price_troughs[-2],
                    recent_price_troughs[-1]
                )
                if div_type == 'bullish':
                    data.loc[data.index[i], 'signal'] = 1
                    
                    # Calculate exit points
                    stop_loss, take_profit = self.calculate_exit_points(
                        entry_price=data['close'].iloc[i],
                        side='long',
                        risk_reward_ratio=self.risk_reward_ratio
                    )
                    
                    # Log signal
                    self.log_signal(
                        timestamp=data.index[i],
                        signal_type='LONG (Bullish Divergence)',
                        price=data['close'].iloc[i],
                        stop_loss=stop_loss,
                        take_profit=take_profit
                    )
                    
            # Check for bearish divergence
            if len(recent_price_peaks) >= 2 and len(recent_rsi_peaks) >= 2:
                div_type = self.check_divergence(
                    data['close'],
                    data['rsi'],
                    recent_price_peaks[-2],
                    recent_price_peaks[-1]
                )
                if div_type == 'bearish':
                    data.loc[data.index[i], 'signal'] = -1
                    
                    # Calculate exit points
                    stop_loss, take_profit = self.calculate_exit_points(
                        entry_price=data['close'].iloc[i],
                        side='short',
                        risk_reward_ratio=self.risk_reward_ratio
                    )
                    
                    # Log signal
                    self.log_signal(
                        timestamp=data.index[i],
                        signal_type='SHORT (Bearish Divergence)',
                        price=data['close'].iloc[i],
                        stop_loss=stop_loss,
                        take_profit=take_profit
                    )
                    
        return data
        
    def calculate_position_size(
        self,
        capital: float,
        entry_price: float,
        stop_loss: float
    ) -> float:
        """Calculate position size based on risk"""
        risk_amount = capital * (self.risk_per_trade / 100)
        price_risk = abs(entry_price - stop_loss)
        
        if price_risk == 0:
            return 0
            
        position_size = risk_amount / price_risk
        return position_size
        
    def calculate_exit_points(
        self,
        entry_price: float,
        side: str,
        risk_reward_ratio: float = None
    ) -> Tuple[float, float]:
        """Calculate stop loss and take profit levels"""
        if risk_reward_ratio is None:
            risk_reward_ratio = self.risk_reward_ratio
            
        atr_value = self.atr_multiplier * self.atr_period
        
        if side == 'long':
            stop_loss = entry_price - atr_value
            take_profit = entry_price + (atr_value * risk_reward_ratio)
        else:  # short
            stop_loss = entry_price + atr_value
            take_profit = entry_price - (atr_value * risk_reward_ratio)
            
        return stop_loss, take_profit
