import logging
from datetime import datetime
from typing import Optional


class Logger:
    """
    Custom logger class for trading bot operations
    """
    def __init__(self, symbol: str, index: int = 0):
        self.symbol = symbol
        self.index = index
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Set up the logger with appropriate configuration"""
        logger = logging.getLogger(f'{self.symbol}_{self.index}')
        logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        
        # Create file handler
        fh = logging.FileHandler(
            f'logs/{self.symbol}_{self.index}_{datetime.now().strftime("%Y%m%d")}.log'
        )
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(ch)
        logger.addHandler(fh)
        
        return logger

    def log_trade(
        self,
        action: str,
        price: float,
        position_size: Optional[float] = None,
        take_profit: Optional[float] = None,
        stop_loss: Optional[float] = None
    ) -> None:
        """Log trade related information"""
        message = f"{action} at {price}"
        if position_size:
            message += f", Size: {position_size}"
        if take_profit:
            message += f", TP: {take_profit}"
        if stop_loss:
            message += f", SL: {stop_loss}"
        
        self.logger.info(message)

    def log_error(self, message: str) -> None:
        """Log error messages"""
        self.logger.error(message)

    def log_info(self, message: str) -> None:
        """Log general information messages"""
        self.logger.info(message)

    def log_warning(self, message: str) -> None:
        """Log warning messages"""
        self.logger.warning(message)
