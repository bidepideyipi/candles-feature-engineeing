# 定时任务使用说明

定时任务功能已集成到主应用中，通过环境变量配置，无需额外的命令行参数。

## 启用定时任务

在 `.env` 文件中设置：

```bash
SCHEDULE_ENABLED=true
SCHEDULE_INTERVAL=15
SCHEDULE_RECIPIENT=284160266@qq.com
SCHEDULE_DATA_SOURCE=mongodb
```

## 环境变量说明

| 变量 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `SCHEDULE_ENABLED` | bool | false | 是否启用定时任务 |
| `SCHEDULE_INTERVAL` | int | 15 | 预测间隔（分钟） |
| `SCHEDULE_RECIPIENT` | str | 284160266@qq.com | 邮件收件人 |
| `SCHEDULE_DATA_SOURCE` | str | mongodb | 数据源：mongodb 或 api |

## 使用方式

### 1. 创建 .env 文件

复制 `.env.example` 到 `.env`：

```bash
cp .env.example .env
```

### 2. 配置环境变量

编辑 `.env` 文件：

```bash
# 启用定时任务
SCHEDULE_ENABLED=true

# 15分钟运行一次
SCHEDULE_INTERVAL=15

# 收件人邮箱
SCHEDULE_RECIPIENT=284160266@qq.com

# 使用 MongoDB 数据源（无网络依赖）
SCHEDULE_DATA_SOURCE=mongodb
```

### 3. 配置 SMTP 邮件

启动服务后，通过 API 配置 SMTP 信息：

```bash
# 配置发件人邮箱
curl -X POST "http://localhost:8000/config?item=smtp.qq.com&key=account&value=284160266@qq.com&desc=发件人邮箱"

# 配置 SMTP 授权码
curl -X POST "http://localhost:8000/config?item=smtp.qq.com&key=authCode&value=gpcmgjmwqlefbica&desc=发件人邮箱授权码"
```

### 4. 启动服务

```bash
# 开发模式（自动重载）
python3 src/main.py --reload

# 生产模式
python3 src/main.py --host 0.0.0.0 --port 8000
```

## 工作原理

1. 定时任务在后台线程中运行
2. 不影响 API 服务的正常响应
3. 每 N 分钟执行一次预测
4. 当置信度 > 60% 时发送邮件提醒
5. 所有日志输出到标准输出和日志文件

## 查看日志

定时任务的日志会输出到控制台，包含：

- 预测结果
- 置信度信息
- 邮件发送状态
- 错误信息

## 配置示例

### 开发环境

```bash
# .env
SCHEDULE_ENABLED=true
SCHEDULE_INTERVAL=15
SCHEDULE_RECIPIENT=284160266@qq.com
SCHEDULE_DATA_SOURCE=mongodb
```

### 生产环境

```bash
# .env
PRODUCTION_MODE=true
SCHEDULE_ENABLED=true
SCHEDULE_INTERVAL=15
SCHEDULE_RECIPIENT=284160266@qq.com
SCHEDULE_DATA_SOURCE=mongodb
```

## 注意事项

1. **邮件配置**：首次运行前必须配置 SMTP 信息，否则不会发送邮件
2. **数据源**：建议使用 `mongodb` 数据源，避免 API 限流
3. **线程安全**：定时任务在独立线程中运行，不影响主服务
4. **生产模式**：配置接口在生产环境下会被禁用

## 停用定时任务

在 `.env` 文件中设置：

```bash
SCHEDULE_ENABLED=false
```

或者直接删除该行（默认为 false）。

## Docker 部署

在 `docker-compose.yml` 中添加环境变量：

```yaml
services:
  api:
    environment:
      - SCHEDULE_ENABLED=true
      - SCHEDULE_INTERVAL=15
      - SCHEDULE_RECIPIENT=284160266@qq.com
      - SCHEDULE_DATA_SOURCE=mongodb
```

## 常见问题

**Q: 如何确认定时任务正在运行？**

A: 启动服务时查看控制台输出，应该看到：
```
Starting scheduled prediction service...
Interval: 15 minutes
Alert recipient: 284160266@qq.com
Data source: MongoDB
```

**Q: 定时任务会影响 API 性能吗？**

A: 不会。定时任务在独立的后台线程中运行，不阻塞主服务。

**Q: 如何修改预测间隔？**

A: 修改 `.env` 文件中的 `SCHEDULE_INTERVAL` 值（分钟），然后重启服务。

**Q: 可以使用多个收件人吗？**

A: 当前版本只支持单个收件人。如需多个收件人，可以创建邮件列表并循环发送。
