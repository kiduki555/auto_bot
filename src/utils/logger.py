import logging

def setup_logger(name: str, log_file: str, level=logging.INFO) -> logging.Logger:
    """로거를 설정하는 함수"""
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    
    return logger

# 예시로 로거를 설정합니다.
if __name__ == "__main__":
    logger = setup_logger('trading_logger', 'trading.log')
    logger.info('로거가 설정되었습니다.')