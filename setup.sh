# Agnes Studio - 快速启动脚本

#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🚀 Agnes Studio 快速启动"
echo "========================"
echo ""

# ============================================================
# 功能选择
# ============================================================
echo "请选择启动方式："
echo "  1) Docker Compose（推荐 - 一键启动）"
echo "  2) 本地开发模式"
echo ""
read -p "请输入选项 (1/2) [默认: 1]: " choice
choice=${choice:-1}

case $choice in
    1)
        echo -e "${BLUE}📦 使用 Docker Compose 启动...${NC}"
        bash setup_docker.sh
        ;;
    2)
        echo -e "${BLUE}🔧 使用本地模式启动...${NC}"
        bash setup_local.sh
        ;;
    *)
        echo -e "${RED}❌ 无效选项${NC}"
        exit 1
        ;;
esac
