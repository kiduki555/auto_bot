from auto_bot.src.test_trade import BacktestManager

def main():
    config_path = "config/backtest_config.json"
    backtester = BacktestManager(config_path)
    # ... 나머지 로직