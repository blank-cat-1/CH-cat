# Sehuatang 爬虫系统 - 重构版

## 项目概述

一个功能完整的论坛爬虫系统，支持订阅管理、定时任务、Telegram通知、Emby集成等。

## 目录结构

```
sehuatang-crawler/
├── backend/                    # 后端服务
│   ├── api/                    # API路由
│   │   └── routes/             # 按功能模块划分的路由
│   │       ├── auth.py         # 认证相关
│   │       ├── crawler.py      # 爬虫管理
│   │       ├── subscription.py # 订阅管理
│   │       ├── magnet.py       # 磁力链接
│   │       ├── search.py       # 搜索功能
│   │       ├── settings.py     # 系统设置
│   │       ├── emby.py         # Emby集成
│   │       ├── telegram.py     # Telegram通知
│   │       ├── checkin.py      # 自动签到
│   │       ├── downloader.py   # 下载器管理
│   │       ├── notification.py  # 通知管理
│   │       └── health.py       # 健康检查
│   │
│   ├── core/                   # 核心模块
│   │   ├── config.py          # 统一配置管理
│   │   ├── database.py        # 数据库连接
│   │   ├── logging.py         # 日志配置
│   │   └── scheduler.py       # 定时任务调度器
│   │
│   ├── models/                 # 数据模型
│   │   ├── magnet.py          # 磁力链接模型
│   │   ├── subscription.py    # 订阅模型
│   │   ├── post.py            # 帖子模型
│   │   ├── user.py            # 用户模型
│   │   ├── checkin.py         # 签到模型
│   │   └── auto_push.py       # 自动推送模型
│   │
│   ├── services/               # 业务服务
│   │   ├── crawler/           # 爬虫核心
│   │   │   ├── engine.py      # 爬虫引擎
│   │   │   ├── http_client.py # HTTP客户端
│   │   │   ├── parser.py      # 页面解析器
│   │   │   └── cookies.py     # Cookie管理
│   │   ├── subscription/      # 订阅服务
│   │   ├── notification/      # 通知服务
│   │   └── integration/       # 第三方集成
│   │
│   ├── migrations/             # 数据库迁移
│   │   └── runner.py          # 迁移运行器
│   │
│   └── main.py                # 应用入口
│
├── frontend/                   # 前端界面
│   └── build/                 # 构建产物
│
├── data/                       # 数据目录
│   ├── cookies/               # Cookie存储
│   ├── logs/                  # 日志文件
│   └── state/                 # 状态文件
│
├── scripts/                    # 脚本目录
│   ├── init_db.sh            # 数据库初始化
│   └── start.sh              # 启动脚本
│
├── docker/                     # Docker配置
│   └── Dockerfile
│
├── docker-compose.yaml          # Docker Compose配置
├── requirements.txt           # Python依赖
└── README.md                   # 项目说明
```

## 技术栈

- **后端框架**: FastAPI + uvicorn
- **数据库**: PostgreSQL + SQLAlchemy
- **爬虫**: httpx + BeautifulSoup
- **任务调度**: APScheduler
- **前端**: React (已构建)
- **通知**: Telegram Bot API

## 快速开始

### 使用 Docker

```bash
docker-compose up -d
```

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python -m migrations.runner

# 启动服务
python -m backend.main
```

## 主要功能

1. **论坛爬虫**: 自动爬取sehuatang论坛帖子
2. **订阅管理**: 支持关键词订阅、板块订阅、作者订阅
3. **定时任务**: 灵活的定时爬取配置
4. **Telegram通知**: 爬取结果即时推送
5. **Emby集成**: 自动同步到Emby媒体库
6. **自动签到**: 每日自动论坛签到
7. **下载器集成**: 支持多种下载器

## API文档

启动服务后访问: http://localhost:8000/docs

## 配置说明

详见 `backend/core/config.py` 或设置环境变量。
