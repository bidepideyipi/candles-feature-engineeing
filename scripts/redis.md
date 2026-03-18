
方案1：先创建 Stream，再创建消费者组

# 1. 先创建一个空的 Stream（添加一条消息然后删除）
XADD signals * dummy "init"
XLEN signals
# 如果需要清空：XDEL signals <message-id>

# 2. 创建消费者组
XGROUP CREATE signals gp 0


方案2：使用 MKSTREAM 选项（推荐）

# 一次性创建 Stream 和消费者组
XGROUP CREATE signals gp 0 MKSTREAM


MKSTREAM 选项会在 Stream 不存在时自动创建一个空的 Stream。

创建消费者组的完整语法

# 完整语法
XGROUP CREATE stream groupname id [MKSTREAM] [ENTRIESREAD entries-read]

# 常用形式
XGROUP CREATE mystream mygroup 0 MKSTREAM


消费者组创建选项详解

选项 描述 示例

0 从 Stream 开头开始消费 XGROUP CREATE s g 0

$ 只消费未来新消息 XGROUP CREATE s g $

MKSTREAM 流不存在时自动创建 XGROUP CREATE s g 0 MKSTREAM

ENTRIESREAD 高级用法，指定已读条目数 XGROUP CREATE s g 0 ENTRIESREAD 100

完整示例流程

# 1. 创建消费者组（自动创建Stream）
XGROUP CREATE signals gp 0 MKSTREAM

# 2. 查看Stream信息
XINFO STREAM signals
XINFO GROUPS signals

# 3. 生产者发送消息
XADD signals * sensor_id 123 value 25.5 timestamp 1640995200000

# 4. 消费者读取消息
XREADGROUP GROUP gp consumer1 COUNT 1 STREAMS signals >

# 5. 确认消息处理完成
XACK signals gp <message-id>


重要注意事项

1. 消费者组是持久的：一旦创建，会永久存在直到删除
2. 删除消费者组：
   XGROUP DESTROY signals gp
   
3. 重新创建消费者组：如果已存在同名的消费者组，会报错：

   (error) BUSYGROUP Consumer Group name already exists
   
4. 查看所有消费者组：
   XINFO GROUPS signals
   

实际应用场景

# 场景：实时监控系统
# 1. 创建处理传感器数据的消费者组
XGROUP CREATE sensor_stream processors 0 MKSTREAM

# 2. 创建用于告警的消费者组
XGROUP CREATE sensor_stream alerts 0

# 3. 创建用于数据备份的消费者组
XGROUP CREATE sensor_stream backup $

# 现在同一个 Stream 有三个独立的消费者组
# 每条消息会被三个组分别消费


最佳实践建议

1. 生产环境：建议在生产代码中总是使用 MKSTREAM，避免 Stream 不存在导致的错误
2. ID 选择：
   • 0：处理所有历史消息 + 新消息

   • $：只处理新消息（适用于纯实时场景）

3. 消费者命名：使用有意义的消费者名称，便于监控
   XREADGROUP GROUP gp worker-01 COUNT 10 STREAMS signals >
   
