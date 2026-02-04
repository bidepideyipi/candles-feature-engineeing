"""
RSI计算器单元测试
测试RSI计算准确性和边界情况
"""

import sys
from pathlib import Path
import numpy as np
import pytest

# 将src目录添加到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from utils.rsi_calculator import RSI_CALCULATOR


class TestRSICalculator:
    """RSICalculator类的测试套件"""
    
    def test_calculate(self):
        prices = np.array([100, 101, 102, 103, 104, 103, 102, 101, 100, 99, 98, 97, 96, 95, 94])
        result = RSI_CALCULATOR.calculate(prices)
        assert result < 50.0
    
if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])