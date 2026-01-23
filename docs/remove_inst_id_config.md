# INST_ID 配置删除说明

## 修改内容

删除了 `src/config/settings.py` 中的 `INST_ID` 配置项及相关引用。

### 主要变更

1. **删除了配置项**
   ```python
   # 删除前
   INST_ID = os.getenv('INST_ID', 'ETH-USDT-SWAP')
   
   # 删除后
   # (该行已被完全移除)
   ```

2. **更新了相关引用**
   将所有 `config.INST_ID` 的引用替换为硬编码的默认值 `'ETH-USDT-SWAP'`：

   **src/collector/data_collector.py:**
   - 删除了未使用的 `self.inst_id = config.INST_ID` 属性

   **src/data/okex_fetcher.py:**
   - `instrument_id = inst_id or config.INST_ID` → `instrument_id = inst_id or 'ETH-USDT-SWAP'`
   - `fetch_candlesticks(inst_id=config.INST_ID, ...)` → `fetch_candlesticks(inst_id="ETH-USDT-SWAP", ...)`
   - `_process_candlestick_data(..., inst_id=config.INST_ID)` → `_process_candlestick_data(..., inst_id="ETH-USDT-SWAP")`
   - `'inst_id': inst_id or config.INST_ID` → `'inst_id': inst_id or 'ETH-USDT-SWAP'`

   **main.py:**
   - `fetch_candlesticks(inst_id=config.INST_ID, ...)` → `fetch_candlesticks(inst_id="ETH-USDT-SWAP", ...)`
   - `_process_candlestick_data(..., inst_id=config.INST_ID)` → `_process_candlestick_data(..., inst_id="ETH-USDT-SWAP")`

### 影响范围

- ✅ **功能不受影响**: 系统仍然默认使用 ETH-USDT-SWAP 交易对
- ✅ **环境变量支持**: 仍可通过方法参数传递其他交易对
- ✅ **代码清理**: 移除了未使用的配置项和属性
- ✅ **一致性**: 所有默认值统一为 'ETH-USDT-SWAP'

### 优势

1. **简化配置**: 减少了不必要的配置项
2. **明确默认值**: 直接在代码中体现默认交易对
3. **减少依赖**: 不再依赖配置模块中的特定项
4. **保持扩展性**: 仍支持通过参数指定其他交易对

### 后续建议

如果未来需要支持多个交易对或希望重新引入配置管理，可以考虑：
1. 创建专门的交易对配置模块
2. 使用枚举类型管理支持的交易对
3. 在更高层级进行交易对选择和路由

---
*此修改简化了配置结构，同时保持了系统的完整功能*