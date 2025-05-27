import os
import json
import logging
import asyncio
import httpx
from typing import Dict, Any, Optional, List
import time
from datetime import datetime
from openai import AsyncOpenAI
from app.core.config import settings
# 暂时移除tenacity依赖
# from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# 配置日志
logger = logging.getLogger(__name__)

class LLMClient:
    """
    LLM客户端类，负责与OpenAI API通信
    """
    
    def __init__(self):
        """初始化LLM客户端"""
        # 从环境变量获取配置
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.timeout = int(os.getenv("LLM_API_TIMEOUT", "60"))
        self.max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        
        # 记录初始化信息
        logger.info(f"[LLMClient.__init__] 初始化LLM客户端: model={self.model}, base={self.api_base}")
        
        # 检查API密钥
        if not self.api_key:
            logger.warning("[LLMClient.__init__] 未设置API密钥，将使用模拟模式")
            self.use_mock = True
        else:
            logger.info("[LLMClient.__init__] API密钥已设置，将使用实际API")
            self.use_mock = False
    
    async def analyze(self, prompt: str) -> str:
        """
        使用LLM分析提示内容
        
        Args:
            prompt: 提示文本
            
        Returns:
            LLM生成的响应文本
        """
        start_time = time.time()
        logger.info(f"[LLMClient.analyze] 开始LLM分析: prompt_length={len(prompt)}")
        
        # 如果没有API密钥，使用模拟响应
        if self.use_mock:
            logger.warning("[LLMClient.analyze] 使用模拟模式")
            await asyncio.sleep(1)  # 模拟延迟
            result = f"这是一个模拟的LLM响应。实际使用时，请设置OPENAI_API_KEY环境变量。\n\n提示内容摘要: {prompt[:100]}..."
            duration_ms = int((time.time() - start_time) * 1000)
            logger.info(f"[LLMClient.analyze] 模拟模式返回结果: length={len(result)}, duration_ms={duration_ms}")
            return result
        
        # 实际API调用
        logger.info(f"[LLMClient.analyze] 准备API请求: model={self.model}, temperature={self.temperature}")
        
        # 构建请求数据
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是一个专业的医疗AI助手，专注于肺部健康分析和相关建议。请给出专业、准确的分析和建议。"},
                        {"role": "user", "content": prompt}
                    ],
            "temperature": self.temperature,
            "max_tokens": 2000
        }
        
        # 记录请求开始
        logger.info(f"[LLMClient.analyze] 发送API请求: endpoint={self.api_base}/chat/completions")
        
        # 尝试调用API，支持重试
        response_text = ""
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
                    }
                    
                    response = await client.post(
                        f"{self.api_base}/chat/completions",
                        headers=headers,
                        json=data
                    )
                    
                    # 检查响应状态
                    if response.status_code != 200:
                        logger.error(f"[LLMClient.analyze] API请求失败: status_code={response.status_code}, response={response.text}")
                        if attempt < self.max_retries - 1:
                            retry_delay = 2 ** attempt  # 指数退避
                            logger.info(f"[LLMClient.analyze] 将在{retry_delay}秒后重试, 尝试次数: {attempt+1}/{self.max_retries}")
                            await asyncio.sleep(retry_delay)
                            continue
                        else:
                            raise Exception(f"API请求失败，状态码: {response.status_code}，响应: {response.text}")
                    
                    # 解析响应
                    resp_json = response.json()
                    response_text = resp_json["choices"][0]["message"]["content"]
                    
                    # 记录响应信息
                    duration_ms = int((time.time() - start_time) * 1000)
                    tokens_used = resp_json.get("usage", {}).get("total_tokens", 0)
                    logger.info(f"[LLMClient.analyze] API请求成功: length={len(response_text)}, tokens={tokens_used}, duration_ms={duration_ms}")
                    
                    # 成功获取响应，退出重试循环
                    break
                    
            except Exception as e:
                logger.error(f"[LLMClient.analyze] API请求异常: {str(e)}", exc_info=True)
                if attempt < self.max_retries - 1:
                    retry_delay = 2 ** attempt  # 指数退避
                    logger.info(f"[LLMClient.analyze] 将在{retry_delay}秒后重试, 尝试次数: {attempt+1}/{self.max_retries}")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"[LLMClient.analyze] 达到最大重试次数，请求失败")
                    raise Exception(f"LLM分析失败: {str(e)}")
        
        return response_text
    
    def _build_analysis_prompt(self, voice_metrics: Dict[str, Any]) -> str:
        """
        构建分析提示词
        
        Args:
            voice_metrics: 语音指标数据
            
        Returns:
            构建好的提示词
        """
        prompt = f"""
        请分析以下语音指标数据，并给出健康建议：
        
        预测结果: {voice_metrics.get('model_prediction')}
        置信度: {voice_metrics.get('model_confidence')}
        
        语音特征:
        - MFCC: {voice_metrics.get('features', {}).get('mfcc')}
        - Chroma: {voice_metrics.get('features', {}).get('chroma')}
        - RMS: {voice_metrics.get('features', {}).get('rms')}
        - ZCR: {voice_metrics.get('features', {}).get('zcr')}
        
        请根据以上数据，给出：
        1. 健康状况评估
        2. 可能的原因分析
        3. 改善建议
        4. 是否需要就医
        """
        
        return prompt 