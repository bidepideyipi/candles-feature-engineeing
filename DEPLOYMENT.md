# CentOS 7 部署指南

本文档介绍如何在 CentOS 7 上部署技术分析助手项目。

## 前置要求

已安装以下服务：
- MongoDB
- Redis
- Node.js
- PM2

## 部署步骤

### 1. 上传项目文件

将项目文件上传到服务器：

```bash
# 使用 scp 上传
scp -r /path/to/technical_analysis_helper root@your-server:/opt/

# 或使用 git clone
cd /opt
git clone <your-repo-url> technical_analysis_helper
cd technical_analysis_helper
```

### 2. 配置 MongoDB 和 Redis 服务

```bash
cd scripts
chmod +x setup_services.sh
./setup_services.sh
```

此脚本会：
- 创建 MongoDB 和 Redis 的配置文件
- 设置服务文件
- 启动服务并设置开机自启
- 检查服务状态和端口监听

### 3. 执行部署脚本

```bash
cd /opt/technical_analysis_helper
chmod +x scripts/deploy.sh
./deploy.sh
```

此脚本会：
- 创建项目目录
- 检查并安装 Python 依赖
- 配置环境变量
- 创建必要的目录
- 检查并启动 MongoDB 和 Redis
- 使用 PM2 启动应用

### 4. 配置环境变量

编辑 `.env` 文件：

```bash
vim /opt/technical_analysis_helper/.env
```

根据实际情况修改配置：

```env
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
```

### 5. 使用 PM2 管理应用

```bash
# 启动应用
pm2 start ecosystem.config.js

# 查看应用状态
pm2 status

# 查看日志
pm2 logs

# 重启应用
pm2 restart all

# 停止应用
pm2 stop all

# 删除应用
pm2 delete all

# 保存 PM2 配置
pm2 save

# 设置 PM2 开机自启
pm2 startup
```

### 6. 验证部署

```bash
# 检查应用状态
pm2 status

# 检查 API 健康状态
curl http://localhost:8000/health

# 查看 API 文档
# 在浏览器中打开：http://your-server-ip:8000/docs
```

## 防火墙配置

如果服务器启用了防火墙，需要开放 8000 端口：

```bash
# 开放 8000 端口
firewall-cmd --permanent --add-port=8000/tcp
firewall-cmd --reload

# 查看已开放的端口
firewall-cmd --list-ports
```

## Nginx 反向代理配置（可选）

如果需要使用域名访问，可以配置 Nginx 反向代理：

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

重启 Nginx：

```bash
nginx -t
systemctl restart nginx
```

## 常见问题

### 1. MongoDB 连接失败

检查 MongoDB 服务状态：

```bash
systemctl status mongod
```

检查 MongoDB 日志：

```bash
tail -f /var/log/mongodb/mongod.log
```

### 2. Redis 连接失败

检查 Redis 服务状态：

```bash
systemctl status redis
redis-cli ping
```

### 3. PM2 启动失败

查看 PM2 日志：

```bash
pm2 logs
```

检查 Python 依赖是否安装完整：

```bash
cd /opt/technical_analysis_helper
pip3 list | grep -E "pandas|numpy|xgboost"
```

### 4. 端口被占用

检查端口占用：

```bash
netstat -tuln | grep 8000
```

停止占用端口的进程或修改 `main.py` 中的端口号。

## 监控和维护

### 日志管理

PM2 日志文件位置：
- 错误日志：`/opt/technical_analysis_helper/logs/pm2-error.log`
- 输出日志：`/opt/technical_analysis_helper/logs/pm2-out.log`
- 合并日志：`/opt/technical_analysis_helper/logs/pm2-combined.log`

### 日志轮转

配置日志轮转，避免日志文件过大：

```bash
vim /etc/logrotate.d/technical-analysis
```

内容：

```
/opt/technical_analysis_helper/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 root root
    sharedscripts
    postrotate
        pm2 reload all
    endscript
}
```

### 性能监控

使用 PM2 Plus 或其他监控工具监控应用性能：

```bash
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 10M
pm2 set pm2-logrotate:retain 7
```

## 更新部署

更新代码后重新部署：

```bash
cd /opt/technical_analysis_helper
git pull  # 或上传新文件

# 重启应用
pm2 restart all

# 或使用零停机更新
pm2 reload all
```

## 备份策略

### MongoDB 数据备份

```bash
# 创建备份脚本
vim /opt/scripts/backup_mongodb.sh
```

内容：

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/mongodb"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

mongodump --host localhost --port 27017 --db technical_analysis --out $BACKUP_DIR/backup_$DATE

# 删除 7 天前的备份
find $BACKUP_DIR -type d -mtime +7 -exec rm -rf {} \;
```

设置定时任务：

```bash
crontab -e
```

添加：

```
0 2 * * * /opt/scripts/backup_mongodb.sh
```

### 模型文件备份

```bash
# 备份模型文件
cp /opt/technical_analysis_helper/models/*.json /opt/backups/models/
cp /opt/technical_analysis_helper/models/*.pkl /opt/backups/models/
```

## 安全建议

1. **修改 MongoDB 默认端口**
2. **启用 MongoDB 认证**
3. **限制 Redis 访问 IP**
4. **使用 HTTPS（通过 Nginx 配置 SSL）**
5. **定期更新系统和依赖包**

## 联系方式

如有问题，请联系技术支持。
