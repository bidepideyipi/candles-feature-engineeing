# Data Collector 重构说明

## 修改内容

删除了重复的 `collector/data_collector.py` 模块，统一使用 `data/okex_fetcher.py` 进行数据收集。

### 主要变更

1. **删除了冗余模块**
   - 删除文件: `src/collector/data_collector.py`
   - 删除目录: `src/collector/` (仅含 `__init__.py`)
   - 删除原因: 功能与 `okex_fetcher.py` 严重重叠

2. **更新了主程序引用**
   ```python
   # 修改前
   from src.collector.data_collector import data_collector
   
   # 修改后  
   from src.data.okex_fetcher import okex_fetcher
   ```

3. **重构了数据收集逻辑**
   ```python
   # 修改前 - 使用 data_collector
   data = data_collector.run_collection_job(args.symbol, args.days)
   # 然后手动存储到 MongoDB
   
   # 修改后 - 使用 okex_fetcher
   max_records = args.days * 24  # 计算记录数
   success = okex_fetcher.fetch_historical_data(max_records=max_records, check_duplicates=False)
   # 自动存储到 MongoDB
   ```

### 功能对比

| 特性 | data_collector | okex_fetcher | 结果 |
|------|----------------|--------------|------|
| API数据获取 | ✅ | ✅ | 保留更强的 |
| MongoDB存储 | ❌ (需手动) | ✅ (内置) | 选择okex_fetcher |
| 分页处理 | ✅ | ✅ | 功能相当 |
| 错误处理 | ✅ | ✅ | 功能相当 |
| 速率限制 | ✅ | ✅ | 功能相当 |

### 优势

1. **消除冗余**: 避免维护两个功能相似的模块
2. **简化架构**: 统一数据收集入口点
3. **减少依赖**: 减少导入和维护成本
4. **功能增强**: 利用 `okex_fetcher` 更完善的MongoDB集成

### 注意事项

- `okex_fetcher.fetch_historical_data()` 接受 `max_records` 而不是 `days` 参数
- 已通过 `max_records = days * 24` 进行转换
- 设置 `check_duplicates=False` 以强制重新收集数据
- 数据会自动存储到MongoDB，无需手动处理

### 后续建议

如果需要更灵活的数据收集控制，可以考虑：
1. 在 `okex_fetcher` 中添加按日期范围收集的方法
2. 提供更多的收集选项（如不同的时间间隔）
3. 增强错误恢复和断点续传功能

---
*此次重构消除了功能重复，简化了代码结构，提升了维护效率*