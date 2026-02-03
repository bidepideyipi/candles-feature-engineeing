import sys
from pathlib import Path
import pytest

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from feature.feature_merge import FeatureMerge

class TestFeatureCreate:
    """_summary_
    这段展示了如何使用FeatureMerge()类来合并特征, 但是没有考虑不同时间维度数据对齐问题
    """
    def test_meger_the_top_one(self):
        feature_merge = FeatureMerge()
        feature_merge.process(inst_id='ETH-USDT-SWAP')
        assert True
    
    
if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])