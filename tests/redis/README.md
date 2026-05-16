# Redis List Handler 使用说明

## 功能概述

Redis List Handler 用于从 Redis List 中读取 Filebeat 发送的消息，并转发到飞书。

## 工作流程

```
Filebeat → Redis List (filebeat:notice) → RedisListHandler → Feishu Sender → 飞书群聊
```

## 消息格式

### Redis List 消息格式（JSON）

```json
{
  "message": "错误日志内容或通知消息",
  "timestamp": 1234567890,
  "level": "error",
  "host": "server-01",
  "service": "api-service"
}
```

**必需字段**：
- `message`: 消息主体内容（会发送到飞书）

**可选字段**：其他字段暂不处理，保留在日志中用于调试

## 安装依赖

```bash
pip install redis
```

## 配置

Redis 配置在 `.env` 文件中：

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1
```

## 使用方式

### 方式 1: 处理单条消息

```python
from stream.redis_list_handler import redis_list_handler

# 处理一条消息
success = redis_list_handler.process_single_message()

if success:
    print("消息处理成功")
else:
    print("没有消息或处理失败")
```

### 方式 2: 持续监听（推荐用于生产环境）

```python
from stream.redis_list_handler import RedisListHandler

handler = RedisListHandler()

# 每 5 秒检查一次，每次只处理一条消息
handler.start_continuous_processing(interval=5.0)
```

### 方式 3: 自定义初始化

```python
from stream.redis_list_handler import RedisListHandler

# 自定义 Redis 配置和 List 名称
handler = RedisListHandler(
    redis_host="192.168.1.100",
    redis_port=6379,
    redis_db=2,
    list_name="my-custom-list"
)

handler.process_single_message()
```

## 工具方法

### 检查连接状态

```python
from stream.redis_list_handler import redis_list_handler

if redis_list_handler.is_connected():
    print("Redis 已连接")
else:
    print("Redis 未连接")
```

### 获取 List 长度

```python
from stream.redis_list_handler import redis_list_handler

length = redis_list_handler.get_list_length()
print(f"待处理消息数: {length}")
```

## 运行示例

### 1. 检查状态

```bash
source .venv/bin/activate
python tests/redis/example_redis_list_handler.py --mode check
```

### 2. 处理单条消息

```bash
python tests/redis/example_redis_list_handler.py --mode single
```

### 3. 持续监听

```bash
python tests/redis/example_redis_list_handler.py --mode continuous
```

## 测试

手动添加测试消息到 Redis：

```python
import redis
import json

r = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)

test_message = {
    "message": "这是一条测试消息",
    "timestamp": 1234567890,
    "level": "info",
    "service": "test-service"
}

# 添加消息到 List
r.rpush("filebeat:notice", json.dumps(test_message))
print(f"消息已添加，当前 List 长度: {r.llen('filebeat:notice')}")
```

## 集成到 PM2

创建 `redis-list-worker.conf`：

```javascript
module.exports = {
  apps: [{
    name: 'redis-list-worker',
    script: 'tests/redis/example_redis_list_handler.py',
    args: '--mode continuous',
    interpreter: 'python3',
    env: {
      PYTHONPATH: './src'
    },
    error_file: './logs/redis-list-worker-error.log',
    out_file: './logs/redis-list-worker-out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    autorestart: true,
    max_restarts: 10,
    min_uptime: '10s'
  }]
};
```

启动：

```bash
pm2 start redis-list-worker.conf
pm2 logs redis-list-worker
```

## 注意事项

1. **处理顺序**：
   - 使用 `LPOP` 从左侧取出，保持 FIFO 顺序
   - 每次只处理一条消息，确保消息处理的实时性

2. **错误处理**：
   - 消息解析失败会记录日志但不会中断处理
   - Redis 或飞书连接失败会记录错误日志

3. **日志管理**：
   - 生产环境建议配置日志文件而非输出到 stdout
   - 使用 `logrotate` 或 PM2 的日志管理功能

4. **监控**：
   - 监控 List 长度，避免消息堆积
   - 监控 Redis 和飞书的连接状态
   - 定期检查错误日志

## 故障排查

### 问题 1: Redis 未连接

**症状**：`Redis not available, cannot process message`

**解决**：
```bash
# 检查 Redis 是否运行
redis-cli ping

# 检查配置
cat .env | grep REDIS
```

### 问题 2: 飞书发送失败

**症状**：`Feishu client not initialized`

**解决**：
```python
# 检查飞书配置
from collect.config_handler import config_handler

config = config_handler.get_config_dict("feishu")
print(config)
```

### 问题 3: 消息格式错误

**症状**：`Failed to parse message as JSON`

**解决**：
```python
# 检查消息格式
import redis
import json

r = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)
msg = r.lindex("filebeat:notice", 0)  # 查看第一条消息（不删除）
print(msg)
try:
    print(json.loads(msg))
except:
    print("Invalid JSON")
```

## 参考资料

- [Redis LPOP 文档](https://redis.io/commands/lpop/)
- [Redis List 数据结构](https://redis.io/docs/data-types/lists/)
- [飞书开放平台](https://open.feishu.cn/)