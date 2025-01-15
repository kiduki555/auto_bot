from typing import Optional, Dict, Any
import asyncio
from datetime import datetime, timedelta

from .trading_bot import TradingBot
from .trade_manager import TradeManager
from config.live_trading_config import TradingConfig, make_decision_options
from utils.logger import Logger
from exchanges.exchange import BinanceExchange


class LiveTrading:
    """
    Handles live trading operations including market data processing and order execution
    """
    def __init__(
        self,
        config: TradingConfig,
        exchange_client: BinanceExchange,
        strategy: str = None,
        notifier: Any = None
    ):
        self.config = config
        self.exchange = exchange_client
        self.logger = Logger(config.symbol)
        
        # 잔고 조회
        balance = self.exchange.get_futures_balance()
        print("Futures Balance:", balance)

        # 현재 가격 조회
        current_price = self.exchange.get_futures_symbol_price("BTCUSDT")
        print("Current BTCUSDT Price:", current_price)

        # 최근 거래 내역 조회
        recent_trades = self.exchange.get_recent_trades("BTCUSDT")
        print("Recent Trades:", recent_trades)

        # TradeManager 초기화
        self.trade_manager = TradeManager(
            exchange=self.exchange,
            symbol=config.symbol,
            risk_per_trade=config.risk_per_trade,
            max_position_size=config.max_position_size
        )
        
        self.bot = None
        self.is_running = False
        self.last_candle_time: Optional[datetime] = None
        self.strategy = strategy
        self.notifier = notifier

    def initialize(self) -> None:
        """Initialize the trading bot with historical data"""
        try:
            # 현재 시간에서 4시간 전의 시간 계산
            four_hours_ago = datetime.utcnow() - timedelta(hours=4)
            start_str = four_hours_ago.strftime("%Y-%m-%d %H:%M:%S")

            # Fetch historical data from exchange
            historical_data = self.exchange.get_historical_klines(
                self.config.symbol,
                self.config.timeframe,
                start_str=start_str,
                end_str="now UTC"  # 현재 시간
            )
            # Ensure historical_data is processed correctly
            if historical_data is None or len(historical_data) == 0:
                raise ValueError("No historical data returned.")
            # Process historical data as needed
            dates = [str(candle[0]) for candle in historical_data]
            open_prices = [candle[1] for candle in historical_data]
            high_prices = [candle[2] for candle in historical_data]
            low_prices = [candle[3] for candle in historical_data]
            close_prices = [candle[4] for candle in historical_data]
            volumes = [candle[5] for candle in historical_data]
            
            # Initialize trading bot
            self.bot = TradingBot(
                symbol=self.config.symbol,
                open_prices=open_prices,
                close_prices=close_prices,
                high_prices=high_prices,
                low_prices=low_prices,
                volumes=volumes,
                dates=dates,
                opening_position=0,
                closing_position=0,
                index=0,
                tick_size=self.exchange.markets[self.config.symbol]['precision']['price'],
                strategy=self.config.strategy,
                tp_sl_choice=self.config.tp_sl_mode,
                sl_multiplier=self.config.sl_multiplier,
                tp_multiplier=self.config.tp_multiplier
            )
            
            self.logger.log_info("Trading bot initialized successfully")
            
        except Exception as e:
            self.logger.log_error(f"Error initializing trading bot: {str(e)}")
            raise

    async def process_new_candle(self, candle: Dict[str, Any]) -> None:
        """
        Process new candle data and execute trading logic
        
        Args:
            candle: Dictionary containing OHLCV data
        """
        try:
            # Update bot with new candle data
            self.bot.process_new_candle(
                open_price=candle['open'],
                close_price=candle['close'],
                high_price=candle['high'],
                low_price=candle['low'],
                volume=candle['volume'],
                date=str(candle['timestamp'])
            )
            
            # Execute trading strategy
            signal = self.bot.execute_strategy()
            
            if signal:
                current_position = self.trade_manager.get_position_status()
                
                if signal == 'buy' and not current_position['has_position']:
                    # Calculate position size and entry parameters
                    position_size = self.trade_manager.calculate_position_size(
                        candle['close'],
                        candle['low'] * (1 - self.config.sl_multiplier)
                    )
                    
                    # Open long position
                    self.trade_manager.open_position(
                        side='long',
                        entry_price=candle['close'],
                        position_size=position_size,
                        stop_loss=candle['low'] * (1 - self.config.sl_multiplier),
                        take_profit=candle['close'] * (1 + self.config.tp_multiplier)
                    )
                    
                elif signal == 'sell' and not current_position['has_position']:
                    # Calculate position size and entry parameters
                    position_size = self.trade_manager.calculate_position_size(
                        candle['close'],
                        candle['high'] * (1 + self.config.sl_multiplier)
                    )
                    
                    # Open short position
                    self.trade_manager.open_position(
                        side='short',
                        entry_price=candle['close'],
                        position_size=position_size,
                        stop_loss=candle['high'] * (1 + self.config.sl_multiplier),
                        take_profit=candle['close'] * (1 - self.config.tp_multiplier)
                    )
            
            # Check stop loss and take profit
            self.trade_manager.check_stop_loss(candle['close'])
            self.trade_manager.check_take_profit(candle['close'])
            
        except Exception as e:
            self.logger.log_error(f"Error processing candle: {str(e)}")

    async def start(self) -> None:
        """Start the live trading process"""
        try:
            self.initialize()
            self.is_running = True
            
            while self.is_running:
                # Fetch latest candle
                latest_candle = self.exchange.client.get_klines(
                    symbol=self.config.symbol,
                    interval=self.config.timeframe,
                    limit=1
                )
                
                if latest_candle:
                    candle_time = datetime.fromtimestamp(latest_candle[0][0] / 1000)
                    
                    if (not self.last_candle_time or 
                        candle_time > self.last_candle_time):
                        # Process new candle
                        candle_data = {
                            'timestamp': candle_time,
                            'open': latest_candle[0][1],
                            'high': latest_candle[0][2],
                            'low': latest_candle[0][3],
                            'close': latest_candle[0][4],
                            'volume': latest_candle[0][5]
                        }
                        
                        await self.process_new_candle(candle_data)
                        self.last_candle_time = candle_time
                
                # Wait before next update
                await asyncio.sleep(1)
                
        except Exception as e:
            self.logger.log_error(f"Error in live trading: {str(e)}")
            self.stop()

    def stop(self) -> None:
        """Stop the live trading process"""
        self.is_running = False
        self.logger.log_info("Live trading stopped")
