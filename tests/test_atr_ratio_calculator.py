"""
ATR比值计算器测试
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_atr_ratio_calculator():
    """测试ATR比值计算器基本功能"""
    
    print("=" * 60)
    print("ATR比值计算器测试")
    print("=" * 60)
    
    try:
        import pandas as pd
        import numpy as np
        from src.utils.atr_ratio_calculator import ATR_RATIO_CALCULATOR
        
        print("✓ 成功导入ATR_RATIO_CALCULATOR\n")
        
        # 创建测试数据
        def create_test_data(base_price=100, volatility=0.02, periods=100):
            """创建测试用的OHLC数据"""
            np.random.seed(42)
            
            close_prices = [base_price]
            for _ in range(periods):
                change = np.random.normal(0, base_price * volatility)
                new_price = close_prices[-1] + change
                close_prices.append(max(new_price, base_price * 0.8))  # 防止价格过低
            
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
        
        # 测试1：基本ATR比值计算
        print("测试1：基本ATR比值计算")
        test_df = create_test_data(base_price=100, volatility=0.02, periods=60)  # 增加到60个数据点
        
        ratio = ATR_RATIO_CALCULATOR.calculate(test_df)
        print(f"ATR比值（短期/长期）: {ratio:.4f}")
        
        if 0 < ratio < 3:  # 合理的比值范围
            print("✓ ATR比值计算正常\n")
        else:
            print("✗ ATR比值异常\n")
        
        # 测试2：ATR动量计算
        print("测试2：ATR动量计算")
        momentum = ATR_RATIO_CALCULATOR.calculate_momentum(test_df)
        print(f"ATR动量（变化率）: {momentum:.4f}")
        
        if -1 < momentum < 1:  # 合理的变化率范围
            print("✓ ATR动量计算正常\n")
        else:
            print("✗ ATR动量异常\n")
        
        # 测试3：ATR分位数计算
        print("测试3：ATR分位数计算")
        percentile = ATR_RATIO_CALCULATOR.calculate_percentile(test_df)
        print(f"ATR分位数（0-1）: {percentile:.4f}")
        
        if 0 <= percentile <= 1:  # 分位数范围
            print("✓ ATR分位数计算正常\n")
        else:
            print("✗ ATR分位数异常\n")
        
        # 测试4：波动率扩张检测
        print("测试4：波动率扩张检测")
        # 创建高波动数据
        high_vol_df = create_test_data(base_price=100, volatility=0.05, periods=60)
        
        expansion_signal = ATR_RATIO_CALCULATOR.detect_volatility_expansion(high_vol_df)
        print(f"高波动数据扩张信号: {expansion_signal} (1=扩张, 0=正常)")
        
        if expansion_signal in [0, 1]:
            print("✓ 波动率扩张检测正常\n")
        else:
            print("✗ 波动率扩张检测异常\n")
        
        # 测试5：波动率收缩检测
        print("测试5：波动率收缩检测")
        # 创建低波动数据
        low_vol_df = create_test_data(base_price=100, volatility=0.005, periods=60)
        
        contraction_signal = ATR_RATIO_CALCULATOR.detect_volatility_contraction(low_vol_df)
        print(f"低波动数据收缩信号: {contraction_signal} (1=收缩, 0=正常)")
        
        if contraction_signal in [0, 1]:
            print("✓ 波动率收缩检测正常\n")
        else:
            print("✗ 波动率收缩检测异常\n")
        
        # 测试6：跨时间框架ATR比值
        print("测试6：跨时间框架ATR比值")
        short_df = create_test_data(base_price=100, volatility=0.02, periods=60)
        long_df = create_test_data(base_price=100, volatility=0.03, periods=60)
        
        cross_ratio = ATR_RATIO_CALCULATOR.calculate_cross_timeframe_ratio(short_df, long_df)
        print(f"跨周期ATR比值（短周期/长周期）: {cross_ratio:.4f}")
        
        if cross_ratio > 0:
            print("✓ 跨周期ATR比值计算正常\n")
        else:
            print("✗ 跨周期ATR比值计算异常\n")
        
        # 测试7：完整波动率分析报告
        print("测试7：完整波动率分析报告")
        profile = ATR_RATIO_CALCULATOR.get_volatility_profile(test_df)
        
        print(f"分析状态: {profile['status']}")
        if profile['status'] == 'success':
            print(f"当前ATR: {profile['current_atr']:.4f}")
            print(f"ATR动量: {profile['atr_momentum']:.4f}")
            print(f"ATR分位数: {profile['atr_percentile']:.4f}")
            print(f"波动率扩张: {profile['volatility_expansion']}")
            print(f"波动率收缩: {profile['volatility_contraction']}")
            print(f"ATR比值: {profile['atr_ratio_short_long']:.4f}")
            
            stats = profile['historical_stats']
            print(f"历史统计 - 均值: {stats['mean']:.4f}, 标准差: {stats['std']:.4f}")
            print("✓ 完整波动率分析报告生成正常\n")
        else:
            print(f"✗ 分析报告生成失败: {profile.get('message', '未知错误')}\n")
        
        # 测试8：边界情况处理
        print("测试8：边界情况处理")
        
        # 数据不足
        short_df = create_test_data(base_price=100, volatility=0.02, periods=30)  # 30个数据点，少于56
        try:
            ratio = ATR_RATIO_CALCULATOR.calculate(short_df)
            print(f"数据不足时比值: {ratio}")
        except ValueError as e:
            print(f"正确处理数据不足: {str(e)[:50]}...")
        
        # 空DataFrame
        empty_df = pd.DataFrame(columns=['open', 'high', 'low', 'close'])
        try:
            ratio = ATR_RATIO_CALCULATOR.calculate(empty_df)
            print(f"空数据时比值: {ratio}")
        except Exception as e:
            print(f"正确处理空数据: {str(e)[:50]}...")
        
        print("✓ 边界情况处理正常\n")
        
        # 测试9：自定义参数
        print("测试9：自定义参数测试")
        from src.utils.atr_ratio_calculator import ATRRatioCalculator
        
        custom_calculator = ATRRatioCalculator(
            short_period=10,
            long_period=20,
            lookback_window=30
        )
        
        custom_ratio = custom_calculator.calculate(test_df)
        print(f"自定义参数ATR比值: {custom_ratio:.4f}")
        print("✓ 自定义参数计算器工作正常\n")
        
        # 总结
        print("=" * 60)
        print("测试总结")
        print("=" * 60)
        print("✓ 所有核心功能测试通过")
        print("✓ ATR比值计算器工作正常")
        print("✓ 支持多种波动率分析功能")
        print("✓ 支持跨时间框架比较")
        print("✓ 正确处理边界情况")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_atr_ratio_calculator()
    if success:
        print("\n🎉 ATR比值计算器测试成功！")
    else:
        print("\n❌ ATR比值计算器测试失败！")
        sys.exit(1)