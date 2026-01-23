# OKEx Fetcher 修改说明

## 修改内容

将 `okex_fetcher.py` 中的 `fetch_candlesticks()` 方法进行了重构，以支持多种交易对。

### 主要变更

1. **移除了类属性 `inst_id`**
   - 原来的 `self.inst_id = config.INST_ID` 被移除
   - 现在不再硬编码特定的交易对

2. **修改了方法签名**
   ```python
   # 旧版本
   def fetch_candlesticks(self, bar: str = "1H", after: Optional[str] = None) -> List[List[str]]:
   
   # 新版本  
   def fetch_candlesticks(self, inst_id: str = None, bar: str = "1H", after: Optional[str] = None) -> List[List[str]]:
   ```

3. **更新了参数处理逻辑**
   ```python
   # 使用提供的 inst_id 或从配置中获取默认值
   instrument_id = inst_id or config.INST_ID
   
   params = {
       "instId": instrument_id,  # 使用动态 instrument_id
       "bar": bar
   }
   ```

4. **更新了所有调用点**
   - `src/data/okex_fetcher.py` 内部调用已更新
   - `main.py` 中的调用已更新
   - 所有调用现在都显式传递 `inst_id=config.INST_ID`

### 使用示例

```python
# 默认行为（使用配置中的交易对）
data = okex_fetcher.fetch_candlesticks(bar="1H")

# 指定特定交易对
data = okex_fetcher.fetch_candlesticks(inst_id="ETH-USDT-SWAP", bar="1H")
data = okex_fetcher.fetch_candlesticks(inst_id="BTC-USDT-SWAP", bar="1H")
data = okex_fetcher.fetch_candlesticks(inst_id="SOL-USDT-SWAP", bar="4H")
```

### 优势

1. **扩展性**: 现在可以轻松支持任何OKEx支持的交易对
2. **灵活性**: 可以为不同交易对使用不同的时间框架
3. **向后兼容**: 现有代码通过默认参数继续工作
4. **明确性**: 调用时明确指定交易对，提高代码可读性

### 注意事项

- 如果不提供 `inst_id` 参数，将使用 `config.INST_ID` 的默认值
- 确保提供的 `inst_id` 是OKEx支持的有效交易对
- 所有现有的调用都已经更新以保持兼容性

---
*此修改使系统更具扩展性，为将来支持多种加密货币交易对奠定了基础*