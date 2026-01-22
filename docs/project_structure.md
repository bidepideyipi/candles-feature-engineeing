# 项目结构说明

## 清理后的目录结构

```
technial_analysis_helper/
├── src/                          # 核心源代码
│   ├── collector/               # 数据采集模块
│   │   ├── __init__.py
│   │   └── data_collector.py    # OKEx API数据采集器
│   ├── config/                  # 配置管理
│   │   └── settings.py          # 项目配置文件
│   ├── data/                    # 数据处理模块
│   │   ├── mongodb_handler.py   # MongoDB数据库操作
│   │   ├── okex_fetcher.py      # OKEx数据获取
│   │   └── training_data_generator.py  # 训练数据生成器
│   ├── feature_engineering/     # 特征工程模块
│   │   ├── __init__.py
│   │   ├── create_feature_dataset.py   # 特征数据集创建
│   │   └── label_generator.py   # 标签生成器
│   ├── ml_training/             # 机器学习训练
│   │   └── __init__.py
│   ├── models/                  # 模型定义
│   │   └── xgboost_trainer.py   # XGBoost训练器
│   ├── utils/                   # 工具函数
│   │   ├── feature_engineering.py     # 特征工程工具
│   │   ├── rate_limiter.py      # 限速器
│   │   └── technical_indicators.py    # 技术指标计算器
│   └── __init__.py
├── notebooks/                   # Jupyter笔记本
│   └── getting_start.ipynb      # 入门指南
├── docs/                        # 文档
│   ├── architecture.md          # 架构设计文档
│   ├── development_plan.md      # 开发计划
│   └── ...                      # 其他技术文档
├── main.py                      # 主程序入口
├── requirements.txt             # 依赖包列表
├── .env.example                 # 环境变量示例
├── .gitignore                   # Git忽略文件
├── PRD.md                       # 产品需求文档
└── README.md                    # 项目说明
```

## 模块功能说明

### 数据采集层 (`src/collector/`)
- `data_collector.py`: 负责从OKEx API采集ETH-USDT的K线数据，包含限速控制

### 数据处理层 (`src/data/`)
- `mongodb_handler.py`: MongoDB数据库连接和数据操作
- `okex_fetcher.py`: OKEx交易所数据获取接口
- `training_data_generator.py`: 训练数据生成和预处理

### 特征工程层 (`src/feature_engineering/`)
- `create_feature_dataset.py`: 创建机器学习训练用的特征数据集
- `label_generator.py`: 生成价格变动的分类标签

### 模型训练层 (`src/models/`)
- `xgboost_trainer.py`: XGBoost模型训练、评估和预测

### 工具层 (`src/utils/`)
- `feature_engineering.py`: 特征工程相关的工具函数
- `rate_limiter.py`: API请求限速控制
- `technical_indicators.py`: 技术指标计算（RSI、布林带等）

## 清理说明

### 删除的重复文件：
1. `src/database/mongo_handler.py` (与 `src/data/mongodb_handler.py` 重复)
2. `src/feature_engineering/technical_indicators.py` (空文件)
3. `src/ml_training/model_trainer.py` (空文件)

### 删除的空目录：
1. `src/database/` (清理后为空目录)

## 使用建议

1. **开发顺序**: 按照数据采集 → 数据存储 → 特征工程 → 模型训练的顺序进行开发
2. **配置管理**: 复制 `.env.example` 为 `.env` 并填写实际配置
3. **依赖安装**: 运行 `pip install -r requirements.txt`
4. **测试运行**: 使用 `main.py` 或 Jupyter notebook 进行测试

---
*项目结构已优化，去除了重复和无用文件，保持了清晰的模块化设计*