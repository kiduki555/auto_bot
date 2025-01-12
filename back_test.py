import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import ccxt
import logging
from typing import Dict

class BacktestManager:
    def __init__(self, symbol: str, timeframe: str, initial_balance: float,
                 risk_percent: float, stop_loss_percent: float, 
                 take_profit_percent: float, leverage: int):
        # 바이낸스 설정
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',
                'adjustForTimeDifference': True
            }
        })
        
        # 기본 설정
        self.symbol = symbol
        self.timeframe = timeframe
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.risk_percent = risk_percent
        self.stop_loss_percent = stop_loss_percent
        self.take_profit_percent = take_profit_percent
        self.leverage = leverage
        
        # 거래 관련 속성
        self.trade_history = []
        self.current_position = None
        self.trailing_stop_price = 0
        
        # 로거 설정
        self.logger = self.setup_logging()

    def setup_logging(self):
        logger = logging.getLogger('BacktestManager')
        logger.setLevel(logging.INFO)
        
        # 포맷터 설정
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # 파일 핸들러
        file_handler = logging.FileHandler('backtest.log', encoding='utf-8')
        file_handler.setFormatter(formatter)
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # 기존 핸들러 제거
        if logger.handlers:
            logger.handlers.clear()
            
        # 새 핸들러 추가
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger

    def fetch_historical_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        try:
            timeframes = {
                '15m': 15 * 60,
                '1h': 60 * 60,
                '4h': 4 * 60 * 60,
                '1d': 24 * 60 * 60
            }
            start_timestamp = int(start_date.timestamp() * 1000)
            ohlcv = self.exchange.fetch_ohlcv(
                self.symbol,
                self.timeframe,
                since=start_timestamp,
                limit=1000
            )
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            self.logger.error(f"Error fetching historical data: {e}")
            raise

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        try:
            # EMA 계산
            df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
            df['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()
            df['ema_55'] = df['close'].ewm(span=55, adjust=False).mean()  # EMA-55 추가
            
            # 볼린저 밴드 계산
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
            
            # RSI 계산
            df['rsi'] = self.calculate_rsi(df['close'], 14)
            
            # MACD 계산
            df['macd'] = df['close'].ewm(span=12, adjust=False).mean() - df['close'].ewm(span=26, adjust=False).mean()
            df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['macd_hist'] = df['macd'] - df['macd_signal']
            
            # 거래량 분석
            df['volume_ma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']
            
            # ATR 계산
            df['atr'] = self.calculate_atr(df, 14)
            
            # ADX 계산
            df['adx'] = self.calculate_adx(df, 14)
            
            return df
        except Exception as e:
            self.logger.error(f"지표 계산 중 오류 발생: {str(e)}")
            raise

    @staticmethod
    def calculate_rsi(series: pd.Series, period: int) -> pd.Series:
        delta = series.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int) -> pd.Series:
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        true_range = high_low.combine(high_close, max).combine(low_close, max)
        return true_range.rolling(window=period).mean()

    @staticmethod
    def calculate_adx(df: pd.DataFrame, period: int) -> pd.Series:
        plus_dm = df['high'].diff()
        minus_dm = -df['low'].diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0

        atr = BacktestManager.calculate_atr(df, period)
        plus_di = 100 * (plus_dm / atr).rolling(window=period).mean()
        minus_di = 100 * (minus_dm / atr).rolling(window=period).mean()
        dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100
        return dx.rolling(window=period).mean()

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        try:
            df = self.calculate_indicators(df)
            
            # 변동성 기반 매매 조건 추가
            df['volatility'] = df['atr'] / df['close'] * 100
            
            # 강화된 롱 진입 조건
            long_conditions = (
                (df['ema_9'] > df['ema_21']) &  # 단기 상승 트렌드
                (df['ema_21'] > df['ema_55']) &  # 중기 상승 트렌드
                (df['close'] > df['bb_middle']) &  # 중간선 위
                (df['macd_hist'] > 0) &  # MACD 상승
                (df['rsi'] > 40) & (df['rsi'] < 70) &  # RSI 중립
                (df['adx'] > 25) &  # 강한 트렌드
                (df['volatility'] < 3)  # 변동성 3% 미만일 때만
            )
            
            # 강화된 숏 진입 조건
            short_conditions = (
                (df['ema_9'] < df['ema_21']) &  # 단기 하락 트렌드
                (df['ema_21'] < df['ema_55']) &  # 중기 하락 트렌드
                (df['close'] < df['bb_middle']) &  # 중간선 아래
                (df['macd_hist'] < 0) &  # MACD 하락
                (df['rsi'] < 60) & (df['rsi'] > 30) &  # RSI 중립
                (df['adx'] > 25) &  # 강한 트렌드
                (df['volatility'] < 3)  # 변동성 3% 미만일 때만
            )
            
            # 시그널 생성
            df['signal'] = 0
            df.loc[long_conditions, 'signal'] = 1
            df.loc[short_conditions, 'signal'] = -1
            
            # 연속 시그널 제거
            df['signal'] = df['signal'] * (df['signal'].shift(1) != df['signal'])
            
            return df
        except Exception as e:
            self.logger.error(f"시그널 생성 중 오류 발생: {str(e)}")
            raise

    def calculate_position_size(self, current_price: float) -> float:
        try:
            risk_amount = self.current_balance * (self.risk_percent / 100)
            stop_loss_distance = (self.stop_loss_percent / 100) * current_price
            position_size = (risk_amount / stop_loss_distance) * self.leverage
            return round(position_size, 6)
        except Exception as e:
            self.logger.error(f"포지션 사이즈 계산 중 오류: {e}")
            return 0

    def update_trailing_stop(self, current_price: float, position: dict) -> float:
        try:
            if position['side'] == 'long':
                profit_pct = (current_price - position['entry_price']) / position['entry_price'] * 100
                if profit_pct >= 1.0:  # 1% 이상 수익 시
                    new_stop = current_price * 0.995  # 0.5% 트레일링 스탑
                    return max(new_stop, self.trailing_stop_price)
            else:  # short position
                profit_pct = (position['entry_price'] - current_price) / position['entry_price'] * 100
                if profit_pct >= 1.0:  # 1% 이상 수익 시
                    new_stop = current_price * 1.005  # 0.5% 트레일링 스탑
                    return min(new_stop, self.trailing_stop_price)
            return self.trailing_stop_price
            
        except Exception as e:
            self.logger.error(f"트레일링 스탑 업데이트 중 오류: {e}")
            return self.trailing_stop_price

    def run_backtest(self, start_date: datetime = None, end_date: datetime = None) -> Dict:
        try:
            if start_date is None:
                end = datetime.now() - timedelta(days=7)
                start = end - timedelta(days=90)
                random_days = random.randint(0, (end - start).days)
                start_date = start + timedelta(days=random_days)
                end_date = start_date + timedelta(days=7)

            self.logger.info(f"백테스트 기간: {start_date} ~ {end_date}")
            
            df = self.fetch_historical_data(start_date, end_date)
            df = self.generate_signals(df)
            
            position = None
            trades = []
            
            for index, row in df.iterrows():
                try:
                    if position is None:  # 포지션이 없을 때
                        if row['signal'] != 0:
                            position_size = self.calculate_position_size(row['close'])
                            position = {
                                'side': 'long' if row['signal'] == 1 else 'short',
                                'size': position_size,
                                'entry_price': row['close'],
                                'entry_time': index
                            }
                            
                    else:  # 포지션이 있을 때
                        if position['side'] == 'long':
                            if row['close'] <= position['entry_price'] * (1 - self.stop_loss_percent / 100):
                                # 손절
                                trades.append({
                                    'side': 'long',
                                    'entry_price': position['entry_price'],
                                    'exit_price': row['close'],
                                    'entry_time': position['entry_time'],
                                    'exit_time': index,
                                    'pnl': (row['close'] - position['entry_price']) * position['size']
                                })
                                position = None
                            elif row['close'] >= position['entry_price'] * (1 + self.take_profit_percent / 100):
                                # 익절
                                trades.append({
                                    'side': 'long',
                                    'entry_price': position['entry_price'],
                                    'exit_price': row['close'],
                                    'entry_time': position['entry_time'],
                                    'exit_time': index,
                                    'pnl': (row['close'] - position['entry_price']) * position['size']
                                })
                                position = None
                        else:  # short position
                            if row['close'] >= position['entry_price'] * (1 + self.stop_loss_percent / 100):
                                # 손절
                                trades.append({
                                    'side': 'short',
                                    'entry_price': position['entry_price'],
                                    'exit_price': row['close'],
                                    'entry_time': position['entry_time'],
                                    'exit_time': index,
                                    'pnl': (position['entry_price'] - row['close']) * position['size']
                                })
                                position = None
                            elif row['close'] <= position['entry_price'] * (1 - self.take_profit_percent / 100):
                                # 익절
                                trades.append({
                                    'side': 'short',
                                    'entry_price': position['entry_price'],
                                    'exit_price': row['close'],
                                    'entry_time': position['entry_time'],
                                    'exit_time': index,
                                    'pnl': (position['entry_price'] - row['close']) * position['size']
                                })
                                position = None
                        
                except Exception as e:
                    self.logger.error(f"거래 처리 중 오류: {e}")
                    continue
                    
            return self.generate_backtest_results(trades)
            
        except Exception as e:
            self.logger.error(f"백테스트 오류: {e}")
            raise

    def generate_backtest_results(self, trades: list) -> dict:
        if not trades:
            self.logger.info("해당 기간 동안 거래가 없었습니다.")
            return {
                "initial_balance": self.initial_balance,
                "final_balance": self.initial_balance,
                "total_return": 0,
                "total_trades": 0,
                "win_rate": 0,
                "avg_profit": 0,
                "max_drawdown": 0
            }

        # 결과 계산
        final_balance = self.initial_balance
        balance_history = [self.initial_balance]
        
        for trade in trades:
            final_balance += trade['pnl']
            balance_history.append(final_balance)

        # 통계 계산
        total_trades = len(trades)
        winning_trades = sum(1 for trade in trades if trade['pnl'] > 0)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        avg_profit = sum(trade['pnl'] for trade in trades) / total_trades if total_trades > 0 else 0
        
        # 최대 손실률 계산
        max_drawdown = 0
        peak = balance_history[0]
        for balance in balance_history:
            if balance > peak:
                peak = balance
            drawdown = (peak - balance) / peak * 100
            max_drawdown = max(max_drawdown, drawdown)

        results = {
            "initial_balance": self.initial_balance,
            "final_balance": final_balance,
            "total_return": ((final_balance - self.initial_balance) / self.initial_balance * 100),
            "total_trades": total_trades,
            "win_rate": win_rate,
            "avg_profit": avg_profit,
            "max_drawdown": max_drawdown
        }

        # 결과 출력
        self.logger.info(f"초기 잔고: {results['initial_balance']:.2f} USDT")
        self.logger.info(f"최종 잔고: {results['final_balance']:.2f} USDT")
        self.logger.info(f"총 수익률: {results['total_return']:.2f}%")
        self.logger.info(f"총 거래 횟수: {results['total_trades']}")
        self.logger.info(f"승률: {results['win_rate']:.2f}%")
        self.logger.info(f"평균 수익: {results['avg_profit']:.2f} USDT")
        self.logger.info(f"최대 손실률: {results['max_drawdown']:.2f}%")

        return results

if __name__ == "__main__":
    backtest = BacktestManager(
        symbol='ETH/USDT',
        timeframe='15m',
        initial_balance=1000,
        risk_percent=0.5,  # 리스크 줄임
        stop_loss_percent=1.0,  # 손절폭 줄임
        take_profit_percent=2.0,  # 익절폭 조정
        leverage=3  # 레버리지 줄임
    )
    results = backtest.run_backtest()
