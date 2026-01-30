import pandas as pd
from .calculator_interface import BaseTechnicalCalculator

class AverageTrueRangeCalculator(BaseTechnicalCalculator):
    def calculate(self, df: pd.DataFrame) -> float:
        """
        计算ATR指标
        Average True Range (volatility) 平均真实波幅
        
        Args:
            df: DataFrame with OHLC data containing 'high', 'low', 'close' columns
        Returns:
            float: 最新ATR值
        """
        
        # Validate required columns
        required_cols = ['high', 'low', 'close']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame must contain columns: {required_cols}")
        
        
        close_prices = df['close'].astype(float)
        
        # 数据验证
        if len(close_prices) < 14:
            raise ValueError("需要至少14个数据点来计算ATR")
        
        high_prices = df['high'].astype(float)
        low_prices = df['low'].astype(float)
        
        # 1. 计算真实波幅(True Range)
        tr_list = []
        for i in range(len(high_prices)):
            if i == 0:
                tr = high_prices[i] - low_prices[i]
            else:
                method1 = high_prices[i] - low_prices[i]
                method2 = abs(high_prices[i] - close_prices[i-1])
                method3 = abs(low_prices[i] - close_prices[i-1])
                tr = max(method1, method2, method3)
            tr_list.append(tr)
        
        # 2. 计算ATR - 使用简单移动平均初始化，然后转为EMA
        tr_series = pd.Series(tr_list)
        
        # 前14个值使用简单移动平均作为初始值
        sma_atr = tr_series.rolling(window=14).mean()
        
        # 从第14个值开始使用EMA平滑
        atr = sma_atr.copy()
        for i in range(14, len(tr_series)):
            atr.iloc[i] = (tr_series.iloc[i] + (14-1) * atr.iloc[i-1]) / 14
        
        return float(atr.iloc[-1])
ATR = AverageTrueRangeCalculator()
