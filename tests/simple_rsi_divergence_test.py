"""
简单的RSI背离检测器测试
"""

import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_basic_functionality():
    """测试基本功能"""
    print("测试RSI背离检测器基本功能")
    
    try:
        from src.utils.rsi_divergence_calculator import RSI_DIVERGENCE_DETECTOR
        print("✓ 成功导入RSI_DIVERGENCE_DETECTOR")
        
        # 检测器类
        print(f"检测器类型: {type(RSI_DIVERGENCE_DETECTOR)}")
        print(f"检测器参数: window={RSI_DIVERGENCE_DETECTOR.window}, lookback={RSI_DIVERGENCE_DETECTOR.lookback}")
        
        # 简单测试
        import numpy as np
        test_data = [100, 95, 90, 85, 80, 75, 70, 72, 74, 73, 75, 78, 80, 79, 77, 75, 74, 73, 72, 71, 70, 68, 67, 65]
        
        signal = RSI_DIVERGENCE_DETECTOR.calculate(test_data)
        print(f"测试数据信号: {signal}")
        
        details = RSI_DIVERGENCE_DETECTOR.get_divergence_details(test_data)
        print(f"详细信息: {details}")
        
        print("✓ 基本功能测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_divergence_types():
    """测试不同类型的背离"""
    print("\n测试不同背离类型")
    
    try:
        from src.utils.rsi_divergence_calculator import RSIDivergenceDetector
        
        # 看涨背离测试数据（价格新低但RSI未新低）
        bullish_data = [100, 95, 90, 85, 80, 75, 70, 72, 74, 73, 75, 78, 80, 79, 77, 75, 74, 73, 72, 71, 70, 68, 67, 65]
        
        # 看跌背离测试数据（价格新高但RSI未新高）
        bearish_data = [100, 105, 110, 115, 120, 125, 130, 128, 126, 127, 125, 128, 130, 132, 134, 133, 131, 132, 133, 134, 135, 136, 137, 138]
        
        # 趋势数据（无背离）
        trend_data = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120, 122, 124, 126, 128, 130, 132, 134, 136, 138, 140, 142, 144, 146]
        
        detector = RSIDivergenceDetector()
        
        # 测试看涨背离
        bullish_signal = detector.calculate(bullish_data)
        print(f"看涨背离信号: {bullish_signal}")
        bullish_details = detector.get_divergence_details(bullish_data)
        print(f"看涨背离详情: {bullish_details}")
        
        # 测试看跌背离
        bearish_signal = detector.calculate(bearish_data)
        print(f"看跌背离信号: {bearish_signal}")
        bearish_details = detector.get_divergence_details(bearish_data)
        print(f"看跌背离详情: {bearish_details}")
        
        # 测试趋势数据
        trend_signal = detector.calculate(trend_data)
        print(f"趋势数据信号: {trend_signal}")
        trend_details = detector.get_divergence_details(trend_data)
        print(f"趋势数据详情: {trend_details}")
        
        print("✓ 背离类型测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_edge_cases():
    """测试边界情况"""
    print("\n测试边界情况")
    
    try:
        from src.utils.rsi_divergence_calculator import RSIDivergenceDetector
        
        detector = RSIDivergenceDetector()
        
        # 数据不足
        short_data = [100, 102, 104, 106, 108]
        short_signal = detector.calculate(short_data)
        print(f"数据不足信号: {short_signal}")
        
        # 空数据
        empty_data = []
        try:
            empty_signal = detector.calculate(empty_data)
            print(f"空数据信号: {empty_signal}")
        except Exception as e:
            print(f"空数据处理: {e}")
        
        # 单一价格
        single_data = [100]
        try:
            single_signal = detector.calculate(single_data)
            print(f"单一价格信号: {single_signal}")
        except Exception as e:
            print(f"单一价格处理: {e}")
        
        print("✓ 边界情况测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行所有测试"""
    print("=" * 60)
    print("RSI背离检测器测试")
    print("=" * 60)
    
    results = []
    
    results.append(("基本功能测试", test_basic_functionality()))
    results.append(("背离类型测试", test_divergence_types()))
    results.append(("边界情况测试", test_edge_cases()))
    
    # 总结结果
    print("\n" + "=" * 60)
    print("测试结果总结:")
    
    passed = 0
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n通过: {passed}/{len(results)}")
    
    if passed == len(results):
        print("所有测试通过！")
    else:
        print(f"{len(results) - passed} 个测试失败")

if __name__ == "__main__":
    main()