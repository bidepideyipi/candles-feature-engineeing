"""
测试实际的API端点
"""

import requests
import json

def test_merge_feature_api():
    """测试合并特征API"""
    
    print("=" * 60)
    print("测试 /fetch/3-merge-feature API")
    print("=" * 60)
    
    try:
        # 调用API
        url = "http://127.0.0.1:8000/fetch/3-merge-feature"
        params = {
            "limit": 10,  # 只处理10条来测试
            "before": None
        }
        
        print(f"调用API: {url}")
        print(f"参数: {params}")
        
        response = requests.get(url, params=params, timeout=60)
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✓ API调用成功")
            print(f"结果: {result}")
        else:
            print(f"✗ API调用失败: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("✗ 无法连接到API服务器，请确保服务器正在运行")
    except Exception as e:
        print(f"✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_merge_feature_api()