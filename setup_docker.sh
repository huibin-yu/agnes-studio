# Agnes Studio - Docker Compose 启动脚本

#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}📦 Agnes Studio - Docker Compose${NC}"
echo "================================="
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装${NC}"
    echo "请安装 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✅ Docker $(docker --version)${NC}"

# 检查 Docker Compose
if ! command -v docker compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose 未安装${NC}"
    echo "Docker Desktop 已包含 Docker Compose"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose $(docker compose version)${NC}"

# 检查 .env 文件
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo -e "${YELLOW}⚠️  .env 文件已创建${NC}"
    echo -e "${YELLOW}⚠️  请编辑 .env 文件，填入你的 Agnes AI API Key${NC}"
    echo ""
    echo "获取 API Key: https://platform.agnes-ai.com"
    echo ""
    read -p "按回车键继续..."
fi

# 检查 AGNES_API_KEY
if grep -q "your_agnes_api_key_here" .env; then
    echo -e "${RED}❌ 请先配置 AGNES_API_KEY${NC}"
    echo "编辑 .env 文件，将 AGNES_API_KEY=your_agnes_api_key_here 替换为你的 API Key"
    exit 1
fi

echo ""
echo "🚀 启动服务..."
echo ""

# 停止旧容器
docker compose down 2>/dev/null

# 构建并启动
docker compose up -d --build

echo ""
echo -e "${GREEN}✅ 服务启动成功！${NC}"
echo ""
echo "📋 访问地址："
echo "   前端: http://localhost:3000"
echo "   后端 API: http://localhost:8000"
echo "   API 文档: http://localhost:8000/docs"
echo ""
echo "📝 常用命令："
echo "   查看日志: docker compose logs -f"
echo "   停止服务: docker compose down"
echo "   重启服务: docker compose restart"
echo ""
echo "📚 详细文档: DOCKER_COMPOSE.md"
echo ""
