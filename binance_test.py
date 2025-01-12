import os
import time
import ccxt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from datetime import datetime
from dotenv import load_dotenv
import logging
import requests
from typing import Dict, Optional
import traceback

# 환경 변수 로드
load_dotenv()
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')
TESTNET = False  # True: 테스트넷, False: 실거래

# 바이낸스 설정
exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
        'testnet': TESTNET
    }
})

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading.log'),
        logging.StreamHandler()
    ]
)

# Telegram 알림 설정
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

class TradingManager:
    def __init__(self, symbol: str = 'ETH/USDT', timeframe: str = '15m',
                 risk_percent: float = 4, stop_loss_percent: float = 2,
                 leverage: int = 3, max_position_size: float = 0.5):
        self.symbol = symbol
        self.timeframe = timeframe
        self.risk_percent = risk_percent
        self.stop_loss_percent = stop_loss_percent
        self.leverage = leverage
        self.max_position_size = max_position_size
        self.trailing_stop_activated = False
        self.trailing_stop_price = 0
        self.retry_count = 3
        self.retry_delay = 5
        self.trade_history = []
        self.balance = 0  # 초기 잔고 설정


        # 로깅 및 텔레그램 설정
        self.setup_logging()
        self.initialize_balance()

    def initialize_balance(self):
        """초기 잔고를 설정합니다."""
        try:
            self.balance = self.execute_with_retry(exchange.fetch_balance)['total']['USDT']
            logging.info(f"초기 잔고 설정 완료: {self.balance:.2f} USDT")
        except Exception as e:
            logging.error(f"초기 잔고 설정 실패: {e}")
            self.balance = 0

    def update_balance(self):
        """실시간 잔고를 업데이트합니다."""
        try:
            self.balance = self.execute_with_retry(exchange.fetch_balance)['total']['USDT']
            logging.info(f"잔고 업데이트: {self.balance:.2f} USDT")
        except Exception as e:
            logging.error(f"잔고 업데이트 실패: {e}")

    def setup_logging(self):
        """로깅 설정을 초기화합니다."""
        log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # 파일 핸들러 설정 (encoding 설정)
        file_handler = logging.FileHandler('trading.log', encoding='utf-8')
        file_handler.setFormatter(log_formatter)
        
        # 콘솔 핸들러 설정
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        
        # 로거 설정
        self.logger = logging.getLogger('TradingBot')
        self.logger.setLevel(logging.INFO)
        
        # 기존 핸들러 제거 (중복 로깅 방지)
        if self.logger.handlers:
            self.logger.handlers.clear()
            
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # 부모 로거로의 전파 방지
        self.logger.propagate = False

    def send_telegram_message(self, message: str) -> None:
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
            try:
                requests.post(url, data=payload)
            except Exception as e:
                logging.error(f"Failed to send Telegram message: {e}")

    def execute_with_retry(self, func, *args, **kwargs):
        for attempt in range(self.retry_count):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.retry_count - 1:
                    raise e
                logging.warning(f"Retry attempt {attempt + 1} after error: {e}")
                time.sleep(self.retry_delay)

    def get_min_trade_amount(self) -> float:
        try:
            markets = self.execute_with_retry(exchange.fetch_markets)
            for market in markets:
                if market['symbol'] == self.symbol:
                    return market['limits']['amount']['min']
            return 0.001
        except Exception as e:
            logging.error(f"Error getting min trade amount: {e}")
            return 0.001

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """기술적 지표들을 계산합니다."""
        try:
            df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
            df['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()
            df['ema_55'] = df['close'].ewm(span=55, adjust=False).mean()
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
            df['rsi'] = self.calculate_rsi(df['close'], 14)
            df['macd'] = df['close'].ewm(span=12, adjust=False).mean() - df['close'].ewm(span=26, adjust=False).mean()
            df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['macd_hist'] = df['macd'] - df['macd_signal']
            return df
        except Exception as e:
            logging.error(f"Error calculating indicators: {e}")
            raise

    def update_trailing_stop(self, current_price: float, position: Dict) -> bool:
        try:
            if not self.trailing_stop_activated:
                return False

            price_change_pct = ((current_price - position['entry_price']) / 
                              position['entry_price'] * 100)
            if position['side'] == 'short':
                price_change_pct = -price_change_pct

            # 트레일링 스탑 로직
            if price_change_pct > 1.0:  # 1% 이상 수익 시 트레일링 스탑 활성화
                new_stop = (current_price * (0.99 if position['side'] == 'long' else 1.01))
                if (position['side'] == 'long' and new_stop > self.trailing_stop_price) or \
                   (position['side'] == 'short' and new_stop < self.trailing_stop_price):
                    self.trailing_stop_price = new_stop
                    logging.info(f"Updated trailing stop: {self.trailing_stop_price}")

                # 트레일링 스탑 히트 체크
                if ((position['side'] == 'long' and current_price < self.trailing_stop_price) or
                    (position['side'] == 'short' and current_price > self.trailing_stop_price)):
                    return True
            return False
        except Exception as e:
            logging.error(f"Error updating trailing stop: {e}")
            return False

    def get_position(self) -> Optional[Dict]:
        try:
            balance = self.execute_with_retry(exchange.fetch_balance)
            positions = balance['info']['positions']
            for position in positions:
                if float(position['positionAmt']) != 0:
                    return {
                        'symbol': position['symbol'],
                        'size': float(position['positionAmt']),
                        'entry_price': float(position['entryPrice']),
                        'side': 'long' if float(position['positionAmt']) > 0 else 'short'
                    }
            return None
        except Exception as e:
            logging.error(f"Error getting position: {e}")
            return None

    def fetch_recent_data(self, limit: int = 100) -> pd.DataFrame:
            """최근 거래 데이터를 가져옵니다."""
            try:
                ohlcv = self.execute_with_retry(
                    exchange.fetch_ohlcv,
                    self.symbol,
                    self.timeframe,
                    limit=limit
                )
                df = pd.DataFrame(
                    ohlcv,
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                )
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                
                # hl2 (중간값) 계산 추가
                df['hl2'] = (df['high'] + df['low']) / 2
                return df
            except Exception as e:
                logging.error(f"Error fetching data: {e}")
                raise

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """기술적 지표들을 계산합니다."""
        try:
            # EMA 계산
            df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
            df['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()
            df['ema_55'] = df['close'].ewm(span=55, adjust=False).mean()
            
            # 볼린저 밴드
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # MACD
            df['macd'] = df['close'].ewm(span=12, adjust=False).mean() - \
                        df['close'].ewm(span=26, adjust=False).mean()
            df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['macd_hist'] = df['macd'] - df['macd_signal']
            
            # 거래량 분석
            df['volume_ma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']
            
            return df
        except Exception as e:
            logging.error(f"Error calculating indicators: {e}")
            raise

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """매매 신호를 생성합니다."""
        try:
            df = self.calculate_indicators(df)
            long_conditions = (
                (df['ema_9'] > df['ema_21']) &
                (df['close'] > df['bb_middle']) &
                (df['macd_hist'] > 0) &
                (df['rsi'] < 60)
            )
            short_conditions = (
                (df['ema_9'] < df['ema_21']) &
                (df['close'] < df['bb_middle']) &
                (df['macd_hist'] < 0) &
                (df['rsi'] > 40)
            )
            df['signal'] = 0
            df.loc[long_conditions, 'signal'] = 1
            df.loc[short_conditions, 'signal'] = -1
            df['signal'] = df['signal'] * (df['signal'].shift(1) != df['signal'])
            return df
        except Exception as e:
            logging.error(f"Error generating signals: {e}")
            raise

    def calculate_position_size(self, current_price: float) -> float:
        try:
            # 리스크 금액 계산
            risk_amount = self.balance * (self.risk_percent / 100)
            
            # 최소 거래 수량 확인
            min_amount = 0.003  # BTC/USDT의 최소 거래 수량
            
            # 포지션 사이즈 계산
            position_size = (risk_amount / current_price) * self.leverage
            
            # 최소 거래 수량 보다 작으면 최소 거래 수량으로 설정
            if position_size < min_amount:
                self.logger.warning(f"계산된 포지션 사이즈({position_size})가 최소 거래 수량({min_amount})보다 작습니다. 최소 거래 수량으로 설정합니다.")
                position_size = min_amount
                
            # 소수점 3자리로 반올림 (Binance 최소 정밀도)
            position_size = round(position_size, 3)
            
            return position_size
            
        except Exception as e:
            self.logger.error(f"포지션 사이즈 계산 중 오류: {e}")
            return min_amount

    def run_trading(self):
        """트레이딩을 실행합니다."""
        try:
            start_message = (
                f"트레이딩 시작...\n"
                f"심볼: {self.symbol}\n"
                f"타임프레임: {self.timeframe}\n"
                f"레버리지: {self.leverage}x\n"
                f"리스크: {self.risk_percent}%\n"
                f"현재 잔고: {self.balance:.2f} USDT"
            )
            logging.info(start_message)
            self.send_telegram_message(start_message)

            last_print_time = datetime.now()

            while True:
                try:
                    # 데이터 가져오기 및 신호 생성
                    df = self.fetch_recent_data()
                    df = self.generate_signals(df)

                    current_position = self.get_position()
                    last_signal = df['signal'].iloc[-1]
                    current_price = self.execute_with_retry(exchange.fetch_ticker, self.symbol)['last']

                    # 상태 업데이트 (10분마다)
                    if (datetime.now() - last_print_time).total_seconds() >= 600:
                        self.update_balance()
                        status_message = (
                            f"상태 업데이트\n"
                            f"시간: {datetime.now()}\n"
                            f"현재 가격: {current_price:.2f}\n"
                            f"잔고: {self.balance:.2f} USDT\n"
                            f"포지션: {current_position if current_position else '없음'}"
                        )
                        logging.info(status_message)
                        self.send_telegram_message(status_message)
                        last_print_time = datetime.now()

                    # 포지션이 없을 때
                    if not current_position or current_position['size'] == 0:
                        if last_signal == 1:
                            self.execute_trade('long', current_price)
                        elif last_signal == -1:
                            self.execute_trade('short', current_price)

                    # 포지션이 있을 때
                    elif current_position['size'] != 0:
                        price_change_pct = ((current_price - current_position['entry_price']) /
                                            current_position['entry_price'] * 100)
                        if current_position['side'] == 'short':
                            price_change_pct = -price_change_pct

                        # 손절/익절/트레일링 스탑 체크
                        if (price_change_pct <= -self.stop_loss_percent or
                                price_change_pct >= self.stop_loss_percent or
                                self.update_trailing_stop(current_price, current_position)):
                            self.execute_trade('close', current_price)

                    time.sleep(10)

                except Exception as e:
                    error_msg = f"메인 루프 오류: {e}\n{traceback.format_exc()}"
                    logging.error(error_msg)
                    self.send_telegram_message(error_msg)
                    time.sleep(10)

        except Exception as e:
            error_msg = f"초기화 오류: {e}\n{traceback.format_exc()}"
            logging.error(error_msg)
            self.send_telegram_message(error_msg)

    def execute_trade(self, action: str, current_price: float = None):
        try:
            if action == 'long':
                position_size = self.calculate_position_size(current_price)
                order = self.execute_with_retry(exchange.create_market_buy_order, self.symbol, position_size)
                self.logger.info(f"롱 포지션 진입: 수량 {position_size}, 가격 {current_price}")
                self.send_telegram_message(f"롱 포지션 진입\n수량: {position_size}\n가격: {current_price}")
                
            elif action == 'short':
                position_size = self.calculate_position_size(current_price)
                order = self.execute_with_retry(exchange.create_market_sell_order, self.symbol, position_size)
                self.logger.info(f"숏 포지션 진입: 수량 {position_size}, 가격 {current_price}")
                self.send_telegram_message(f"숏 포지션 진입\n수량: {position_size}\n가격: {current_price}")
                
            elif action == 'close':
                current_position = self.get_position()
                if current_position:
                    position_size = abs(current_position['size'])
                    if current_position['side'] == 'long':
                        order = self.execute_with_retry(exchange.create_market_sell_order, self.symbol, position_size)
                    else:
                        order = self.execute_with_retry(exchange.create_market_buy_order, self.symbol, position_size)
                    self.logger.info(f"포지션 청산: 수량 {position_size}, 가격 {current_price}")
                    self.send_telegram_message(f"포지션 청산\n수량: {position_size}\n가격: {current_price}")
                    
        except Exception as e:
            self.logger.error(f"거래 실행 오류: {e}")
            self.send_telegram_message(f"거래 실행 오류: {e}")

if __name__ == "__main__":
    trader = TradingManager()
    trader.run_trading()