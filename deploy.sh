#!/usr/bin/env bash
# ===============================================
# Sehuatang 爬虫系统 - 一键部署脚本
# ===============================================
# 
# 一键安装:
#   curl -fsSL https://raw.githubusercontent.com/blank-cat-1/CH-cat/main/deploy.sh | bash
#
# 或下载后运行:
#   curl -fsSL https://raw.githubusercontent.com/blank-cat-1/CH-cat/main/deploy.sh -o deploy.sh
#   chmod +x deploy.sh && ./deploy.sh
#
# ===============================================

set -e

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
        exit 1
    fi
    
    if ! check_command git; then
        log_error "Git 未安装"
        exit 1
    fi
    
    # 检查 Docker Compose
    if ! docker compose version &> /dev/null && ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    log_success "环境检查通过"
}

# 获取 Docker Compose 命令
get_compose_cmd() {
    if docker compose version &> /dev/null; then
        echo "docker compose"
    else
        echo "docker-compose"
    fi
}

# 检查网络
check_network() {
    log_info "检查网络连接..."
    if curl -fsSL --max-time 5 https://github.com > /dev/null 2>&1; then
        log_success "网络连接正常"
        return 0
    else
        log_error "无法连接到 GitHub"
        return 1
    fi
}

# 克隆/更新代码
update_code() {
    if [ -d "${TARGET_DIR}/.git" ]; then
        log_info "检测到已有安装，正在更新..."
        # 先暂存本地修改
        git -C "${TARGET_DIR}" stash -u 2>/dev/null || true
        # 获取远程更新
        git -C "${TARGET_DIR}" fetch origin main
        # 检查是否需要重新克隆
        if ! git -C "${TARGET_DIR}" diff --quiet origin/main -- frontend/build/ 2>/dev/null; then
            log_warn "检测到新的必要文件，重新克隆仓库..."
            rm -rf "${TARGET_DIR}"
            mkdir -p "$(dirname "${TARGET_DIR}")"
            git clone https://github.com/${GITHUB_REPO}.git "${TARGET_DIR}"
        else
            git -C "${TARGET_DIR}" reset --hard origin/main
        fi
    else
        log_info "正在克隆仓库到 ${TARGET_DIR}..."
        mkdir -p "$(dirname "${TARGET_DIR}")"
        # 如果目录存在但为空，删除它
        if [ -d "${TARGET_DIR}" ] && [ -z "$(ls -A "${TARGET_DIR}")" ]; then
            rmdir "${TARGET_DIR}"
        fi
        git clone https://github.com/${GITHUB_REPO}.git "${TARGET_DIR}"
    fi
}

# 构建镜像
build_image() {
    log_info "构建 Docker 镜像 (包含 Chrome + ChromeDriver)..."
    
    COMPOSE_CMD=$(get_compose_cmd)
    $COMPOSE_CMD -f "${TARGET_DIR}/docker-compose.yml" build --no-cache
    
    log_success "镜像构建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    COMPOSE_CMD=$(get_compose_cmd)
    $COMPOSE_CMD -f "${TARGET_DIR}/docker-compose.yml" up -d
    
    # 等待服务启动
    sleep 3
    
    log_success "服务启动完成"
}

# 查看状态
show_status() {
    COMPOSE_CMD=$(get_compose_cmd)
    $COMPOSE_CMD -f "${TARGET_DIR}/docker-compose.yml" ps
    
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        log_success "爬虫服务运行中"
    else
        log_error "爬虫服务未运行"
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

# 一键安装
install_all() {
    show_banner
    
    # 1. 检查环境
    check_env
    
    # 2. 检查网络
    check_network
    
    # 3. 克隆/更新代码
    update_code
    
    # 4. 创建配置文件
    if [ ! -f "${TARGET_DIR}/.env" ] && [ -f "${TARGET_DIR}/.env.example" ]; then
        log_info "创建配置文件..."
        cp "${TARGET_DIR}/.env.example" "${TARGET_DIR}/.env"
        log_warn "请编辑 ${TARGET_DIR}/.env 文件配置必要的环境变量"
    fi
    
    # 5. 构建并启动
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
    echo "配置文件: ${TARGET_DIR}/.env"
    echo ""
    
    # 显示状态
    show_status
}

# 主函数
main() {
    install_all
}

main "$@"
