from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime

from .trading_bot import TradingBot
from .trade_manager import TradeManager
from ..config.backtest_config import BacktestConfig
from ..utils.logger import Logger


class Backtester:
    """
    Backtesting engine for trading strategies
    """
    def __init__(
        self,
        config: BacktestConfig,
        historical_data: pd.DataFrame,
        initial_balance: float = 10000.0
    ):
        self.config = config
        self.data = historical_data
        self.logger = Logger(config.symbol, index=0)
        
        self.trade_manager = TradeManager(
            symbol=config.symbol,
            initial_balance=initial_balance,
            risk_per_trade=config.risk_per_trade,
            max_position_size=config.max_position_size
        )
        
        self.bot = None
        self.results = {
            'trades': [],
            'equity_curve': [],
            'performance_metrics': {}
        }

    def initialize_bot(self) -> None:
        """Initialize trading bot with historical data"""
        try:
            self.bot = TradingBot(
                symbol=self.config.symbol,
                open_prices=self.data['open'].tolist(),
                close_prices=self.data['close'].tolist(),
                high_prices=self.data['high'].tolist(),
                low_prices=self.data['low'].tolist(),
                volumes=self.data['volume'].tolist(),
                dates=self.data.index.tolist(),
                opening_position=0,
                closing_position=0,
                index=0,
                tick_size=self.config.tick_size,
                strategy=self.config.strategy,
                tp_sl_choice=self.config.tp_sl_mode,
                sl_multiplier=self.config.sl_multiplier,
                tp_multiplier=self.config.tp_multiplier,
                backtesting=True
            )
            
        except Exception as e:
            self.logger.log_error(f"Error initializing bot for backtesting: {str(e)}")
            raise

    def run_backtest(self) -> Dict[str, Any]:
        """
        Run backtest on historical data
        
        Returns:
            Dictionary containing backtest results
        """
        self.initialize_bot()
        
        for i in range(len(self.data)):
            try:
                # Update bot with new candle
                self.bot.process_new_candle(
                    open_price=self.data['open'].iloc[i],
                    close_price=self.data['close'].iloc[i],
                    high_price=self.data['high'].iloc[i],
                    low_price=self.data['low'].iloc[i],
                    volume=self.data['volume'].iloc[i],
                    date=str(self.data.index[i])
                )
                
                # Execute strategy
                signal = self.bot.execute_strategy()
                
                if signal:
                    current_position = self.trade_manager.get_position_status()
                    
                    if signal == 'buy' and not current_position['has_position']:
                        # Calculate position size and entry parameters
                        position_size = self.trade_manager.calculate_position_size(
                            self.data['close'].iloc[i],
                            self.data['low'].iloc[i] * (1 - self.config.sl_multiplier)
                        )
                        
                        # Open long position
                        self.trade_manager.open_position(
                            side='long',
                            entry_price=self.data['close'].iloc[i],
                            position_size=position_size,
                            stop_loss=self.data['low'].iloc[i] * (1 - self.config.sl_multiplier),
                            take_profit=self.data['close'].iloc[i] * (1 + self.config.tp_multiplier)
                        )
                        
                    elif signal == 'sell' and not current_position['has_position']:
                        # Calculate position size and entry parameters
                        position_size = self.trade_manager.calculate_position_size(
                            self.data['close'].iloc[i],
                            self.data['high'].iloc[i] * (1 + self.config.sl_multiplier)
                        )
                        
                        # Open short position
                        self.trade_manager.open_position(
                            side='short',
                            entry_price=self.data['close'].iloc[i],
                            position_size=position_size,
                            stop_loss=self.data['high'].iloc[i] * (1 + self.config.sl_multiplier),
                            take_profit=self.data['close'].iloc[i] * (1 - self.config.tp_multiplier)
                        )
                
                # Check stop loss and take profit
                self.trade_manager.check_stop_loss(self.data['close'].iloc[i])
                self.trade_manager.check_take_profit(self.data['close'].iloc[i])
                
                # Update equity curve
                self.results['equity_curve'].append({
                    'date': self.data.index[i],
                    'equity': self.trade_manager.balance,
                    'position': self.trade_manager.current_position
                })
                
            except Exception as e:
                self.logger.log_error(f"Error in backtest at index {i}: {str(e)}")
                continue

        # Calculate performance metrics
        self.calculate_performance_metrics()
        
        return self.results

    def calculate_performance_metrics(self) -> None:
        """Calculate trading performance metrics"""
        if not self.results['equity_curve']:
            return

        equity_curve = pd.DataFrame(self.results['equity_curve'])
        trades = pd.DataFrame(self.trade_manager.trade_history)
        
        if trades.empty:
            return

        # Basic metrics
        total_trades = len(trades)
        profitable_trades = len(trades[trades['profit_loss'] > 0])
        win_rate = profitable_trades / total_trades if total_trades > 0 else 0
        
        # Returns
        total_return = (equity_curve['equity'].iloc[-1] - equity_curve['equity'].iloc[0]) / equity_curve['equity'].iloc[0]
        daily_returns = equity_curve['equity'].pct_change().dropna()
        
        # Risk metrics
        max_drawdown = 0
        peak = equity_curve['equity'].iloc[0]
        for value in equity_curve['equity']:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, drawdown)

        # Store metrics
        self.results['performance_metrics'] = {
            'total_trades': total_trades,
            'profitable_trades': profitable_trades,
            'win_rate': win_rate,
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': daily_returns.mean() / daily_returns.std() if len(daily_returns) > 0 else 0,
            'average_trade': trades['profit_loss'].mean() if not trades.empty else 0,
            'best_trade': trades['profit_loss'].max() if not trades.empty else 0,
            'worst_trade': trades['profit_loss'].min() if not trades.empty else 0
        }
