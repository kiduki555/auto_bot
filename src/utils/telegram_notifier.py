from typing import Optional, Dict, Any
import asyncio
from datetime import datetime
import telegram
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update
import os
from dotenv import load_dotenv

load_dotenv()

print("Telegram Bot Token:", os.getenv('TELEGRAM_BOT_TOKEN'))  # 디버깅용 출력


class TelegramNotifier:
    """
    Telegram notification handler for trading bot
    """
    def __init__(
        self,
        token: Optional[str] = None,
        chat_id: Optional[str] = None,
        bot_name: str = "Me-Bot"
    ):
        self.token = token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.bot_name = bot_name
        
        if not self.token:
            raise ValueError("Telegram bot token not provided")
        
        # Initialize bot
        self.bot = telegram.Bot(token=self.token)
        self.app = Application.builder().token(self.token).build()
        
        # Register command handlers
        self.app.add_handler(CommandHandler("start", self._start_command))
        self.app.add_handler(CommandHandler("status", self._status_command))
        self.app.add_handler(CommandHandler("balance", self._balance_command))
        self.app.add_handler(CommandHandler("positions", self._positions_command))
        self.app.add_handler(CommandHandler("performance", self._performance_command))
        
        # Store bot state
        self.bot_state = {
            'is_trading': False,
            'current_balance': 0.0,
            'open_positions': [],
            'last_trade': None,
            'daily_pnl': 0.0
        }

    async def start(self) -> None:
        """Start the telegram bot"""
        try:
            if self.app.running:
                await self.app.stop()  # Ensure to stop if already running
            await self.app.initialize()  # Ensure the application is initialized
            await self.app.start()

        except Exception as e:
            print(f"Error starting Telegram bot: {str(e)}")

    async def stop(self) -> None:
        """Stop the telegram bot"""
        try:
            await self.app.stop()
            await self.app.shutdown()
        except Exception as e:
            print(f"Error stopping Telegram bot: {str(e)}")

    async def send_message(
        self,
        message: str,
        parse_mode: str = 'HTML'
    ) -> None:
        """
        Send message to telegram chat
        
        Args:
            message: Message text to send
            parse_mode: Message parse mode ('HTML' or 'Markdown')
        """
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode
            )
        except Exception as e:
            print(f"Error sending Telegram message: {str(e)}")

    async def send_trade_notification(
        self,
        trade_type: str,
        symbol: str,
        entry_price: float,
        position_size: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> None:
        """
        Send trade notification
        
        Args:
            trade_type: Type of trade ('BUY' or 'SELL')
            symbol: Trading pair symbol
            entry_price: Entry price
            position_size: Position size
            stop_loss: Stop loss price
            take_profit: Take profit price
        """
        message = (
            f"🔔 <b>New {trade_type} Trade</b>\n\n"
            f"Symbol: {symbol}\n"
            f"Entry Price: {entry_price:.8f}\n"
            f"Position Size: {position_size:.8f}\n"
        )
        
        if stop_loss:
            message += f"Stop Loss: {stop_loss:.8f}\n"
        if take_profit:
            message += f"Take Profit: {take_profit:.8f}\n"
            
        message += f"\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        await self.send_message(message)

    async def send_trade_close_notification(
        self,
        symbol: str,
        close_type: str,
        close_price: float,
        profit_loss: float,
        profit_loss_percentage: float
    ) -> None:
        """
        Send trade close notification
        
        Args:
            symbol: Trading pair symbol
            close_type: Type of close ('TP', 'SL', or 'Manual')
            close_price: Close price
            profit_loss: Profit/Loss amount
            profit_loss_percentage: Profit/Loss percentage
        """
        emoji = "🟢" if profit_loss > 0 else "🔴"
        message = (
            f"{emoji} <b>Trade Closed</b>\n\n"
            f"Symbol: {symbol}\n"
            f"Close Type: {close_type}\n"
            f"Close Price: {close_price:.8f}\n"
            f"P/L: {profit_loss:.8f} ({profit_loss_percentage:.2f}%)\n\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        await self.send_message(message)

    async def send_error_notification(
        self,
        error_type: str,
        error_message: str,
        additional_info: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send error notification
        
        Args:
            error_type: Type of error
            error_message: Error message
            additional_info: Additional error information
        """
        message = (
            f"⚠️ <b>Error Alert</b>\n\n"
            f"Type: {error_type}\n"
            f"Message: {error_message}\n"
        )
        
        if additional_info:
            message += "\nAdditional Information:\n"
            for key, value in additional_info.items():
                message += f"{key}: {value}\n"
                
        message += f"\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        await self.send_message(message)

    async def send_daily_summary(
        self,
        total_trades: int,
        winning_trades: int,
        profit_loss: float,
        best_trade: float,
        worst_trade: float
    ) -> None:
        """
        Send daily trading summary
        
        Args:
            total_trades: Total number of trades
            winning_trades: Number of winning trades
            profit_loss: Total profit/loss
            best_trade: Best trade profit
            worst_trade: Worst trade loss
        """
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        emoji = "🟢" if profit_loss > 0 else "🔴"
        
        message = (
            f"📊 <b>Daily Trading Summary</b>\n\n"
            f"Total Trades: {total_trades}\n"
            f"Win Rate: {win_rate:.2f}%\n"
            f"P/L: {emoji} {profit_loss:.8f}\n"
            f"Best Trade: {best_trade:.8f}\n"
            f"Worst Trade: {worst_trade:.8f}\n\n"
            f"Date: {datetime.now().strftime('%Y-%m-%d')}"
        )
        
        await self.send_message(message)

    async def _start_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /start command"""
        welcome_message = (
            f"👋 Welcome to {self.bot_name}!\n\n"
            "Available commands:\n"
            "/status - Get bot status\n"
            "/balance - Get account balance\n"
            "/positions - View open positions\n"
            "/performance - Get performance stats"
        )
        await update.message.reply_text(welcome_message)

    async def _status_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /status command"""
        status = "🟢 Running" if self.bot_state['is_trading'] else "🔴 Stopped"
        message = (
            f"Bot Status: {status}\n"
            f"Current Balance: {self.bot_state['current_balance']:.8f}\n"
            f"Daily P/L: {self.bot_state['daily_pnl']:.8f}"
        )
        await update.message.reply_text(message)

    async def _balance_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /balance command"""
        message = f"Current Balance: {self.bot_state['current_balance']:.8f}"
        await update.message.reply_text(message)

    async def _positions_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /positions command"""
        if not self.bot_state['open_positions']:
            await update.message.reply_text("No open positions")
            return
            
        message = "Open Positions:\n\n"
        for pos in self.bot_state['open_positions']:
            message += (
                f"Symbol: {pos['symbol']}\n"
                f"Side: {pos['side']}\n"
                f"Size: {pos['size']:.8f}\n"
                f"Entry: {pos['entry']:.8f}\n"
                f"Current P/L: {pos['pnl']:.8f}\n\n"
            )
        await update.message.reply_text(message)

    async def _performance_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /performance command"""
        if not self.bot_state['last_trade']:
            await update.message.reply_text("No trade history available")
            return
            
        message = (
            "Performance Stats:\n\n"
            f"Daily P/L: {self.bot_state['daily_pnl']:.8f}\n"
            f"Last Trade: {self.bot_state['last_trade']['pnl']:.8f}\n"
        )
        await update.message.reply_text(message)

    def update_state(
        self,
        state_updates: Dict[str, Any]
    ) -> None:
        """
        Update bot state
        
        Args:
            state_updates: Dictionary of state updates
        """
        self.bot_state.update(state_updates)
