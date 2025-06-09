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
from app.core.llm import LLMClient, get_llm_client
from app.core.config import settings
from app.websockets.manager import websocket_manager

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
        self.db = db
        logger.info("[LLMService.__init__] 初始化LLM服务")
        self.repository = LLMRepository(db)
        self.llm_client = get_llm_client()
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
    
    async def chat_with_llm(
        self,
        user_id: int,
        message: str,
        session_id: Optional[int] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """与LLM进行对话（带历史）"""
        try:
            logger.info(f"[LLMService.chat_with_llm] 开始处理聊天请求: user_id={user_id}, session_id={session_id}")
            # 构建对话历史prompt
            prompt = ""
            if history and isinstance(history, list) and len(history) > 0:
                for msg in history:
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    prompt += f"{role}: {content}\n"
                prompt += f"user: {message}\n"
            else:
                prompt = f"用户ID: {user_id}\n用户问题: {message}\n\n请根据用户的问题提供关于语音健康分析的回答。\n如果问题与语音健康无关，请礼貌地引导用户询问与语音健康相关的问题。"
            # 调用LLM
            analysis = await self.llm_client.analyze(prompt)
            logger.info(f"[LLMService.chat_with_llm] LLM分析完成: user_id={user_id}")
            # 对话历史已由前端维护，后端不再存储
            return {
                "analysis": analysis,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"[LLMService.chat_with_llm] 处理聊天请求失败: {str(e)}", exc_info=True)
            raise

    async def get_conversation_history(
        self,
        session_id: int
    ) -> List[Dict[str, Any]]:
        """获取对话历史"""
        try:
            logger.info(f"[LLMService.get_conversation_history] 获取对话历史: session_id={session_id}")
            # 使用仓库获取对话历史
            history = self.repository.get_conversation_history(session_id)
            logger.info(f"[LLMService.get_conversation_history] 获取到对话历史: session_id={session_id}, 消息数量={len(history)}")
            return history
        except Exception as e:
            logger.error(f"[LLMService.get_conversation_history] 获取对话历史失败: {str(e)}", exc_info=True)
            raise

    async def get_latest_suggestion(
        self,
        session_id: int
    ) -> Dict[str, Any]:
        """获取最新的 LLM 建议"""
        try:
            logger.info(f"[LLMService.get_latest_suggestion] 获取最新建议: session_id={session_id}")
            
            # 获取会话信息
            session = self.repository.get_session_by_id(session_id)
            if not session:
                logger.warning(f"[LLMService.get_latest_suggestion] 会话不存在: session_id={session_id}")
                raise ValueError("诊断会话不存在")
            
            return {
                "session_id": session.id,
                "diagnosis_suggestion": session.diagnosis_suggestion,
                "follow_up_questions": json.loads(session.follow_up_questions or "[]")
            }
        except Exception as e:
            logger.error(f"[LLMService.get_latest_suggestion] 获取最新建议失败: {str(e)}", exc_info=True)
            raise

    async def save_conversation(
        self,
        user_id: int,
        session_id: int,
        user_message: Dict[str, str],
        assistant_message: Dict[str, str]
    ) -> bool:
        """保存对话历史（已废弃，前端维护历史，后端不再存储）"""
        logger.info(f"[LLMService.save_conversation] 跳过保存对话: session_id={session_id}")
        return True

    async def get_analysis_history(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取分析历史"""
        try:
            logger.info(f"[LLMService.get_analysis_history] 获取分析历史: user_id={user_id}, skip={skip}, limit={limit}")
            result = self.repository.get_analysis_history(user_id, skip, limit)
            logger.info(f"[LLMService.get_analysis_history] 获取分析历史成功: user_id={user_id}, 记录数={len(result)}")
            return result
        except Exception as e:
            logger.error(f"[LLMService.get_analysis_history] 获取分析历史失败: {str(e)}", exc_info=True)
            raise

    async def get_display_summary(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """获取用于显示的摘要数据"""
        try:
            logger.info(f"[LLMService.get_display_summary] 获取显示摘要: user_id={user_id}")
            result = self.repository.get_display_summary(user_id)
            logger.info(f"[LLMService.get_display_summary] 获取显示摘要成功: user_id={user_id}")
            return result
        except Exception as e:
            logger.error(f"[LLMService.get_display_summary] 获取显示摘要失败: {str(e)}", exc_info=True)
            raise

    async def get_realtime_data(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """获取实时监控数据"""
        try:
            logger.info(f"[LLMService.get_realtime_data] 获取实时数据: user_id={user_id}")
            result = self.repository.get_realtime_data(user_id)
            logger.info(f"[LLMService.get_realtime_data] 获取实时数据成功: user_id={user_id}")
            return result
        except Exception as e:
            logger.error(f"[LLMService.get_realtime_data] 获取实时数据失败: {str(e)}", exc_info=True)
            raise

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
            self.repository.update_session_diagnosis_suggestion(session_id, analysis_result)
            
            # 创建新的对话记录
            self.repository.create_conversation(
                session_id=session_id,
                role="assistant",
                content=analysis_result
            )
            
            return {
                "session_id": session_id,
                "analysis": analysis_result,
                "timestamp": session.diagnosis_processed_at
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
                "content": response.data.analysis,
                "created_at": datetime.utcnow().isoformat()
            })
            
            # 保存整个对话历史
            self.repository.save_conversation(session_id, conversation_history)
            logger.info(f"[handle_follow_up] 对话历史已保存: session_id={session_id}, 总消息数={len(conversation_history)}")
            
            return {
                "session_id": session_id,
                "question": question,
                "response": response.data.analysis,
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
    
    async def summarize_conversation(
        self,
        session_id: int,
        user_id: int,
        frontend_conversation: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """总结对话内容，生成最终诊断建议"""
        try:
            logger.info(f"[summarize_conversation] 开始总结对话: session_id={session_id}, user_id={user_id}, 是否使用前端传递的对话: {frontend_conversation is not None}")
            
            # 获取会话信息
            session = self.repository.get_session_by_id(session_id, user_id)
            if not session:
                logger.error(f"[summarize_conversation] 诊断会话不存在: session_id={session_id}, user_id={user_id}")
                raise HTTPException(
                    status_code=404,
                    detail="诊断会话不存在"
                )
            
            # 确定使用哪个对话历史
            conversation_history = None
            if frontend_conversation is not None:
                # 使用前端传递的对话
                conversation_history = frontend_conversation
                logger.info(f"[summarize_conversation] 使用前端传递的对话，消息数量: {len(conversation_history)}")
                
                # 标准化conversation格式
                try:
                    # 确保每个消息都有role和content字段
                    standardized_conversation = []
                    for msg in conversation_history:
                        # 提取role和content，如果不存在则使用默认值
                        role = msg.get('role', 'unknown')
                        content = msg.get('content', '')
                        if not isinstance(content, str):
                            content = str(content)  # 确保content是字符串
                        
                        standardized_conversation.append({
                            'role': role,
                            'content': content
                        })
                    conversation_history = standardized_conversation
                    logger.info(f"[summarize_conversation] 已标准化conversation格式，消息数量: {len(conversation_history)}")
                except Exception as e:
                    logger.error(f"[summarize_conversation] 标准化conversation格式失败: {str(e)}", exc_info=True)
                    raise HTTPException(
                        status_code=422,
                        detail=f"无效的对话格式: {str(e)}"
                    )
            else:
                # 使用数据库中的对话历史
                conversation_history = self.repository.get_conversation_history(session_id)
                logger.info(f"[summarize_conversation] 使用数据库中的对话历史，消息数量: {len(conversation_history) if conversation_history else 0}")
            
            if not conversation_history:
                logger.warning(f"[summarize_conversation] 无对话内容可总结: session_id={session_id}")
                return {
                    "session_id": session_id,
                    "summary": "无对话内容可总结",
                    "status": "warning"
                }
            
            # 标准化对话格式
            standardized_conversation = []
            for msg in conversation_history:
                if isinstance(msg, dict):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    if not isinstance(content, str):
                        content = str(content)  # 确保content是字符串
                    
                    standardized_conversation.append({
                        'role': role,
                        'content': content
                    })
            
            logger.info(f"[summarize_conversation] 标准化后的对话消息数量: {len(standardized_conversation)}")
            
            # 构建总结提示词
            prompt = self._build_summary_prompt(standardized_conversation)
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
#主数据流用到
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
- 音频质量得分（满分为100%）: {voice_metrics.model_confidence}
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
- 音频质量得分（满分为100%）: {metrics.get('confidence', '未提供')}

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
    
    
    def _build_summary_prompt(self, conversation: list) -> str:
        """根据对话内容构建总结提示词"""
        try:
            # 确保每条消息都有role和content字段
            formatted_messages = []
            for item in conversation:
                role = item.get('role', 'unknown')
                content = item.get('content', '')
                if not isinstance(content, str):
                    content = str(content)  # 确保content是字符串
                
                formatted_messages.append(f"{role}: {content}")
            
            conv_text = "\n".join(formatted_messages)
            prompt = f"请根据以下对话内容，总结本次语音健康分析的诊断建议：\n{conv_text}\n\n请用简明、专业的语言给出最终诊断建议。"
            return prompt
        except Exception as e:
            logger.error(f"构建总结提示词失败: {str(e)}", exc_info=True)
            return "请总结对话内容，给出诊断建议。"  # 提供一个简单的备用提示词
#第一次发送过来
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
                return {"error": "语音指标不存在"}
            # 获取历史诊断建议（最近3条）
            history = self.repository.get_analysis_history(user_id, skip=0, limit=3)
            history_suggestions = [item['diagnosis_suggestion'] for item in history if item.get('diagnosis_suggestion')] if history else []
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
                # WebSocket实时推送到前端仪表盘
                logger.info(f"准备推送AI诊断建议，user_id: {user_id}, 类型: {type(user_id)}")
                try:
                    # 检查WebSocketManager中是否有该用户的连接
                    has_connection = user_id in websocket_manager.active_connections
                    logger.info(f"用户 {user_id} 是否有WebSocket连接: {has_connection}")
                    await websocket_manager.send_message(
                        user_id,
                        json.dumps({
                            "type": "llm_analysis",
                            "session_id": session_id,
                            "analysis": analysis_result,
                            "llm_prompt": prompt
                        })
                    )
                    logger.info(f"[analyze_with_llm] 已通过WebSocket推送AI诊断建议: session_id={session_id}, user_id={user_id}")
                except Exception as e:
                    logger.error(f"[analyze_with_llm] WebSocket推送失败: {str(e)}", exc_info=True)
                # 直接返回分析结果和prompt，不立即保存
                return {
                    "session_id": session_id,
                    "analysis": analysis_result,
                    "prompt": prompt,
                    "timestamp": datetime.now()
                }
            except Exception as e:
                logger.error(f"[analyze_with_llm] LLM分析失败: {str(e)}", exc_info=True)
                error_message = f"分析过程中出现错误: {str(e)}"
                return {
                    "session_id": session_id,
                    "error": error_message,
                    "prompt": prompt,
                    "timestamp": datetime.now()
                }
        except Exception as e:
            logger.error(f"[analyze_with_llm] 处理失败: {str(e)}", exc_info=True)
            return {
                "error": f"处理失败: {str(e)}"
            } 