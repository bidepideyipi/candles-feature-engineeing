import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from feature.feature_label_extreme_high import FeatureLabelExtremeHigh


class TestFeatureLabelExtremeHigh:
    """
    测试极端波动标签生成器 - 最高价版本
    """
    
    def test_loop_extreme_label_high(self):
        """
        测试循环生成极端波动标签 - 最高价版本
        """
        feature_label_extreme_high = FeatureLabelExtremeHigh()  
        result = feature_label_extreme_high.loop(inst_id='ETH-USDT-SWAP', limit=200)
        assert result, "极端波动标签生成失败"
        
if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
    