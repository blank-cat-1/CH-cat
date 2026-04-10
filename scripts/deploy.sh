#!/bin/bash
# =================================================================
# Sehuatang 爬虫系统 - NAS 自动部署脚本
#
# 功能：
#   1. 自动拉取最新代码
#   2. 构建 Docker 镜像（自动安装 Chrome + ChromeDriver）
#   3. 启动服务
#   4. 查看状态和日志
#
# 使用方式：
#   bash deploy.sh                    # 交互式菜单
#   bash deploy.sh install            # 一键安装
#   bash deploy.sh update             # 更新并重启
#   bash deploy.sh logs              # 查看日志
#   bash deploy.sh restart            # 重启服务
# =================================================================

set -e

# 配置
REPO_URL="https://github.com/你的用户名/sehuatang-crawler.git"  # 修改为你的仓库地址
PROJECT_DIR="/volume1/docker/sehuatang-crawler"  # NAS 上的项目目录
CONTAINER_NAME="sehuatang-crawler"
COMPOSE_FILE="docker-compose.yaml"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查命令
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "需要安装: $1"
        return 1
    fi
    return 0
}

# 检查环境
check_env() {
    log_info "检查环境..."
    
    # 检查 Docker
    if ! check_command docker; then
        log_error "Docker 未安装，请先安装 Docker"
        return 1
    fi
    
    # 检查 Docker Compose
    if ! check_command docker-compose && ! docker compose version &> /dev/null; then
        log_error "Docker Compose 未安装"
        return 1
    fi
    
    # 检查 Git
    if ! check_command git; then
        log_error "Git 未安装"
        return 1
    fi
    
    log_success "环境检查通过"
    return 0
}

# 获取 Docker Compose 命令
get_compose_cmd() {
    if docker compose version &> /dev/null; then
        echo "docker compose"
    else
        echo "docker-compose"
    fi
}

# 拉取代码
pull_code() {
    log_info "拉取最新代码..."
    
    COMPOSE_CMD=$(get_compose_cmd)
    
    if [ -d "$PROJECT_DIR/.git" ]; then
        cd "$PROJECT_DIR"
        git pull origin main || git pull origin master
        log_success "代码更新完成"
    else
        log_warn "项目目录不存在，是否要克隆仓库？"
        read -p "输入仓库地址 (直接回车使用默认: $REPO_URL): " INPUT_URL
        REPO_URL=${INPUT_URL:-$REPO_URL}
        
        read -p "确认克隆到 $PROJECT_DIR ? (y/n): " confirm
        if [ "$confirm" = "y" ]; then
            mkdir -p "$(dirname $PROJECT_DIR)"
            git clone "$REPO_URL" "$PROJECT_DIR"
            log_success "仓库克隆完成"
        else
            log_error "取消操作"
            return 1
        fi
    fi
}

# 构建镜像
build_image() {
    log_info "构建 Docker 镜像 (包含 Chrome + ChromeDriver)..."
    
    COMPOSE_CMD=$(get_compose_cmd)
    
    cd "$PROJECT_DIR"
    $COMPOSE_CMD build --no-cache crawler
    
    log_success "镜像构建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    COMPOSE_CMD=$(get_compose_cmd)
    
    cd "$PROJECT_DIR"
    $COMPOSE_CMD up -d
    
    log_success "服务启动完成"
    show_status
}

# 停止服务
stop_services() {
    log_info "停止服务..."
    
    COMPOSE_CMD=$(get_compose_cmd)
    
    cd "$PROJECT_DIR"
    $COMPOSE_CMD down
    
    log_success "服务已停止"
}

# 查看状态
show_status() {
    echo ""
    echo "========================================"
    echo "  服务状态"
    echo "========================================"
    
    COMPOSE_CMD=$(get_compose_cmd)
    
    cd "$PROJECT_DIR"
    $COMPOSE_CMD ps
    
    echo ""
    echo "========================================"
    echo "  容器健康检查"
    echo "========================================"
    
    # 检查容器是否运行
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        log_success "爬虫服务运行中"
        
        # 获取容器信息
        CONTAINER_STATUS=$(docker inspect --format='{{.State.Status}}' $CONTAINER_NAME 2>/dev/null || echo "unknown")
        CONTAINER_IMAGE=$(docker inspect --format='{{.Config.Image}}' $CONTAINER_NAME 2>/dev/null || echo "unknown")
        
        echo "  状态: $CONTAINER_STATUS"
        echo "  镜像: $CONTAINER_IMAGE"
        echo ""
        echo "  访问地址:"
        echo "    - 后端 API: http://localhost:8900"
        echo "    - 前端界面: http://localhost:3000"
    else
        log_error "爬虫服务未运行"
    fi
}

# 查看日志
show_logs() {
    log_info "查看日志 (Ctrl+C 退出)..."
    echo ""
    
    read -p "查看哪个容器的日志? [1] crawler [2] postgres [3] all: " choice
    choice=${choice:-1}
    
    case $choice in
        1)
            docker logs -f $CONTAINER_NAME
            ;;
        2)
            docker logs -f ${CONTAINER_NAME}-postgres 2>/dev/null || docker logs -f sehuatang-postgres
            ;;
        3)
            COMPOSE_CMD=$(get_compose_cmd)
            cd "$PROJECT_DIR"
            $COMPOSE_CMD logs -f
            ;;
        *)
            docker logs -f $CONTAINER_NAME
            ;;
    esac
}

# 重启服务
restart_services() {
    log_info "重启服务..."
    
    COMPOSE_CMD=$(get_compose_cmd)
    
    cd "$PROJECT_DIR"
    $COMPOSE_CMD restart
    
    log_success "服务已重启"
    show_status
}

# 一键安装
install_all() {
    log_info "========================================"
    log_info "  开始一键部署"
    log_info "========================================"
    echo ""
    
    # 1. 检查环境
    if ! check_env; then
        return 1
    fi
    
    # 2. 拉取代码
    pull_code || true
    
    # 3. 构建并启动
    cd "$PROJECT_DIR"
    
    # 检查配置文件
    if [ ! -f ".env" ] && [ -f ".env.example" ]; then
        log_info "创建配置文件..."
        cp .env.example .env
        log_warn "请编辑 .env 文件配置必要的环境变量"
    fi
    
    # 4. 构建镜像
    build_image
    
    # 5. 启动服务
    start_services
    
    echo ""
    log_success "========================================"
    log_success "  部署完成!"
    log_success "========================================"
    echo ""
    echo "访问地址:"
    echo "  - 后端 API: http://localhost:8900"
    echo "  - 前端界面: http://localhost:3000"
    echo "  - API 文档: http://localhost:8900/docs"
    echo ""
    echo "初始密码: admin123 (请及时修改)"
    echo ""
}

# 更新并重启
update_and_restart() {
    log_info "========================================"
    log_info "  更新并重启"
    log_info "========================================"
    echo ""
    
    pull_code
    build_image
    restart_services
    
    log_success "更新完成!"
}

# 清理
cleanup() {
    log_warn "清理 Docker 资源..."
    
    COMPOSE_CMD=$(get_compose_cmd)
    
    cd "$PROJECT_DIR"
    $COMPOSE_CMD down --volumes --remove-orphans
    docker system prune -f
    
    log_success "清理完成"
}

# 卸载
uninstall() {
    log_warn "========================================"
    log_warn "  卸载服务"
    log_warn "========================================"
    read -p "确认卸载? 这将删除所有容器和数据! (y/n): " confirm
    
    if [ "$confirm" = "y" ]; then
        COMPOSE_CMD=$(get_compose_cmd)
        
        cd "$PROJECT_DIR"
        $COMPOSE_CMD down -v --remove-orphans
        
        log_success "卸载完成"
    else
        log_info "取消操作"
    fi
}

# 显示菜单
show_menu() {
    echo ""
    echo "========================================"
    echo "  Sehuatang 爬虫系统 - 部署管理"
    echo "========================================"
    echo ""
    echo "  1) 一键安装/更新"
    echo "  2) 拉取最新代码"
    echo "  3) 构建镜像"
    echo "  4) 启动服务"
    echo "  5) 停止服务"
    echo "  6) 重启服务"
    echo "  7) 查看状态"
    echo "  8) 查看日志"
    echo "  9) 清理资源"
    echo "  10) 卸载"
    echo "  0) 退出"
    echo ""
    echo -n "请选择 [0-10]: "
}

# 主函数
main() {
    COMMAND=$1
    
    case $COMMAND in
        install)
            install_all
            ;;
        update)
            update_and_restart
            ;;
        pull)
            pull_code
            ;;
        build)
            build_image
            ;;
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        cleanup)
            cleanup
            ;;
        uninstall)
            uninstall
            ;;
        "")
            # 交互式菜单
            while true; do
                show_menu
                read choice
                
                case $choice in
                    1) install_all ;;
                    2) pull_code ;;
                    3) build_image ;;
                    4) start_services ;;
                    5) stop_services ;;
                    6) restart_services ;;
                    7) show_status ;;
                    8) show_logs ;;
                    9) cleanup ;;
                    10) uninstall ;;
                    0) exit 0 ;;
                    *) log_error "无效选择" ;;
                esac
                
                echo ""
                read -p "按回车继续..."
            done
            ;;
        *)
            echo "用法: $0 {install|update|pull|build|start|stop|restart|status|logs|cleanup|uninstall}"
            echo ""
            echo "快速命令:"
            echo "  $0 install    # 一键安装"
            echo "  $0 update     # 更新并重启"
            echo "  $0 logs       # 查看日志"
            echo "  $0 restart    # 重启服务"
            ;;
    esac
}

main "$@"
