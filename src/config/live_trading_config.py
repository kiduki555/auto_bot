from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class TradingConfig:
    """Configuration for live trading parameters"""
    symbol: str
    timeframe: str
    strategy: str
    risk_per_trade: float
    max_position_size: float
    tp_sl_mode: str
    sl_multiplier: float
    tp_multiplier: float
    use_trailing_stop: bool
    trailing_stop_activation: float
    trailing_stop_distance: float


def make_decision_options(
    config: TradingConfig,
    current_price: float,
    position_size: float
) -> Dict[str, Any]:
    """
    Generate trading decision options based on configuration
    
    Args:
        config: Trading configuration
        current_price: Current market price
        position_size: Size of the position
        
    Returns:
        Dictionary containing decision parameters
    """
    return {
        'symbol': config.symbol,
        'timeframe': config.timeframe,
        'strategy': config.strategy,
        'position_size': position_size,
        'tp_sl_mode': config.tp_sl_mode,
        'sl_multiplier': config.sl_multiplier,
        'tp_multiplier': config.tp_multiplier,
        'current_price': current_price,
        'use_trailing_stop': config.use_trailing_stop,
        'trailing_stop_activation': config.trailing_stop_activation,
        'trailing_stop_distance': config.trailing_stop_distance
    }


def custom_tp_sl_functions(
    price: float,
    direction: int,
    atr_value: Optional[float] = None,
    config: Optional[TradingConfig] = None
) -> Dict[str, float]:
    """
    Calculate custom take profit and stop loss levels
    
    Args:
        price: Entry price
        direction: Trade direction (1 for long, -1 for short)
        atr_value: Average True Range value if available
        config: Trading configuration if available
        
    Returns:
        Dictionary containing take profit and stop loss prices
    """
    if atr_value and config:
        sl_distance = atr_value * config.sl_multiplier
        tp_distance = atr_value * config.tp_multiplier
    else:
        # Default to percentage-based if ATR not available
        sl_distance = price * 0.02  # 2% default stop loss
        tp_distance = price * 0.04  # 4% default take profit

    if direction == 1:  # Long position
        stop_loss = price - sl_distance
        take_profit = price + tp_distance
    else:  # Short position
        stop_loss = price + sl_distance
        take_profit = price - tp_distance

    return {
        'stop_loss': stop_loss,
        'take_profit': take_profit
    }


def wait_for_candle_close() -> bool:
    """
    Determine whether to wait for candle close before making trading decisions
    
    Returns:
        bool: True if should wait for candle close, False otherwise
    """
    return True  # Default to conservative approach
