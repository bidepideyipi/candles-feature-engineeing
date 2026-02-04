import sys
from pathlib import Path
import pytest

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from feature.feature_label import FeatureLabel

class TestFeatureCreate:
    """_summary_
    这段展示了如何使用FeatureMerge()类来合并特征
    loop()考虑了不同时间维度数据对齐问题
    """
    def test_meger_the_top_one(self):
        feature_label = FeatureLabel()
        feature_label.loop(inst_id='ETH-USDT-SWAP', limit=20000)
        assert True
    
    
if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])