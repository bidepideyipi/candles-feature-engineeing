# ETH期权猎手工具架构设计文档

## 1. 系统概述

### 1.1 产品定位
ETH期权猎手工具是一个专业的加密货币量化分析平台，专注于ETH-USDT交易对的期权策略支持。通过自动化数据采集、智能特征工程和机器学习模型训练，为期权交易提供量化的涨跌预测信号。

### 1.2 核心价值
- **数据驱动**: 基于真实市场数据的定量分析
- **多时间维度**: 短期、中期、长期趋势综合判断
- **风险控制**: 7级分类体系平衡收益与风险
- **易于集成**: 模块化设计便于扩展和维护

## 2. 整体架构设计

### 2.1 系统架构图
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   数据采集层     │───▶│   数据存储层     │───▶│   特征工程层     │
│                 │    │                 │    │                 │
│ • OKEx API接口   │    │ • MongoDB数据库  │    │ • 技术指标计算   │
│ • 限速控制模块   │    │ • 数据持久化     │    │ • 标签生成系统   │
│ • 错误处理机制   │    │ • 索引优化       │    │ • 特征向量化     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                    │
                                                    ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   模型训练层     │◀───│   配置管理层     │◀───│   应用接口层     │
│                 │    │                 │    │                 │
│ • XGBoost训练器  │    │ • 环境变量管理   │    │ • Jupyter接口    │
│ • 性能评估模块   │    │ • 参数配置中心   │    │ • 命令行工具     │
│ • 可视化报告     │    │ • 日志管理系统   │    │ • API服务接口    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 2.2 技术栈选型

#### 核心框架
- **Python 3.8+**: 主要开发语言
- **XGBoost**: 机器学习模型引擎
- **MongoDB**: 非关系型数据库
- **pandas/numpy**: 数据处理库

#### 辅助工具
- **requests**: HTTP客户端
- **matplotlib/seaborn**: 数据可视化
- **scikit-learn**: 机器学习工具包
- **python-dotenv**: 环境配置管理

#### 开发工具
- **Jupyter Notebook**: 交互式开发环境
- **pytest**: 单元测试框架
- **black**: 代码格式化工具

## 3. 模块详细设计

### 3.1 数据采集模块 (collector)

#### 类结构设计
```python
class OKExDataFetcher:
    def __init__(self):
        """Initialize OKEx API client"""
        self.base_url = config.OKEX_API_BASE_URL
        self.session = requests.Session()
        
    def fetch_candlesticks(self, inst_id: str = None, bar: str = "1H", after: Optional[str] = None):
        """获取K线数据
        Args:
            inst_id: 交易对标识 (如 "ETH-USDT-SWAP")
            bar: 时间间隔 (如 "1H", "4H", "1D")
            after: 时间戳用于分页获取历史数据
        """
        pass
        
    def fetch_historical_data(self, inst_id: str = None, bar: str = "1H", max_records: int = 100000, check_duplicates: bool = True):
        """拉取历史数据并写入MongoDB
        Args:
            inst_id: 交易对标识
            bar: 时间间隔
            max_records: 最大记录数
            check_duplicates: 是否检查重复数据
        """
        pass
        
    def _process_candlestick_data(self, raw_data, inst_id: str = None, bar: str = "1H"):
        """处理K线数据格式"""
        pass
        
    def _save_to_mongodb(self, data):
        """保存到MongoDB"""
        pass
```

#### 关键特性
- **动态交易对支持**: 支持任意inst_id参数
- **多时间间隔**: 支持1m/5m/15m/1H/4H/1D等多种时间间隔
- **去重检查**: 基于inst_id+bar+timestamp的复合键去重
- **分页获取**: 支持通过after参数获取历史数据
- **速率限制**: 集成Redis令牌桶算法控制API请求频率

### 3.2 数据存储模块 (database)

#### 数据库模式设计
```javascript
// K线数据集合 (candlesticks)
{
    "_id": ObjectId,
    "bar": String,              // 时间间隔 (如 "1D", "1H", "15m")
    "inst_id": String,          // 交易对标识 (如 "ETH-USDT-SWAP")
    "timestamp": Number,        // 时间戳 (毫秒)
    "open": Number,             // 开盘价
    "high": Number,             // 最高价
    "low": Number,              // 最低价
    "close": Number,            // 收盘价
    "volume": Number,           // 成交量
    "vol_ccy": Number,          // 交易额
    "vol_ccy_quote": Number,    // 计价货币交易额
    "confirm": Number           // 确认状态 (1=已确认)
}

// 特征数据集合 (features)
{
    "_id": ObjectId,
    "inst_id": String,         // 交易对标识 (如 "ETH-USDT-SWAP")
    "bar": String,             // 时间间隔 (如 "1H")
    "timestamp": Number,       // 时间戳 (毫秒)
    "features": {
        // 1小时基础特征
        "close_1h_normalized": Number,    // 价格标准化
        "volume_1h_normalized": Number,   // 成交量标准化
        "rsi_14_1h": Number,              // 标准短期动量指标
        "macd_line_1h": Number,           // MACD快线
        "macd_signal_1h": Number,         // MACD信号线
        
        // 时间编码特征
        "hour_cos": Number,               // 小时余弦编码
        "hour_sin": Number,               // 小时正弦编码
        "day_of_week": Number,            // 星期几
        
        // 15分钟高频特征
        "rsi_14_15m": Number,             // 15分钟RSI
        "volume_impulse_15m": Number,     // 15分钟成交量脉冲
        
        // 4小时中期特征
        "rsi_14_4h": Number,              // 4小时RSI
        "trend_continuation_4h": Number   // 4小时趋势延续强度
    },
    "label": Number,           // 1-7分类标签
    "future_return": Number,   // 实际收益率
    "processed_at": ISODate
}

// 标准化参数集合 (normalizer)
{
    "_id": ObjectId,
    "inst_id": String,        // 交易对标识 (如 "ETH-USDT-SWAP")
    "bar": String,            // 时间间隔 (如 "1H", "15m", "4H")
    "mean": Number,           // 训练期间的均值
    "std": Number,            // 训练期间的标准差
    "created_at": ISODate,    // 创建时间
    "updated_at": ISODate     // 更新时间
}
```

#### 标准化参数管理
为了确保特征在训练和预测时的一致性，需要把对应币种的mean和std独立计算并保存到MongoDB集合normalizer中。每次训练完成后，系统会自动计算并保存当前训练数据的统计参数，在预测时使用这些固定的参数进行标准化。

#### 索引策略
```javascript
// candlesticks集合索引
db.candlesticks.createIndex({"symbol": 1, "timestamp": -1, "bar": 1})
db.candlesticks.createIndex({"timestamp": 1})

// features集合索引
db.features.createIndex({"timestamp": -1})
db.features.createIndex({"label": 1})

// normalizer集合索引
db.normalizer.createIndex({"inst_id": 1, "bar": 1}, {unique: true})
db.normalizer.createIndex({"updated_at": -1})
```

### 3.3 特征工程模块 (feature_engineering)

#### 标准化一致性保证
为了确保特征在训练和预测时的一致性，系统采用以下策略：

1. **训练阶段**：计算训练数据的均值和标准差，保存到MongoDB的`normalizer`集合中
2. **预测阶段**：从`normalizer`集合获取对应的统计参数，使用固定参数进行标准化
3. **参数结构**：`{"inst_id": "ETH-USDT-SWAP", "bar": "1H", "mean": 1234.56, "std": 78.90}`

#### 核心算法流程
```python
class FeatureEngineer:
    def __init__(self):
        self.time_windows = {
            'short': 12,    # 12小时
            'medium': 48,   # 2天
            'long': 192     # 8天
        }
        
    def calculate_rsi(self, prices, window):
        """计算RSI指标"""
        pass
        
    def calculate_bollinger_bands(self, prices, window):
        """计算布林带指标"""
        pass
        
    def generate_labels(self, df):
        """生成7级分类标签"""
        # 计算24小时后的价格变化率
        # 根据预设区间进行分类映射
        pass
        
    def create_feature_dataset(self, df, stride=10):
        """创建训练数据集"""
        pass
```

#### 特征向量构成
```
MVP最小可行特征集 (12-15个特征):

基础层特征 (1H):
- close_1h_normalized: 价格标准化
- volume_1h_normalized: 成交量标准化
- rsi_14_1h: 标准短期动量指标
- macd_line_1h, macd_signal_1h: 趋势跟踪

时间编码特征:
- hour_cos, hour_sin: 周期性时间特征
- day_of_week: 星期几周期性

高频特征 (15m):
- rsi_14_15m: 快速动量反应
- volume_impulse_15m: 成交量脉冲 (20周期窗口)

中期特征 (4H):
- rsi_14_4h: 中期动量
- trend_continuation_4h: 趋势延续强度
```

### 3.4 机器学习模块 (ml_trainer)

#### 模型架构
```python
class MLTrainer:
    def __init__(self):
        self.model = xgb.XGBClassifier(
            objective='multi:softprob',
            num_class=7,
            max_depth=6,
            learning_rate=0.1,
            n_estimators=200,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42
        )
        
    def prepare_training_data(self, stride=10):
        """准备训练数据"""
        pass
        
    def train_model(self, validation_split=0.2):
        """训练模型"""
        pass
        
    def evaluate_model(self):
        """评估模型性能"""
        pass
        
    def plot_performance_report(self):
        """生成可视化报告"""
        pass
```

#### 评估指标体系
- **主指标**: 多分类准确率 (Accuracy)
- **辅助指标**: 
  - 各类别精确率 (Precision)
  - 各类别召回率 (Recall)
  - F1分数 (F1-Score)
  - 混淆矩阵 (Confusion Matrix)

## 4. 接口设计

### 4.1 Jupyter Notebook接口
```python
# 简洁的一行式调用
from src.collector import OkexDataCollector
collector = OkexDataCollector()
collector.run_collection_job()

from src.feature_engineer import FeatureEngineer
engineer = FeatureEngineer()
engineer.process_all_data(stride=15)

from src.ml_trainer import MLTrainer
trainer = MLTrainer()
trainer.execute_full_pipeline(plot_report=True)
```

### 4.2 命令行接口
```bash
# 数据采集
python main.py collect --symbol ETH-USDT --days 365

# 特征工程
python main.py engineer --stride 10

# 模型训练
python main.py train --validation-split 0.2 --plot
```

### 4.3 配置文件接口
```python
# .env配置文件
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=eth_options_hunter
OKEX_API_KEY=your_api_key
OKEX_API_SECRET=your_api_secret
RATE_LIMIT=20

# settings.py配置中心
COLLECTION_CONFIG = {
    'batch_size': 100,
    'rate_limit': 20,
    'retry_attempts': 3
}

TRAINING_CONFIG = {
    'stride': 10,
    'validation_split': 0.2,
    'plot_results': True
}
```

## 5. 性能优化策略

### 5.1 内存管理
- **流式处理**: 分批加载大型数据集
- **缓存机制**: 频繁访问的数据内存缓存
- **垃圾回收**: 及时释放无用对象

### 5.2 计算优化
- **向量化运算**: 使用numpy进行批量计算
- **并行处理**: I/O密集型任务多线程处理
- **算法优化**: 时间复杂度敏感操作优化

### 5.3 数据库优化
- **索引优化**: 关键查询字段建立复合索引
- **分片策略**: 大数据量时考虑水平分片
- **连接池**: 复用数据库连接资源

## 6. 安全设计

### 6.1 API安全
- **密钥管理**: 敏感信息环境变量存储
- **请求签名**: OKEx API认证机制
- **访问控制**: IP白名单和频率限制

### 6.2 数据安全
- **备份策略**: 定期数据库备份
- **传输加密**: HTTPS通信协议
- **权限控制**: 最小权限原则

## 7. 监控与运维

### 7.1 系统监控
- **健康检查**: 各模块运行状态监控
- **性能指标**: 响应时间、吞吐量统计
- **错误追踪**: 异常日志记录和告警

### 7.2 日志系统
```python
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 日志格式
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

---

*本文档为ETH期权猎手工具v1.0版本的完整架构设计*