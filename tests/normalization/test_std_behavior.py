#!/usr/bin/env python3
"""
测试 pandas std() 的行为
"""
import pandas as pd

# 测试单个值
s1 = pd.Series([100.0])
print(f"单个值: {s1.values}")
print(f"  std(): {s1.std()}")
print(f"  std() == 0: {s1.std() == 0}")
print(f"  pd.isna(std()): {pd.isna(s1.std())}")
print(f"  std() is None: {s1.std() is None}")

print()

# 测试所有值相同
s2 = pd.Series([100.0, 100.0, 100.0])
print(f"所有值相同: {s2.values}")
print(f"  std(): {s2.std()}")
print(f"  std() == 0: {s2.std() == 0}")
print(f"  pd.isna(std()): {pd.isna(s2.std())}")

print()

# 测试正常值
s3 = pd.Series([100.0, 101.0, 102.0])
print(f"正常值: {s3.values}")
print(f"  std(): {s3.std()}")
print(f"  std() == 0: {s3.std() == 0}")
print(f"  pd.isna(std()): {pd.isna(s3.std())}")