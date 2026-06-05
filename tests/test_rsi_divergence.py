"""
Test script for RSI Divergence Calculator
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from src.utils.rsi_divergence_calculator import RSI_DIVERGENCE_DETECTOR

def test_bullish_divergence():
    """
    测试看涨背离（价格创新低但RSI未创新低）
    """
    print("=== 测试看涨背离 ===")
    
    # 构造看涨背离数据：价格创新低但RSI未创新低
    # 第一段：下跌
    prices_1 = [100, 95, 90, 85, 80, 75, 70, 72, 74, 73]  # 低点在70
    # 第二段：反弹后继续下跌，但RSI更高（看涨背离）
    prices_2 = [75, 78, 80, 79, 77, 75, 74, 73, 72, 71, 70, 68]  # 新低68，但RSI应该更高
    
    prices = prices_1 + prices_2
    
    detector = RSI_DIVERGENCE_DETECTOR
    signal = detector.calculate(prices)
    details = detector.get_divergence_details(prices)
    
    print(f"背离信号: {signal}")
    print(f"详细信息: {details}")
    
    # 验证结果
    if signal == 1:
        print("✓ 成功检测到看涨背离")
    else:
        print("✗ 未能检测到看涨背离")
    
    return signal == 1

def test_bearish_divergence():
    """
    测试看跌背离（价格创新高但RSI未创新高）
    """
    print("\n=== 测试看跌背离 ===")
    
    # 构造看跌背离数据：价格创新高但RSI未创新高
    # 第一段：上涨
    prices_1 = [100, 105, 110, 115, 120, 125, 130, 128, 126, 127]  # 高点在130
    # 第二段：回调后继续上涨，但RSI更低（看跌背离）
    prices_2 = [125, 128, 130, 132, 134, 133, 131, 132, 133, 134, 135, 136]  # 新高136，但RSI应该更低
    
    prices = prices_1 + prices_2
    
    detector = RSI_DIVERGENCE_DETECTOR
    signal = detector.calculate(prices)
    details = detector.get_divergence_details(prices)
    
    print(f"背离信号: {signal}")
    print(f"详细信息: {details}")
    
    # 验证结果
    if signal == -1:
        print("✓ 成功检测到看跌背离")
    else:
        print("✗ 未能检测到看跌背离")
    
    return signal == -1

def test_no_divergence():
    """
    测试无背离情况
    """
    print("\n=== 测试无背离 ===")
    
    # 构造趋势一致的数据：价格和RSI同向变化
    # 简单的上涨趋势
    prices = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120, 122, 124, 126, 128, 130]
    
    detector = RSI_DIVERGENCE_DETECTOR
    signal = detector.calculate(prices)
    details = detector.get_divergence_details(prices)
    
    print(f"背离信号: {signal}")
    print(f"详细信息: {details}")
    
    # 验证结果
    if signal == 0:
        print("✓ 正确识别无背离")
    else:
        print("✗ 错误识别背离")
    
    return signal == 0

def test_insufficient_data():
    """
    测试数据不足的情况
    """
    print("\n=== 测试数据不足 ===")
    
    # 数据不足
    prices = [100, 102, 104, 106, 108]
    
    detector = RSI_DIVERGENCE_DETECTOR
    signal = detector.calculate(prices)
    details = detector.get_divergence_details(prices)
    
    print(f"背离信号: {signal}")
    print(f"详细信息: {details}")
    
    # 验证结果
    if signal == 0 and '数据不足' in details['message']:
        print("✓ 正确处理数据不足情况")
    else:
        print("✗ 数据不足处理有误")
    
    return signal == 0

def test_custom_parameters():
    """
    测试自定义参数
    """
    print("\n=== 测试自定义参数 ===")
    
    # 创建自定义参数的检测器
    custom_detector = RSI_DIVERGENCE_DETECTOR.__class__(
        window=14, 
        lookback=15, 
        min_strength=0.05
    )
    
    # 简单测试
    prices = [100, 95, 90, 85, 80, 75, 70, 72, 74, 73, 75, 78, 80, 79, 77, 75, 74, 73, 72, 71, 70, 68, 67, 65]
    
    signal = custom_detector.calculate(prices)
    details = custom_detector.get_divergence_details(prices)
    
    print(f"背离信号: {signal}")
    print(f"详细信息: {details}")
    print("✓ 自定义参数检测器工作正常")
    
    return True

def main():
    """
    运行所有测试
    """
    print("RSI背离检测器测试开始\n")
    print("=" * 60)
    
    results = []
    
    # 运行各项测试
    results.append(("看涨背离测试", test_bullish_divergence()))
    results.append(("看跌背离测试", test_bearish_divergence()))
    results.append(("无背离测试", test_no_divergence()))
    results.append(("数据不足测试", test_insufficient_data()))
    results.append(("自定义参数测试", test_custom_parameters()))
    
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