"""
直接测试特征创建器，不依赖API
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径（与main.py相同）
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_feature_creators_directly():
    """直接测试特征创建器"""
    
    print("=" * 60)
    print("直接测试特征创建器")
    print("=" * 60)
    
    try:
        import pandas as pd
        import numpy as np
        
        # 创建更真实的数据
        def create_realistic_candles(periods=48, base_price=100):
            """创建真实的蜡烛数据"""
            np.random.seed(42)
            candles = []
            
            for i in range(periods):
                # 模拟价格波动
                change = np.random.normal(0, 0.01)  # 1%标准差
                new_price = base_price * (1 + change)
                
                high = new_price * (1 + np.random.uniform(0, 0.005))
                low = new_price * (1 - np.random.uniform(0, 0.005))
                open_price = base_price
                
                candles.append({
                    'open': round(open_price, 2),
                    'high': round(max(high, open_price, new_price), 2),
                    'low': round(min(low, open_price, new_price), 2),
                    'close': round(new_price, 2),
                    'timestamp': 1700000000000 + i * 3600000,  # 从某个时间戳开始
                    'record_hour': i % 24,
                    'day_of_week': i % 7,
                    'volume': np.random.randint(1000, 5000)
                })
                
                base_price = new_price  # 延续价格
            
            return candles
        
        # 导入特征创建器
        print("\n导入特征创建器模块...")
        from src.feature.feature_1h_creator import Feature1HCreator
        from src.feature.feature_4h_creator import Feature4HCreator
        print("✓ 成功导入特征创建器\n")
        
        # 创建测试数据
        print("创建测试数据...")
        candles1h = create_realistic_candles(periods=48)
        candles4h = create_realistic_candles(periods=48)
        
        print(f"✓ 创建1H数据: {len(candles1h)}条")
        print(f"✓ 创建4H数据: {len(candles4h)}条\n")
        
        # 测试1H特征创建器
        print("测试1H特征创建器...")
        print("-" * 40)
        
        creator1h = Feature1HCreator(
            close_mean=100.0, 
            close_std=5.0, 
            vol_mean=3000.0, 
            vol_std=1000.0
        )
        
        try:
            feature1h = creator1h.calculate(candles1h)
            print("✓ 1H特征创建成功")
            print(f"  新增特征:")
            print(f"    atr_ratio_1h_15m: {feature1h.atr_ratio_1h_15m}")
            print(f"    rsi_divergence_1h: {feature1h.rsi_divergence_1h}")
            print(f"  其他特征:")
            print(f"    rsi_14_1h: {feature1h.rsi_14_1h}")
            print(f"    macd_line_1h: {feature1h.macd_line_1h}")
            print(f"    volume_impulse_1h: {feature1h.volume_impulse_1h}")
            
            # 检查是否为零
            if feature1h.atr_ratio_1h_15m == 0.0 and feature1h.rsi_divergence_1h == 0:
                print("  ⚠️ 新增特征全为0，可能有问题")
            else:
                print("  ✓ 新增特征正常")
                
        except Exception as e:
            print(f"✗ 1H特征创建失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试4H特征创建器
        print("\n测试4H特征创建器...")
        print("-" * 40)
        
        creator4h = Feature4HCreator(
            close_mean=100.0, 
            close_std=5.0
        )
        
        try:
            feature4h = creator4h.calculate(candles4h)
            print("✓ 4H特征创建成功")
            print(f"  新增特征:")
            print(f"    atr_ratio_4h_1h: {feature4h.atr_ratio_4h_1h}")
            print(f"    rsi_divergence_4h: {feature4h.rsi_divergence_4h}")
            print(f"  其他特征:")
            print(f"    rsi_14_4h: {feature4h.rsi_14_4h}")
            print(f"    macd_line_4h: {feature4h.macd_line_4h}")
            print(f"    atr_4h: {feature4h.atr_4h}")
            
            # 检查是否为零
            if feature4h.atr_ratio_4h_1h == 0.0 and feature4h.rsi_divergence_4h == 0:
                print("  ⚠️ 新增特征全为0，可能有问题")
            else:
                print("  ✓ 新增特征正常")
                
        except Exception as e:
            print(f"✗ 4H特征创建失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试计算器本身
        print("\n直接测试计算器...")
        print("-" * 40)
        
        from src.utils.atr_ratio_calculator import ATR_RATIO_CALCULATOR
        from src.utils.rsi_divergence_calculator import RSI_DIVERGENCE_DETECTOR
        
        # 测试ATR比值计算器
        df1h = pd.DataFrame(candles1h)
        try:
            atr_ratio = ATR_RATIO_CALCULATOR.calculate(df1h)
            print(f"✓ ATR比值计算器正常: {atr_ratio}")
        except Exception as e:
            print(f"✗ ATR比值计算器失败: {e}")
        
        # 测试RSI背离计算器
        close1h = pd.Series([c['close'] for c in candles1h])
        try:
            rsi_divergence = RSI_DIVERGENCE_DETECTOR.calculate(close1h)
            print(f"✓ RSI背离计算器正常: {rsi_divergence}")
        except Exception as e:
            print(f"✗ RSI背离计算器失败: {e}")
        
        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_feature_creators_directly()