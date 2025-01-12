# config.py
import yaml

def load_config(file_path: str) -> dict:
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

def get_backtest_config() -> dict:
    return load_config('../config/backtest_config.yaml')

def get_trading_config() -> dict:
    return load_config('../config/trading_config.yaml')