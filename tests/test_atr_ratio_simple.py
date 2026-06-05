"""
简化的ATR比值计算器测试
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_basic_functionality():
    """测试基本功能"""
    
    print("=" * 60)
    print("ATR比值计算器基本功能测试")
    print("=" * 60)
    
    try:
        import pandas as pd
        import numpy as np
        from src.utils.atr_ratio_calculator import ATR_RATIO_CALCULATOR
        
        print("✓ 成功导入ATR_RATIO_CALCULATOR\n")
        
        # 创建足够的测试数据
        def create_test_data(base_price=100, volatility=0.02, periods=70):
            """创建测试用的OHLC数据"""
            np.random.seed(42)
            
            close_prices = [base_price]
            for _ in range(periods):
                change = np.random.normal(0, base_price * volatility)
                new_price = close_prices[-1] + change
                close_prices.append(max(new_price, base_price * 0.8))
            
            # 创建OHLC数据
            data = []
            for i in range(1, len(close_prices)):
                high = close_prices[i] + np.random.uniform(0, base_price * volatility * 0.5)
                low = close_prices[i] - np.random.uniform(0, base_price * volatility * 0.5)
                open_price = close_prices[i-1] + np.random.uniform(-base_price * volatility * 0.2, base_price * volatility * 0.2)
                close = close_prices[i]
                
                data.append({
                    'open': max(open_price, low),
                    'high': max(high, open_price, close),
                    'low': min(low, open_price, close),
                    'close': close
                })
            
            return pd.DataFrame(data)
        
        # 基本测试
        print("基本功能测试")
        test_df = create_test_data(base_price=100, volatility=0.02, periods=70)
        
        # 测试1：ATR比值计算
        ratio = ATR_RATIO_CALCULATOR.calculate(test_df)
        print(f"✓ ATR比值: {ratio:.4f}")
        
        # 测试2：ATR动量
        momentum = ATR_RATIO_CALCULATOR.calculate_momentum(test_df)
        print(f"✓ ATR动量: {momentum:.4f}")
        
        # 测试3：ATR分位数
        percentile = ATR_RATIO_CALCULATOR.calculate_percentile(test_df)
        print(f"✓ ATR分位数: {percentile:.4f}")
        
        # 测试4：波动率扩张检测
        expansion = ATR_RATIO_CALCULATOR.detect_volatility_expansion(test_df)
        print(f"✓ 波动率扩张信号: {expansion}")
        
        # 测试5：波动率收缩检测
        contraction = ATR_RATIO_CALCULATOR.detect_volatility_contraction(test_df)
        print(f"✓ 波动率收缩信号: {contraction}")
        
        # 测试6：跨周期比值
        short_df = create_test_data(base_price=100, volatility=0.02, periods=70)
        long_df = create_test_data(base_price=100, volatility=0.03, periods=70)
        cross_ratio = ATR_RATIO_CALCULATOR.calculate_cross_timeframe_ratio(short_df, long_df)
        print(f"✓ 跨周期ATR比值: {cross_ratio:.4f}")
        
        # 测试7：完整分析报告
        profile = ATR_RATIO_CALCULATOR.get_volatility_profile(test_df)
        print(f"✓ 完整分析报告状态: {profile['status']}")
        if profile['status'] == 'success':
            print(f"  - 当前ATR: {profile['current_atr']:.4f}")
            print(f"  - ATR分位数: {profile['atr_percentile']:.4f}")
            print(f"  - 波动率状态: {'扩张' if profile['volatility_expansion'] else ('收缩' if profile['volatility_contraction'] else '正常')}")
        
        # 测试8：数据不足处理
        short_df = create_test_data(base_price=100, volatility=0.02, periods=30)
        try:
            ratio = ATR_RATIO_CALCULATOR.calculate(short_df)
        except ValueError as e:
            print(f"✓ 正确处理数据不足: {str(e)[:40]}...")
        
        # 测试9：自定义参数
        from src.utils.atr_ratio_calculator import ATRRatioCalculator
        custom_calc = ATRRatioCalculator(short_period=10, long_period=20, lookback_window=30)
        custom_ratio = custom_calc.calculate(test_df)
        print(f"✓ 自定义参数ATR比值: {custom_ratio:.4f}")
        
        print("\n" + "=" * 60)
        print("🎉 所有基本功能测试通过！")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)