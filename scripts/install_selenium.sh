#!/bin/bash
# =================================================================
# Selenium 环境自动安装脚本
# 用于本地开发环境自动配置 Chrome/ChromeDriver
# =================================================================

set -e

echo "=========================================="
echo "  Selenium 环境自动安装脚本"
echo "=========================================="

# 检测操作系统
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/debian_version ]; then
            echo "debian"
        elif [ -f /etc/redhat-release ]; then
            echo "redhat"
        else
            echo "linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# 安装 Linux (Debian/Ubuntu)
install_linux_debian() {
    echo "[*] 检测到 Debian/Ubuntu 系统..."

    # 检测架构
    ARCH=$(dpkg --print-architecture)
    echo "[*] CPU 架构: $ARCH"

    # 安装依赖
    echo "[*] 安装系统依赖..."
    sudo apt-get update
    sudo apt-get install -y \
        wget \
        gnupg \
        libasound2 \
        libgbm1 \
        libnss3 \
        libxss1 \
        libxv1 \
        libgtk-3-0 \
        fonts-liberation \
        xdg-utils \
        xvfb \
        unzip

    # 添加中文字体支持
    sudo apt-get install -y fonts-noto-cjk || true

    if [ "$ARCH" = "amd64" ]; then
        # AMD64: 安装 Google Chrome
        echo "[*] 安装 Google Chrome..."
        wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg
        echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
        sudo apt-get update
        sudo apt-get install -y --no-install-recommends google-chrome-stable

        # 安装 ChromeDriver
        echo "[*] 安装 ChromeDriver..."
        pip install seleniumbase
        seleniumbase install chromedriver

        echo "[*] Chrome 路径: $(which google-chrome)"
        echo "[*] ChromeDriver 路径: $(python -c 'from selenium.webdriver.chrome.service import Service; from seleniumbase import get_drivers_dir; import os; print(os.path.join(get_drivers_dir(), "chromedriver"))')"

    else
        # ARM64/其他: 安装 Chromium
        echo "[*] 安装 Chromium..."
        sudo apt-get install -y --no-install-recommends chromium chromium-driver

        echo "[*] Chromium 路径: $(which chromium)"
        echo "[*] ChromeDriver 路径: $(which chromedriver)"
    fi
}

# 安装 Linux (RedHat/CentOS)
install_linux_redhat() {
    echo "[*] 检测到 RedHat/CentOS 系统..."

    ARCH=$(uname -m)
    echo "[*] CPU 架构: $ARCH"

    # 安装依赖
    echo "[*] 安装系统依赖..."
    sudo yum install -y \
        wget \
        gtk3 \
        libX11 \
        libXkr4xi \
        libXcomposite \
        libXcursor \
        libXdamage \
        libXext \
        libXfixes \
        libXi \
        libXrandr \
        libXtst \
        mesa-libgbm \
        nss \
        at-spi2-atk \
        cups-libs \
        liberation-fonts \
        xdg-utils \
        Xvfb \
        dejavu-sans-fonts

    if [ "$ARCH" = "x86_64" ]; then
        # 安装 Chrome
        echo "[*] 安装 Google Chrome..."
        sudo wget -O /etc/yum.repos.d/google-chrome.repo https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
        sudo yum install -y google-chrome-stable

        # 安装 ChromeDriver
        echo "[*] 安装 ChromeDriver..."
        pip install seleniumbase
        seleniumbase install chromedriver
    else
        # 安装 Chromium
        echo "[*] 安装 Chromium..."
        sudo yum install -y chromium
    fi
}

# 安装 macOS
install_macos() {
    echo "[*] 检测到 macOS 系统..."

    # 检查是否安装了 Homebrew
    if ! command -v brew &> /dev/null; then
        echo "[!] 需要安装 Homebrew"
        echo "请访问: https://brew.sh"
        exit 1
    fi

    # 安装 Chrome
    if [ ! -d "/Applications/Google Chrome.app" ]; then
        echo "[*] 安装 Google Chrome..."
        brew install --cask google-chrome
    else
        echo "[*] Google Chrome 已安装"
    fi

    # 安装 ChromeDriver
    echo "[*] 安装 ChromeDriver..."
    brew install chromedriver

    # 安装 seleniumbase（用于管理）
    pip install seleniumbase
}

# 安装 Windows (WSL2 或 PowerShell)
install_windows() {
    echo "[*] 检测到 Windows 系统..."

    if command -v wsl.exe &> /dev/null; then
        echo "[*] 检测到 WSL2"
        echo "[!] 建议在 WSL2 中使用 Xvfb 运行 Chrome"
        echo "[*] 请在 WSL2 中运行此脚本"
    else
        echo "[!] Windows 原生不支持 Selenium headless Chrome"
        echo "[*] 建议使用以下方案之一:"
        echo "    1. 使用 WSL2 (Windows Subsystem for Linux 2)"
        echo "    2. 使用 Docker (推荐: docker-compose up -d)"
        echo "    3. 使用远程 ChromeDriver"
    fi

    # 仍然尝试安装 Python 依赖
    echo "[*] 安装 Python 依赖..."
    pip install selenium seleniumbase webdriver-manager
}

# 安装 Python 依赖
install_python_deps() {
    echo "[*] 安装 Python 依赖..."
    pip install -r requirements.txt
}

# 主流程
main() {
    OS=$(detect_os)
    echo "[*] 操作系统: $OS"

    case $OS in
        debian)
            install_linux_debian
            ;;
        redhat)
            install_linux_redhat
            ;;
        macos)
            install_macos
            ;;
        windows)
            install_windows
            ;;
        linux)
            # 默认当作 debian
            install_linux_debian
            ;;
        *)
            echo "[!] 不支持的操作系统: $OS"
            exit 1
            ;;
    esac

    # 安装 Python 依赖
    install_python_deps

    echo ""
    echo "=========================================="
    echo "  ✅ 安装完成!"
    echo "=========================================="
    echo ""
    echo "后续步骤:"
    echo "  1. 启动应用: python -m uvicorn backend.main:app --reload"
    echo "  2. 访问: http://localhost:8000"
    echo "  3. 运行爬虫测试: curl -X POST http://localhost:8000/api/crawler/browser/start"
    echo ""
}

# 运行
main "$@"
