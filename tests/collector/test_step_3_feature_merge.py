import sys
from pathlib import Path
import pytest
import logging

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from feature.feature_merge import FeatureMerge

# 配置日志输出到控制台
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

class TestFeatureCreate:
    """_summary
    这段展示了如何使用FeatureMerge()类来合并特征
    loop()考虑了不同时间维度数据对齐问题
    """
    def test_meger_the_top_one(self):
        feature_merge = FeatureMerge()
        feature_merge.loop(before=1765983600000, limit=14400)
        assert True
    
    
if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])