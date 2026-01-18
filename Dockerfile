FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝整个项目
COPY . .

# 暴露端口
EXPOSE 5000

# 直接用 gunicorn 启动 app.py 中的 app
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5000", "app:app"]