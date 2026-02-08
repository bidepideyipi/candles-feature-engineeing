# 部署指南

本文档介绍如何部署 Technical Analysis Helper 项目到生产环境。

## 目录

- [Docker 部署（推荐）](#docker-部署推荐)
- [环境配置](#环境配置)
- [数据持久化](#数据持久化)
- [监控和日志](#监控和日志)
- [故障排除](#故障排除)

---

## Docker 部署（推荐）

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 2GB 可用内存
- 至少 5GB 可用磁盘空间

### 快速开始

#### 1. 克隆仓库

```bash
git clone <repository-url>
cd technial_analysis_helper
```

#### 2. 准备模型文件

将训练好的模型文件放到 `models/` 目录：

```bash
# 必需文件
models/xgboost_model.json
models/xgboost_model_scaler.pkl
models/xgboost_model_features.json
```

#### 3. 启动服务

```bash
# 使用 Docker Compose 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f api

# 停止服务
docker-compose down
```

#### 4. 验证部署

```bash
# 检查服务状态
docker-compose ps

# 检查 API 健康状态
curl http://localhost:8000/health

# 测试预测接口
curl http://localhost:8000/fetch/5-predict?inst_id=ETH-USDT-SWAP
```

### 服务架构

Docker Compose 会启动以下服务：

```
┌─────────────────────────────────────────────┐
│          technical-analysis-network          │
├─────────────────────────────────────────────┤
│  MongoDB    Redis       API            │
│  :27017     :6379       :8000           │
└─────────────────────────────────────────────┘
```

**服务说明：**

| 服务 | 容器名 | 端口 | 作用 |
|------|---------|------|------|
| MongoDB | technical-analysis-mongodb | 27017 | 数据存储 |
| Redis | technical-analysis-redis | 6379 | 缓存和限流 |
| API | technical-analysis-api | 8000 | API 服务 |

---

## 环境配置

### Docker Compose 环境变量

在 `docker-compose.yml` 中配置的环境变量：

```yaml
api:
  environment:
    # 生产模式
    - PRODUCTION_MODE=true
    
    # MongoDB 配置
    - MONGODB_URI=mongodb://mongodb:27017
    - MONGODB_DATABASE=technical_analysis
    - MONGODB_CANDLESTICKS_COLLECTION=candlesticks
    - MONGODB_FEATURES_COLLECTION=features
    - MONGODB_NORMALIZER_COLLECTION=normalizer
    
    # Redis 配置
    - REDIS_HOST=redis
    - REDIS_PORT=6379
    - REDIS_DB=1
    
    # OKX API 配置
    - OKEX_API_BASE_URL=https://www.okx.com
    - INST_ID=ETH-USDT-SWAP
```

### 自定义配置

#### 修改数据库密码

```yaml
mongodb:
  environment:
    MONGO_INITDB_ROOT_USERNAME: admin
    MONGO_INITDB_ROOT_PASSWORD: your_secure_password
    MONGO_INITDB_DATABASE: technical_analysis
```

**重要：** 同时更新 API 服务的 `MONGODB_URI` 环境变量以包含认证信息：

```yaml
api:
  environment:
    - MONGODB_URI=mongodb://admin:your_secure_password@mongodb:27017/technical_analysis?authSource=admin
```

#### 修改端口映射

```yaml
services:
  mongodb:
    ports:
      - "27018:27017"  # 映射到主机 27018
  
  redis:
    ports:
      - "6380:6379"   # 映射到主机 6380
  
  api:
    ports:
      - "8080:8000"   # 映射到主机 8080
```

#### 添加更多交易对

```yaml
api:
  environment:
    - INST_ID=ETH-USDT-SWAP
    # 可以添加其他交易对
    # - INST_ID=BTC-USDT-SWAP
```

---

## 数据持久化

### Docker 卷配置

默认情况下，Docker Compose 会创建以下卷来持久化数据：

```yaml
volumes:
  mongodb_data:
    driver: local
  redis_data:
    driver: local
```

### 查看数据卷

```bash
# 列出所有卷
docker volume ls

# 查看卷详情
docker volume inspect technial_analysis_helper_mongodb_data
docker volume inspect technial_analysis_helper_redis_data
```

### 备份数据

#### MongoDB 备份

```bash
# 创建备份目录
mkdir -p backups/mongodb

# 备份 MongoDB
docker exec technical-analysis-mongodb mongodump \
  --host=localhost \
  --port=27017 \
  --db=technical_analysis \
  --username=admin \
  --password=admin123 \
  --archive=/backup/mongodb/backup_$(date +%Y%m%d_%H%M%S).gz

# 复制到主机
docker cp technical-analysis-mongodb:/backup ./backups/mongodb
```

#### 恢复 MongoDB

```bash
# 停止 MongoDB 服务
docker-compose stop mongodb

# 删除现有数据
docker volume rm technial_analysis_helper_mongodb_data

# 创建新卷
docker volume create technial_analysis_helper_mongodb_data

# 启动 MongoDB
docker-compose up -d mongodb

# 恢复备份
docker cp ./backups/mongodb/backup.gz technical-analysis-mongodb:/backup/
docker exec technical-analysis-mongodb mongorestore \
  --host=localhost \
  --port=27017 \
  --db=technical_analysis \
  --username=admin \
  --password=admin123 \
  /backup/backup.gz
```

#### 模型文件备份

```bash
# 创建备份目录
mkdir -p backups/models

# 备份模型文件
cp -r models backups/models/backup_$(date +%Y%m%d_%H%M%S)
```

---

## 监控和日志

### 查看实时日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 只查看 API 日志
docker-compose logs -f api

# 查看最近 100 行
docker-compose logs --tail=100 api

# 查看特定时间的日志
docker-compose logs --since="2024-01-01T00:00:00" api
```

### 日志文件

日志会持久化到 `./logs/` 目录：

```bash
# 查看日志目录
ls -lh logs/

# 实时查看日志
tail -f logs/api.log
```

### 健康检查

```bash
# 检查 API 健康状态
curl http://localhost:8000/health

# 响应
# {"status":"healthy"}
```

### 性能监控

使用 Docker 监控命令：

```bash
# 查看资源使用
docker stats

# 查看容器详细信息
docker inspect technical-analysis-api

# 查看容器资源限制
docker stats --no-stream technical-analysis-api
```

---

## 更新部署

### 更新代码

```bash
# 拉取最新代码
git pull origin main

# 重新构建镜像
docker-compose build

# 重启服务
docker-compose up -d
```

### 更新模型

```bash
# 停止服务
docker-compose down

# 替换模型文件
cp /path/to/new/models/xgboost_model.json models/
cp /path/to/new/models/xgboost_model_scaler.pkl models/
cp /path/to/new/models/xgboost_model_features.json models/

# 重新启动
docker-compose up -d
```

### 更新依赖

```bash
# 重新构建镜像（会自动运行 pip install -r requirements.txt）
docker-compose build --no-cache

# 重启服务
docker-compose up -d
```

---

## 生产环境优化

### 资源限制

在 `docker-compose.yml` 中添加资源限制：

```yaml
api:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 4G
      reservations:
        cpus: '1.0'
        memory: 2G
```

### 安全配置

#### 1. 使用环境变量管理敏感信息

创建 `.env` 文件（不要提交到 Git）：

```env
MONGO_INITDB_ROOT_PASSWORD=your_secure_password
```

在 `docker-compose.yml` 中引用：

```yaml
mongodb:
  environment:
    MONGO_INITDB_ROOT_PASSWORD: ${MONGO_INITDB_ROOT_PASSWORD}
```

#### 2. 限制网络访问

```yaml
api:
  networks:
    - technical-analysis-network
  # 只允许来自特定网络的访问
```

#### 3. 使用反向代理（Nginx）

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 多实例部署

```yaml
# docker-compose.production.yml
services:
  api-1:
    build: .
    environment:
      - INST_ID=ETH-USDT-SWAP
    ports:
      - "8001:8000"
  
  api-2:
    build: .
    environment:
      - INST_ID=BTC-USDT-SWAP
    ports:
      - "8002:8000"
```

```bash
# 启动多个实例
docker-compose -f docker-compose.production.yml up -d
```

---

## 故障排除

### 容器无法启动

```bash
# 查看容器日志
docker-compose logs api

# 检查容器状态
docker-compose ps

# 查看详细错误
docker-compose logs --tail=50 api
```

常见问题：

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 端口冲突 | 8000 端口被占用 | 修改 docker-compose.yml 中的端口映射 |
| 内存不足 | 容器 OOM | 增加内存限制或关闭其他服务 |
| 模型文件缺失 | 无法加载模型 | 确保 models/ 目录包含所有必需文件 |
| MongoDB 连接失败 | 数据库未就绪 | 检查 MongoDB 容器日志和健康状态 |

### 数据库连接问题

```bash
# 测试 MongoDB 连接
docker exec -it technical-analysis-mongodb mongosh \
  --username admin \
  --password admin123 \
  --eval "db.adminCommand('ping')"

# 测试 Redis 连接
docker exec -it technical-analysis-redis redis-cli ping

# 查看数据库数据
docker exec -it technical-analysis-mongodb mongosh \
  --username admin \
  --password admin123 \
  technical_analysis

# 列出集合
show collections

# 查看数据数量
db.candlesticks.count()
db.features.count()
```

### API 响应缓慢

```bash
# 检查容器资源使用
docker stats technical-analysis-api

# 查看日志中的慢查询
docker-compose logs api | grep "slow"

# 增加 API 容器的资源限制
```

### 重新构建镜像

如果遇到依赖或缓存问题：

```bash
# 停止所有服务
docker-compose down

# 删除旧镜像
docker rmi technial_analysis_helper-api

# 重新构建（不使用缓存）
docker-compose build --no-cache

# 启动服务
docker-compose up -d
```

---

## 生产环境检查清单

部署到生产环境前，请确认：

- [ ] 修改了默认数据库密码
- [ ] 配置了环境变量（不硬编码敏感信息）
- [ ] 设置了适当的资源限制
- [ ] 配置了日志持久化
- [ ] 设置了数据备份策略
- [ ] 配置了健康检查
- [ ] 配置了反向代理（如需要）
- [ ] 测试了所有 API 端点
- [ ] 验证了模型文件存在
- [ ] 配置了监控和告警
- [ ] 设置了自动重启策略
- [ ] 限制了不必要的端口暴露
- [ ] 配置了 HTTPS（通过反向代理）

---

## 清理

### 清理未使用的资源

```bash
# 停止所有服务
docker-compose down

# 删除所有容器、网络、卷
docker-compose down -v

# 清理未使用的镜像
docker image prune -a

# 清理未使用的卷
docker volume prune
```

### 完全清理（警告：会删除所有数据）

```bash
# 停止并删除所有服务
docker-compose down -v

# 删除项目相关的所有镜像
docker rmi $(docker images | grep technial_analysis_helper | awk '{print $3}')
```

---

## 支持

如遇部署问题，请检查：

1. Docker 日志：`docker-compose logs -f`
2. 容器状态：`docker-compose ps`
3. 资源使用：`docker stats`
4. 项目文档：[README.md](README.md) 或 [README_CN.md](README_CN.md)
