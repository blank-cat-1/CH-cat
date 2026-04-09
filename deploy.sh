#!/usr/bin/env bash
# ===============================================
# Sehuatang 爬虫系统 - 一键部署脚本
# ===============================================
#
# 下载方式:
#   curl -fsSL https://raw.githubusercontent.com/blank-cat-1/CH-cat/main/deploy.sh -o deploy.sh
#   chmod +x deploy.sh
#   ./deploy.sh
#
# 命令行安装:
#   curl -fsSL https://raw.githubusercontent.com/blank-cat-1/CH-cat/main/deploy.sh | bash install
#
# ===============================================

# 配置
GITHUB_REPO="blank-cat-1/CH-cat"
TARGET_DIR="/opt/sehuatang-crawler"
CONTAINER_NAME="sehuatang-crawler"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
    
    if ! check_command docker; then
        log_error "Docker 未安装，请先安装 Docker"
        return 1
    fi
    
    if ! check_command git; then
        log_error "Git 未安装"
        return 1
    fi
    
    # 检查 Docker Compose (支持 docker compose 和 docker-compose 两种)
    if ! docker compose version &> /dev/null && ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
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

# 克隆/更新代码
update_code() {
    if [ -d "${TARGET_DIR}/.git" ]; then
        log_info "检测到已有安装，正在更新..."
        # 先暂存本地修改，避免冲突
        git -C "${TARGET_DIR}" stash -u 2>/dev/null || true
        # 强制拉取，避免本地冲突文件
        git -C "${TARGET_DIR}" fetch origin main
        # 检查是否需要重新克隆（如果有新文件在远程）
        if ! git -C "${TARGET_DIR}" diff --quiet origin/main -- frontend/build/ 2>/dev/null; then
            log_warn "检测到新的必要文件，重新克隆仓库..."
            sudo rm -rf "${TARGET_DIR}"
            sudo mkdir -p /opt
            sudo git clone https://github.com/${GITHUB_REPO}.git "${TARGET_DIR}"
        else
            git -C "${TARGET_DIR}" reset --hard origin/main
        fi
    else
        log_info "正在克隆仓库到 ${TARGET_DIR}..."
        sudo mkdir -p /opt
        sudo git clone https://github.com/${GITHUB_REPO}.git "${TARGET_DIR}"
    fi
}

# 拉取代码
pull_code() {
    log_info "拉取最新代码..."
    
    if [ -d "${TARGET_DIR}/.git" ]; then
        # 先暂存本地修改，避免冲突
        git -C "${TARGET_DIR}" stash 2>/dev/null || true
        git -C "${TARGET_DIR}" pull origin main
        log_success "代码更新完成"
    else
        log_error "项目目录不存在，请先安装"
        return 1
    fi
}

# 构建镜像
build_image() {
    log_info "构建 Docker 镜像 (包含 Chrome + ChromeDriver)..."
    
    COMPOSE_CMD=$(get_compose_cmd)
    update_code
    $COMPOSE_CMD -f "${TARGET_DIR}/docker-compose.yml" build --no-cache
    
    log_success "镜像构建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    COMPOSE_CMD=$(get_compose_cmd)
    $COMPOSE_CMD -f "${TARGET_DIR}/docker-compose.yml" up -d
    
    log_success "服务启动完成"
    show_status
}

# 停止服务
stop_services() {
    log_info "停止服务..."
    
    COMPOSE_CMD=$(get_compose_cmd)
    $COMPOSE_CMD -f "${TARGET_DIR}/docker-compose.yml" down
    
    log_success "服务已停止"
}

# 查看状态
show_status() {
    echo ""
    echo "========================================"
    echo "  服务状态"
    echo "========================================"
    
    COMPOSE_CMD=$(get_compose_cmd)
    $COMPOSE_CMD -f "${TARGET_DIR}/docker-compose.yml" ps
    
    echo ""
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        log_success "爬虫服务运行中"
        echo "  访问地址: http://localhost:8900"
    else
        log_error "爬虫服务未运行"
    fi
}

# 查看日志
show_logs() {
    log_info "查看日志 (Ctrl+C 退出)..."
    echo ""
    
    COMPOSE_CMD=$(get_compose_cmd)
    $COMPOSE_CMD -f "${TARGET_DIR}/docker-compose.yml" logs -f
}

# 重启服务
restart_services() {
    log_info "重启服务..."
    
    COMPOSE_CMD=$(get_compose_cmd)
    $COMPOSE_CMD -f "${TARGET_DIR}/docker-compose.yml" restart
    
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
    
    # 2. 克隆/更新代码
    update_code
    
    # 3. 检查配置文件
    if [ ! -f "${TARGET_DIR}/.env" ] && [ -f "${TARGET_DIR}/.env.example" ]; then
        log_info "创建配置文件..."
        cp "${TARGET_DIR}/.env.example" "${TARGET_DIR}/.env"
        log_warn "请编辑 ${TARGET_DIR}/.env 文件配置必要的环境变量"
    fi
    
    # 4. 构建并启动
    build_image
    start_services
    
    echo ""
    log_success "========================================"
    log_success "  部署完成!"
    log_success "========================================"
    echo ""
    echo "访问地址:"
    echo "  - 后端 API: http://localhost:8900"
    echo "  - API 文档: http://localhost:8900/docs"
    echo ""
}

# 清理
cleanup() {
    log_warn "清理 Docker 资源..."
    
    COMPOSE_CMD=$(get_compose_cmd)
    $COMPOSE_CMD -f "${TARGET_DIR}/docker-compose.yml" down --volumes --remove-orphans 2>/dev/null || true
    docker system prune -f 2>/dev/null || true
    
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
        $COMPOSE_CMD -f "${TARGET_DIR}/docker-compose.yml" down -v --remove-orphans 2>/dev/null || true
        sudo rm -rf "${TARGET_DIR}"
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

# 检查网络
check_network() {
    echo -e "${YELLOW}[检查]${NC} 检查网络连接..."
    if curl -fsSL --max-time 5 https://github.com > /dev/null 2>&1; then
        echo -e "${GREEN}[OK]${NC} 网络连接正常"
        return 0
    else
        echo -e "${RED}[错误]${NC} 无法连接到 GitHub"
        return 1
    fi
}

# 显示欢迎信息
show_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║     Sehuatang 爬虫系统 - 一键部署脚本                   ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 主函数
main() {
    show_banner
    
    # 获取脚本所在目录和当前目录
    SCRIPT_SOURCE="${BASH_SOURCE[0]}"
    SCRIPT_DIR="$(cd "$(dirname "${SCRIPT_SOURCE}")" && pwd)"
    CURRENT_DIR="$(pwd)"
    
    # 确定项目目录优先级：
    # 1. 如果当前目录有 docker-compose.yml，用当前目录
    # 2. 否则用默认的 /opt/sehuatang-crawler
    if [ -f "${CURRENT_DIR}/docker-compose.yml" ]; then
        TARGET_DIR="${CURRENT_DIR}"
        log_info "检测到当前目录为项目目录: ${TARGET_DIR}"
    elif [ -f "${SCRIPT_DIR}/docker-compose.yml" ]; then
        TARGET_DIR="${SCRIPT_DIR}"
        log_info "检测到脚本目录为项目目录: ${TARGET_DIR}"
    fi
    
    COMMAND=$1
    
    case $COMMAND in
        install)
            if ! check_env; then exit 1; fi
            if [ ! -d "${TARGET_DIR}/.git" ]; then
                check_network || exit 1
                sudo mkdir -p /opt
                sudo git clone https://github.com/${GITHUB_REPO}.git "${TARGET_DIR}"
            fi
            install_all
            ;;
        update|pull)
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
            ;;
    esac
}

main "$@"
