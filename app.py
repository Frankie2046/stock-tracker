import os
import requests
from flask import Flask, render_template
from flask_caching import Cache
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from config.log import logger
from config.apollo import apollo
# ---------------------------
# 加载环境变量
load_dotenv()

FMP_API_KEY = os.getenv("SECRET")

app = Flask(__name__)

# ---------------------------
# Redis 缓存配置
# cache = Cache(config={
#     "CACHE_TYPE": "RedisCache",
#     "CACHE_REDIS_HOST": "redis",
#     "CACHE_REDIS_PORT": 6379,
#     "CACHE_DEFAULT_TIMEOUT": 600  # 缓存 10 分钟
# })
# cache.init_app(app)
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})
cache.init_app(app)

# ---------------------------
# 获取股票数据
@cache.memoize(timeout=600)
def get_fmp_data(ticker):
    app.logger.debug(f"请求 FMP API: {ticker}")
    url = f"https://financialmodelingprep.com/stable/quote?symbol={ticker}&apikey={FMP_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data:
            return {}

        item = data[0]
        price = item.get('price', 0)
        high_52w = item.get('yearHigh', 0)
        low_52w = item.get('yearLow', 0)
        diff_percent = ((price - high_52w) / high_52w * 100) if high_52w else 0

        result = {
            'symbol': item.get('symbol'),
            'name': item.get('name'),
            'last_close': round(price, 2),
            'high_52w': round(high_52w, 2),
            'low_52w': round(low_52w, 2),
            'diff_percent': round(diff_percent, 2)
        }
        return result

    except Exception as e:
        app.logger.error(f"API 请求失败: {ticker} -> {e}")
        return {}

# ---------------------------
# 并行请求所有股票
def fetch_all_stocks(TICKERS):
    with ThreadPoolExecutor(max_workers=len(TICKERS)) as executor:
        results = executor.map(get_fmp_data, TICKERS)
    return list(results)

@app.route('/')
def index():
    cfg = apollo.config
    logger.debug(f"Serving current config: {cfg}")
    TICKERS = cfg.get("tickers", "AAPL").split(",")
    stocks = fetch_all_stocks(TICKERS)
    app.logger.debug(f"最终 stocks 数据: {stocks}")
    return render_template('index.html', stocks=stocks)

if __name__ == "__main__":
    # debug=False，生产环境使用 Gunicorn
    app.run(host="0.0.0.0", port=5001, debug=False)