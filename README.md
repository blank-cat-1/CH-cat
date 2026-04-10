# Sehuatang 爬虫系统

论坛爬虫、订阅管理、通知推送系统。

## 🚀 一键部署（NAS/服务器）

镜像由 GitHub Actions 自动构建，无需克隆代码，直接拉取运行。

```bash
# 一条命令搞定（下载 docker-compose.yml 和 .env，然后启动）
curl -fsSL https://raw.githubusercontent.com/blank-cat-1/CH-cat/main/docker-compose.yml -o docker-compose.yml \
  && curl -fsSL https://raw.githubusercontent.com/blank-cat-1/CH-cat/main/.env.example -o .env \
  && docker compose up -d

# 编辑 .env 填入必要的环境变量后重启
docker compose down && docker compose up -d

# 更新时
docker compose pull && docker compose up -d
```

### 手动复制部署

如果无法访问 GitHub raw，也可以直接复制下方文件内容到本地部署。

**1. 创建 `docker-compose.yml`：**

```yaml
version: '3.8'

services:
  crawler:
    image: ghcr.io/blank-cat-1/ch-cat:latest
    container_name: sehuatang-crawler
    ports:
      - "8900:8000"
      - "3000:3000"
    env_file:
      - .env
    environment:
      - DATABASE_HOST=postgres
      - DATABASE_PORT=5432
      - DATABASE_NAME=${DATABASE_NAME:-sehuatang_db}
      - DATABASE_USER=${DATABASE_USER:-postgres}
      - DATABASE_PASSWORD=${DATABASE_PASSWORD:-postgres123}
      - PYTHONPATH=/app/backend
      - ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin123}
      - SELENIUM_HEADLESS=${SELENIUM_HEADLESS:-true}
      - SELENIUM_PAGE_TIMEOUT=${SELENIUM_PAGE_TIMEOUT:-30}
      - USE_SELENIUM_MODE=${USE_SELENIUM_MODE:-true}
      - CHROME_BIN=/usr/bin/google-chrome
    volumes:
      - data:/app/data
      - logs:/app/logs
    depends_on:
      - postgres
    restart: unless-stopped
    shm_size: '2gb'

  postgres:
    image: postgres:15-alpine
    container_name: sehuatang-postgres
    ports:
      - "15432:5432"
    env_file:
      - .env
    environment:
      - POSTGRES_DB=${DATABASE_NAME:-sehuatang_db}
      - POSTGRES_USER=${DATABASE_USER:-postgres}
      - POSTGRES_PASSWORD=${DATABASE_PASSWORD:-postgres123}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  data:
  logs:
  postgres_data:

networks:
  default:
    name: sehuatang-network
```

**2. 创建 `.env` 环境变量文件：**

```bash
# 数据库
DATABASE_NAME=sehuatang_db
DATABASE_USER=postgres
DATABASE_PASSWORD=你的密码

# 管理员
ADMIN_PASSWORD=你的管理员密码

# Telegram（可选）
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Selenium
SELENIUM_HEADLESS=true
USE_SELENIUM_MODE=true
```

**3. 启动服务：**

```bash
docker compose up -d
```

## 功能特性

- **论坛爬虫**: 自动爬取sehuatang论坛帖子（Selenium 自动维护 Cookie）
- **订阅管理**: 支持关键词订阅、板块订阅、作者订阅
- **定时任务**: 灵活的定时爬取配置
- **Telegram通知**: 爬取结果即时推送
- **Emby集成**: 自动同步到Emby媒体库
- **自动签到**: 每日自动论坛签到
- **自动Cookie**: Selenium 自动处理 Cloudflare/年龄验证

## 快速开始

### 使用 Docker (推荐)

```bash
# 拉取最新镜像并启动
docker compose up -d

# 查看日志
docker compose logs -f
```

### 本地开发

```bash
# 1. 安装 Selenium 环境（自动安装 Chrome + ChromeDriver）
# Linux/macOS:
bash scripts/install_selenium.sh

# Windows (推荐使用 WSL2):
# 先安装 WSL2，然后运行上述脚本

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 启动服务
cd backend
python -m uvicorn main:app --reload
```

## 目录结构

```
sehuatang-crawler/
├── backend/                 # 后端服务
│   ├── api/                # API路由
│   │   └── routes/        # 路由模块
│   ├── core/              # 核心模块
│   │   ├── config.py      # 配置管理
│   │   ├── database.py     # 数据库连接
│   │   ├── logging.py      # 日志配置
│   │   └── scheduler.py    # 定时任务
│   ├── models/             # 数据模型
│   │   ├── subscription.py # 订阅模型
│   │   ├── post.py         # 帖子模型
│   │   └── ...
│   ├── services/          # 业务服务
│   │   ├── crawler/       # 爬虫核心
│   │   │   ├── selenium_browser.py  # Selenium 浏览器管理
│   │   │   ├── http_client.py       # HTTP 客户端
│   │   │   ├── engine.py            # 爬虫引擎
│   │   │   └── ...
│   │   └── notification.py # 通知服务
│   └── main.py            # 应用入口
├── frontend/              # 前端界面
│   └── build/            # 构建产物
├── scripts/              # 脚本
│   ├── install_selenium.sh  # Selenium 自动安装脚本
│   └── start.sh          # 启动脚本
├── docker/               # Docker配置
│   └── Dockerfile         # 自动安装 Chrome + ChromeDriver
├── docker-compose.yml
└── requirements.txt
```

## API 文档

启动后访问: http://localhost:8000/docs

## 主要API

### 订阅管理
- `GET /api/subscriptions` - 获取订阅列表
- `POST /api/subscriptions` - 创建订阅
- `PUT /api/subscriptions/{id}` - 更新订阅
- `DELETE /api/subscriptions/{id}` - 删除订阅
- `POST /api/subscriptions/{id}/run` - 立即运行订阅

### 爬虫管理
- `GET /api/crawler/status` - 获取爬虫状态
- `POST /api/crawler/browser/start` - 启动浏览器
- `POST /api/crawler/browser/stop` - 停止浏览器
- `POST /api/crawler/browser/restart` - 重启浏览器
- `GET /api/crawler/browser/status` - 获取浏览器状态
- `POST /api/crawler/cookies` - 更新Cookie
- `POST /api/crawler/cookies/sync` - 同步浏览器Cookie

### 签到
- `GET /api/checkin/config` - 获取签到配置
- `POST /api/checkin/now` - 立即签到

## 配置说明

通过环境变量配置:

| 变量 | 说明 | 默认值 |
|------|------|--------|
| DATABASE_HOST | 数据库主机 | localhost |
| DATABASE_PORT | 数据库端口 | 5432 |
| DATABASE_NAME | 数据库名称 | sehuatang_db |
| DATABASE_USER | 数据库用户 | postgres |
| DATABASE_PASSWORD | 数据库密码 | - |
| ADMIN_PASSWORD | 管理员密码 | admin123 |
| TELEGRAM_BOT_TOKEN | Telegram机器人Token | - |
| SELENIUM_HEADLESS | Selenium无头模式 | true |
| SELENIUM_USER_AGENT | 自定义User-Agent | Chrome默认 |
| SELENIUM_PAGE_TIMEOUT | 页面超时时间(秒) | 30 |
| USE_SELENIUM_MODE | 启用Selenium模式 | true |

## Selenium 自动 Cookie 机制

项目使用 Selenium 自动维护 Cookie，无需手动配置：

1. **自动处理 Cloudflare 验证**
2. **自动处理年龄验证**
3. **自动处理 safeid 验证**
4. **自动保存/加载 Cookie**
5. **自动重试失败请求**

首次访问时会自动完成所有验证，后续请求自动复用 Cookie。

## 许可证

MIT
