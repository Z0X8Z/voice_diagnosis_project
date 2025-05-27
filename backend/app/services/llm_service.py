import json
import logging
import httpx
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
import time
from sqlalchemy.orm import Session
from app.db.models import VoiceMetrics, DiagnosisSession
from fastapi import HTTPException

from app.repositories.llm_repository import LLMRepository
from app.core.llm import LLMClient
from app.core.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMService:
    """
    大型语言模型(LLM)服务类
    负责与外部LLM API通信，处理语音分析请求和问答功能
    """
    
    def __init__(self, db: Session):
        """
        初始化LLM服务
        """
        self.repository = LLMRepository(db)
        self.llm_client = LLMClient()
        # 优先从settings读取，如果环境变量有覆盖则用环境变量
        self.api_key = os.getenv("OPENAI_API_KEY", settings.OPENAI_API_KEY)
        self.api_endpoint = os.getenv("OPENAI_API_BASE", settings.OPENAI_API_BASE)
        self.model_name = os.getenv("OPENAI_MODEL", settings.OPENAI_MODEL)
        self.timeout = int(os.getenv("LLM_API_TIMEOUT", "60"))
        
        # 检查API密钥
        if not self.api_key:
            logger.warning("LLM API密钥未设置，将使用模拟响应")
            self.use_mock = True
        else:
            self.use_mock = False
            
        logger.info(f"LLM服务初始化完成，使用模型: {self.model_name}")
    
    async def analyze_session(
        self,
        session_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """分析诊断会话"""
        try:
            # 获取会话信息
            session = self.repository.get_session_by_id(session_id, user_id)
            if not session:
                raise HTTPException(
                    status_code=404,
                    detail="诊断会话不存在"
                )
            
            # 获取语音指标
            voice_metrics = self.repository.get_voice_metrics(session_id)
            if not voice_metrics:
                raise HTTPException(
                    status_code=404,
                    detail="语音指标不存在"
                )
            
            # 获取历史对话
            conversation_history = self.repository.get_conversation_history(session_id)
            
            # 构建提示词
            prompt = self._build_analysis_prompt(voice_metrics, conversation_history)
            
            # 调用 LLM 进行分析
            analysis_result = await self.llm_client.analyze(prompt)
            
            # 保存分析结果
            self.repository.update_session_llm_suggestion(session_id, analysis_result)
            
            # 创建新的对话记录
            self.repository.create_conversation(
                session_id=session_id,
                role="assistant",
                content=analysis_result
            )
            
            return {
                "session_id": session_id,
                "analysis": analysis_result,
                "timestamp": session.llm_processed_at
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"分析会话失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"分析失败: {str(e)}"
            )
    
    async def handle_follow_up(
        self,
        session_id: int,
        user_id: int,
        question: str
    ) -> Dict[str, Any]:
        """处理后续问题"""
        try:
            logger.info(f"[handle_follow_up] 开始处理用户问题: session_id={session_id}, user_id={user_id}")
            logger.info(f"[handle_follow_up] 用户问题: {question}")
            
            # 获取会话信息
            session = self.repository.get_session_by_id(session_id, user_id)
            if not session:
                logger.error(f"[handle_follow_up] 诊断会话不存在: session_id={session_id}, user_id={user_id}")
                raise HTTPException(
                    status_code=404,
                    detail="诊断会话不存在"
                )
            
            # 获取对话历史
            conversation_history = self.repository.get_conversation_history(session_id)
            logger.info(f"[handle_follow_up] 获取到的对话历史数量: {len(conversation_history)}")
            
            # 保存用户问题
            conversation_history.append({
                "role": "user",
                "content": question,
                "created_at": datetime.utcnow().isoformat()
            })
            
            # 构建提示词
            prompt = self._build_follow_up_prompt(question, conversation_history)
            logger.info(f"[handle_follow_up] 构建的提示词长度: {len(prompt)}")
            
            # 调用 LLM 处理问题
            logger.info(f"[handle_follow_up] 开始调用LLM分析: session_id={session_id}")
            response = await self.llm_client.analyze(prompt)
            logger.info(f"[handle_follow_up] LLM返回的回答长度: {len(response)}")
            
            # 保存 LLM 回答
            conversation_history.append({
                "role": "assistant",
                "content": response,
                "created_at": datetime.utcnow().isoformat()
            })
            
            # 保存整个对话历史
            self.repository.save_conversation(session_id, conversation_history)
            logger.info(f"[handle_follow_up] 对话历史已保存: session_id={session_id}, 总消息数={len(conversation_history)}")
            
            return {
                "session_id": session_id,
                "question": question,
                "response": response,
                "conversation_history": conversation_history
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[handle_follow_up] 处理问题失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"处理失败: {str(e)}"
            )
    
    async def get_conversation_history(
        self,
        session_id: int,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """获取对话历史"""
        try:
            # 验证会话所有权
            session = self.repository.get_session_by_id(session_id, user_id)
            if not session:
                raise HTTPException(
                    status_code=404,
                    detail="诊断会话不存在"
                )
            
            # 获取对话历史
            conversations = self.repository.get_conversation_history(session_id)
            
            return [
                {
                    "role": conv.role,
                    "content": conv.content,
                    "timestamp": conv.created_at
                }
                for conv in conversations
            ]
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取对话历史失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"获取失败: {str(e)}"
            )
    
    async def get_latest_suggestion(
        self,
        session_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """获取最新的 LLM 建议"""
        try:
            # 验证会话所有权
            session = self.repository.get_session_by_id(session_id, user_id)
            if not session:
                raise HTTPException(
                    status_code=404,
                    detail="诊断会话不存在"
                )
            
            return {
                "session_id": session_id,
                "suggestion": session.llm_suggestion,
                "timestamp": session.llm_processed_at
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取最新建议失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"获取失败: {str(e)}"
            )
    
    async def get_analysis_history(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取分析历史"""
        try:
            return self.repository.get_analysis_history(user_id, skip, limit)
        except Exception as e:
            logger.error(f"获取分析历史失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"获取失败: {str(e)}"
            )
    
    async def get_display_summary(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """获取用于显示的摘要数据"""
        try:
            return self.repository.get_display_summary(user_id)
        except Exception as e:
            logger.error(f"获取显示摘要失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"获取失败: {str(e)}"
            )
    
    async def get_realtime_data(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """获取实时监控数据"""
        try:
            return self.repository.get_realtime_data(user_id)
        except Exception as e:
            logger.error(f"获取实时数据失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"获取失败: {str(e)}"
            )
    
    def _build_analysis_prompt(
        self,
        voice_metrics: VoiceMetrics,
        history_suggestions: list = None
    ) -> str:
        """构建分析提示词，包含当前语音指标和历史诊断建议"""
        prompt = f"""
请分析以下语音指标数据，并结合用户过往的诊断建议，给出本次健康分析：\n
当前语音指标：
- 预测结果: {voice_metrics.model_prediction}
- 置信度: {voice_metrics.model_confidence}
- MFCC: {[getattr(voice_metrics, f'mfcc_{i}') for i in range(1, 14)]}
- Chroma: {[getattr(voice_metrics, f'chroma_{i}') for i in range(1, 13)]}
- RMS: {voice_metrics.rms}
- ZCR: {voice_metrics.zcr}
- Mel Spectrogram: {voice_metrics.mel_spectrogram}
"""
        if history_suggestions:
            prompt += "\n历史诊断建议：\n"
            for idx, item in enumerate(history_suggestions, 1):
                prompt += f"{idx}. {item}\n"
        prompt += "\n请结合上述信息，给出本次健康状况评估、原因分析、改善建议和是否需要就医。"
        return prompt
    
    def _build_follow_up_prompt(
        self,
        question: str,
        conversation_history: list
    ) -> str:
        """构建后续问题提示词"""
        # 构建对话历史文本
        history_text = ""
        for item in conversation_history:
            if item["role"] == "assistant":
                history_text += f"医疗助手: {item['content']}\n\n"
            elif item["role"] == "user":
                history_text += f"用户: {item['content']}\n\n"
        
        # 构建提示词
        prompt = f"""
你是一个专业的医疗AI助手，专注于肺部健康分析。
请根据以下对话历史和用户的新问题，给出有见地的回答。

### 对话历史:
{history_text}

### 用户新问题:
{question}

请提供专业、易懂的回答。如果问题超出你的专业范围，请建议用户咨询专业医生。
"""
        return prompt
    
    async def analyze_voice_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用LLM分析语音数据
        
        Args:
            input_data: 包含用户信息和语音指标的字典
            
        Returns:
            LLM分析结果的字典
        """
        logger.info(f"开始LLM语音分析，用户ID: {input_data.get('user_id')}")
        
        start_time = time.time()
        
        # 如果设置为模拟模式或API调用失败，使用模拟响应
        if self.use_mock:
            response = self._mock_voice_analysis(input_data)
            response["response_time_ms"] = int((time.time() - start_time) * 1000)
            return response
        
        try:
            # 构建提示
            prompt = self._build_voice_analysis_prompt(input_data)
            
            # 调用LLM API
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_endpoint,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model_name,
                        "messages": [
                            {"role": "system", "content": "你是一个医疗AI助手，专注于分析语音特征以检测肺部健康问题。你的分析应基于提供的语音指标数据。"},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 1000
                    }
                )
                
                # 检查响应
                if response.status_code != 200:
                    logger.error(f"LLM API调用失败: {response.status_code} - {response.text}")
                    return self._mock_voice_analysis(input_data)
                
                # 解析LLM响应
                llm_response = response.json()
                content = llm_response["choices"][0]["message"]["content"]
                
                # 将LLM响应解析为结构化数据
                try:
                    # 尝试直接解析JSON
                    result = json.loads(content)
                except json.JSONDecodeError:
                    # 如果不是JSON格式，进行手动解析
                    result = self._parse_llm_text_response(content)
                
                result["response_time_ms"] = int((time.time() - start_time) * 1000)
                return result
                
        except Exception as e:
            logger.error(f"LLM分析过程中发生错误: {str(e)}")
            # 出错时返回模拟响应
            response = self._mock_voice_analysis(input_data)
            response["response_time_ms"] = int((time.time() - start_time) * 1000)
            return response
    
    async def answer_followup_question(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理用户的后续问题
        
        Args:
            input_data: 包含用户问题、对话历史和上下文的字典
            
        Returns:
            包含LLM回答的字典
        """
        logger.info(f"处理后续问题，用户ID: {input_data.get('user_id')}")
        
        start_time = time.time()
        
        # 如果设置为模拟模式或API调用失败，使用模拟响应
        if self.use_mock:
            response = self._mock_followup_answer(input_data)
            response["response_time_ms"] = int((time.time() - start_time) * 1000)
            return response
            
        try:
            # 构建消息历史
            messages = [
                {"role": "system", "content": "你是一个医疗AI助手，专注于回答关于肺部健康和语音分析的问题。基于之前的诊断结果提供有见地的回答。"},
            ]
            
            # 添加先前分析
            if "previous_analysis" in input_data and input_data["previous_analysis"]:
                messages.append({
                    "role": "assistant", 
                    "content": f"基于您的语音数据分析，我之前的诊断结果是：{input_data['previous_analysis']}"
                })
            
            # 添加对话历史
            if "conversation_history" in input_data and input_data["conversation_history"]:
                for item in input_data["conversation_history"]:
                    messages.append({"role": "user", "content": item["question"]})
                    messages.append({"role": "assistant", "content": item["answer"]})
            
            # 添加当前问题
            messages.append({"role": "user", "content": input_data["question"]})
            
            # 调用LLM API
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_endpoint,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model_name,
                        "messages": messages,
                        "temperature": 0.5,
                        "max_tokens": 800
                    }
                )
                
                # 检查响应
                if response.status_code != 200:
                    logger.error(f"LLM API调用失败: {response.status_code} - {response.text}")
                    return self._mock_followup_answer(input_data)
                
                # 解析LLM响应
                llm_response = response.json()
                content = llm_response["choices"][0]["message"]["content"]
                
                result = {
                    "answer": content,
                    "response_time_ms": int((time.time() - start_time) * 1000),
                    "source_references": []  # 实际应用中，可以从LLM响应中提取或从知识库中关联
                }
                
                return result
                
        except Exception as e:
            logger.error(f"处理后续问题时发生错误: {str(e)}")
            # 出错时返回模拟响应
            response = self._mock_followup_answer(input_data)
            response["response_time_ms"] = int((time.time() - start_time) * 1000)
            return response
    
    def _build_voice_analysis_prompt(self, input_data: Dict[str, Any]) -> str:
        """构建用于语音分析的提示"""
        metrics = input_data.get("voice_metrics", {})
        user_info = {
            "user_id": input_data.get("user_id", "未知"),
            "username": input_data.get("username", "用户"),
            "age": input_data.get("age", "未知"),
            "gender": input_data.get("gender", "未知")
        }
        
        prompt = f"""
请分析以下语音指标数据，评估用户的肺部健康状况:

用户信息:
- ID: {user_info['user_id']}
- 姓名: {user_info['username']}
- 年龄: {user_info['age']}
- 性别: {user_info['gender']}

语音指标:
- 基频(F0): {metrics.get('f0', '未提供')} Hz
- 谐噪比(HNR): {metrics.get('hnr', '未提供')} dB
- 短时能量: {metrics.get('short_time_energy', '未提供')}
- 过零率: {metrics.get('zero_crossing_rate', '未提供')}
- 频谱质心: {metrics.get('spectral_centroid', '未提供')} Hz
- 模型预测: {metrics.get('prediction', '未提供')}
- 置信度: {metrics.get('confidence', '未提供')}

请提供以下格式的JSON响应:
{{
  "summary": "简明的一段话总结分析结果",
  "detailed_explanation": "更详细的解释，包括各项指标的分析",
  "health_status": "健康状态评估",
  "confidence_level": "分析的置信度(0-1)",
  "recommendations": ["建议1", "建议2", "..."],
  "follow_up_suggestions": ["建议关注的方面1", "可以进一步探讨的问题2"]
}}
"""
        return prompt
    
    def _parse_llm_text_response(self, text: str) -> Dict[str, Any]:
        """
        解析非JSON格式的LLM文本响应
        """
        # 基本结构
        result = {
            "summary": "",
            "detailed_explanation": "",
            "health_status": "未确定",
            "confidence_level": 0.5,
            "recommendations": [],
            "follow_up_suggestions": []
        }
        
        # 尝试从文本中提取各部分
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
                
            # 检测章节头
            if "总结" in line or "摘要" in line or "summary" in line.lower():
                current_section = "summary"
                continue
            elif "详细" in line or "解释" in line or "explanation" in line.lower():
                current_section = "detailed_explanation"
                continue
            elif "健康状态" in line or "状况" in line or "health" in line.lower() and "status" in line.lower():
                current_section = "health_status"
                continue
            elif "置信" in line or "信心" in line or "confidence" in line.lower():
                current_section = "confidence_level"
                continue
            elif "建议" in line or "推荐" in line or "recommendation" in line.lower():
                current_section = "recommendations"
                continue
            elif "后续" in line or "进一步" in line or "follow" in line.lower() and "up" in line.lower():
                current_section = "follow_up_suggestions"
                continue
            
            # 根据当前章节添加内容
            if current_section == "summary":
                result["summary"] += line + " "
            elif current_section == "detailed_explanation":
                result["detailed_explanation"] += line + " "
            elif current_section == "health_status":
                result["health_status"] = line
            elif current_section == "confidence_level":
                try:
                    confidence = float(line.split("：")[-1].strip())
                    result["confidence_level"] = confidence
                except:
                    pass
            elif current_section == "recommendations":
                if line.startswith("-") or line.startswith("*"):
                    result["recommendations"].append(line[1:].strip())
                else:
                    result["recommendations"].append(line)
            elif current_section == "follow_up_suggestions":
                if line.startswith("-") or line.startswith("*"):
                    result["follow_up_suggestions"].append(line[1:].strip())
                else:
                    result["follow_up_suggestions"].append(line)
        
        # 清理结果
        result["summary"] = result["summary"].strip()
        result["detailed_explanation"] = result["detailed_explanation"].strip()
        
        return result
    
    def _mock_voice_analysis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成模拟的语音分析响应"""
        metrics = input_data.get("voice_metrics", {})
        prediction = metrics.get("prediction", "正常")
        
        if prediction == "正常" or prediction == "健康":
            return {
                "summary": "基于语音分析，您的肺部状况良好。声音特征显示正常的肺部功能，无异常。",
                "detailed_explanation": "您的语音指标在正常范围内，包括基频、谐噪比和短时能量等关键指标都表现良好。这些指标反映了您的呼吸系统功能正常，气流通畅，声带振动规律。",
                "health_status": "健康",
                "confidence_level": 0.92,
                "recommendations": [
                    "保持健康的生活方式",
                    "定期进行身体检查",
                    "避免长时间处于空气污染环境"
                ],
                "follow_up_suggestions": [
                    "如何通过锻炼提高肺活量？",
                    "日常生活中如何保护呼吸系统健康？",
                    "哪些因素可能影响语音健康指标？"
                ]
            }
        else:
            return {
                "summary": "您的语音分析结果显示可能存在一些呼吸系统方面的异常。建议您咨询专业医生进行进一步的诊断。",
                "detailed_explanation": "我注意到您的谐噪比和频谱质心指标与正常值有一定差异，这可能与呼吸道炎症或其他肺部问题相关。声音参数的变化反映了气流通过声带和声道时的异常模式。",
                "health_status": "异常",
                "confidence_level": 0.85,
                "recommendations": [
                    "建议咨询呼吸科医生进行专业评估",
                    "考虑进行肺功能测试以获得更准确的诊断",
                    "避免刺激性环境（如烟雾、粉尘等）",
                    "注意休息，避免声带过度使用"
                ],
                "follow_up_suggestions": [
                    "我的症状可能与哪些疾病相关？",
                    "在就医前我应该注意什么？",
                    "如何改善我的呼吸质量？"
                ]
            }
    
    def _mock_followup_answer(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成模拟的后续问题回答"""
        question = input_data.get("question", "")
        
        # 根据问题类型生成不同的回答
        if "锻炼" in question or "肺活量" in question:
            answer = "提高肺活量的有效锻炼包括：有氧运动（如慢跑、游泳和骑自行车）、呼吸训练（深呼吸练习和吹气球）、瑜伽和普拉提等。保持规律性是关键，建议每周至少进行3-4次，每次30分钟以上的有氧运动。游泳特别有效，因为它结合了有氧运动和呼吸控制。"
        elif "保护" in question or "呼吸系统" in question:
            answer = "保护呼吸系统健康的方法包括：避免吸烟和二手烟环境；减少接触空气污染物；在污染严重时佩戴适当的口罩；保持室内空气流通；定期清洁空调和加湿器；保持良好的个人卫生习惯；接种肺炎和流感疫苗；规律锻炼增强肺功能；保持充分水分，帮助稀释呼吸道粘液。"
        elif "因素" in question or "影响" in question:
            answer = "影响语音健康指标的因素很多，主要包括：呼吸系统疾病（如感冒、哮喘、肺炎等）；声带相关问题（如声带小结、声带麻痹）；过度使用声音导致疲劳；空气污染和刺激物；过敏反应；情绪状态（紧张会影响呼吸模式）；年龄变化；吸烟和饮酒；药物副作用；全身健康状况。即使是轻微的上呼吸道感染也能显著改变语音特征。"
        elif "症状" in question or "疾病" in question:
            answer = "语音分析中发现的异常可能与多种呼吸系统疾病相关，包括：慢性阻塞性肺病(COPD)、哮喘、支气管炎、肺炎、喉炎、声带小结或息肉、上呼吸道感染等。不同疾病会对不同的语音特征产生影响，例如COPD可能影响肺活量和发声持续时间，而喉炎则主要影响声带振动特性。请注意，语音分析只是初步筛查工具，确诊需要专业医生和更全面的检查。"
        elif "就医" in question or "医生" in question:
            answer = "在就医前，建议您：记录症状的发生时间、持续时间和可能的诱因；注意观察是否有其他伴随症状（如咳嗽、胸痛、呼吸困难等）；如有可能，录制一段语音样本以便医生比较；准备好个人病史和家族病史信息；列出正在服用的所有药物；记录近期可能的环境变化或接触史。这些信息将帮助医生更准确地诊断病因。就诊时最好选择呼吸科或耳鼻喉科医生。"
        else:
            answer = "感谢您的提问。基于您的语音分析数据和当前的健康状况，我建议您保持健康的生活方式，包括规律锻炼、均衡饮食和充足休息。肺部健康与整体健康密切相关，良好的生活习惯是预防呼吸系统问题的基础。如果您有特定的健康顾虑，建议咨询专业医生获取个性化的建议。定期进行健康检查也是保持健康的重要方式。"
        
        return {
            "answer": answer
        }

    async def analyze_voice_metrics(
        self,
        db: Session,
        session_id: int,
        voice_metrics: VoiceMetrics
    ) -> Dict[str, Any]:
        """
        分析语音指标并生成建议
        
        Args:
            db: 数据库会话
            session_id: 诊断会话ID
            voice_metrics: 语音指标对象
            
        Returns:
            包含分析结果和建议的字典
        """
        try:
            # 准备分析数据
            analysis_data = {
                "user_id": voice_metrics.user_id,
                "voice_metrics": {
                    "mfcc": [
                        voice_metrics.mfcc_1, voice_metrics.mfcc_2, voice_metrics.mfcc_3,
                        voice_metrics.mfcc_4, voice_metrics.mfcc_5, voice_metrics.mfcc_6,
                        voice_metrics.mfcc_7, voice_metrics.mfcc_8, voice_metrics.mfcc_9,
                        voice_metrics.mfcc_10, voice_metrics.mfcc_11, voice_metrics.mfcc_12,
                        voice_metrics.mfcc_13
                    ],
                    "chroma": [
                        voice_metrics.chroma_1, voice_metrics.chroma_2, voice_metrics.chroma_3,
                        voice_metrics.chroma_4, voice_metrics.chroma_5, voice_metrics.chroma_6,
                        voice_metrics.chroma_7, voice_metrics.chroma_8, voice_metrics.chroma_9,
                        voice_metrics.chroma_10, voice_metrics.chroma_11, voice_metrics.chroma_12
                    ],
                    "rms": voice_metrics.rms,
                    "zcr": voice_metrics.zcr,
                    "mel_spectrogram": json.loads(voice_metrics.mel_spectrogram) if voice_metrics.mel_spectrogram else [],
                    "model_prediction": voice_metrics.model_prediction,
                    "model_confidence": voice_metrics.model_confidence
                }
            }

            # 构建提示
            prompt = self._build_analysis_prompt(voice_metrics)

            # 调用LLM进行分析
            if self.use_mock:
                result = self._mock_voice_analysis(analysis_data)
            else:
                try:
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        response = await client.post(
                            self.api_endpoint,
                            headers={
                                "Authorization": f"Bearer {self.api_key}",
                                "Content-Type": "application/json"
                            },
                            json={
                                "model": self.model_name,
                                "messages": [
                                    {"role": "system", "content": "你是一个专业的医疗AI助手，专注于分析语音特征以检测肺部健康问题。请提供专业、准确的分析和建议。"},
                                    {"role": "user", "content": prompt}
                                ],
                                "temperature": 0.3,
                                "max_tokens": 1000
                            }
                        )

                        if response.status_code != 200:
                            logger.error(f"LLM API调用失败: {response.status_code} - {response.text}")
                            result = self._mock_voice_analysis(analysis_data)
                        else:
                            llm_response = response.json()
                            content = llm_response["choices"][0]["message"]["content"]
                            try:
                                result = json.loads(content)
                            except json.JSONDecodeError:
                                result = self._parse_llm_text_response(content)

                except Exception as e:
                    logger.error(f"LLM分析过程中发生错误: {str(e)}")
                    result = self._mock_voice_analysis(analysis_data)

            # 更新诊断会话
            session = db.query(DiagnosisSession).filter(
                DiagnosisSession.id == session_id
            ).first()

            if session:
                session.llm_suggestion = result.get("suggestion", "")
                session.llm_processed_at = datetime.now()
                db.commit()

            return result

        except Exception as e:
            logger.error(f"分析语音指标失败: {str(e)}")
            return {
                "analysis": "分析过程中发生错误",
                "suggestion": "请稍后重试或联系客服",
                "risk_level": "未知",
                "follow_up": "建议重新进行语音分析"
            }

    async def summarize_with_llm(self, session_id: int, user_id: int, conversation: list) -> dict:
        """用LLM对对话内容进行总结，写入diagnosis_suggestion字段"""
        try:
            # 构建总结提示词
            prompt = self._build_summary_prompt(conversation)
            result = await self.llm_client.analyze(prompt)
            self.repository.update_session_diagnosis_suggestion(session_id, result)
            return {"session_id": session_id, "diagnosis_suggestion": result}
        except Exception as e:
            error_msg = f"LLM总结失败: {str(e)}"
            self.repository.update_session_diagnosis_suggestion(session_id, error_msg)
            return {"session_id": session_id, "diagnosis_suggestion": error_msg}

    def _build_summary_prompt(self, conversation: list) -> str:
        """根据对话内容构建总结提示词"""
        conv_text = "\n".join([f"{item['role']}: {item['content']}" for item in conversation])
        prompt = f"请根据以下对话内容，总结本次语音健康分析的诊断建议：\n{conv_text}\n\n请用简明、专业的语言给出最终诊断建议。"
        return prompt

    async def analyze_with_llm(
        self,
        session_id: int,
        user_id: int
    ) -> dict:
        try:
            # 获取会话信息
            session = self.repository.get_session_by_id(session_id, user_id)
            if not session:
                logger.warning(f"[analyze_with_llm] 诊断会话不存在: session_id={session_id}, user_id={user_id}")
                return {"error": "诊断会话不存在"}
            # 获取语音指标
            voice_metrics = self.repository.get_voice_metrics(session_id)
            if not voice_metrics:
                logger.warning(f"[analyze_with_llm] 语音指标不存在: session_id={session_id}")
                self.repository.update_session_llm_suggestion(
                    session_id, 
                    "无法进行分析：未找到相关语音指标数据。"
                )
                return {"error": "语音指标不存在"}
            # 获取历史诊断建议（最近3条）
            history = self.repository.get_analysis_history(user_id, skip=0, limit=3)
            history_suggestions = [item['llm_suggestion'] for item in history if item.get('llm_suggestion')] if history else []
            logger.info(f"[analyze_with_llm] 当前语音指标: prediction={voice_metrics.model_prediction}, confidence={voice_metrics.model_confidence}, mfcc={[getattr(voice_metrics, f'mfcc_{i}') for i in range(1, 14)]}, chroma={[getattr(voice_metrics, f'chroma_{i}') for i in range(1, 13)]}, rms={voice_metrics.rms}, zcr={voice_metrics.zcr}, mel_spectrogram={voice_metrics.mel_spectrogram}")
            logger.info(f"[analyze_with_llm] 历史诊断建议: {history_suggestions}")
            # 构建提示词
            prompt = self._build_analysis_prompt(voice_metrics, history_suggestions)
            logger.info(f"[analyze_with_llm] 构建LLM分析提示词: {prompt}")
            # 调用 LLM 进行分析
            try:
                logger.info(f"[analyze_with_llm] 开始调用LLM进行分析: session_id={session_id}")
                analysis_result = await self.llm_client.analyze(prompt)
                logger.info(f"[analyze_with_llm] LLM分析完成，返回内容: {analysis_result}")
                # 保存分析结果
                self.repository.update_session_llm_suggestion(session_id, analysis_result)
                logger.info(f"[analyze_with_llm] 保存LLM分析结果成功: session_id={session_id}")
                return {
                    "session_id": session_id,
                    "analysis": analysis_result,
                    "timestamp": datetime.now()
                }
            except Exception as e:
                logger.error(f"[analyze_with_llm] LLM分析失败: {str(e)}", exc_info=True)
                # 保存错误信息
                error_message = f"分析过程中出现错误: {str(e)}"
                self.repository.update_session_llm_suggestion(session_id, error_message)
                return {
                    "session_id": session_id,
                    "error": error_message,
                    "timestamp": datetime.now()
                }
        except Exception as e:
            logger.error(f"[analyze_with_llm] 处理失败: {str(e)}", exc_info=True)
            return {
                "error": f"处理失败: {str(e)}"
            } 

    async def summarize_conversation(
        self,
        session_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """总结对话内容，生成最终诊断建议"""
        try:
            logger.info(f"[summarize_conversation] 开始总结对话: session_id={session_id}, user_id={user_id}")
            
            # 获取会话信息
            session = self.repository.get_session_by_id(session_id, user_id)
            if not session:
                logger.error(f"[summarize_conversation] 诊断会话不存在: session_id={session_id}, user_id={user_id}")
                raise HTTPException(
                    status_code=404,
                    detail="诊断会话不存在"
                )
            
            # 获取对话历史
            conversation_history = self.repository.get_conversation_history(session_id)
            if not conversation_history:
                logger.warning(f"[summarize_conversation] 无对话内容可总结: session_id={session_id}")
                return {
                    "session_id": session_id,
                    "summary": "无对话内容可总结",
                    "status": "warning"
                }
            
            logger.info(f"[summarize_conversation] 对话历史消息数量: {len(conversation_history)}")
            
            # 构建总结提示词
            prompt = self._build_summary_prompt(conversation_history)
            logger.info(f"[summarize_conversation] 构建的总结提示词长度: {len(prompt)}")
            
            # 调用 LLM 总结对话
            logger.info(f"[summarize_conversation] 开始调用LLM进行总结: session_id={session_id}")
            summary = await self.llm_client.analyze(prompt)
            logger.info(f"[summarize_conversation] LLM返回的总结内容长度: {len(summary)}")
            
            # 保存总结结果到诊断建议字段
            self.repository.update_session_diagnosis_suggestion(session_id, summary)
            logger.info(f"[summarize_conversation] 总结已保存到诊断建议字段: session_id={session_id}")
            
            return {
                "session_id": session_id,
                "summary": summary,
                "status": "success"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[summarize_conversation] 总结对话失败: {str(e)}", exc_info=True)
            error_msg = f"总结失败: {str(e)}"
            # 即使失败也尝试保存错误信息
            try:
                self.repository.update_session_diagnosis_suggestion(session_id, f"总结处理失败: {str(e)}")
                logger.info(f"[summarize_conversation] 错误信息已保存: session_id={session_id}")
            except Exception as inner_e:
                logger.error(f"[summarize_conversation] 保存错误信息也失败了: {str(inner_e)}")
            raise HTTPException(
                status_code=500,
                detail=error_msg
            ) 