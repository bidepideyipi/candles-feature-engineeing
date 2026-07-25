"""
Option C: XGBoost 三分类 market regime（TREND_UP / TREND_DOWN / RANGE）
使用时间序列切分，专注 regime 相关特征。
"""
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler

from config.settings import config
from collect.feature_handler import feature_handler
from feature.feature_types import Feature
from regime.regime_types import REGIME_DESCRIPTION, REGIME_LABELS, REGIME_STRATEGY, MarketRegime

logger = logging.getLogger(__name__)

REGIME_FEATURE_COLUMNS = [
    "adx_4h", "plus_di_4h", "minus_di_4h", "trend_continuation_4h",
    "ema_12_4h", "ema_26_4h", "ema_48_4h",
    "ema_cross_4h_12_26", "ema_cross_4h_26_48",
    "atr_4h", "atr_ratio_4h_1h", "rsi_14_4h", "rsi_divergence_4h",
    "macd_histogram_4h", "macd_line_4h", "macd_signal_4h",
    "adx_1h", "plus_di_1h", "minus_di_1h", "atr_ratio_1h_15m", "rsi_14_1h",
    "atr_15m", "rsi_14_15m", "stoch_k_15m", "stoch_d_15m",
    "bollinger_position_1d", "atr_1d", "rsi_14_1d",
    "price_momentum_proxy",
]

EXCLUDED_FIELDS = {
    "_id", "inst_id", "bar", "timestamp",
    "label", "label_high", "label_low", "regime_label", "price",
}


class RegimeTrainer:
    """训练/加载 regime 三分类模型。"""

    def __init__(self, model_save_path: str = None):
        self.model_save_path = model_save_path or config.REGIME_MODEL_SAVE_PATH
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns: Optional[List[str]] = None

    def train_model(
        self,
        inst_id: str = "ETH-USDT-SWAP",
        bar: str = "1H",
        limit: int = 10000,
        test_ratio: float = 0.2,
    ) -> Dict[str, Any]:
        features = feature_handler.get_features_for_regime(
            inst_id=inst_id, bar=bar, limit=limit
        )
        if not features or len(features) < 200:
            raise ValueError(f"regime 标注样本不足: {len(features) if features else 0}")

        df = pd.DataFrame(features)
        df = df.sort_values("timestamp").reset_index(drop=True)

        if "price" in df.columns:
            df["price_momentum_proxy"] = df["price"].pct_change(4).fillna(0)
        else:
            df["price_momentum_proxy"] = 0.0

        targets = df["regime_label"].astype(int) - 1  # XGBoost 0-indexed

        available = [c for c in REGIME_FEATURE_COLUMNS if c in df.columns]
        if not available:
            raise ValueError("无可用 regime 特征列")

        self.feature_columns = available
        features_df = df[available].ffill().fillna(0)

        split_idx = int(len(features_df) * (1 - test_ratio))
        X_train = features_df.iloc[:split_idx]
        X_test = features_df.iloc[split_idx:]
        y_train = targets.iloc[:split_idx]
        y_test = targets.iloc[split_idx:]

        logger.info(
            "Regime 时间切分 train=%s test=%s features=%s",
            len(X_train), len(X_test), len(available),
        )
        logger.info("Train label dist:\n%s", y_train.value_counts().sort_index())
        logger.info("Test  label dist:\n%s", y_test.value_counts().sort_index())

        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        num_classes = int(targets.max()) + 1
        params = {
            "objective": "multi:softprob",
            "num_class": num_classes,
            "max_depth": 6,
            "learning_rate": 0.05,
            "subsample": 0.85,
            "colsample_bytree": 0.85,
            "min_child_weight": 5,
            "gamma": 0.1,
            "reg_alpha": 0.1,
            "reg_lambda": 1.0,
            "random_state": 42,
            "eval_metric": "mlogloss",
        }

        dtrain = xgb.DMatrix(X_train_scaled, label=y_train)
        dtest = xgb.DMatrix(X_test_scaled, label=y_test)

        self.model = xgb.train(
            params,
            dtrain,
            num_boost_round=150,
            evals=[(dtrain, "train"), (dtest, "test")],
            early_stopping_rounds=15,
            verbose_eval=False,
        )

        y_pred_proba = self.model.predict(dtest)
        y_pred = np.argmax(y_pred_proba, axis=1)
        accuracy = accuracy_score(y_test, y_pred)

        unique = sorted(np.unique(np.concatenate([y_test, y_pred])))
        class_names = [REGIME_LABELS.get(MarketRegime(i + 1), str(i + 1)) for i in unique]
        report = classification_report(
            y_test, y_pred, labels=unique, target_names=class_names, output_dict=True
        )
        conf = confusion_matrix(y_test, y_pred, labels=unique).tolist()

        self.save_model()

        results = {
            "accuracy": float(accuracy),
            "train_size": len(X_train),
            "test_size": len(X_test),
            "feature_columns": available,
            "classification_report": report,
            "confusion_matrix": conf,
            "test_period": {
                "from_ts": int(df.iloc[split_idx]["timestamp"]),
                "to_ts": int(df.iloc[-1]["timestamp"]),
            },
            "trained_at": datetime.now().isoformat(),
        }
        logger.info("Regime model accuracy (time-split test): %.4f", accuracy)
        return results

    def predict(
        self, features_input: Union[pd.DataFrame, List[Dict[str, Any]], List[Feature]]
    ) -> Tuple[np.ndarray, np.ndarray]:
        if self.model is None or self.feature_columns is None:
            raise ValueError("Model not loaded")

        if isinstance(features_input, list):
            rows = []
            for item in features_input:
                rows.append(item.to_dict() if isinstance(item, Feature) else item)
            features_df = pd.DataFrame(rows)
        else:
            features_df = features_input.copy()

        if "price" in features_df.columns:
            features_df["price_momentum_proxy"] = 0.0

        features_df = features_df[self.feature_columns].fillna(0)
        scaled = self.scaler.transform(features_df)
        probabilities = self.model.predict(xgb.DMatrix(scaled))
        predictions = np.argmax(probabilities, axis=1) + 1
        return predictions, probabilities

    def predict_single(
        self, feature_input: Union[Dict[str, Any], Feature]
    ) -> Tuple[int, np.ndarray, str, float]:
        feature_dict = feature_input.to_dict() if isinstance(feature_input, Feature) else feature_input
        preds, probs = self.predict([feature_dict])
        regime = int(preds[0])
        idx = regime - 1
        confidence = float(probs[0][idx]) if idx < len(probs[0]) else 0.0
        strategy = REGIME_STRATEGY.get(MarketRegime(regime), "none")
        return regime, probs[0], strategy, confidence

    def build_prediction_payload(
        self, feature_input: Union[Dict[str, Any], Feature]
    ) -> Dict[str, Any]:
        feature_dict = feature_input.to_dict() if isinstance(feature_input, Feature) else feature_input
        regime, probs, strategy, confidence = self.predict_single(feature_dict)

        prob_dict = {
            int(i + 1): round(float(p), 4)
            for i, p in enumerate(probs)
        }
        regime_enum = MarketRegime(regime)

        return {
            "type": "regime",
            "timestamp": feature_dict.get("timestamp"),
            "inst_id": feature_dict.get("inst_id", "ETH-USDT-SWAP"),
            "bar": feature_dict.get("bar", "1H"),
            "regime": regime,
            "regime_label": REGIME_LABELS.get(regime_enum, str(regime)),
            "regime_description": REGIME_DESCRIPTION.get(regime_enum, ""),
            "recommended_strategy": strategy,
            "confidence": round(confidence, 4),
            "probabilities": prob_dict,
            "price": feature_dict.get("price"),
            "features_count": len(self.feature_columns or []),
        }

    def save_model(self):
        if self.model is None:
            return
        os.makedirs(os.path.dirname(self.model_save_path) or ".", exist_ok=True)
        self.model.save_model(self.model_save_path)
        joblib.dump(self.scaler, self.model_save_path.replace(".json", "_scaler.pkl"))
        with open(self.model_save_path.replace(".json", "_features.json"), "w") as f:
            json.dump(self.feature_columns, f)
        logger.info("Regime model saved to %s", self.model_save_path)

    def load_model(self) -> bool:
        try:
            if not os.path.exists(self.model_save_path):
                logger.warning("Regime model not found: %s", self.model_save_path)
                return False
            self.model = xgb.Booster()
            self.model.load_model(self.model_save_path)
            self.scaler = joblib.load(
                self.model_save_path.replace(".json", "_scaler.pkl")
            )
            with open(self.model_save_path.replace(".json", "_features.json")) as f:
                self.feature_columns = json.load(f)
            return True
        except Exception as e:
            logger.error("Failed to load regime model: %s", e)
            return False


regime_trainer = RegimeTrainer()
