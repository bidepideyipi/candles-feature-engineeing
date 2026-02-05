"""
XGBoost model trainer for cryptocurrency price movement classification.
"""

import logging
import os
import json
import joblib
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any, Optional, List
from datetime import datetime

import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.preprocessing import StandardScaler
from sklearn.utils.class_weight import compute_class_weight

from config.settings import config
from collect.feature_handler import feature_handler

logger = logging.getLogger(__name__)

class XGBoostTrainer:
    """Trains and manages XGBoost classification models."""
    
    # 非特征字段列表（需要从训练数据中排除）
    EXCLUDED_FIELDS = {'_id', 'inst_id', 'bar', 'timestamp', 'label'}
    
    def __init__(self):
        """Initialize the trainer."""
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = None
        self.model_save_path = config.MODEL_SAVE_PATH
        
        # Create models directory if it doesn't exist
        os.makedirs(os.path.dirname(self.model_save_path), exist_ok=True)
    
    def train_model(self, 
                   inst_id: str = None,
                   bar: str = None,
                   limit: int = 10000,
                   test_size: float = 0.2,
                   cv_folds: int = 5,
                   use_class_weight: bool = True) -> Dict[str, Any]:
        """
        Train XGBoost model with cross-validation from MongoDB features collection.
        
        Args:
            inst_id: Instrument ID to filter features
            bar: Time interval to filter features
            limit: Maximum number of features to retrieve
            test_size: Proportion of data to use for testing
            cv_folds: Number of cross-validation folds
            use_class_weight: Whether to use class weights to handle imbalance
            
        Returns:
            Dictionary with training results and metrics
        """
        logger.info("Starting XGBoost model training")
        
        # Fetch features from MongoDB
        features = feature_handler.get_features(limit=limit, inst_id=inst_id, bar=bar)
        
        if not features:
            raise ValueError("No features found in MongoDB")
        
        logger.info(f"Retrieved {len(features)} features from MongoDB")
        
        # Convert to DataFrame and separate features and labels
        features_df, targets_series = self._prepare_training_data(features)
        
        if features_df.empty or targets_series.empty:
            raise ValueError("Empty training data after preparation")
        
        # Store feature column names
        self.feature_columns = list(features_df.columns)
        logger.info(f"Number of features: {len(self.feature_columns)}")
        
        # Handle missing values
        features_df = features_df.fillna(features_df.mean())
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            features_df, targets_series, 
            test_size=test_size, 
            random_state=42,
            stratify=targets_series
        )
        
        logger.info(f"Training set size: {len(X_train)}")
        logger.info(f"Test set size: {len(X_test)}")
        
        # Get unique classes and number of classes
        unique_classes = np.unique(targets_series)
        num_classes = len(unique_classes)
        
        logger.info(f"Number of classes in data: {num_classes}")
        logger.info(f"Classes: {sorted([cls + 1 for cls in unique_classes])}")  # +1 to convert back to 1-indexed
        
        # Calculate class weights for imbalanced data
        sample_weights = None
        if use_class_weight:
            class_weights = compute_class_weight('balanced', classes=unique_classes, y=y_train)
            weight_dict = dict(zip(unique_classes, class_weights))
            
            logger.info("Class weights calculated:")
            for cls, weight in weight_dict.items():
                logger.info(f"  Class {cls + 1}: {weight:.4f}")
            
            sample_weights = np.array([weight_dict[label] for label in y_train])
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Convert to DMatrix for XGBoost
        dtrain = xgb.DMatrix(X_train_scaled, label=y_train, weight=sample_weights)
        dtest = xgb.DMatrix(X_test_scaled, label=y_test)
        
        # XGBoost parameters (旧版)
        # params = {
        #     'objective': 'multi:softprob',
        #     'num_class': num_classes,
        #     'max_depth': 6,
        #     'learning_rate': 0.1,
        #     'subsample': 0.8,
        #     'colsample_bytree': 0.8,
        #     'random_state': 42,
        #     'eval_metric': 'mlogloss'
        # }
        
        # XGBoost parameters (新版)
        params = {
            'objective': 'multi:softprob',
            'num_class': num_classes,  # 3类
            'max_depth': 8,           # 增加深度
            'learning_rate': 0.05,     # 降低学习率
            'num_boost_round': 300,     # 增加迭代次数
            'early_stopping_rounds': 20,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
            'eval_metric': 'mlogloss',
            'min_child_weight': 3,
            'gamma': 0.1,
            'reg_alpha': 0.1,
            'reg_lambda': 1
        }
        
        # Train model
        logger.info("Training XGBoost model...")
        self.model = xgb.train(
            params,
            dtrain,
            num_boost_round=300,
            evals=[(dtrain, 'train'), (dtest, 'test')],
            early_stopping_rounds=20,          # 从 10 增加到 20
            verbose_eval=False
        )
        
        # Make predictions
        y_pred_proba = self.model.predict(dtest)
        y_pred = np.argmax(y_pred_proba, axis=1)
        
        # Cross-validation
        logger.info("Performing cross-validation...")
        cv_scores = self._cross_validate_with_weights(
            X_train_scaled, y_train, cv_folds, params, sample_weights
        )
        
        # Calculate metrics
        results = self._calculate_metrics(y_test, y_pred, y_pred_proba, cv_scores)
        
        # Save model
        self.save_model()
        
        logger.info("Model training completed successfully")
        return results
    
    def _cross_validate_with_weights(self, X: np.ndarray, y: np.ndarray, 
                                   cv_folds: int, params: Dict[str, Any], 
                                   sample_weights: np.ndarray = None) -> np.ndarray:
        """
        Perform cross-validation with sample weights.
        
        Args:
            X: Feature matrix
            y: Target labels
            cv_folds: Number of cross-validation folds
            params: XGBoost parameters
            sample_weights: Sample weights for training
            
        Returns:
            Array of cross-validation scores
        """
        from sklearn.model_selection import StratifiedKFold
        from sklearn.metrics import accuracy_score
        
        y_array = y.values if hasattr(y, 'values') else np.array(y)
        
        skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
        cv_scores = []
        
        for fold, (train_idx, val_idx) in enumerate(skf.split(X, y_array), 1):
            logger.info(f"Cross-validation fold {fold}/{cv_folds}")
            
            X_fold_train, X_fold_val = X[train_idx], X[val_idx]
            y_fold_train, y_fold_val = y_array[train_idx], y_array[val_idx]
            
            # Prepare DMatrix for training
            if sample_weights is not None:
                fold_weights = sample_weights[train_idx]
                dtrain = xgb.DMatrix(X_fold_train, label=y_fold_train, weight=fold_weights)
            else:
                dtrain = xgb.DMatrix(X_fold_train, label=y_fold_train)
            
            dval = xgb.DMatrix(X_fold_val, label=y_fold_val)
            
            # Train model
            model = xgb.train(
                params,
                dtrain,
                num_boost_round=100,
                evals=[(dtrain, 'train'), (dval, 'val')],
                early_stopping_rounds=10,
                verbose_eval=False
            )
            
            # Make predictions and score
            y_pred_proba = model.predict(dval)
            y_pred = np.argmax(y_pred_proba, axis=1)
            fold_score = accuracy_score(y_fold_val, y_pred)
            cv_scores.append(fold_score)
            
            logger.info(f"  Fold {fold} accuracy: {fold_score:.4f}")
        
        return np.array(cv_scores)
    
    def _prepare_training_data(self, features: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare training data from MongoDB features.
        
        Args:
            features: List of feature dictionaries from MongoDB
            
        Returns:
            Tuple of (features DataFrame, targets Series)
        """
        df = pd.DataFrame(features)
        
        # 检查是否有 label 字段
        if 'label' not in df.columns:
            raise ValueError("Features data missing 'label' field")
        
        # 移除没有 label 的记录
        df = df[df['label'].notna()]
        if len(df) == 0:
            raise ValueError("No features with valid labels found")
        
        # 提取目标变量，转换为0索引（XGBoost要求标签从0开始）
        targets = df['label'].astype(int) - 1
        
        # 提取特征列，排除非特征字段
        feature_columns = [col for col in df.columns if col not in self.EXCLUDED_FIELDS]
        
        # 检查特征列是否为空
        if not feature_columns:
            raise ValueError("No feature columns found after excluding non-feature fields")
        
        # 提取特征数据
        features_df = df[feature_columns].copy()
        
        logger.info(f"Prepared training data: {len(features_df)} samples, {len(feature_columns)} features")
        logger.info(f"Feature columns: {feature_columns}")
        logger.info(f"Label distribution:\n{targets.value_counts().sort_index()}")
        
        return features_df, targets
    
    def _calculate_metrics(self, 
                          y_true: np.ndarray, 
                          y_pred: np.ndarray,
                          y_pred_proba: np.ndarray,
                          cv_scores: np.ndarray) -> Dict[str, Any]:
        """Calculate various performance metrics."""
        # Basic metrics
        accuracy = accuracy_score(y_true, y_pred)
        
        # Get unique classes in the actual data
        unique_classes = sorted(np.unique(np.concatenate([y_true, y_pred])))
        
        # Convert 0-indexed classes back to original labels (1-7)
        actual_class_labels = [int(cls) + 1 for cls in unique_classes]
        
        # Classification report
        class_report = classification_report(
            y_true, y_pred, 
            labels=unique_classes,
            target_names=[str(label) for label in actual_class_labels],
            output_dict=True
        )
        
        # Confusion matrix
        conf_matrix = confusion_matrix(y_true, y_pred, labels=unique_classes)
        
        # Per-class confidence (y_true现在是0索引，y_pred_proba也是0索引)
        class_confidence = {}
        for class_index, class_label in zip(unique_classes, actual_class_labels):
            class_indices = (y_true == class_index)
            if np.sum(class_indices) > 0:
                class_confidence[class_label] = float(np.mean(
                    y_pred_proba[class_indices, class_index]
                ))
            else:
                class_confidence[class_label] = 0.0
        
        results = {
            'accuracy': float(accuracy),
            'cv_mean_accuracy': float(cv_scores.mean()),
            'cv_std_accuracy': float(cv_scores.std()),
            'classification_report': class_report,
            'confusion_matrix': conf_matrix.tolist(),
            'class_confidence': class_confidence,
            'trained_at': datetime.now().isoformat()
        }
        
        # Log results
        logger.info(f"Accuracy: {accuracy:.4f}")
        logger.info(f"CV Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
        logger.info("Per-class confidence:")
        for class_label, confidence in class_confidence.items():
            logger.info(f"  Class {class_label}: {confidence:.4f}")
        
        return results
    
    def predict(self, features_input: pd.DataFrame or List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Make predictions on new data.
        
        Args:
            features_input: DataFrame with features or List of feature dictionaries from MongoDB
            
        Returns:
            Tuple of (predicted classes, prediction probabilities)
        """
        if self.model is None:
            raise ValueError("Model not trained yet")
        
        if self.feature_columns is None:
            raise ValueError("Feature columns not defined")
        
        # 如果输入是字典列表，转换为 DataFrame
        if isinstance(features_input, list):
            features_df = pd.DataFrame(features_input)
            # 提取特征列，排除非特征字段
            features_df = features_df[[col for col in features_df.columns if col not in self.EXCLUDED_FIELDS]]
        else:
            features_df = features_input.copy()
        
        # Ensure features are in the same order as training
        features_df = features_df[self.feature_columns]
        
        # Handle missing values
        features_df = features_df.fillna(features_df.mean())
        
        # Scale features
        features_scaled = self.scaler.transform(features_df)
        
        # Convert to DMatrix
        dmatrix = xgb.DMatrix(features_scaled)
        
        # Predict
        probabilities = self.model.predict(dmatrix)
        predictions = np.argmax(probabilities, axis=1)
        
        # Convert back to original class labels (1-7)
        predictions = predictions + 1
        
        return predictions, probabilities
    
    def predict_single(self, feature_dict: Dict[str, Any]) -> Tuple[int, np.ndarray]:
        """
        Make prediction on a single feature dictionary.
        
        Args:
            feature_dict: Single feature dictionary from MongoDB
            
        Returns:
            Tuple of (predicted class, prediction probabilities)
        """
        predictions, probabilities = self.predict([feature_dict])
        return predictions[0], probabilities[0]
    
    def save_model(self):
        """Save the trained model and scaler."""
        if self.model is None:
            logger.warning("No model to save")
            return
        
        # Save XGBoost model
        self.model.save_model(self.model_save_path)
        logger.info(f"Model saved to {self.model_save_path}")
        
        # Save scaler
        scaler_path = self.model_save_path.replace('.json', '_scaler.pkl')
        joblib.dump(self.scaler, scaler_path)
        logger.info(f"Scaler saved to {scaler_path}")
        
        # Save feature columns
        features_path = self.model_save_path.replace('.json', '_features.json')
        with open(features_path, 'w') as f:
            json.dump(self.feature_columns, f)
        logger.info(f"Feature columns saved to {features_path}")
    
    def load_model(self) -> bool:
        """
        Load a trained model from disk.
        
        Returns:
            bool: True if loading successful, False otherwise
        """
        try:
            # Load XGBoost model
            if os.path.exists(self.model_save_path):
                self.model = xgb.Booster()
                self.model.load_model(self.model_save_path)
                logger.info(f"Model loaded from {self.model_save_path}")
            else:
                logger.warning(f"Model file not found: {self.model_save_path}")
                return False
            
            # Load scaler
            scaler_path = self.model_save_path.replace('.json', '_scaler.pkl')
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
                logger.info(f"Scaler loaded from {scaler_path}")
            else:
                logger.warning(f"Scaler file not found: {scaler_path}")
                return False
            
            # Load feature columns
            features_path = self.model_save_path.replace('.json', '_features.json')
            if os.path.exists(features_path):
                with open(features_path, 'r') as f:
                    self.feature_columns = json.load(f)
                logger.info(f"Feature columns loaded from {features_path}")
            else:
                logger.warning(f"Feature columns file not found: {features_path}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

# Global instance
xgb_trainer = XGBoostTrainer()