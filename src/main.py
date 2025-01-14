import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from src.config.live_trading_config import TradingConfig
from src.core.live_trading import LiveTrading
from src.utils.telegram_notifier import TelegramNotifier
from src.utils.logger import Logger
from src.strategies.implementations.adaptive_supertrend_strategy import AdaptiveSuperTrendStrategy
from src.strategies.implementations.future_trend_strategy import FutureTrendStrategy

# Load environment variables
load_dotenv()

# Initialize logger
logger = Logger('Main')


async def main():
    try:
        # Load configuration
        config = TradingConfig(
            symbol=os.getenv('TRADING_SYMBOL', 'BTCUSDT'),
            timeframe=os.getenv('TRADING_TIMEFRAME', '1h'),
            strategy=os.getenv('TRADING_STRATEGY', 'adaptive_supertrend'),
            risk_per_trade=float(os.getenv('RISK_PER_TRADE', 0.02)),
            max_position_size=float(os.getenv('MAX_POSITION_SIZE', 1.0)),
            tp_sl_mode=os.getenv('TP_SL_MODE', 'atr'),
            sl_multiplier=float(os.getenv('SL_MULTIPLIER', 2.0)),
            tp_multiplier=float(os.getenv('TP_MULTIPLIER', 3.0)),
            use_trailing_stop=os.getenv('USE_TRAILING_STOP', 'false').lower() == 'true',
            trailing_stop_activation=float(os.getenv('TRAILING_STOP_ACTIVATION', 0.01)),
            trailing_stop_distance=float(os.getenv('TRAILING_STOP_DISTANCE', 0.005))
        )
        
        # Initialize Telegram notifier
        notifier = TelegramNotifier()
        
        # Initialize trading bot
        trader = LiveTrading(
            config=config,
            strategy=AdaptiveSuperTrendStrategy(),  # 사용할 전략
            notifier=notifier
        )
        
        # Start Telegram bot
        await notifier.start()
        
        # Start trading
        await trader.start()
        
        # Keep the program running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.log_info("Shutting down...")
        await trader.stop()
        await notifier.stop()
    except Exception as e:
        logger.log_error(f"Error in main: {str(e)}")
        if 'notifier' in locals():  # notifier가 초기화된 경우에만 호출
            await notifier.send_error_notification(
                error_type="Main Error",
                error_message=str(e)
            )
        raise


if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())
