from typing import List, Dict, Any, Optional, Union
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from ta.trend import ema_indicator
from ta.momentum import rsi
from ta.volatility import average_true_range


class TradingHelper:
    """
    Helper class for common trading functions and utilities
    """
    @staticmethod
    def calculate_indicators(
        prices: pd.DataFrame,
        config: Dict[str, Any]
    ) -> Dict[str, pd.Series]:
        """
        Calculate common technical indicators
        
        Args:
            prices: DataFrame with OHLCV data
            config: Dictionary with indicator parameters
            
        Returns:
            Dictionary of calculated indicators
        """
        indicators = {}
        
        # Calculate EMAs
        for period in config.get('ema_periods', [20, 50, 200]):
            indicators[f'ema_{period}'] = ema_indicator(
                prices['close'],
                window=period
            )
        
        # Calculate RSI
        if 'rsi_period' in config:
            indicators['rsi'] = rsi(
                prices['close'],
                window=config['rsi_period']
            )
        
        # Calculate ATR
        if 'atr_period' in config:
            indicators['atr'] = average_true_range(
                prices['high'],
                prices['low'],
                prices['close'],
                window=config['atr_period']
            )
        
        return indicators

    @staticmethod
    def calculate_position_size(
        account_balance: float,
        risk_per_trade: float,
        entry_price: float,
        stop_loss: float,
        leverage: float = 1.0
    ) -> float:
        """
        Calculate position size based on risk parameters
        
        Args:
            account_balance: Current account balance
            risk_per_trade: Risk percentage per trade (0-1)
            entry_price: Entry price
            stop_loss: Stop loss price
            leverage: Trading leverage
            
        Returns:
            Position size
        """
        if entry_price <= 0 or stop_loss <= 0:
            return 0
            
        risk_amount = account_balance * risk_per_trade
        price_risk = abs(entry_price - stop_loss)
        
        if price_risk == 0:
            return 0
            
        position_size = (risk_amount / price_risk) * leverage
        return position_size

    @staticmethod
    def calculate_tp_sl_levels(
        entry_price: float,
        direction: int,
        atr_value: Optional[float] = None,
        risk_reward_ratio: float = 1.5,
        sl_multiplier: float = 2.0,
        tp_multiplier: float = 3.0,
        use_atr: bool = True
    ) -> Dict[str, float]:
        """
        Calculate take profit and stop loss levels
        
        Args:
            entry_price: Entry price
            direction: Trade direction (1 for long, -1 for short)
            atr_value: ATR value if available
            risk_reward_ratio: Risk/Reward ratio
            sl_multiplier: Stop loss multiplier
            tp_multiplier: Take profit multiplier
            use_atr: Whether to use ATR for calculations
            
        Returns:
            Dictionary with take profit and stop loss prices
        """
        if use_atr and atr_value:
            sl_distance = atr_value * sl_multiplier
            tp_distance = atr_value * tp_multiplier
        else:
            # Use percentage-based calculation
            sl_distance = entry_price * 0.02  # 2% default
            tp_distance = sl_distance * risk_reward_ratio

        if direction == 1:  # Long position
            stop_loss = entry_price - sl_distance
            take_profit = entry_price + tp_distance
        else:  # Short position
            stop_loss = entry_price + sl_distance
            take_profit = entry_price - tp_distance

        return {
            'stop_loss': stop_loss,
            'take_profit': take_profit
        }

    @staticmethod
    def calculate_trailing_stop(
        current_price: float,
        entry_price: float,
        direction: int,
        activation_percentage: float = 0.01,
        trailing_distance: float = 0.005
    ) -> Optional[float]:
        """
        Calculate trailing stop level
        
        Args:
            current_price: Current market price
            entry_price: Entry price
            direction: Trade direction (1 for long, -1 for short)
            activation_percentage: Percentage gain needed to activate trailing stop
            trailing_distance: Distance to maintain for trailing stop
            
        Returns:
            Trailing stop price if activated, None otherwise
        """
        if direction == 1:  # Long position
            profit_percentage = (current_price - entry_price) / entry_price
            if profit_percentage >= activation_percentage:
                return current_price * (1 - trailing_distance)
        else:  # Short position
            profit_percentage = (entry_price - current_price) / entry_price
            if profit_percentage >= activation_percentage:
                return current_price * (1 + trailing_distance)
                
        return None

    @staticmethod
    def normalize_timeframe(
        timeframe: str
    ) -> str:
        """
        Normalize timeframe string to standard format
        
        Args:
            timeframe: Timeframe string (e.g., '1m', '1h', '1d')
            
        Returns:
            Normalized timeframe string
        """
        timeframe = timeframe.lower()
        if timeframe[-1] not in ['m', 'h', 'd']:
            raise ValueError(f"Invalid timeframe format: {timeframe}")
            
        value = int(timeframe[:-1])
        unit = timeframe[-1]
        
        return f"{value}{unit}"

    @staticmethod
    def get_candle_timestamps(
        timeframe: str,
        timezone: str = 'UTC'
    ) -> Dict[str, datetime]:
        """
        Get current and next candle timestamps
        
        Args:
            timeframe: Timeframe string (e.g., '1m', '1h', '1d')
            timezone: Timezone string
            
        Returns:
            Dictionary with current and next candle timestamps
        """
        tz = pytz.timezone(timezone)
        current_time = datetime.now(tz)
        
        timeframe = TradingHelper.normalize_timeframe(timeframe)
        value = int(timeframe[:-1])
        unit = timeframe[-1]
        
        if unit == 'm':
            minutes = value
            current_candle = current_time.replace(
                second=0,
                microsecond=0,
                minute=current_time.minute // minutes * minutes
            )
            next_candle = current_candle + timedelta(minutes=minutes)
        elif unit == 'h':
            hours = value
            current_candle = current_time.replace(
                second=0,
                microsecond=0,
                minute=0,
                hour=current_time.hour // hours * hours
            )
            next_candle = current_candle + timedelta(hours=hours)
        else:  # daily
            days = value
            current_candle = current_time.replace(
                second=0,
                microsecond=0,
                minute=0,
                hour=0
            )
            next_candle = current_candle + timedelta(days=days)
            
        return {
            'current_candle': current_candle,
            'next_candle': next_candle
        }

    @staticmethod
    def calculate_trade_metrics(
        trades: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Calculate trading performance metrics
        
        Args:
            trades: List of trade dictionaries
            
        Returns:
            Dictionary of performance metrics
        """
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'average_profit': 0,
                'max_drawdown': 0
            }
            
        total_trades = len(trades)
        profitable_trades = len(
            [t for t in trades if t['profit_loss'] > 0]
        )
        win_rate = profitable_trades / total_trades
        
        gross_profit = sum(
            t['profit_loss'] for t in trades if t['profit_loss'] > 0
        )
        gross_loss = abs(sum(
            t['profit_loss'] for t in trades if t['profit_loss'] < 0
        ))
        profit_factor = (
            gross_profit / gross_loss if gross_loss != 0 else float('inf')
        )
        
        average_profit = sum(
            t['profit_loss'] for t in trades
        ) / total_trades
        
        # Calculate maximum drawdown
        equity_curve = []
        current_equity = 0
        max_equity = 0
        max_drawdown = 0
        
        for trade in trades:
            current_equity += trade['profit_loss']
            equity_curve.append(current_equity)
            max_equity = max(max_equity, current_equity)
            drawdown = (max_equity - current_equity) / max_equity if max_equity > 0 else 0
            max_drawdown = max(max_drawdown, drawdown)
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'average_profit': average_profit,
            'max_drawdown': max_drawdown
        }
