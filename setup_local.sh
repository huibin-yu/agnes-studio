# Agnes Studio - 本地开发模式启动脚本

#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔧 Agnes Studio - 本地开发模式${NC}"
echo "================================="
echo ""

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js 未安装${NC}"
    echo "请安装 Node.js 18+: https://nodejs.org/"
    exit 1
fi
echo -e "${GREEN}✅ Node.js $(node -v)${NC}"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python 3 $(python3 --version)${NC}"

# 配置 .env
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

# 安装前端依赖
echo ""
echo -e "${BLUE}📦 安装前端依赖...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
    echo -e "${GREEN}✅ 前端依赖安装完成${NC}"
else
    echo -e "${GREEN}✅ 前端依赖已存在${NC}"
fi

# 安装后端依赖
echo ""
echo -e "${BLUE}📦 安装后端依赖...${NC}"
cd ../backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ 虚拟环境已创建${NC}"
fi

source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1
echo -e "${GREEN}✅ 后端依赖安装完成${NC}"

# 创建目录
mkdir -p uploads generated

echo ""
echo -e "${GREEN}🎉 项目配置完成！${NC}"
echo ""
echo "📋 启动方式："
echo ""
echo "  终端 1 (后端):"
echo "    cd backend && source venv/bin/activate"
echo "    uvicorn app.main:app --reload --port 8000"
echo ""
echo "  终端 2 (前端):"
echo "    cd frontend && npm run dev"
echo ""
echo "  访问: http://localhost:3000"
echo ""
