import requests
from flask import Flask, render_template
from flask_caching import Cache
from dotenv import load_dotenv
import os
import time
# 加载 .env 文件内容到环境变量
load_dotenv()

# 配置信息
# FMP_API_KEY= "你的_API_KEY_放在这里"  # 填入你的 API Key
FMP_API_KEY = os.getenv("SECRET")

app = Flask(__name__)

# 缓存配置
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})
cache.init_app(app)

TICKERS = ["AAPL","MSFT","GOOGL","AMZN","NVDA","META","TSLA"]

# @cache.cached(timeout=6, key_prefix='fmp_stock_data')
@cache.memoize(timeout=600)
def get_fmp_data(ticker):
    print(f"正在请求 FMP 官方 API 数据...,{ticker}")
    url = f"https://financialmodelingprep.com/stable/quote?symbol={ticker}&apikey={FMP_API_KEY}"
    print(f"请求的 URL: {url}")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data:
            # FMP 返回的字段名非常直观
            price = item.get('price')
            high_52w = item.get('yearHigh')
            low_52w = item.get('yearLow')
            # 计算距52周高位的差值百分比
            diff_percent = 0
            if high_52w and price:
                diff_percent = ((price - high_52w) / high_52w) * 100
                
            results.append({
                'symbol': item.get('symbol'),
                'name': item.get('name'),
                'last_close': round(price, 2) if price else 0,
                'high_52w': round(high_52w, 2) if high_52w else 0,
                'low_52w': round(low_52w, 2) if low_52w else 0,
                'diff_percent': round(diff_percent, 2)
            })
        print(f"FMP API 数据请求成功: {results}")
        # 按照 TICKERS 的原始顺序简单排序（可选）
        return results[0]
    except Exception as e:
        print(f"API 请求失败: {e}")
        return []

@app.route('/')
def index():
    stocks = []
    for ticker in TICKERS:
        time.sleep(0.1)
        stocks.append(get_fmp_data(ticker))
    print(stocks)
    return render_template('index.html', stocks=stocks)

if __name__ == '__main__':
    app.run(host="0.0.0.0",debug=True,port = 5000)

