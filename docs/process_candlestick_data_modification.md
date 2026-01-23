# OKEx Fetcher 数据处理修改说明

## 修改内容

对 `_process_candlestick_data()` 方法进行了增强，以支持多交易对数据处理。

### 主要变更

1. **修改了方法签名**
   ```python
   # 旧版本
   def _process_candlestick_data(self, raw_data: List[List[str]]) -> List[Dict[str, Any]]:
   
   # 新版本
   def _process_candlestick_data(self, raw_data: List[List[str]], inst_id: str = None) -> List[Dict[str, Any]]:
   ```

2. **在处理的数据中添加了 `inst_id` 字段**
   ```python
   processed.append({
       'timestamp': int(candle[0]),
       'open': float(candle[1]),
       'high': float(candle[2]),
       'low': float(candle[3]),
       'close': float(candle[4]),
       'volume': float(candle[5]),
       'vol_ccy': float(candle[6]),
       'vol_ccy_quote': float(candle[7]),
       'confirm': int(candle[8]),
       'inst_id': inst_id or config.INST_ID  # 新增字段
   })
   ```

3. **更新了所有调用点**
   - `src/data/okex_fetcher.py` 中的内部调用已更新
   - `main.py` 中的调用已更新
   - 所有调用现在都传递 `inst_id=config.INST_ID`

### 使用示例

```python
# 处理ETH数据
eth_data = okex_fetcher._process_candlestick_data(raw_eth_data, inst_id="ETH-USDT-SWAP")

# 处理BTC数据  
btc_data = okex_fetcher._process_candlestick_data(raw_btc_data, inst_id="BTC-USDT-SWAP")

# 使用默认配置
default_data = okex_fetcher._process_candlestick_data(raw_data)  # 使用config.INST_ID
```

### 数据结构变化

现在每个处理后的数据记录都会包含 `inst_id` 字段：

```python
{
    'timestamp': 1234567890000,
    'open': 3100.5,
    'high': 3150.2,
    'low': 3080.1,
    'close': 3134.8,
    'volume': 12345.6,
    'vol_ccy': 38210987.4,
    'vol_ccy_quote': 38210987.4,
    'confirm': 1,
    'inst_id': 'ETH-USDT-SWAP'  # 新增字段
}
```

### 优势

1. **数据溯源**: 每条记录都明确标识了来源交易对
2. **多币种支持**: 便于处理和区分不同币种的数据
3. **数据库查询**: 可以按交易对进行数据筛选和聚合
4. **向前兼容**: 现有代码继续正常工作

### 注意事项

- 如果不提供 `inst_id` 参数，默认使用 `config.INST_ID`
- 确保在调用时传递正确的交易对标识符
- 数据库中的现有记录不会自动更新 `inst_id` 字段

---
*此修改增强了数据处理能力，为多币种支持和数据分析提供了更好的基础*