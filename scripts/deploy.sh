#!/bin/bash
#
# 一键部署脚本 - 从开发机部署到生产机
# 用法: ./deploy.sh [production]
#

set -e

# 配置
PRODUCTION_HOST="106.12.165.68"
PRODUCTION_USER="root"
PRODUCTION_DIR="/opt/fund-system"
GIT_REPO="https://github.com/zhangroc/fund-system.git"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查参数
if [ "$1" != "production" ]; then
    echo "用法: $0 production"
    echo ""
    echo "示例:"
    echo "  $0 production    # 部署到生产机"
    exit 1
fi

# 获取项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo ""
log_info "=== 公募基金筛选系统部署脚本 ==="
echo ""

# 步骤1: 检查本地代码状态
log_info "步骤1: 检查本地代码状态..."
cd "$PROJECT_ROOT"

# 检查是否有未提交的更改
if [ -n "$(git status --porcelain)" ]; then
    log_warn "本地有未提交的更改:"
    git status --short
    echo ""
    read -p "是否继续部署? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "已取消部署"
        exit 0
    fi
fi

# 步骤2: 推送到 GitHub
log_info "步骤2: 推送到 GitHub..."
git add -A
git commit -m "deploy: 部署到生产机 $(date '+%Y-%m-%d %H:%M:%S')" 2>/dev/null || true
git push origin main
log_info "代码已推送到 GitHub"

# 步骤3: 远程部署
log_info "步骤3: 远程部署到生产机 ($PRODUCTION_HOST)..."

ssh $PRODUCTION_USER@$PRODUCTION_HOST << 'EOF'
set -e

echo ""
echo "[INFO] 开始部署到生产机..."
cd /opt/fund-system

# 检查目录是否存在
if [ ! -d ".git" ]; then
    echo "[INFO] 首次部署，克隆代码仓库..."
    git clone https://github.com/zhangroc/fund-system.git /opt/fund-system
    cd /opt/fund-system
fi

# 拉取最新代码
echo "[INFO] 拉取最新代码..."
git pull origin main

# 停止旧容器
echo "[INFO] 停止旧容器..."
docker-compose down || true

# 构建新镜像
echo "[INFO] 构建新镜像..."
docker-compose build --no-cache

# 启动服务
echo "[INFO] 启动服务..."
docker-compose up -d

# 等待服务启动
echo "[INFO] 等待服务启动..."
sleep 5

# 检查服务状态
echo ""
echo "=== 服务状态 ==="
docker-compose ps

echo ""
echo "[INFO] 检查容器日志..."
docker-compose logs --tail=20

echo ""
echo "=========================================="
echo "[OK] 部署完成!"
echo "=========================================="
EOF

log_info "部署完成!"
echo ""
log_info "访问地址: http://106.12.165.68"
echo ""