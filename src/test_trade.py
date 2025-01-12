import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import ccxt
import logging
from typing import Dict
from src.utils.config_loader import ConfigLoader

class BacktestManager:
    def __init__(self, config_path: str):
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
        
        # 위험 관리 설정
        risk_settings = trading_settings['risk_management']
        self.risk_percent = risk_settings['risk_per_trade_percent']
        self.stop_loss_percent = risk_settings['stop_loss_percent']
        self.take_profit_percent = risk_settings['take_profit_percent']
        self.leverage = trading_settings['leverage']
        
        # 수수료 설정
        fee_settings = self.backtest_config['fee_settings']
        self.maker_fee = fee_settings['maker_fee']
        self.taker_fee = fee_settings['taker_fee']
        self.slippage = fee_settings['slippage']
        
        # 거래 관련 속성
        self.trade_history = []