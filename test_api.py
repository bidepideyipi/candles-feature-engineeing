"""
Test script for the training data API endpoints.
"""

import requests
import json
import time

API_BASE_URL = "http://127.0.0.1:8000"

def test_health_endpoint():
    """Test the health check endpoint."""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Health check passed: {data}")
            return True
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check error: {e}")
        return False

def test_data_stats():
    """Test the data statistics endpoint."""
    print("\nTesting data stats endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/data-stats")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Data stats: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"✗ Data stats failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Data stats error: {e}")
        return False

def test_fetch_historical_data():
    """Test the fetch historical data endpoint."""
    print("\nTesting fetch historical data endpoint...")
    payload = {
        "max_records": 1000,
        "force_refresh": False
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/fetch-historical-data",
            json=payload
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Fetch historical data: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"✗ Fetch historical data failed: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"✗ Fetch historical data error: {e}")
        return False

def test_generate_training_data():
    """Test the generate training data endpoint."""
    print("\nTesting generate training data endpoint...")
    payload = {
        "max_records": 5000,
        "stride": 20,
        "prediction_horizon": 24,
        "force_refresh": False
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/generate-training-data",
            json=payload
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Generate training data started: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"✗ Generate training data failed: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"✗ Generate training data error: {e}")
        return False

def test_training_status():
    """Test the training status endpoint."""
    print("\nTesting training status endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/training-status")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Training status: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"✗ Training status failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Training status error: {e}")
        return False

def main():
    """Run all API tests."""
    print("=" * 50)
    print("TRAINING DATA API TESTS")
    print("=" * 50)
    
    # Test basic endpoints
    health_ok = test_health_endpoint()
    stats_ok = test_data_stats()
    
    if not health_ok:
        print("\n⚠ API server may not be running!")
        print("Start it with: python main.py api")
        return
    
    # Test data fetching
    fetch_ok = test_fetch_historical_data()
    
    # Test training data generation
    generate_ok = test_generate_training_data()
    
    # Check status
    if generate_ok:
        print("\nWaiting 5 seconds for background processing...")
        time.sleep(5)
        test_training_status()
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Health endpoint: {'✓' if health_ok else '✗'}")
    print(f"Data stats: {'✓' if stats_ok else '✗'}")
    print(f"Fetch historical data: {'✓' if fetch_ok else '✗'}")
    print(f"Generate training data: {'✓' if generate_ok else '✗'}")

if __name__ == "__main__":
    main()