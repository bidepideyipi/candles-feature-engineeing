import logging
from typing import Dict, Any

from collect.candlestick_handler import candlestick_handler
from collect.feature_handler import feature_handler
from config.settings import config

# Create logger
log = logging.getLogger(__name__)

class FeatureLabel:
    
    def loop(self, inst_id: str, limit: int = 5000, onlyFixNone: bool = True) -> bool:
        """
        循环合并特征标签
        """
        features = feature_handler.get_features(inst_id = inst_id, bar = "1H", limit = limit, isNull = onlyFixNone)
        if not features or len(features) == 0:
            log.warning(f"获取特征失败, inst_id: {inst_id}, bar: 1H")
            return False
        
        for i, feature in enumerate(features):
            if i >= limit:
                break
            labels = self.process(feature = feature)
            timestamp = feature.get("timestamp")
            feature_handler.update_feature_label(inst_id = inst_id, timestamp = timestamp, label = labels["label"], label_high = labels["label_high"], label_low = labels["label_low"])
        
        return True
    
    def process(self, feature: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理单个特征，生成24小时后Close价格的涨跌幅度标签
        """
        inst_id = feature.get("inst_id")
        timestamp = feature.get("timestamp")
        candles = candlestick_handler.get_candlestick_data(inst_id = inst_id, bar = "1H", limit = 24, after = timestamp)
        
        if not candles or len(candles) != 24:
            log.warning(f"获取1H蜡烛数据失败, inst_id: {inst_id}, timestamp: {timestamp}")
            return False
        
        first_open = candles[0].get("open")
        last_close = candles[-1].get("close")
        max_high = max(c.get("high") for c in candles)
        min_low = min(c.get("low") for c in candles)
        
        if first_open is None or last_close is None or first_open == 0:
            log.warning(f"价格数据异常, first_open: {first_open}, last_close: {last_close}")
            return False
        
        price_change_pct = (last_close - first_open) / first_open * 100
        price_change_pct_high = (max_high - first_open) / first_open * 100
        price_change_pct_low = (min_low - first_open) / first_open * 100
        
        label = self._classify_price_change(price_change_pct)
        label_high = self._classify_price_change_high(price_change_pct_high)
        label_low = self._classify_price_change_low(price_change_pct_low)
        
        log.info(f"分类结果 - inst_id: {inst_id}, timestamp: {timestamp}, 涨跌幅: {price_change_pct:.2f}%, 分类: {label}")
        
        return {"label": label, "label_high": label_high, "label_low": label_low}
    
    def _classify_price_change(self, price_change_pct: float) -> int:
        """
        根据涨跌幅度分类
        """
        thresholds = config.CLASSIFICATION_THRESHOLDS
        
        for label_id, (lower, upper) in thresholds.items():
            if lower < price_change_pct <= upper:
                return label_id
        
        log.warning(f"未匹配到分类, price_change_pct: {price_change_pct:.2f}")
        return 3
    
    def _classify_price_change_high(self, price_change_pct: float) -> int:
        """
        根据涨跌幅度分类
        """
        thresholds = config.CLASSIFICATION_THRESHOLDS_HIGH  
        
        for label_id, (lower, upper) in thresholds.items():
            if lower < price_change_pct <= upper:
                return label_id
            
        log.warning(f"未匹配到分类, price_change_pct: {price_change_pct:.2f}")
        return 1
    
    def _classify_price_change_low(self, price_change_pct: float) -> int:
        """
        根据涨跌幅度分类
        """
        thresholds = config.CLASSIFICATION_THRESHOLDS_LOW  
        
        for label_id, (lower, upper) in thresholds.items():
            if lower < price_change_pct <= upper:
                return label_id
        
        log.warning(f"未匹配到分类, price_change_pct: {price_change_pct:.2f}")
        return 3
        
        