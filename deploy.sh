#!/usr/bin/env bash
# ===============================================
# Sehuatang 爬虫系统 - 一键部署脚本
# ===============================================
#
# 一行命令安装:
#   curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/sehuatang-crawler-refactor/main/deploy.sh | bash
#
# 或者下载后运行:
#   curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/sehuatang-crawler-refactor/main/deploy.sh -o deploy.sh
#   chmod +x deploy.sh
#   ./deploy.sh
#
# ===============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# GitHub 配置 - 请修改为你的仓库地址
GITHUB_REPO="blank-cat-1/CH-cat"
GITHUB_RAW="https://raw.githubusercontent.com/${GITHUB_REPO}/main"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAIN_SCRIPT="${SCRIPT_DIR}/scripts/deploy.sh"

# 显示欢迎信息
show_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║     Sehuatang 爬虫系统 - 一键部署脚本                   ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 检查是否有网络
check_network() {
    echo -e "${YELLOW}[检查]${NC} 检查网络连接..."
    if curl -fsSL --max-time 5 https://github.com > /dev/null 2>&1; then
        echo -e "${GREEN}[OK]${NC} 网络连接正常"
        return 0
    else
        echo -e "${RED}[错误]${NC} 无法连接到 GitHub，请检查网络"
        return 1
    fi
}

# 仓库安装目录
TARGET_DIR="/opt/sehuatang-crawler"

# 克隆或更新仓库
clone_or_update_repo() {
    if [ -d "${TARGET_DIR}/.git" ]; then
        echo -e "${YELLOW}[更新]${NC} 检测到已有安装，正在更新..."
        cd "${TARGET_DIR}" && git pull
    else
        echo -e "${YELLOW}[安装]${NC} 正在克隆仓库到 ${TARGET_DIR}..."
        sudo mkdir -p /opt
        sudo git clone https://github.com/${GITHUB_REPO}.git "${TARGET_DIR}"
    fi
}

# 下载并执行主脚本
download_and_run_main_script() {
    local repo_dir="$1"
    local main_script="${repo_dir}/scripts/deploy.sh"
    
    # 检查主脚本是否存在
    if [ ! -f "${main_script}" ]; then
        echo -e "${RED}[错误]${NC} 找不到主脚本: ${main_script}"
        exit 1
    fi
    
    # 使脚本可执行
    chmod +x "${main_script}"
    
    echo -e "${GREEN}[完成]${NC} 准备启动部署菜单..."
    echo ""
    
    # 执行主脚本（传入参数）
    exec bash "${main_script}" "$@"
}

# 主函数
main() {
    show_banner
    
    # 如果已经在这个仓库目录下，直接运行本地脚本
    if [ -f "${SCRIPT_DIR}/scripts/deploy.sh" ]; then
        echo -e "${GREEN}[本地]${NC} 检测到本地部署脚本"
        exec bash "${SCRIPT_DIR}/scripts/deploy.sh" "$@"
    fi
    
    # 否则需要下载
    check_network || exit 1
    
    echo ""
    echo -e "${YELLOW}[1/2]${NC} 获取仓库..."
    clone_or_update_repo
    
    echo ""
    echo -e "${YELLOW}[2/2]${NC} 启动部署程序..."
    download_and_run_main_script "${TARGET_DIR}" "$@"
}

# 显示帮助
show_help() {
    show_banner
    echo "使用方法:"
    echo "  bash ${0} [命令]"
    echo ""
    echo "命令:"
    echo "  install    一键安装/更新"
    echo "  update     拉取最新代码"
    echo "  build      构建 Docker 镜像"
    echo "  start      启动服务"
    echo "  stop       停止服务"
    echo "  restart    重启服务"
    echo "  status     查看状态"
    echo "  logs       查看日志"
    echo "  clean      清理资源"
    echo "  uninstall  卸载"
    echo ""
    echo "无参数时显示交互式菜单"
    echo ""
    echo "或者直接运行完整部署脚本:"
    echo "  bash scripts/deploy.sh"
}

# 根据参数执行
case "${1:-}" in
    install|update|build|start|stop|restart|status|logs|clean|uninstall)
        main "$@"
        ;;
    -h|--help|help)
        show_help
        ;;
    *)
        main
        ;;
esac
