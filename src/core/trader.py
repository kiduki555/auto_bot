from typing import Dict, Any
from .exchange import BinanceExchange
from ..strategies.base import Strategy
import logging

class Trader:
    def __init__(self, exchange: BinanceExchange, strategy: Strategy, config: Dict[str, Any]):
        self.exchange = exchange
        self.strategy = strategy
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def execute_trades(self, symbol: str):
        try:
            # 데이터 가져오기
            data = self.exchange.get_historical_data(symbol, self.config['interval'])
            
            # 시그널 생성
            signals = self.strategy.generate_signals(data)
            
            # 마지막 시그널에 따라 포지션 진입/청산
            last_signal = signals.iloc[-1]
            
            if last_signal == 1:  # 롱 진입
                self.logger.info(f"Opening LONG position for {symbol}")
                # 롱 포지션 로직 구현
            elif last_signal == -1:  # 숏 진입
                self.logger.info(f"Opening SHORT position for {symbol}")
                # 숏 포지션 로직 구현
                
        except Exception as e:
            self.logger.error(f"Error executing trades: {str(e)}")