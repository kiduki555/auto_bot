trading-project
├── src
│   ├── strategies
│   │   ├── __init__.py
│   │   ├── base_strategy.py
│   │   └── momentum_strategy.py
│   ├── tests
│   │   ├── __init__.py
│   │   ├── test_trade
│   │   │   ├── __init__.py
│   │   │   └── backtest.py
│   │   └── real_trade
│   │       ├── __init__.py
│   │       └── live_trade.py
│   ├── utils
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── logger.py
│   └── main.py
├── data
│   ├── historical
│   │   └── binance
│   └── results
│       ├── backtest
│       └── live
├── config
│   ├── backtest_config.yaml
│   └── trading_config.yaml
├── requirements.txt
└── README.md