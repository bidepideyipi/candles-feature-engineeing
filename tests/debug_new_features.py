"""
调试特征创建器的新增特征问题
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def debug_feature_calculation():
    """调试特征计算"""
    
    print("=" * 60)
    print("调试特征创建器新增特征")
    print("=" * 60)
    
    try:
        import pandas as pd
        import numpy as np
        
        # 模拟真实的数据结构
        def create_realistic_candles(periods=60, base_price=100, volatility=0.02):
            """创建真实的蜡烛数据结构"""
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
        
        # 测试1：直接测试ATR比值计算器
        print("\n测试1：直接测试ATR比值计算器")
        print("-" * 40)
        
        from src.utils.atr_ratio_calculator import ATR_RATIO_CALCULATOR
        
        candles48 = create_realistic_candles(periods=48)
        df48 = pd.DataFrame(candles48)
        
        print(f"数据形状: {df48.shape}")
        print(f"数据列: {list(df48.columns)}")
        print(f"前3行数据:\n{df48.head(3)}")
        
        try:
            atr_ratio = ATR_RATIO_CALCULATOR.calculate(df48)
            print(f"✓ ATR比值计算成功: {atr_ratio}")
        except Exception as e:
            print(f"✗ ATR比值计算失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试2：直接测试RSI背离计算器
        print("\n测试2：直接测试RSI背离计算器")
        print("-" * 40)
        
        from src.utils.rsi_divergence_calculator import RSI_DIVERGENCE_DETECTOR
        
        close_prices = pd.Series([item['close'] for item in candles48])
        
        print(f"收盘价数据长度: {len(close_prices)}")
        print(f"收盘价范围: {close_prices.min():.2f} - {close_prices.max():.2f}")
        
        try:
            rsi_divergence = RSI_DIVERGENCE_DETECTOR.calculate(close_prices)
            print(f"✓ RSI背离计算成功: {rsi_divergence}")
        except Exception as e:
            print(f"✗ RSI背离计算失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试3：测试1H特征创建器
        print("\n测试3：测试1H特征创建器")
        print("-" * 40)
        
        from src.feature.feature_1h_creator import Feature1HCreator
        
        candles1h_48 = create_realistic_candles(periods=48)
        print(f"1H蜡烛数据数量: {len(candles1h_48)}")
        
        creator1h = Feature1HCreator(close_mean=100.0, close_std=10.0)
        
        try:
            feature1h = creator1h.calculate(candles1h_48)
            print(f"✓ 1H特征创建成功")
            print(f"  ATR比值特征: {feature1h.atr_ratio_1h_15m}")
            print(f"  RSI背离特征: {feature1h.rsi_divergence_1h}")
            print(f"  其他特征样本:")
            print(f"    RSI_14_1h: {feature1h.rsi_14_1h}")
            print(f"    MACD_line_1h: {feature1h.macd_line_1h}")
        except Exception as e:
            print(f"✗ 1H特征创建失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试4：测试4H特征创建器
        print("\n测试4：测试4H特征创建器")
        print("-" * 40)
        
        from src.feature.feature_4h_creator import Feature4HCreator
        
        candles4h_48 = create_realistic_candles(periods=48)
        print(f"4H蜡烛数据数量: {len(candles4h_48)}")
        
        creator4h = Feature4HCreator(close_mean=100.0, close_std=10.0)
        
        try:
            feature4h = creator4h.calculate(candles4h_48)
            print(f"✓ 4H特征创建成功")
            print(f"  ATR比值特征: {feature4h.atr_ratio_4h_1h}")
            print(f"  RSI背离特征: {feature4h.rsi_divergence_4h}")
            print(f"  其他特征样本:")
            print(f"    RSI_14_4h: {feature4h.rsi_14_4h}")
            print(f"    MACD_line_4h: {feature4h.macd_line_4h}")
        except Exception as e:
            print(f"✗ 4H特征创建失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试5：检查数据量不足的情况
        print("\n测试5：检查数据量不足的情况")
        print("-" * 40)
        
        candles_small = create_realistic_candles(periods=30)  # 少于48
        df_small = pd.DataFrame(candles_small)
        
        print(f"数据量: {len(candles_small)} (需要至少48)")
        
        try:
            atr_ratio = ATR_RATIO_CALCULATOR.calculate(df_small)
            print(f"✗ 不应该成功，但结果: {atr_ratio}")
        except Exception as e:
            print(f"✓ 预期的错误: {e}")
        
        # 测试6：检查数据库中的实际数据格式
        print("\n测试6：模拟数据库数据格式")
        print("-" * 40)
        
        # 模拟从MongoDB获取的数据格式
        mock_db_data = [
            {
                '_id': 'test_1',
                'timestamp': 1234567890000,
                'open': 100.5,
                'high': 101.0,
                'low': 100.0,
                'close': 100.8,
                'volume': 1000,
                'record_hour': 12,
                'day_of_week': 3
            },
            {
                '_id': 'test_2', 
                'timestamp': 1234567890000 + 3600000,
                'open': 100.8,
                'high': 101.5,
                'low': 100.5,
                'close': 101.2,
                'volume': 1200,
                'record_hour': 13,
                'day_of_week': 3
            }
        ]
        
        print(f"数据库数据样本: {mock_db_data[0]}")
        print(f"是否有缺失字段: {set(['open', 'high', 'low', 'close']) - set(mock_db_data[0].keys())}")
        
        print("\n" + "=" * 60)
        print("调试测试完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 调试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_feature_calculation()