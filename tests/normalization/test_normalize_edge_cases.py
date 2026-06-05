#!/usr/bin/env python3
"""
测试归一化器对边界情况的处理
"""
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from utils.normalize_encoder import NORMALIZED

def test_empty_data():
    """测试空数据"""
    print("=" * 60)
    print("测试 1: 空数据")
    print("=" * 60)
    try:
        close = []
        result = NORMALIZED.calculate(close)
        print("✗ 错误：应该抛出 ValueError")
        return False
    except ValueError as e:
        print(f"✓ 正确捕获异常: {e}")
        return True
    except Exception as e:
        print(f"✗ 意外异常: {e}")
        return False

def test_identical_values():
    """测试所有值相同的情况"""
    print("\n" + "=" * 60)
    print("测试 2: 所有值相同（std=0）")
    print("=" * 60)
    try:
        close = [100.0, 100.0, 100.0, 100.0, 100.0]
        print(f"  输入数据: {close}")
        result = NORMALIZED.calculate(close)
        print("✗ 错误：应该抛出 ValueError")
        return False
    except ValueError as e:
        print(f"✓ 正确捕获异常: {e}")
        return True
    except Exception as e:
        print(f"✗ 意外异常: {e}")
        return False

def test_normal_data():
    """测试正常数据"""
    print("\n" + "=" * 60)
    print("测试 3: 正常数据")
    print("=" * 60)
    try:
        close = [100.0, 101.5, 102.3, 99.8, 101.0, 100.5]
        print(f"  输入数据: {close}")
        normalized, mean, std = NORMALIZED.calculate(close)
        print(f"  均值: {mean:.4f}")
        print(f"  标准差: {std:.4f}")
        print(f"  归一化值: {normalized:.4f}")
        print("✓ 计算成功")
        return True
    except Exception as e:
        print(f"✗ 异常: {e}")
        return False

def test_single_value():
    """测试单个值的情况"""
    print("\n" + "=" * 60)
    print("测试 4: 单个值（std=0）")
    print("=" * 60)
    try:
        close = [100.0]
        print(f"  输入数据: {close}")
        result = NORMALIZED.calculate(close)
        print("✗ 错误：应该抛出 ValueError")
        return False
    except ValueError as e:
        print(f"✓ 正确捕获异常: {e}")
        return True
    except Exception as e:
        print(f"✗ 意外异常: {e}")
        return False

def test_pandas_series():
    """测试 pandas Series"""
    print("\n" + "=" * 60)
    print("测试 5: pandas Series")
    print("=" * 60)
    try:
        close = pd.Series([100.0, 101.5, 102.3, 99.8, 101.0, 100.5])
        print(f"  输入数据: {close.tolist()}")
        normalized, mean, std = NORMALIZED.calculate(close)
        print(f"  均值: {mean:.4f}")
        print(f"  标准差: {std:.4f}")
        print(f"  归一化值: {normalized:.4f}")
        print("✓ 计算成功")
        return True
    except Exception as e:
        print(f"✗ 异常: {e}")
        return False

if __name__ == "__main__":
    results = []
    results.append(test_empty_data())
    results.append(test_identical_values())
    results.append(test_normal_data())
    results.append(test_single_value())
    results.append(test_pandas_series())
    
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    print(f"通过: {sum(results)}/{len(results)}")
    print(f"失败: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("\n✓ 所有测试通过")
        sys.exit(0)
    else:
        print("\n✗ 部分测试失败")
        sys.exit(1)