# Sehuatang 爬虫系统

论坛爬虫、订阅管理、通知推送系统。

## 功能特性

- **论坛爬虫**: 自动爬取sehuatang论坛帖子
- **订阅管理**: 支持关键词订阅、板块订阅、作者订阅
- **定时任务**: 灵活的定时爬取配置
- **Telegram通知**: 爬取结果即时推送
- **Emby集成**: 自动同步到Emby媒体库
- **自动签到**: 每日自动论坛签到

## 快速开始

### 使用 Docker (推荐)

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 本地开发

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
export DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/sehuatang_db

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
│   │   └── notification.py # 通知服务
│   └── main.py            # 应用入口
├── frontend/              # 前端界面
│   └── build/            # 构建产物
├── scripts/              # 脚本
├── docker/               # Docker配置
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
- `POST /api/crawler/cookies` - 更新Cookie

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

## 许可证

MIT
