FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# ==================== 安装系统依赖 ====================
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    # Chrome/Chromium 依赖的字体和库
    libasound2 \
    libgbm1 \
    libnss3 \
    libxss1 \
    libxv1 \
    libgtk-3-0 \
    fonts-liberation \
    fonts-noto-cjk \
    xdg-utils \
    # 无头模式所需
    xvfb \
    # 清理
    && rm -rf /var/lib/apt/lists/*

# ==================== 安装 Chrome / ChromeDriver ====================
# 检测 CPU 架构，AMD64 用 Chrome，其他架构用 Chromium
RUN if [ "$(dpkg --print-architecture)" = "amd64" ]; then \
    # AMD64: 安装 Google Chrome
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends google-chrome-stable && \
    # 使用 seleniumbase 安装匹配的 ChromeDriver
    pip install --no-cache-dir seleniumbase && \
    seleniumbase install chromedriver; \
    else \
    # ARM64/其他: 安装 Chromium
    apt-get update && \
    apt-get install -y --no-install-recommends chromium chromium-driver; \
    fi

# ==================== 复制依赖文件 ====================
COPY requirements.txt .

# 安装 Python 依赖
RUN rm -rf ~/.cache/pip && pip install --no-cache-dir -r requirements.txt

# 全局安装 serve
RUN npm install -g serve

# 复制应用代码
COPY backend/ ./backend/
COPY frontend/build/ ./frontend/build/
COPY scripts/ ./scripts/

# 创建数据目录
RUN mkdir -p /app/data/cookies /app/data/logs /app/logs

# ==================== Selenium 环境变量 ====================
# Chrome 相关
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROMEDRIVER_PATH=/root/.cache/selenium/chromedriver
# 无头模式
ENV PYTEST_XVFB=1
ENV DISPLAY=:99

# 暴露端口
EXPOSE 8000 3000

# 启动脚本
CMD ["/bin/bash", "/app/scripts/start.sh"]
