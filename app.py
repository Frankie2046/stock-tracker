import requests
from flask import Flask, render_template
from flask_caching import Cache
from dotenv import load_dotenv
import os
import time
import logging
from logging.handlers import RotatingFileHandler

# -----------------------
# 配置环境和日志
# -----------------------
load_dotenv()
FMP_API_KEY = os.getenv("SECRET")  # .env 里必须有 SECRET=你的 API_KEY

app = Flask(__name__)

# 设置缓存
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})
cache.init_app(app)

# 日志配置
log_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
# 控制台日志
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.DEBUG)

# 文件日志，自动轮转 5MB，保留 3 个备份
file_handler = RotatingFileHandler("app_debug.log", maxBytes=5*1024*1024, backupCount=3)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.DEBUG)

# 添加到 Flask 默认 logger
app.logger.setLevel(logging.DEBUG)
app.logger.addHandler(console_handler)
app.logger.addHandler(file_handler)

# -----------------------
# 配置
# -----------------------
TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]

# -----------------------
# 获取 FMP 数据
# -----------------------
@cache.memoize(timeout=600)  # 缓存 10 分钟
def get_fmp_data(ticker):
    app.logger.debug(f"请求 FMP API 数据: {ticker}")
    url = f"https://financialmodelingprep.com/stable/quote?symbol={ticker}&apikey={FMP_API_KEY}"
    app.logger.debug(f"请求 URL: {url}")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data:
            price = item.get('price')
            high_52w = item.get('yearHigh')
            low_52w = item.get('yearLow')
            diff_percent = ((price - high_52w) / high_52w * 100) if price and high_52w else 0
            results.append({
                'symbol': item.get('symbol'),
                'name': item.get('name'),
                'last_close': round(price, 2) if price else 0,
                'high_52w': round(high_52w, 2) if high_52w else 0,
                'low_52w': round(low_52w, 2) if low_52w else 0,
                'diff_percent': round(diff_percent, 2)
            })
        app.logger.debug(f"FMP API 数据返回: {results}")
        return results[0] if results else {}
    except Exception as e:
        app.logger.exception(f"API 请求失败: {e}")
        return {}

# -----------------------
# Flask 路由
# -----------------------
@app.route('/')
def index():
    stocks = []
    for ticker in TICKERS:
        time.sleep(0.1)  # 避免请求太快被封
        stocks.append(get_fmp_data(ticker))
    app.logger.debug(f"最终 stocks 数据: {stocks}")
    return render_template('index.html', stocks=stocks)

# -----------------------
# 启动
# -----------------------
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)