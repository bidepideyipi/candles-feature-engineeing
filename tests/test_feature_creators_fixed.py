"""
测试修复后的ATR比值和RSI背离计算器
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_feature_creators():
    """测试特征创建器的新功能"""
    
    print("=" * 60)
    print("测试特征创建器新功能")
    print("=" * 60)
    
    try:
        import pandas as pd
        import numpy as np
        from src.feature.feature_1h_creator import Feature1HCreator
        from src.feature.feature_4h_creator import Feature4HCreator
        
        print("✓ 成功导入特征创建器\n")
        
        # 创建测试数据
        def create_test_candles(periods=60, base_price=100, volatility=0.02):
            """创建测试蜡烛数据"""
            np.random.seed(42)
            
            candles = []
            for i in range(periods):
                high = base_price * (1 + np.random.uniform(0, volatility))
                low = base_price * (1 - np.random.uniform(0, volatility))
                open_price = base_price * (1 + np.random.uniform(-volatility/2, volatility/2))
                close_price = base_price * (1 + np.random.uniform(-volatility/2, volatility/2))
                
                candles.append({
                    'open': round(open_price, 2),
                    'high': round(max(high, open_price, close_price), 2),
                    'low': round(min(low, open_price, close_price), 2),
                    'close': round(close_price, 2),
                    'timestamp': i * 3600000,  # 每小时
                    'record_hour': i % 24,
                    'day_of_week': i % 7,
                    'volume': np.random.randint(100, 1000)
                })
                
                base_price = close_price  # 价格延续
            
            return candles
        
        # 测试1H特征创建器
        print("测试1: 1小时特征创建器")
        candles1h = create_test_candles(periods=60)
        
        creator1h = Feature1HCreator(close_mean=100.0, close_std=10.0)
        feature1h = creator1h.calculate(candles1h)
        
        print(f"✓ ATR比值特征: {feature1h.atr_ratio_1h_15m}")
        print(f"✓ RSI背离特征: {feature1h.rsi_divergence_1h}")
        
        # 验证特征类型
        assert isinstance(feature1h.atr_ratio_1h_15m, (int, float)), "ATR比值应该是数字类型"
        assert isinstance(feature1h.rsi_divergence_1h, (int, float)), "RSI背离应该是数字类型"
        print("✓ 特征类型正确\n")
        
        # 测试4H特征创建器
        print("测试2: 4小时特征创建器")
        candles4h = create_test_candles(periods=60)  # 需要足够的数据点
        
        creator4h = Feature4HCreator(close_mean=100.0, close_std=10.0)
        feature4h = creator4h.calculate(candles4h)
        
        print(f"✓ ATR比值特征: {feature4h.atr_ratio_4h_1h}")
        print(f"✓ RSI背离特征: {feature4h.rsi_divergence_4h}")
        
        # 验证特征类型
        assert isinstance(feature4h.atr_ratio_4h_1h, (int, float)), "ATR比值应该是数字类型"
        assert isinstance(feature4h.rsi_divergence_4h, (int, float)), "RSI背离应该是数字类型"
        print("✓ 特征类型正确\n")
        
        # 验证RSI背离信号范围
        print("测试3: 验证RSI背离信号范围")
        assert feature4h.rsi_divergence_4h in [-1, 0, 1], "RSI背离应该是-1, 0, 或 1"
        assert feature1h.rsi_divergence_1h in [-1, 0, 1], "RSI背离应该是-1, 0, 或 1"
        print("✓ RSI背离信号范围正确\n")
        
        print("=" * 60)
        print("🎉 所有特征创建器测试通过！")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_feature_creators()
    sys.exit(0 if success else 1)