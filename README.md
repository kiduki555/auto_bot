## Auto Bot

### 1. **Project Overview**
- **Project Name**: Smart Trading System
- **Purpose and Key Features**: This project implements various trading strategies to support automated trading. Users can select multiple strategies and generate trading signals based on real-time data.
- **Problem Solving Approach or Value Provided**: This system aims to maximize profits by leveraging market volatility and helps users easily manage and apply strategies.
- **Brief Introduction Sentence**: "This project is designed to maximize investor profits through automated trading."

---

### 2. **Environment Variables Explanation**
- **Description of env items**: This project runs in a Python environment and includes the necessary libraries and packages. The `.env` file is used to manage sensitive information such as API keys.
```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here  # Telegram bot authentication token
TELEGRAM_CHAT_ID=your_chat_id_here        # ID of the Telegram chat to send messages

# Trading Configuration
TRADING_SYMBOL=BTCUSDT                    # Symbol of the asset to trade
TRADING_TIMEFRAME=1h                      # Trading time frame
TRADING_STRATEGY=adaptive_supertrend      # Name of the strategy to use
RISK_PER_TRADE=0.02                       # Risk per trade
MAX_POSITION_SIZE=1.0                     # Maximum position size
TP_SL_MODE=atr                            # Take Profit/Stop Loss mode
SL_MULTIPLIER=2.0                         # Stop Loss multiplier
TP_MULTIPLIER=3.0                         # Take Profit multiplier
USE_TRAILING_STOP=false                   # Whether to use trailing stop (true/false)
TRAILING_STOP_ACTIVATION=0.01            # Trailing stop activation value
TRAILING_STOP_DISTANCE=0.005              # Trailing stop distance

# Binance API Configuration
BINANCE_API_KEY=your_binance_api_key_here  # Binance API key
BINANCE_API_SECRET=your_binance_api_secret_here  # Binance API secret
BINANCE_TESTNET_API_KEY=your_testnet_api_key_here  # Binance testnet API key
BINANCE_TESTNET_API_SECRET=your_testnet_api_secret_here  # Binance testnet API secret

# Environment Configuration
USE_TESTNET=true  # Set to true to use testnet, false to use live Binance
```

---

### 3. **Features**
- **Key Features**
  - **Various Trading Strategies**: Supports multiple strategies such as Smart Money Concepts, Future Trend, Adaptive SuperTrend, etc.
  - **Real-time Data Processing**: Collects and analyzes real-time data through exchange APIs.
  - **Signal Generation and Trade Execution**: Generates trading signals based on each strategy and automatically executes trades.
  - **Customizable**: Users can adjust the parameters of the strategies for tailored trading.

---

### 4. **Strategy List**
- **Smart Money Concepts**: Generates trading signals by analyzing market structure.
- **Future Trend**: Generates trading signals based on volume data.
- **Adaptive SuperTrend**: Analyzes market volatility using an adaptive SuperTrend.
- **EMACrossover**: Generates trading signals based on short-term and long-term EMA crossovers.
- **Triple EMA**: Determines market direction using three EMAs.
- **Stochastic RSI**: Generates trading signals by combining Stochastic RSI and MACD.
- **Supertrend**: Generates trading signals using the Supertrend indicator.
- **MACD Crossover**: Generates trading signals based on MACD crossovers.

---

### 5. **Installation Instructions**
- **Instructions on how to install and run the project.**

#### General Setup:
1. **Prerequisites**
   - Python 3.9 or higher
   - Required libraries: pandas, ta, requests, etc.

2. **Installation Steps**
   - Clone or download the project:
     ```bash
     git clone https://github.com/kiduki555/auto_bot
     ```
   - Install dependencies:
     ```bash
     pip install -r requirements.txt
     ```
   - Run the application:
     ```bash
     python main.py
     ```

---

### 6. **Usage**
- **Specific instructions on how to use the project.**
- Example commands, API usage, GUI operation methods, etc.
- Code examples or commands:
  ```python
  from strategies.implementations.smart_money_concepts import SmartMoneyConcepts
  
  strategy = SmartMoneyConcepts()
  signal = strategy.get_signal(data, current_position)
  print(signal)
  ```

---

### 7. **Contribution Guidelines**
- **How to contribute to the project.**
- Contribution procedures: forking, pull request (PR) methods, commit message rules, etc.
- Add a welcoming message for contributors: "All contributions are welcome! Let's improve this project together."

---

### 8. **Issue Reporting and Feedback**
- **How to report bugs or provide suggestions.**
- Link to the Issues tab or email address: "If you have any bugs or suggestions, please use the [Issues](https://github.com/kiduki555/auto_bot/issues) tab."

---

### 9. **License**
- **License applied to the project**: This project is licensed under the [MIT License](LICENSE).

---

### 10. **Author Information**
- **Project Author**: 
  - Name: Jae-Hong Kim
  - Contact: kiduki555@gmail.com

---

### 11. **Acknowledgments**
- **Open-source projects, libraries, or tools used**: 
```
python-binance>=1.0.19
pandas>=1.5.0
numpy>=1.23.0
ta>=0.10.0
scikit-learn>=1.0.0
matplotlib>=3.5.0
plotly>=5.10.0
python-dotenv>=0.20.0
colorlog>=6.7.0
tabulate>=0.9.0
joblib>=1.2.0
pytest>=7.0.0
black>=22.0.0
flake8>=5.0.0
mypy>=1.0.0
coverage>=7.0.0
python-telegram-bot>=20.0
```
---

### 12. **TODO List**
- **Future features or improvements for the project**:
```
Binance API integration:
[ ] Add more methods to the BinanceExchange class (e.g., balance retrieval, order history retrieval, etc.).
[ ] Add logging functionality for results after executing trades.
Strategy implementation:
[ ] Write test cases for all strategies in src/strategies/implementations.
[ ] Add documentation and usage examples for each strategy.
Logging improvements:
[ ] Add functionality to set logging levels (DEBUG, INFO, ERROR, etc.).
[ ] Add functionality to manage log file retention periods.
Error handling:
[ ] Add various exception handling for API calls.
[ ] Add functionality to provide clear error messages to users.
Environment variable management:
[ ] Add an example of the .env file in src/.env.example to guide users on required environment variables.
[ ] Set default values when loading environment variables to enhance code flexibility.
Unit testing:
[ ] Write unit tests for all major functionalities.
[ ] Add test automation to the CI/CD pipeline.
Documentation:
[ ] Add project setup and execution methods to the README.md file.
[ ] Add docstrings for each module and class.
Performance optimization:
[ ] Explore ways to optimize data processing and API calls.
[ ] Analyze performance comparisons between backtesting and live trading.
User interface:
[ ] Explore ways to improve user interaction through CLI or GUI.
[ ] Add functionality to save and load user settings.
Other:
[ ] Update and reflect the latest changes in the Binance API.
[ ] Review additional technical indicators and strategy implementations.
```