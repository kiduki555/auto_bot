from binance.client import Client
import os

class BinanceExchange:
    def __init__(self):
        self.markets = {}
        if os.getenv('USE_TESTNET', 'false').lower() == 'true':
            self.client = Client(
                os.getenv('BINANCE_TESTNET_API_KEY'),
                os.getenv('BINANCE_TESTNET_API_SECRET'),
                testnet=True
            )
        else:
            self.client = Client(
                os.getenv('BINANCE_API_KEY'),
                os.getenv('BINANCE_API_SECRET')
            )
        # 거래소 정보 가져오기
        exchange_info = self.client.get_exchange_info()

        # 필요한 심볼만 필터링
        target_symbols = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT']
        self.markets = {
            symbol['symbol']: {
                'precision': {
                    'price': symbol['quoteAssetPrecision'],  # 가격 소수점 자리수
                    'amount': symbol['baseAssetPrecision'],  # 수량 소수점 자리수
                }
            }
            for symbol in exchange_info['symbols'] if symbol['symbol'] in target_symbols
        }

    # 1. 선물 계좌 잔액 조회
    def get_futures_balance(self):
        """Get the balance of the futures account"""
        try:
            balance_info = self.client.futures_account_balance()
            # USDT 잔액만 필터링하여 반환
            usdt_balance = next(item for item in balance_info if item['asset'] == 'USDT')
            return usdt_balance
        except Exception as e:
            print(f"Error fetching futures balance: {str(e)}")
            return None

    # 2. 선물 거래 주문
    def place_futures_order(self, symbol: str, side: str, quantity: float, order_type='MARKET'):
        """Place a futures order on Binance"""
        try:
            if side.lower() == 'buy':
                return self.client.futures_create_order(symbol=symbol, side='BUY', type=order_type, quantity=quantity)
            elif side.lower() == 'sell':
                return self.client.futures_create_order(symbol=symbol, side='SELL', type=order_type, quantity=quantity)
            else:
                raise ValueError("Invalid order side. Use 'buy' or 'sell'.")
        except Exception as e:
            print(f"Error placing futures order: {str(e)}")
            return None

    # 3. 현재 가격 조회
    def get_futures_symbol_price(self, symbol: str):
        """Get the current price of a futures symbol"""
        try:
            price = self.client.futures_symbol_ticker(symbol=symbol)
            return price
        except Exception as e:
            print(f"Error fetching symbol price: {str(e)}")
            return None

    # 4. 활성 주문 조회
    def get_open_orders(self, symbol: str):
        """Get all open orders for a specific symbol"""
        try:
            open_orders = self.client.futures_get_open_orders(symbol=symbol)
            return open_orders
        except Exception as e:
            print(f"Error fetching open orders: {str(e)}")
            return None

    # 5. 주문 취소
    def cancel_order(self, symbol: str, order_id: str):
        """Cancel a specific order"""
        try:
            cancel_response = self.client.futures_cancel_order(symbol=symbol, orderId=order_id)
            return cancel_response
        except Exception as e:
            print(f"Error canceling order: {str(e)}")
            return None

    # 6. 레버리지 설정
    def change_leverage(self, symbol: str, leverage: int):
        """Change leverage for a specific symbol"""
        try:
            response = self.client.futures_change_leverage(symbol=symbol, leverage=leverage)
            return response
        except Exception as e:
            print(f"Error changing leverage: {str(e)}")
            return None

    # 7. 포지션 정보 조회
    def get_position_info(self, symbol: str):
        """Get position information for a specific symbol"""
        try:
            positions = self.client.futures_position_information(symbol=symbol)
            return positions
        except Exception as e:
            print(f"Error fetching position information: {str(e)}")
            return None

    # 8. 최근 거래 내역 조회
    def get_recent_trades(self, symbol: str):
        """Get recent trades for a specific symbol"""
        try:
            recent_trades = self.client.futures_recent_trades(symbol=symbol)
            return recent_trades
        except Exception as e:
            print(f"Error fetching recent trades: {str(e)}")
            return None

    # 9. 캔들 차트 데이터 조회
    def get_historical_klines(self, symbol: str, interval: str, start_str: str, end_str: str):
        """Get historical kline data asynchronously"""
        try:
            # Use the Binance API client to fetch historical klines
            candlesticks = self.client.get_historical_klines(symbol=symbol, interval=interval, start_str=start_str, end_str=end_str)
            return candlesticks
        except Exception as e:
            print(f"Error fetching historical klines: {str(e)}")
            return None 