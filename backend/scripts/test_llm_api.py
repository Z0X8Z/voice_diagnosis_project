import os
import sys
import json
import httpx
from app.core.config import settings


def test_llm_api():
    api_key = os.getenv("OPENAI_API_KEY", settings.OPENAI_API_KEY)
    api_base = os.getenv("OPENAI_API_BASE", settings.OPENAI_API_BASE)
    model = os.getenv("OPENAI_MODEL", settings.OPENAI_MODEL)
    url = api_base.rstrip("/") + "/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": "你好，大模型连通性自动测试。请用一句话回复我。"}
        ]
    }
    print(f"\n测试地址: {url}")
    print(f"模型: {model}")
    print(f"Key前6位: {api_key[:6]}")
    try:
        resp = httpx.post(url, headers=headers, json=data, timeout=30)
        print(f"HTTP状态码: {resp.status_code}")
        print("响应内容:")
        print(resp.text)
        if resp.status_code == 200:
            try:
                result = resp.json()
                print("\n大模型API测试通过！返回内容摘要:")
                print(json.dumps(result["choices"][0]["message"], ensure_ascii=False, indent=2))
            except Exception as e:
                print(f"解析返回内容失败: {e}")
        else:
            print("大模型API测试未通过，请检查API Key、模型名、API地址和网络。")
    except Exception as e:
        print(f"请求过程中发生异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_llm_api() 