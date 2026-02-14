#!/usr/bin/env python3
"""
Simple unit test for email sending functionality.
Tests SMTP configuration and email sending using MongoDB config.
"""

import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from collect.config_handler import config_handler
from utils.email_sender import EmailSender
from config.settings import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def test_smtp_config():
    """Test 1: Check if SMTP configuration exists in MongoDB."""
    print("=" * 60)
    print("Test 1: Check SMTP Configuration")
    print("=" * 60)
    
    smtp_config = config_handler.get_config_dict("smtp.qq.com")
    
    if not smtp_config:
        print("❌ FAILED: SMTP configuration not found")
        print("Please run:")
        print('  curl -X POST "http://localhost:8000/config?item=smtp.qq.com&key=account&value=your_email@qq.com&desc=发件人邮箱"')
        print('  curl -X POST "http://localhost:8000/config?item=smtp.qq.com&key=authCode&value=your_auth_code&desc=发件人邮箱授权码"')
        return False
    
    print("✓ SMTP Configuration found:")
    for key, value in smtp_config.items():
        if key == 'authCode':
            print(f"  {key}: {'*' * len(value)} (hidden)")
        else:
            print(f"  {key}: {value}")
    
    # Check required keys
    required_keys = ['account', 'authCode']
    missing_keys = [key for key in required_keys if key not in smtp_config]
    
    if missing_keys:
        print(f"❌ FAILED: Missing required keys: {missing_keys}")
        return False
    
    print("✓ All required keys present")
    return True


def test_email_sender_init():
    """Test 2: Initialize EmailSender with MongoDB config."""
    print("\n" + "=" * 60)
    print("Test 2: Initialize EmailSender")
    print("=" * 60)
    
    try:
        email_sender = EmailSender(smtp_item="smtp.qq.com")
        
        if not email_sender.smtp_config:
            print("❌ FAILED: Could not load SMTP config")
            return False
        
        print("✓ EmailSender initialized successfully")
        print(f"  Account: {email_sender.smtp_config.get('account')}")
        print(f"  Host: {email_sender.smtp_config.get('host', 'smtp.qq.com')}")
        print(f"  Port: {email_sender.smtp_config.get('port', '587')}")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_send_simple_email():
    """Test 3: Send a simple test email."""
    print("\n" + "=" * 60)
    print("Test 3: Send Simple Test Email")
    print("=" * 60)
    
    try:
        email_sender = EmailSender(smtp_item="smtp.qq.com")
        
        result = email_sender.send_email(
            to_email="284160266@qq.com",
            subject="技术分析助手 - 邮件发送测试",
            content="""
            <h2>邮件发送测试</h2>
            <p>这是一封来自技术分析助手的测试邮件。</p>
            <p><strong>测试时间:</strong> {email_sender.get_current_time()}</p>
            <hr>
            <p><small>如果您收到此邮件，说明邮件配置正常。</small></p>
            """,
            is_html=True
        )
        
        if result:
            print("✓ SUCCESS: Test email sent successfully")
            print("  Please check your inbox: 284160266@qq.com")
            return True
        else:
            print("❌ FAILED: Email send returned False")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_send_trading_alert():
    """Test 4: Send a simulated trading alert."""
    print("\n" + "=" * 60)
    print("Test 4: Send Trading Alert")
    print("=" * 60)
    
    try:
        email_sender = EmailSender(smtp_item="smtp.qq.com")
        
        # Simulate prediction data
        prediction_data = {
            "timestamp": 1739520000000,  # 2026-02-14
            "prediction": 5,
            "prediction_label": "暴涨 (>3.6%)",
            "probabilities": {
                "1": 0.05,
                "2": 0.10,
                "3": 0.15,
                "4": 0.20,
                "5": 0.50  # 50% confidence
            }
        }
        
        result = email_sender.send_trading_alert(
            to_email="284160266@qq.com",
            prediction_data=prediction_data,
            confidence_threshold=0.4  # Lower threshold for testing
        )
        
        if result:
            print("✓ SUCCESS: Trading alert sent successfully")
            print(f"  Prediction: {prediction_data['prediction_label']}")
            print(f"  Confidence: {prediction_data['probabilities']['5']:.1%}")
            return True
        else:
            print("❌ FAILED: Trading alert send returned False")
            print("  This usually means confidence is below threshold")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_send_low_confidence():
    """Test 5: Test low confidence alert (should not send)."""
    print("\n" + "=" * 60)
    print("Test 5: Send Low Confidence Alert (Should Not Send)")
    print("=" * 60)
    
    try:
        email_sender = EmailSender(smtp_item="smtp.qq.com")
        
        # Simulate prediction data with low confidence
        prediction_data = {
            "timestamp": 1739520000000,
            "prediction": 3,
            "prediction_label": "横盘 (-1.2% ~ 1.2%)",
            "probabilities": {
                "1": 0.20,
                "2": 0.25,
                "3": 0.30,  # 30% confidence - below threshold
                "4": 0.15,
                "5": 0.10
            }
        }
        
        result = email_sender.send_trading_alert(
            to_email="284160266@qq.com",
            prediction_data=prediction_data,
            confidence_threshold=0.6  # 60% threshold
        )
        
        if not result:
            print("✓ SUCCESS: Low confidence alert correctly blocked")
            print(f"  Prediction: {prediction_data['prediction_label']}")
            print(f"  Confidence: {prediction_data['probabilities']['3']:.1%} (below 60% threshold)")
            return True
        else:
            print("❌ FAILED: Low confidence alert was sent (should be blocked)")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all email sender tests."""
    print("\n" + "=" * 60)
    print("技术分析助手 - 邮件发送单元测试")
    print("=" * 60)
    print(f"MongoDB URI: {config.MONGODB_URI}")
    print(f"MongoDB Database: {config.MONGODB_DATABASE}")
    print(f"Production Mode: {config.PRODUCTION_MODE}")
    print("=" * 60 + "\n")
    
    tests = [
        ("Test 1: SMTP Configuration", test_smtp_config),
        ("Test 2: EmailSender Init", test_email_sender_init),
        ("Test 3: Simple Email", test_send_simple_email),
        ("Test 4: Trading Alert", test_send_trading_alert),
        ("Test 5: Low Confidence", test_send_low_confidence),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ EXCEPTION in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！邮件配置正常工作。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查配置。")
        return 1


if __name__ == '__main__':
    sys.exit(main())
