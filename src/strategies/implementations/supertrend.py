from src.strategies.base import Strategy
import pandas as pd
import ta

class SupertrendStrategy(Strategy):
    def __init__(self, period: int = 10, multiplier: float = 3.0):
        self.period = period
        self.multiplier = multiplier
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        high = data['high']
        low = data['low']
        close = data['close']
        
        # Supertrend 계산
        st = ta.trend.Supertrend(high, low, close, self.period, self.multiplier)
        supertrend = st.supertrend()
        
        # 시그널 생성
        signals = pd.Series(index=data.index, data=0)
        signals[close > supertrend] = 1  # 롱 포지션
        signals[close < supertrend] = -1  # 숏 포지션
        
        return signals

    def get_strategy_name(self) -> str:
        return f"Supertrend_{self.period}_{self.multiplier}"