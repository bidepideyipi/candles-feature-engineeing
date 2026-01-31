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
    
    def test_calculate_rsi(self):
        prices = np.array([100, 101, 102, 103, 104, 103, 102, 101, 100, 99, 98, 97, 96, 95, 94])
        result = RSI_CALCULATOR.calculate(prices)
        assert result < 50.0
    
#     def test_basic_rsi_calculation(self):
#         """使用已知值测试基本RSI计算"""
#         # 创建具有明显上涨/下跌趋势的测试数据
#         prices = np.array([100, 101, 102, 103, 104, 103, 102, 101, 100, 99, 98, 97, 96, 95, 94])
#         calculator = RSICalculator(window=14)
        
#         result = calculator.calculate(prices)
        
#         # 结果长度应与输入相同
#         assert len(result) == len(prices)
#         # 前14个值应为NaN（数据不足）
#         # assert result.iloc[:14].isna().all()
#         # 最后一个值应为有效的RSI
#         assert not np.isnan(result.iloc[-1])
#         # RSI应在0到100之间
#         assert 0 <= result.iloc[-1] <= 100
    
#     def test_rsi_with_upward_trend(self):
#         """测试强上升趋势的RSI（应该较高）"""
#         # 创建强烈上涨的价格
#         # np.linspace(star, stop, num)
#         # # 生成从100到150之间均匀分布的30个数值
#         prices = np.linspace(100, 150, 30)  # 强烈上涨趋势
#         calculator = RSICalculator(window=14)
        
#         last_rsi = calculator.get_last(prices)
        
#         # 强势上涨时RSI应该较高
#         assert last_rsi > 70  # 通常>70表示超买
#         assert not np.isnan(last_rsi)
    
#     def test_rsi_with_downward_trend(self):
#         """测试强下降趋势的RSI（应该较低）"""
#         # 创建强烈下跌的价格
#         prices = np.linspace(150, 100, 30)  # 强烈下跌趋势
#         calculator = RSICalculator(window=14)
        
#         last_rsi = calculator.get_last(prices)
        
#         # 强势下跌时RSI应该较低
#         assert last_rsi < 30  # 通常<30表示超卖
#         assert not np.isnan(last_rsi)
    
#     def test_rsi_with_sideways_movement(self):
#         """测试横盘/中性走势的RSI"""
#         # 创建围绕均值振荡的价格
#         t = np.linspace(0, 4*np.pi, 50)
#         prices = 100 + 10 * np.sin(t)  # 围绕100振荡
#         calculator = RSICalculator(window=14)
        
#         last_rsi = calculator.get_last(prices)
        
#         # 中性市场RSI应在50左右
#         assert 30 <= last_rsi <= 70
#         assert not np.isnan(last_rsi)
    
#     def test_different_window_sizes(self):
#         """测试不同窗口大小的RSI"""
#         prices = np.random.RandomState(42).randn(100).cumsum() + 100
#         prices = np.abs(prices)  # 确保价格为正数
        
#         # 测试不同的窗口大小
#         for window in [7, 14, 21]:
#             calculator = RSICalculator(window=window)
#             result = calculator.calculate(prices)
            
#             # 应有正确数量的NaN值
#             # nan_count = result.iloc[:window-1].isna().sum()
#             # assert nan_count == window - 1
            
#             # 窗口期后应有有效值
#             assert not result.iloc[window-1:].isna().all()
    
#     # def test_fillna_option(self):
#     #     """测试NaN填充选项"""
#     #     prices = np.array([100, 101, 102, 103, 104])  # 对于14周期RSI来说太短
#     #     calculator = RSICalculator(window=14, fillna=True)
        
#     #     result = calculator.calculate(prices)
        
#     #     # 使用fillna=True时，不应有NaN值
#     #     assert not result.isna().any()
#     #     # 填充的值应为50（中性）
#     #     assert (result[:13] == 50).all()
    
#     def test_edge_case_empty_input(self):
#         """测试空输入的处理"""
#         calculator = RSICalculator(window=14)
        
#         # 空数组
#         empty_array = np.array([])
#         result = calculator.calculate(empty_array)
#         assert len(result) == 0
        
#         # 单个值
#         single_value = np.array([100])
#         result = calculator.calculate(single_value)
#         assert len(result) == 1
#         assert np.isnan(result.iloc[0])
    
#     def test_edge_case_constant_prices(self):
#         """测试恒定价格（无变化）的RSI"""
#         prices = np.full(30, 100)  # 所有价格都是100
#         calculator = RSICalculator(window=14)
        
#         result = calculator.calculate(prices)
#         last_rsi = calculator.get_last(prices)
        
#         # 没有价格变化时，RSI应为NaN或50
#         # （取决于实现，但应优雅处理）
#         assert np.isnan(last_rsi) or last_rsi == 50
    
#     def test_input_types(self):
#         """测试不同的输入类型"""
#         prices_list = [100, 101, 102, 101, 100, 99, 98, 99, 100, 101]
#         prices_array = np.array(prices_list)
#         prices_series = pd.Series(prices_list)
        
#         calculator = RSICalculator(window=5)
        
#         # 所有输入类型都应该工作
#         result_list = calculator.calculate(prices_list)
#         result_array = calculator.calculate(prices_array)
#         result_series = calculator.calculate(prices_series)
        
#         # 结果应该等价
#         pd.testing.assert_series_equal(result_list, result_array)
#         pd.testing.assert_series_equal(result_array, result_series)
    
#     def test_known_values_validation(self):
#         """针对已知RSI值进行测试"""
#         # 具有已知预期结果的简单测试用例
#         prices = np.array([44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.85, 46.08, 45.89, 46.03, 45.63, 46.28, 46.28, 46.00, 46.03, 46.41, 46.22, 45.64, 46.21, 46.25, 45.71, 46.45, 45.78, 45.35, 44.03, 44.18, 44.22, 44.57, 43.42, 42.66, 43.13])
        
#         calculator = RSICalculator(window=14)
#         result = calculator.calculate(prices)
        
#         # 第15个值（索引14）应是第一个有效的RSI
#         # 这是一个合理性检查 - 确切值取决于实现
#         assert not np.isnan(result.iloc[14])
#         assert 0 <= result.iloc[14] <= 100


# class TestConvenienceFunctions:
#     """便利函数的测试套件"""
    
#     def test_calculate_rsi_function(self):
#         """测试calculate_rsi便利函数"""
#         prices = np.array([100, 101, 102, 101, 100, 99, 98, 99, 100, 101])
        
#         # 应与类方法工作相同
#         result_func = calculate_rsi(prices, window=5)
#         calculator = RSICalculator(window=5)
#         result_class = calculator.calculate(prices)
        
#         pd.testing.assert_series_equal(result_func, result_class)
    
#     def test_get_rsi_last_function(self):
#         """测试get_rsi_last便利函数"""
#         prices = np.array([100, 101, 102, 101, 100, 99, 98, 99, 100, 101])
        
#         # 应与类方法工作相同
#         result_func = get_rsi_last(prices, window=5)
#         calculator = RSICalculator(window=5)
#         result_class = calculator.get_last(prices)
        
#         assert result_func == result_class


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])