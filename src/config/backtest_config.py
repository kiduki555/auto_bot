from dataclasses import dataclass
from typing import Optional


@dataclass
class BacktestConfig:
    """Configuration for backtesting parameters"""
    symbol: str
    timeframe: str
    strategy: str
    start_date: str
    end_date: str
    initial_balance: float = 10000.0
    risk_per_trade: float = 0.02
    max_position_size: float = 1.0
    tp_sl_mode: str = 'atr'
    sl_multiplier: float = 2.0
    tp_multiplier: float = 3.0
    tick_size: float = 0.01
    commission_rate: float = 0.001
    use_trailing_stop: bool = False
    trailing_stop_activation: float = 0.01
    trailing_stop_distance: float = 0.005

    def to_dict(self) -> dict:
        """Convert config to dictionary"""
        return {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'strategy': self.strategy,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'initial_balance': self.initial_balance,
            'risk_per_trade': self.risk_per_trade,
            'max_position_size': self.max_position_size,
            'tp_sl_mode': self.tp_sl_mode,
            'sl_multiplier': self.sl_multiplier,
            'tp_multiplier': self.tp_multiplier,
            'tick_size': self.tick_size,
            'commission_rate': self.commission_rate,
            'use_trailing_stop': self.use_trailing_stop,
            'trailing_stop_activation': self.trailing_stop_activation,
            'trailing_stop_distance': self.trailing_stop_distance
        }

    @classmethod
    def from_dict(cls, config_dict: dict) -> 'BacktestConfig':
        """Create config from dictionary"""
        return cls(**config_dict)
