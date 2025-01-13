import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from config.live_trading_config import TradingConfig
from core.live_trading import LiveTrading
from utils.telegram_notifier import TelegramNotifier
from utils.logger import Logger

# Load environment variables
load_dotenv()

# Initialize logger
logger = Logger('Main')


async def main():
    try:
        # Load configuration
        config = TradingConfig()
        
        # Initialize Telegram notifier
        notifier = TelegramNotifier()
        
        # Initialize trading bot
        trader = LiveTrading(
            config=config,
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
        if notifier:
            await notifier.send_error_notification(
                error_type="Main Error",
                error_message=str(e)
            )
        raise


if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())
