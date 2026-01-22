"""
Label generator for 7-level classification system.
Calculates future return and maps to discrete categories.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional

from ..config.settings import config

logger = logging.getLogger(__name__)

class LabelGenerator:
    """
    Generates 7-level classification labels based on future return predictions.
    """
    
    def __init__(self):
        """
        Initialize label generator with classification thresholds from config.
        """
        self.thresholds = config.CLASSIFICATION_THRESHOLDS
        self.class_labels = sorted(self.thresholds.keys())
    
    def generate_labels(self, df: pd.DataFrame, prediction_horizon: int = 24) -> pd.DataFrame:
        """
        Generate classification labels for a DataFrame of price data.
        
        Args:
            df: DataFrame with OHLCV data
            prediction_horizon: Number of periods to look ahead for return calculation
            
        Returns:
            DataFrame with added labels and future returns
        """
        if len(df) < prediction_horizon + 1:
            logger.warning(f"Insufficient data for label generation. Need at least {prediction_horizon + 1} periods.")
            return df
        
        # Ensure data is sorted by timestamp
        df = df.sort_values('timestamp').reset_index(drop=True).copy()
        
        # Calculate future returns
        future_returns = []
        labels = []
        
        for i in range(len(df)):
            if i + prediction_horizon < len(df):
                current_price = df['close'].iloc[i]
                future_price = df['close'].iloc[i + prediction_horizon]
                return_pct = (future_price / current_price - 1) * 100
                future_returns.append(return_pct)
                labels.append(self._classify_return(return_pct))
            else:
                future_returns.append(np.nan)
                labels.append(None)
        
        # Add to DataFrame
        df['future_return'] = future_returns
        df['classification_label'] = labels
        
        logger.info(f"Generated labels for {len([l for l in labels if l is not None])} samples")
        return df
    
    def _classify_return(self, return_pct: float) -> int:
        """
        Classify return percentage into discrete categories.
        
        Args:
            return_pct: Return percentage
            
        Returns:
            Classification label (-3 to 3)
        """
        for label, (min_val, max_val) in self.thresholds.items():
            if min_val <= return_pct < max_val:
                return label
        return 0  # Default to neutral class
    
    def get_label_distribution(self, labels: List[int]) -> Dict[int, int]:
        """
        Get distribution of classification labels.
        
        Args:
            labels: List of classification labels
            
        Returns:
            Dictionary of label counts
        """
        from collections import Counter
        valid_labels = [label for label in labels if label is not None]
        distribution = Counter(valid_labels)
        
        logger.info(f"Label distribution: {dict(distribution)}")
        return dict(distribution)
    
    def analyze_label_balance(self, labels: List[int]) -> Dict[str, Any]:
        """
        Analyze label balance and provide statistics.
        
        Args:
            labels: List of classification labels
            
        Returns:
            Dictionary of balance statistics
        """
        valid_labels = [label for label in labels if label is not None]
        total_labels = len(valid_labels)
        
        if total_labels == 0:
            logger.warning("No valid labels for balance analysis")
            return {}
        
        distribution = self.get_label_distribution(valid_labels)
        
        # Calculate balance metrics
        max_count = max(distribution.values())
        min_count = min(distribution.values())
        
        balance_stats = {
            'total_labels': total_labels,
            'label_distribution': distribution,
            'max_count': max_count,
            'min_count': min_count,
            'balance_ratio': min_count / max_count if max_count > 0 else 0,
            'is_balanced': min_count / max_count > 0.1  # Considered balanced if min is at least 10% of max
        }
        
        logger.info(f"Label balance analysis: {balance_stats}")
        return balance_stats

# Global instance
label_generator = LabelGenerator()