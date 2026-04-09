# NAS 部署指南

本文档介绍如何在 NAS（群晖、威联通等）上一键部署 Sehuatang 爬虫系统。

## 支持的 NAS 系统

- 群晖 Synology DSM 7.x+
- 威联通 QNAP QTS 5.x+
- 其他支持 Docker 的 NAS

## 快速开始

### 方式一：SSH 一键部署

```bash
# 1. SSH 连接到 NAS
ssh admin@你的NAS_IP

# 2. 创建项目目录
mkdir -p /volume1/docker/sehuatang-crawler
cd /volume1/docker/sehuatang-crawler

# 3. 下载部署脚本
curl -O https://raw.githubusercontent.com/你的用户名/sehuatang-crawler/main/scripts/deploy.sh
chmod +x deploy.sh

# 4. 一键部署
./deploy.sh install
```

### 方式二：手动部署

```bash
# 1. SSH 连接到 NAS
ssh admin@你的NAS_IP

# 2. 创建目录
mkdir -p /volume1/docker/sehuatang-crawler
cd /volume1/docker/sehuatang-crawler

# 3. 克隆仓库（修改为你的仓库地址）
git clone https://github.com/你的用户名/sehuatang-crawler.git .

# 4. 复制并编辑配置
cp .env.example .env
nano .env  # 编辑配置

# 5. 构建并启动
docker-compose build
docker-compose up -d

# 6. 查看状态
docker-compose ps
docker-compose logs -f
```

## 部署脚本命令

```bash
# 交互式菜单
./deploy.sh

# 一键安装/更新
./deploy.sh install

# 更新并重启
./deploy.sh update

# 查看日志
./deploy.sh logs

# 重启服务
./deploy.sh restart

# 停止服务
./deploy.sh stop

# 查看状态
./deploy.sh status
```

## 群晖（Synology）注意事项

### 1. 启用 SSH
- 控制面板 → 终端机和SNMP → 启用 SSH

### 2. 安装 Docker 套件
- Package Center → 安装 Docker

### 3. 创建共享文件夹
- 控制面板 → 共享文件夹 → 创建 `docker` 文件夹

### 4. SSH 部署
```bash
ssh admin@群晖IP
sudo -i  # 切换到 root
cd /volume1/docker
./deploy.sh install
```

### 5. 群晖 Docker 配置
如果遇到权限问题，在 Docker 套件设置中勾选：
- "启用 Docker 日志"
- "启用具有最高权限的容器"

## 威联通（QNAP）注意事项

### 1. 启用 SSH
- 控制台 → Telnet / SSH → 启用

### 2. 安装 Container Station
- App Center → 安装 Container Station

### 3. SSH 部署
```bash
ssh admin@威联通IP
cd /share/Container/sehuatang-crawler
./deploy.sh install
```

## 配置说明

复制 `.env.example` 为 `.env` 并配置：

```bash
# 数据库密码（必填）
DATABASE_PASSWORD=你的强密码

# 管理后台密码（必填）
ADMIN_PASSWORD=你的强密码

# Telegram 通知（可选）
TELEGRAM_BOT_TOKEN=你的Bot Token
TELEGRAM_CHAT_ID=你的Chat ID

# Selenium 配置（可选，通常不需要修改）
SELENIUM_HEADLESS=true
USE_SELENIUM_MODE=true
```

## 访问服务

部署成功后，访问：

| 服务 | 地址 |
|------|------|
| 后端 API | http://NAS_IP:8900 |
| 前端界面 | http://NAS_IP:3000 |
| API 文档 | http://NAS_IP:8900/docs |
| 数据库 | localhost:15432 |

默认管理密码：`admin123`（请及时修改）

## 数据持久化

所有数据存储在 Docker volumes 中：
- `data` - Cookie、日志等
- `postgres_data` - 数据库

如需备份：
```bash
# 备份数据库
docker exec sehuatang-postgres pg_dump -U postgres sehuatang_db > backup.sql

# 导出数据卷
docker run --rm -v sehuatang-crawler_data:/data -v $(pwd):/backup alpine tar czf /backup/data.tar.gz -C /data .
```

## 常见问题

### Q: 容器启动失败，提示权限错误
A: 在 NAS 上给目录权限：
```bash
chmod -R 777 /volume1/docker/sehuatang-crawler
```

### Q: Chrome 无法启动
A: 检查是否正确挂载 `/dev/shm`，或增加 shm_size：
```yaml
crawler:
  shm_size: '2gb'
```

### Q: 爬取失败，提示 Cloudflare 验证
A: 确保 Selenium 模式已启用（默认已启用），检查日志：
```bash
./deploy.sh logs
```

### Q: 如何更新到最新版本
```bash
./deploy.sh update
```

## 卸载

```bash
./deploy.sh uninstall
```
