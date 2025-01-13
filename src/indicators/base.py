from abc import ABC, abstractmethod
import pandas as pd

class Strategy(ABC):
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """전략 시그널 생성"""
        pass

    @abstractmethod
    def get_strategy_name(self) -> str:
        """전략 이름 반환"""
        pass