#!/usr/bin/env python3
"""
测试代理连接
"""
import sys
import os
import requests
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from config.settings import config

def test_proxy():
    """测试代理连接"""
    print("=" * 60)
    print("代理配置测试")
    print("=" * 60)
    print(f"\n配置信息:")
    print(f"  PROXY_ENABLED: {config.PROXY_ENABLED}")
    print(f"  PRODUCTION_MODE: {config.PRODUCTION_MODE}")
    print(f"  PROXY_HOST: {config.PROXY_HOST}")
    print(f"  PROXY_PORT: {config.PROXY_PORT}")
    print(f"  PROXY_URL: {config.PROXY_URL}")
    
    if config.PROXY_ENABLED and not config.PRODUCTION_MODE:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        proxy_dict = {
            'http': config.PROXY_URL,
            'https': config.PROXY_URL
        }
        print(f"\n✓ 代理已启用")
        print(f"  代理地址: {config.PROXY_URL}")
        print(f"  SSL 验证: 禁用（开发环境）")
    else:
        print(f"\n✗ 代理未启用")
        proxy_dict = None
    
    # 测试连接
    print(f"\n开始测试连接...")
    test_url = "https://www.okx.com/api/v5/public/time"
    
    try:
        print(f"  请求 URL: {test_url}")
        print(f"  使用代理: {'是' if proxy_dict else '否'}")
        if proxy_dict:
            print(f"  代理配置: {proxy_dict}")
        
        response = requests.get(
            test_url,
            proxies=proxy_dict,
            timeout=10,
            verify=False  # 禁用 SSL 验证
        )
        
        print(f"\n✓ 连接成功!")
        print(f"  状态码: {response.status_code}")
        print(f"  响应: {response.text[:200]}")
        return True
        
    except requests.exceptions.ProxyError as e:
        print(f"\n✗ 代理错误:")
        print(f"  {e}")
        return False
        
    except requests.exceptions.ConnectionError as e:
        print(f"\n✗ 连接错误:")
        print(f"  {e}")
        if proxy_dict:
            print(f"\n可能的原因:")
            print(f"  1. 代理服务器未运行")
            print(f"  2. 代理端口 {config.PROXY_PORT} 未开放")
            print(f"  3. 防火墙阻止连接")
        return False
        
    except Exception as e:
        print(f"\n✗ 未知错误:")
        print(f"  {e}")
        return False

if __name__ == "__main__":
    success = test_proxy()
    print("\n" + "=" * 60)
    sys.exit(0 if success else 1)