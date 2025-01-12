import ccxt

# 바이낸스 설정
exchange = ccxt.binance({
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',  # 선물 거래
    }
})

# 심볼 설정
symbol = 'BTC/USDT'

# 최소 거래 금액 확인 함수
def fetch_min_trade_amount(exchange, symbol):
    """
    거래소에서 심볼의 최소 거래 금액을 확인합니다.
    
    :param exchange: ccxt 바이낸스 인스턴스
    :param symbol: 확인할 거래 페어 (예: 'ETH/USDT')
    :return: 최소 거래 금액 (float)
    """
    try:
        markets = exchange.fetch_markets()  # 모든 시장 정보 가져오기
        for market in markets:
            if market['symbol'] == symbol:
                return market['limits']['amount']['min']  # 최소 거래 금액 반환
        return None
    except Exception as e:
        print(f"Error fetching minimum trade amount: {e}")
        return None

# 최소 거래 금액 가져오기
min_trade_amount = fetch_min_trade_amount(exchange, symbol)

# 결과 출력
if min_trade_amount:
    print(f"Minimum trade amount for {symbol}: {min_trade_amount} ETH")
else:
    print(f"Could not fetch minimum trade amount for {symbol}.")
