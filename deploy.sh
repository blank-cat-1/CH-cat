#!/usr/bin/env bash
# ===============================================
# Sehuatang 爬虫系统 - 一键部署脚本
# ===============================================
#
# 一行命令安装:
#   curl -fsSL https://raw.githubusercontent.com/blank-cat-1/CH-cat/main/deploy.sh | bash
#
# ===============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# GitHub 配置
GITHUB_REPO="blank-cat-1/CH-cat"
TARGET_DIR="/opt/sehuatang-crawler"

# 显示欢迎信息
show_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║     Sehuatang 爬虫系统 - 一键部署脚本                   ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo -e "${NC}"
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

# 克隆或更新仓库
clone_or_update_repo() {
    if [ -d "${TARGET_DIR}/.git" ]; then
        echo -e "${YELLOW}[更新]${NC} 检测到已有安装，正在更新..."
        git -C "${TARGET_DIR}" pull
    else
        echo -e "${YELLOW}[安装]${NC} 正在克隆仓库到 ${TARGET_DIR}..."
        sudo mkdir -p /opt
        sudo git clone https://github.com/${GITHUB_REPO}.git "${TARGET_DIR}"
    fi
}

# 执行主脚本
run_main_script() {
    local main_script="${TARGET_DIR}/scripts/deploy.sh"
    
    if [ ! -f "${main_script}" ]; then
        echo -e "${RED}[错误]${NC} 找不到主脚本: ${main_script}"
        exit 1
    fi
    
    chmod +x "${main_script}"
    echo -e "${GREEN}[完成]${NC} 准备启动部署菜单..."
    echo ""
    
    # 执行主脚本
    exec bash "${main_script}" "$@"
}

# 主函数
main() {
    show_banner
    
    # 如果已在仓库目录
    if [ -f "./scripts/deploy.sh" ]; then
        echo -e "${GREEN}[本地]${NC} 检测到本地部署脚本"
        exec bash "./scripts/deploy.sh" "$@"
    fi
    
    check_network || exit 1
    
    echo ""
    echo -e "${YELLOW}[1/2]${NC} 获取仓库..."
    clone_or_update_repo
    
    echo ""
    echo -e "${YELLOW}[2/2]${NC} 启动部署程序..."
    run_main_script "$@"
}

main "$@"
