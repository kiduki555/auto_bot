import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import ccxt
import logging
from typing import Dict
from src.utils.config_loader import ConfigLoader

class BacktestManager:
    def __init__(self, config_path: str = "config/backtest_config.json"):
        # 설정 로드
        self.config = ConfigLoader(config_path).get_config()
        self.backtest_config = self.config['backtest']
        
        # 거래소 설정
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',
                'adjustForTimeDifference': True
            }
        })
        
        # 기본 설정
        trading_settings = self.backtest_config['trading_settings']
        self.symbol = self.backtest_config['data_settings']['symbols'][0]
        self.timeframe = self.backtest_config['time_settings']['timeframe']
        self.initial_balance = trading_settings['initial_balance']
        self.current_balance = self.initial_balance
        self.leverage = trading_settings['leverage']
        
        # 위험 관리 설정
        risk_settings = trading_settings['risk_management']
        self.risk_percent = risk_settings['risk_per_trade_percent']
        self.stop_loss_percent = risk_settings['stop_loss_percent']
        self.take_profit_percent = risk_settings['take_profit_percent']
        
        # 수수료 설정
        fee_settings = self.backtest_config['fee_settings']
        self.maker_fee = fee_settings['maker_fee']
        self.taker_fee = fee_settings['taker_fee']
        self.slippage = fee_settings['slippage']
        
        # 거래 관련 속성
        self.trade_history = []
        self.current_position = None
        self.trailing_stop_price = 0
        
        # 로거 설정
        self.logger = self.setup_logging()
        
    def setup_logging(self):
        logger = logging.getLogger('BacktestManager')
        logger.setLevel(logging.INFO)
        
        # 로그 디렉토리 설정
        log_dir = self.backtest_config['performance_metrics']['export_directory']
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        file_handler = logging.FileHandler(f'{log_dir}/backtest.log', encoding='utf-8')
        file_handler.setFormatter(formatter)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        if logger.handlers:
            logger.handlers.clear()
            
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger

    # ... [기존 메서드들은 동일하게 유지] ...

if __name__ == "__main__":
    try:
        # 백테스트 설정 파일 경로
        config_path = "config/backtest_config.json"
        
        # 백테스트 매니저 초기화
        backtest = BacktestManager(config_path)
        
        # 백테스트 기간 설정
        start_date = datetime.strptime(backtest.backtest_config['time_settings']['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(backtest.backtest_config['time_settings']['end_date'], '%Y-%m-%d')
        
        # 백테스트 실행
        results = backtest.run_backtest(start_date, end_date)
        
        # 결과 저장
        if backtest.backtest_config['performance_metrics']['export_results']:
            results_df = pd.DataFrame([results])
            export_path = f"{backtest.backtest_config['performance_metrics']['export_directory']}/backtest_results.csv"
            results_df.to_csv(export_path, index=False)
            print(f"Results saved to {export_path}")
            
    except Exception as e:
        print(f"Error during backtest: {e}")