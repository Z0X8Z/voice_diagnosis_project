from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from app.core.security import get_current_user
from app.db.session import get_db
from app.db.models import User
from app.services.microphone_test_service import MicrophoneTestService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/instructions")
async def get_test_instructions(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取麦克风测试说明"""
    try:
        service = MicrophoneTestService()
        return service.generate_test_instructions()
    except Exception as e:
        logger.error(f"获取测试说明失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取测试说明失败: {str(e)}"
        )

@router.post("/analyze")
async def analyze_microphone_quality(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    noise_file: UploadFile = File(..., description="环境噪声录音文件"),
    breath_file: UploadFile = File(..., description="呼吸音录音文件")
) -> Dict[str, Any]:
    """
    分析麦克风质量
    
    Args:
        noise_file: 环境噪声录音文件（建议2秒）
        breath_file: 呼吸音录音文件（建议5秒）
    
    Returns:
        麦克风质量评估结果
    """
    try:
        logger.info(f"用户 {current_user.id} 开始麦克风质量评估")
        
        # 验证文件格式
        allowed_types = ['audio/wav', 'audio/webm', 'audio/mp3', 'audio/ogg']
        
        if noise_file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"环境噪声文件格式不支持: {noise_file.content_type}"
            )
        
        if breath_file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"呼吸音文件格式不支持: {breath_file.content_type}"
            )
        
        # 读取文件内容并验证文件大小
        try:
            # 读取噪声文件
            noise_content = await noise_file.read()
            if len(noise_content) > 10 * 1024 * 1024:  # 10MB
                raise HTTPException(
                    status_code=400,
                    detail="环境噪声文件过大，请上传小于10MB的文件"
                )
            
            if len(noise_content) < 1000:  # 文件太小
                raise HTTPException(
                    status_code=400,
                    detail="环境噪声文件太小，请确保录音时长至少1-2秒"
                )
            
            # 读取呼吸音文件
            breath_content = await breath_file.read()
            if len(breath_content) > 10 * 1024 * 1024:  # 10MB
                raise HTTPException(
                    status_code=400,
                    detail="呼吸音文件过大，请上传小于10MB的文件"
                )
            
            if len(breath_content) < 1000:  # 文件太小
                raise HTTPException(
                    status_code=400,
                    detail="呼吸音文件太小，请确保录音时长至少3-5秒"
                )
            
            # 重新创建UploadFile对象以便服务使用
            from io import BytesIO
            noise_file_stream = BytesIO(noise_content)
            breath_file_stream = BytesIO(breath_content)
            
            # 创建新的UploadFile对象
            from fastapi import UploadFile
            noise_file_new = UploadFile(
                filename=noise_file.filename,
                file=noise_file_stream,
                content_type=noise_file.content_type
            )
            breath_file_new = UploadFile(
                filename=breath_file.filename,
                file=breath_file_stream,
                content_type=breath_file.content_type
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"读取文件失败: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"文件读取失败: {str(e)}"
            )
        
        # 调用服务进行分析
        service = MicrophoneTestService()
        result = await service.analyze_microphone_quality(noise_file_new, breath_file_new)
        
        logger.info(f"用户 {current_user.id} 麦克风质量评估完成，评分: {result['quality_score']}")
        
        return {
            "user_id": current_user.id,
            "test_result": result,
            "message": "麦克风质量评估完成" if result["test_passed"] else "麦克风质量需要改善"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户 {current_user.id} 麦克风质量评估失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"麦克风质量评估失败: {str(e)}"
        )

@router.get("/quick-test")
async def quick_microphone_test(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    快速麦克风测试说明
    为前端提供简化的测试流程指导
    """
    return {
        "title": "麦克风快速测试",
        "description": "快速检查您的麦克风是否适合语音诊断",
        "test_flow": [
            {
                "id": "noise_test",
                "title": "环境噪声测试",
                "instruction": "请保持安静2秒钟，我们将检测环境噪声水平",
                "duration": 2,
                "button_text": "开始噪声测试"
            },
            {
                "id": "breath_test", 
                "title": "呼吸音测试",
                "instruction": "请靠近麦克风10-20厘米，正常呼吸5秒钟",
                "duration": 5,
                "button_text": "开始呼吸测试"
            }
        ],
        "tips": [
            "确保在安静的环境中进行测试",
            "关闭风扇、空调等可能产生噪音的设备",
            "测试期间请保持与麦克风的稳定距离",
            "如果测试未通过，请根据建议调整后重新测试"
        ]
    }

@router.post("/check-breath-quality")
async def check_breath_quality(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    breath_file: UploadFile = File(..., description="呼吸音录音文件")
) -> Dict[str, Any]:
    """
    检查单个呼吸音文件的质量（用于多次录音的实时检测）
    
    Args:
        breath_file: 呼吸音录音文件
    
    Returns:
        呼吸音质量评估结果
    """
    try:
        logger.info(f"用户 {current_user.id} 开始呼吸音质量检测")
        
        # 验证文件格式
        allowed_types = ['audio/wav', 'audio/webm', 'audio/mp3', 'audio/ogg']
        
        if breath_file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"呼吸音文件格式不支持: {breath_file.content_type}"
            )
        
        # 读取文件内容并验证文件大小
        try:
            breath_content = await breath_file.read()
            if len(breath_content) > 10 * 1024 * 1024:  # 10MB
                raise HTTPException(
                    status_code=400,
                    detail="呼吸音文件过大，请上传小于10MB的文件"
                )
            
            if len(breath_content) < 500:  # 文件太小
                raise HTTPException(
                    status_code=400,
                    detail="呼吸音文件太小，请确保录音时长至少2-3秒"
                )
            
            # 重新创建UploadFile对象
            from io import BytesIO
            breath_file_stream = BytesIO(breath_content)
            
            breath_file_new = UploadFile(
                filename=breath_file.filename,
                file=breath_file_stream,
                content_type=breath_file.content_type
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"读取呼吸音文件失败: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"文件读取失败: {str(e)}"
            )
        
        # 调用服务进行质量检测
        service = MicrophoneTestService()
        result = await service.analyze_breath_quality_only(breath_file_new)
        
        logger.info(f"用户 {current_user.id} 呼吸音质量检测完成，评分: {result['quality_score']}, 可接受: {result['is_acceptable']}")
        
        return {
            "user_id": current_user.id,
            "quality_result": result,
            "message": "呼吸音质量检测完成"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户 {current_user.id} 呼吸音质量检测失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"呼吸音质量检测失败: {str(e)}"
        ) 