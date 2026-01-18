import logging
import sys

def get_logger(name="AppLogger", level=logging.DEBUG):
    """返回一个标准化 logger"""
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        logger.setLevel(level)
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
        )
        # 控制台输出
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

# 默认 logger，可直接 import 使用
logger = get_logger()