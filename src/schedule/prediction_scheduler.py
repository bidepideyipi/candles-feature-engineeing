"""
Prediction scheduler for running scheduled prediction tasks.
"""
import logging
import time
from datetime import datetime
from typing import Dict, Any

from models.xgboost_trainer import xgb_trainer,xgb_trainer_high,xgb_trainer_low
from feature.feature_merge import FeatureMerge
from utils.email_sender import email_sender
from collect.config_handler import config_handler
from config.settings import config
from collect.feature_prediction_handler import feature_pr_handler

logger = logging.getLogger(__name__)


class PredictionScheduler:
    """Scheduled prediction task manager."""
    
    def __init__(self):
        self.interval_minutes = config.SCHEDULE_INTERVAL
        self.recipient = config.SCHEDULE_RECIPIENT
        self.from_local = False
    
    # def check_prediction_confidence(self, prediction_data: Dict[str, Any], threshold: float = 0.6) -> bool:
    #     """
    #     Check if prediction confidence meets threshold.
        
    #     Args:
    #         prediction_data: Prediction data from predict_price_movement()
    #         threshold: Confidence threshold (default: 0.6 = 60%)
            
    #     Returns:
    #         bool: True if confidence meets threshold
    #     """
    #     try:
    #         prediction = prediction_data.get('prediction')
    #         probabilities = prediction_data.get('probabilities', {})
            
    #         if not prediction or not probabilities:
    #             logger.warning("Invalid prediction data")
    #             return False
            
    #         if prediction == 3:
    #             logger.info("Prediction is 3 (横盘-1.2% ~ 1.2%), confidence check skipped")
    #             return False
            
    #         confidence = probabilities.get(prediction, 0)
    #         logger.info(f"Prediction: {prediction}, Confidence: {confidence:.2%}, Threshold: {threshold:.0%}")
            
    #         if confidence < threshold:
    #             logger.info(f"Confidence {confidence:.2%} below threshold {threshold:.0%}, alert skipped")
    #             return False
            
    #         return True
            
    #     except Exception as e:
    #         logger.error(f"Error checking confidence: {e}", exc_info=True)
    #         return False
    
    def predict_price_movement(self) -> Dict[str, Any]:
        """
        Predict price movement and return prediction data.
        
        Returns:
            Prediction data dictionary
        """
        try:
            if not xgb_trainer.load_model():
                logger.error("Failed to load model")
                return None
            
            if not xgb_trainer_high.load_model():
                logger.error("Failed to load model high")
                return None
            
            if not xgb_trainer_low.load_model():
                logger.error("Failed to load model low")
                return None
            
            feature_merge = FeatureMerge()
            if self.from_local:
                features = feature_merge.quick_process_eth_from_mongodb()
            else:
                features = feature_merge.quick_process_eth()
            
            if features is None:
                logger.error("Failed to extract features")
                return None
            
            # 保存特征数据到MongoDB
            current_ts = int(datetime.now().timestamp() * 1000)
            feature_pr_handler.save_feature(features, current_ts)
            
            # 进行预测
            
            prediction, probabilities = xgb_trainer.predict_single(features)
            class_labels = config.CLASSIFICATION_THRESHOLDS_DESC
            prob_dict = {}
            for i, prob in enumerate(probabilities):
                class_num = i + 1
                prob_dict[class_num] = round(float(prob), 4)
                
            prediction_high, probabilities_high = xgb_trainer_high.predict_single(features)
            class_labels_high = config.CLASSIFICATION_THRESHOLDS_HIGH_DESC
            prob_dict_high = {}
            for i, prob in enumerate(probabilities_high):
                class_num = i + 1
                prob_dict_high[class_num] = round(float(prob), 4)
            
            prediction_low, probabilities_low = xgb_trainer_low.predict_single(features)
            class_labels_low = config.CLASSIFICATION_THRESHOLDS_LOW_DESC
            prob_dict_low = {}
            for i, prob in enumerate(probabilities_low):
                class_num = i + 1
                prob_dict_low[class_num] = round(float(prob), 4)
            
            prediction_result = {
                "timestamp": features.get("timestamp"),
                "prediction": int(prediction),
                "prediction_label": class_labels.get(prediction, f"类别 {prediction}"),
                "prediction_high": int(prediction_high),
                "prediction_high_label": class_labels_high.get(prediction_high, f"类别 {prediction_high}"),
                "prediction_low": int(prediction_low),
                "prediction_low_label": class_labels_low.get(prediction_low, f"类别 {prediction_low}"),
                "probabilities": prob_dict,
                "probabilities_high": prob_dict_high,
                "probabilities_low": prob_dict_low,
                "features_count": len(xgb_trainer.feature_columns),
                "inst_id": "ETH-USDT-SWAP",
                "bar": "1H"
            }
            
            feature_pr_handler.update_feature_prediction_label(
                inst_id="ETH-USDT-SWAP",
                timestamp=current_ts,
                label=prediction_result.get("prediction"),
                label_high=prediction_result.get("prediction_high"),
                label_low=prediction_result.get("prediction_low")
            );
            
            return prediction_result
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return None
    
    def run(self):
        """
        >>>...主入口...<<<
        Run prediction cycle at configured interval.
        This function runs in a separate thread.
        """
        logger.info(f"Starting scheduled prediction service, Interval: {self.interval_minutes} minutes")
        logger.info(f"Alert recipient: {self.recipient}, Data source: {'MongoDB' if self.from_local else 'API'}")
              
        cycle_count = 0
        while True:
            try:
                cycle_count += 1
                logger.info(f"=== Prediction cycle #{cycle_count} ===")
                logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Get prediction
                # 进行预测
                prediction_data = self.predict_price_movement()
                
                if prediction_data:
                    logger.info(f"Prediction completed:")
                    logger.info(f"  Prediction: {prediction_data.get('prediction_label')}")
                    logger.info(f"  Probabilities: {prediction_data.get('probabilities')}")
                    
                    # Check confidence and send email alert
                    try:
                        if prediction_data.get('probabilities_high').get(prediction_data.get('prediction_high')) >= 0.75 or prediction_data.get('probabilities_low').get(prediction_data.get('prediction_low')) >= 0.75:
                            logger.info("Confidence meets threshold, sending email alert...")
                            email_sender.send_trading_alert(
                                to_email=self.recipient,
                                prediction_data=prediction_data
                            )
                        else:
                            logger.info("Confidence below threshold, no email sent")
                    except Exception as e:
                        logger.error(f"Error in confidence check or email sending: {e}", exc_info=True)
                else:
                    logger.error("Prediction failed")
                
                logger.info(f"=== Cycle #{cycle_count} completed ===")
                logger.info(f"Waiting {self.interval_minutes} minutes until next cycle...")
                logger.info("")
                
                # Wait for next cycle
                time.sleep(self.interval_minutes * 60)
                
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, shutting down scheduled task...")
                break
            except Exception as e:
                logger.error(f"Error in prediction cycle: {e}", exc_info=True)
                logger.info(f"Retrying in {self.interval_minutes} minutes...")
                try:
                    time.sleep(self.interval_minutes * 60)
                except KeyboardInterrupt:
                    logger.info("Received keyboard interrupt during retry wait, shutting down...")
                    break
        
        logger.info("Scheduled prediction task stopped")


# Global instance
prediction_scheduler = PredictionScheduler()
