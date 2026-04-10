FROM python:3.11-slim

WORKDIR /app

# ==================== 安装系统依赖 ====================
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    libasound2 \
    libgbm1 \
    libnss3 \
    libxss1 \
    libxv1 \
    libgtk-3-0 \
    fonts-liberation \
    fonts-noto-cjk \
    xdg-utils \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# ==================== 安装 Chrome + ChromeDriver（AMD64）====================
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub \
    | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] \
    http://dl.google.com/linux/chrome/deb/ stable main" \
    > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖（seleniumbase 会自动管理 selenium 版本）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装 chromium-driver（ChromeDriver）
RUN pip install --no-cache-dir seleniumbase && \
    seleniumbase install chromedriver

# ==================== 复制应用代码 ====================
COPY backend/ ./backend/
COPY frontend/build/ ./frontend/build/
COPY scripts/ ./scripts/

# 创建数据目录
RUN mkdir -p /app/data/cookies /app/data/logs /app/logs

# ==================== 环境变量 ====================
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROMEDRIVER_PATH=/root/.cache/selenium/chromedriver
ENV PYTEST_XVFB=1
ENV DISPLAY=:99
ENV PYTHONPATH=/app/backend

EXPOSE 8000 3000

CMD ["/bin/bash", "/app/scripts/start.sh"]
