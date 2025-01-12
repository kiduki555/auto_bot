# Auto Trading Bot Project

암호화폐 자동 거래 봇 프로젝트입니다. 바이낸스 선물 거래를 지원하며 백테스트와 실시간 거래 기능을 제공합니다.

## 주요 기능

- 백테스트 시스템
- 실시간 거래 시스템
- 다중 전략 지원
- 텔레그램 알림
- 위험 관리 시스템
- 성능 분석 및 리포트

## 디렉토리 구조

```
trading-project
├── src
│   ├── strategies          # 거래 전략을 정의하는 모듈
│   ├── tests               # 테스트 관련 모듈
│   ├── utils               # 유틸리티 함수 및 클래스
│   └── main.py             # 애플리케이션의 진입점
├── data                    # 데이터 저장소
│   ├── historical          # 역사적 데이터
│   └── results             # 결과 저장소
├── config                  # 설정 파일
├── requirements.txt        # 프로젝트 의존성
└── README.md               # 프로젝트 문서
```

## 설치

1. 이 저장소를 클론합니다.
2. 필요한 패키지를 설치합니다:

```
pip install -r requirements.txt
```

## 사용법

1. `src/main.py`를 실행하여 애플리케이션을 시작합니다.
2. 원하는 거래 전략을 `src/strategies` 디렉토리에 추가합니다.
3. 백테스트를 실행하려면 `src/tests/test_trade/backtest.py`를 사용합니다.
4. 실시간 거래를 실행하려면 `src/tests/real_trade/live_trade.py`를 사용합니다.

## 기여

기여를 원하시는 분은 이 저장소를 포크하고 변경 사항을 제출해 주세요. 모든 기여는 환영합니다!

## 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다.
