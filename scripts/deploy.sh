#!/bin/bash

# 技术分析助手部署脚本 (CentOS 7)
# 前提：已安装 MongoDB, Redis, Node.js, PM2

set -e

echo "========================================="
echo "技术分析助手部署脚本"
echo "========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 项目路径
PROJECT_DIR="/opt/technical_analysis_helper"
APP_USER="root"

# 创建项目目录
echo -e "${GREEN}[1/7] 创建项目目录${NC}"
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 检查 Python 环境
echo -e "${GREEN}[2/7] 检查 Python 环境${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Python3 未安装，正在安装...${NC}"
    yum install -y python3 python3-pip python3-devel
else
    echo -e "${GREEN}Python3 已安装: $(python3 --version)${NC}"
fi

# 安装 Python 依赖
echo -e "${GREEN}[3/7] 安装 Python 依赖${NC}"
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    echo -e "${GREEN}Python 依赖安装完成${NC}"
else
    echo -e "${RED}requirements.txt 文件不存在${NC}"
    exit 1
fi

# 配置环境变量
echo -e "${GREEN}[4/7] 配置环境变量${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}已从 .env.example 创建 .env 文件${NC}"
        echo -e "${YELLOW}请根据实际情况修改 .env 文件${NC}"
    else
        cat > .env << 'EOF'
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=technical_analysis
MONGODB_CANDLESTICKS_COLLECTION=candlesticks
MONGODB_FEATURES_COLLECTION=features
MONGODB_NORMALIZER_COLLECTION=normalizer

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1

# OKEx API Configuration
OKEX_API_BASE_URL=https://www.okx.com

# Model Configuration
MODEL_SAVE_PATH=models/xgboost_model.json
FEATURE_WINDOW_SIZE=300
EOF
        echo -e "${GREEN}已创建 .env 文件${NC}"
    fi
else
    echo -e "${GREEN}.env 文件已存在${NC}"
fi

# 创建 models 目录
echo -e "${GREEN}[5/7] 创建 models 目录${NC}"
mkdir -p models

# 检查 MongoDB 服务
echo -e "${GREEN}[6/7] 检查 MongoDB 服务${NC}"
if systemctl is-active --quiet mongod; then
    echo -e "${GREEN}MongoDB 服务正在运行${NC}"
else
    echo -e "${YELLOW}启动 MongoDB 服务...${NC}"
    systemctl start mongod
    systemctl enable mongod
    echo -e "${GREEN}MongoDB 服务已启动${NC}"
fi

# 检查 Redis 服务
echo -e "${GREEN}[7/7] 检查 Redis 服务${NC}"
if systemctl is-active --quiet redis; then
    echo -e "${GREEN}Redis 服务正在运行${NC}"
else
    echo -e "${YELLOW}启动 Redis 服务...${NC}"
    systemctl start redis
    systemctl enable redis
    echo -e "${GREEN}Redis 服务已启动${NC}"
fi

# 使用 PM2 启动应用
echo ""
echo "========================================="
echo -e "${GREEN}使用 PM2 启动应用${NC}"
echo "========================================="

if command -v pm2 &> /dev/null; then
    pm2 restart ecosystem.config.js || pm2 start ecosystem.config.js
    pm2 save
    pm2 startup
    echo -e "${GREEN}应用已使用 PM2 启动${NC}"
else
    echo -e "${RED}PM2 未安装，请先安装 PM2${NC}"
    exit 1
fi

echo ""
echo "========================================="
echo -e "${GREEN}部署完成！${NC}"
echo "========================================="
echo ""
echo "查看应用状态: pm2 status"
echo "查看应用日志: pm2 logs"
echo "重启应用: pm2 restart all"
echo "停止应用: pm2 stop all"
echo ""
echo "API 文档: http://localhost:8000/docs"
echo ""
