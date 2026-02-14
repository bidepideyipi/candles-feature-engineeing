"""
Prediction scheduler for running scheduled prediction tasks.
"""
import logging
import time
from datetime import datetime
from typing import Dict, Any

from models.xgboost_trainer import xgb_trainer
from feature.feature_merge import FeatureMerge
from utils.email_sender import email_sender
from collect.config_handler import config_handler
from config.settings import config

logger = logging.getLogger(__name__)


class PredictionScheduler:
    """Scheduled prediction task manager."""
    
    def __init__(self):
        self.interval_minutes = config.SCHEDULE_INTERVAL
        self.recipient = config.SCHEDULE_RECIPIENT
        self.from_local = False
    
    def check_prediction_confidence(self, prediction_data: Dict[str, Any], threshold: float = 0.6) -> bool:
        """
        Check if prediction confidence meets threshold.
        
        Args:
            prediction_data: Prediction data from predict_price_movement()
            threshold: Confidence threshold (default: 0.6 = 60%)
            
        Returns:
            bool: True if confidence meets threshold
        """
        try:
            prediction = prediction_data.get('prediction')
            probabilities = prediction_data.get('probabilities', {})
            
            if not prediction or not probabilities:
                logger.warning("Invalid prediction data")
                return False
            
            if prediction == 3:
                logger.info("Prediction is 3 (横盘-1.2% ~ 1.2%), confidence check skipped")
                return False
            
            confidence = probabilities.get(prediction, 0)
            logger.info(f"Prediction: {prediction}, Confidence: {confidence:.2%}, Threshold: {threshold:.0%}")
            
            if confidence < threshold:
                logger.info(f"Confidence {confidence:.2%} below threshold {threshold:.0%}, alert skipped")
                return False
            
            if prediction == 2:
                return probabilities.get(2, 0) - probabilities.get(4, 0) >= threshold
            if prediction == 4:
                return probabilities.get(4, 0) - probabilities.get(2, 0) >= threshold
            if prediction == 1:
                return probabilities.get(1, 0) - probabilities.get(5, 0) >= threshold
            if prediction == 5:
                return probabilities.get(5, 0) - probabilities.get(1, 0) >= threshold
            
        except Exception as e:
            logger.error(f"Error checking confidence: {e}", exc_info=True)
            return False
    
    def send_alert_email(self, prediction_data: Dict[str, Any]) -> bool:
        """
        Send email alert for high-confidence prediction.
        
        Args:
            prediction_data: Prediction data from predict_price_movement()
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            logger.info("Preparing to send email alert...")
            result = email_sender.send_trading_alert(
                to_email=self.recipient,
                prediction_data=prediction_data,
                confidence_threshold=0.6
            )
            
            if result:
                logger.info(f"Email alert sent to {self.recipient}")
            else:
                logger.warning(f"Email alert not sent (confidence below threshold or send failed)")
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending alert email: {e}", exc_info=True)
            return False
    
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
            
            feature_merge = FeatureMerge()
            if self.from_local:
                features = feature_merge.quick_process_eth_from_mongodb()
            else:
                features = feature_merge.quick_process_eth()
            
            if features is None:
                logger.error("Failed to extract features")
                return None
            
            prediction, probabilities = xgb_trainer.predict_single(features)
            
            class_labels = {
                1: "暴跌 (<-3.6%)",
                2: "下跌 (-3.6% ~ -1.2%)",
                3: "横盘 (-1.2% ~ 1.2%)",
                4: "上涨 (1.2% ~ 3.6%)",
                5: "暴涨 (>3.6%)"
            }
            
            prob_dict = {}
            for i, prob in enumerate(probabilities):
                class_num = i + 1
                prob_dict[class_num] = round(float(prob), 4)
            
            return {
                "timestamp": features.get("timestamp"),
                "prediction": int(prediction),
                "prediction_label": class_labels.get(prediction, f"类别 {prediction}"),
                "probabilities": prob_dict,
                "features_count": len(xgb_trainer.feature_columns),
                "inst_id": "ETH-USDT-SWAP"
            }
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return None
    
    def check_email_config(self) -> bool:
        """
        Check if email configuration is set up in MongoDB.
        
        Returns:
            bool: True if email configuration exists
        """
        try:
            smtp_config = config_handler.get_config_dict("smtp.qq.com")
            
            if not smtp_config:
                logger.error("Email configuration not found in MongoDB")
                logger.error("Please configure SMTP settings:")
                logger.error("  POST /config?item=smtp.qq.com&key=account&value=your_email@qq.com&desc=发件人邮箱")
                logger.error("  POST /config?item=smtp.qq.com&key=authCode&value=your_smtp_auth_code&desc=发件人邮箱授权码")
                return False
            
            required_keys = ['account', 'authCode']
            for key in required_keys:
                if key not in smtp_config:
                    logger.error(f"Missing email config key: {key}")
                    return False
            
            logger.info("Email configuration validated")
            return True
            
        except Exception as e:
            logger.error(f"Error checking email config: {e}")
            return False
    
    def run(self):
        """
        Run prediction cycle at configured interval.
        This function runs in a separate thread.
        """
        logger.info("Starting scheduled prediction service...")
        logger.info(f"Interval: {self.interval_minutes} minutes")
        logger.info(f"Alert recipient: {self.recipient}")
        logger.info(f"Data source: {'MongoDB' if self.from_local else 'API'}")
        logger.info(f"Confidence threshold: 60%")
        
        if not self.check_email_config():
            logger.warning("Email configuration not found, scheduled task will run but no alerts will be sent")
        
        cycle_count = 0
        while True:
            try:
                cycle_count += 1
                logger.info(f"=== Prediction cycle #{cycle_count} ===")
                logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Get prediction
                prediction_data = self.predict_price_movement()
                
                if prediction_data:
                    logger.info(f"Prediction completed:")
                    logger.info(f"  Prediction: {prediction_data.get('prediction_label')}")
                    logger.info(f"  Probabilities: {prediction_data.get('probabilities')}")
                    
                    # Check confidence and send email alert
                    try:
                        if self.check_prediction_confidence(prediction_data, threshold=0.6):
                            logger.info("Confidence meets threshold, sending email alert...")
                            self.send_alert_email(prediction_data)
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
