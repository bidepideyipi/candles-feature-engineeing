#!/bin/bash

# MongoDB 和 Redis 服务配置脚本 (CentOS 7)

set -e

echo "========================================="
echo "配置 MongoDB 和 Redis 服务"
echo "========================================="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# MongoDB 配置
echo -e "${GREEN}[1/3] 配置 MongoDB${NC}"

# 创建 MongoDB 数据目录
mkdir -p /var/lib/mongo
mkdir -p /var/log/mongodb
chown -R mongod:mongod /var/lib/mongo
chown -R mongod:mongod /var/log/mongodb

# 创建 MongoDB 配置文件
if [ ! -f "/etc/mongod.conf" ]; then
    cat > /etc/mongod.conf << 'EOF'
storage:
  dbPath: /var/lib/mongo
  journal:
    enabled: true
systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log
net:
  port: 27017
  bindIp: 0.0.0.0
security:
  authorization: enabled
EOF
    echo -e "${GREEN}MongoDB 配置文件已创建${NC}"
else
    echo -e "${GREEN}MongoDB 配置文件已存在${NC}"
fi

# 复制服务文件
cp mongodb.service /etc/systemd/system/mongod.service
systemctl daemon-reload

# Redis 配置
echo -e "${GREEN}[2/3] 配置 Redis${NC}"

# 创建 Redis 数据目录
mkdir -p /var/lib/redis
mkdir -p /var/log/redis
chown -R redis:redis /var/lib/redis
chown -R redis:redis /var/log/redis

# 创建 Redis 配置文件
if [ ! -f "/etc/redis.conf" ]; then
    cat > /etc/redis.conf << 'EOF'
bind 0.0.0.0
protected-mode yes
port 6379
tcp-backlog 511
timeout 0
tcp-keepalive 300
daemonize no
supervised no
pidfile /var/run/redis/redis.pid
loglevel notice
logfile /var/log/redis/redis.log
databases 16
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /var/lib/redis
maxmemory 256mb
maxmemory-policy allkeys-lru
EOF
    echo -e "${GREEN}Redis 配置文件已创建${NC}"
else
    echo -e "${GREEN}Redis 配置文件已存在${NC}"
fi

# 复制服务文件
cp redis.service /etc/systemd/system/redis.service
systemctl daemon-reload

# 启动服务
echo -e "${GREEN}[3/3] 启动服务${NC}"

# 启动 MongoDB
systemctl start mongod
systemctl enable mongod
echo -e "${GREEN}MongoDB 服务已启动并设置为开机自启${NC}"

# 启动 Redis
systemctl start redis
systemctl enable redis
echo -e "${GREEN}Redis 服务已启动并设置为开机自启${NC}"

# 检查服务状态
echo ""
echo "========================================="
echo -e "${GREEN}服务状态检查${NC}"
echo "========================================="

echo ""
echo "MongoDB 状态:"
systemctl status mongod --no-pager | head -n 10

echo ""
echo "Redis 状态:"
systemctl status redis --no-pager | head -n 10

# 检查端口监听
echo ""
echo "========================================="
echo -e "${GREEN}端口监听检查${NC}"
echo "========================================="

if netstat -tuln | grep -q ':27017'; then
    echo -e "${GREEN}MongoDB 正在监听 27017 端口${NC}"
else
    echo -e "${YELLOW}MongoDB 未监听 27017 端口${NC}"
fi

if netstat -tuln | grep -q ':6379'; then
    echo -e "${GREEN}Redis 正在监听 6379 端口${NC}"
else
    echo -e "${YELLOW}Redis 未监听 6379 端口${NC}"
fi

echo ""
echo "========================================="
echo -e "${GREEN}服务配置完成！${NC}"
echo "========================================="
