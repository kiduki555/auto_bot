# Auto Bot - Cryptocurrency Automated Trading Bot

## 🚀 Overview
An advanced cryptocurrency trading bot equipped with various technical analysis strategies, real-time trading, and backtesting systems.

## ✨ Key Features
- Multiple trading strategies (MACD, RSI, VWAP)
- Real-time trading with Binance
- Safe testing through paper trading
- Comprehensive backtesting capabilities
- Telegram notification integration
- Risk management system
- Built-in technical indicators library

## 🔧 Project Structure
```
auto-bot/
├── scripts/        # Execution scripts
│   ├── run_bot.py      # Real-time trading
│   └── run_backtest.py # Backtesting
├── src/            # Source code
│   ├── core/           # Core trading logic
│   ├── indicators/     # Technical indicators
│   ├── strategies/     # Trading strategies
│   └── utils/          # Utilities
├── .env            # Environment variables
└── requirements.txt # Dependency packages
```

## 📋 Available Strategies
1. **MACD Crossover Strategy**
   - Trend-following using MACD indicators
   - Customizable parameters

2. **RSI Divergence Strategy**
   - Detects price/RSI divergences
   - Multi-timeframe analysis

3. **VWAP Bounce Strategy**
   - Utilizes volume-weighted average price
   - Support/resistance level analysis

## 🚀 Getting Started

### 1. Clone the repository:
```bash
git clone https://github.com/yourusername/auto-bot.git
cd auto-bot
```

### 2. Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Set up the `.env` file:
```env
# Binance API
API_KEY=your_api_key
API_SECRET=your_api_secret

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Trading Settings
RISK_PER_TRADE=1.0
LEVERAGE=1
```

## 💻 Usage

### Real-Time Trading
#### Paper Trading Mode:
```bash
python scripts/run_bot.py --mode paper --strategy macd_crossover --symbol BTCUSDT --interval 1h
```

#### Live Trading Mode:
```bash
python scripts/run_bot.py --mode live --strategy macd_crossover --symbol BTCUSDT --interval 1h
```

### Backtesting
#### Basic Backtest:
```bash
python scripts/run_backtest.py --strategy macd_crossover
```

#### Detailed Backtest:
```bash
python scripts/run_backtest.py \
    --strategy macd_crossover \
    --symbol BTCUSDT \
    --interval 1h \
    --start-date 2023-01-01 \
    --end-date 2023-12-31 \
    --capital 10000
```

## ⚙️ Configuration Options

### Strategy Parameters:
- `risk_per_trade`: Risk percentage per trade (default: 1.0%)
- `leverage`: Leverage multiplier (default: 1)
- `stop_loss`: Stop-loss ratio
- `take_profit`: Take-profit ratio

### Supported Timeframes:
- Intraday: 1m, 3m, 5m, 15m, 30m
- Hourly: 1h, 2h, 4h, 6h, 8h, 12h
- Daily: 1d, 3d, 1w, 1M

## 📊 Performance Metrics
- Win rate
- Risk/reward ratio
- Maximum drawdown
- Sharpe ratio
- Daily/Monthly returns

## 🔒 Security
- API keys stored securely as environment variables
- Safe testing via paper trading
- Controlled risk management

## 📝 License
This project is licensed under the MIT License.

