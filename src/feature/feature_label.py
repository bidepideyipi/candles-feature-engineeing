import logging
from typing import Dict, Any

from collect.candlestick_handler import candlestick_handler
from collect.feature_handler import feature_handler
from config.settings import config

# Create logger
log = logging.getLogger(__name__)

class FeatureLabel:
    
    def loop(self, inst_id: str, limit: int = 5000) -> bool:
        """
        循环合并特征标签
        """
        features = feature_handler.get_features(inst_id = inst_id, bar = "1H", limit = limit)
        if not features or len(features) == 0:
            log.warning(f"获取特征失败, inst_id: {inst_id}, bar: 1H")
            return False
        
        for i, feature in enumerate(features):
            if i >= limit:
                break
            self.process(feature = feature)
        
        return True
    
    def process(self, feature: Dict[str, Any]) -> bool:
        inst_id = feature.get("inst_id")
        timestamp = feature.get("timestamp")
        candles = candlestick_handler.get_candlestick_data(inst_id = inst_id, bar = "1H", limit = 24, after = timestamp)
        
        if not candles or len(candles) != 24:
            log.warning(f"获取1H蜡烛数据失败, inst_id: {inst_id}, timestamp: {timestamp}")
            return False
        
        first_open = candles[0].get("open")
        last_close = candles[-1].get("close")
        
        if first_open is None or last_close is None or first_open == 0:
            log.warning(f"价格数据异常, first_open: {first_open}, last_close: {last_close}")
            return False
        
        price_change_pct = (last_close - first_open) / first_open * 100
        
        label = self._classify_price_change(price_change_pct)
        
        log.info(f"分类结果 - inst_id: {inst_id}, timestamp: {timestamp}, 涨跌幅: {price_change_pct:.2f}%, 分类: {label}")
        
        feature_handler.update_feature_label(inst_id = inst_id, timestamp = timestamp, label = label)
        
        return True
    
    def _classify_price_change(self, price_change_pct: float) -> int:
        """
        根据涨跌幅度分类
        """
        thresholds = config.CLASSIFICATION_THRESHOLDS
        
        for label_id, (lower, upper) in thresholds.items():
            if lower < price_change_pct <= upper:
                return label_id
        
        return 4
        
        