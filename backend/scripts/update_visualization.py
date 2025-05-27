#!/usr/bin/env python3
"""
更新可视化API脚本
用于更新可视化API以适配新的声音指标
"""

import os
import sys
import logging

# 添加父目录到系统路径，使脚本可以导入app模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_visualization_endpoint():
    """
    更新可视化API端点
    """
    try:
        # 找到诊断API文件
        diagnosis_api_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'api', 'v1', 'endpoints', 'diagnosis.py')
        
        if not os.path.exists(diagnosis_api_path):
            logger.error(f"找不到文件: {diagnosis_api_path}")
            return False
        
        # 读取文件内容
        with open(diagnosis_api_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # 查找可视化API
        if "def get_visualization_data" not in content:
            logger.error("找不到可视化API端点")
            return False
        
        # 更新API
        old_code = """    # 准备可视化数据
    visualization_data = {
        "session_id": session_id,
        "time_domain": {
            "short_time_energy": metrics.short_time_energy,
            "zero_crossing_rate": metrics.zero_crossing_rate
        },
        "frequency_domain": {
            "f0": metrics.f0,
            "spectral_centroid": metrics.spectral_centroid,
            "hnr": metrics.hnr
        },
        "analysis": {
            "prediction": metrics.model_prediction,
            "confidence": metrics.model_confidence
        }
    }"""
        
        new_code = """    # 准备可视化数据
    visualization_data = {
        "session_id": session_id,
        "time_domain": {
            "rms": metrics.rms,
            "zcr": metrics.zcr
        },
        "frequency_domain": {
            "centroid": metrics.centroid,
            "bandwidth": metrics.bandwidth,
            "rolloff": metrics.rolloff
        },
        "mfcc_features": {
            "mfcc": [getattr(metrics, f"mfcc_{i+1}", 0) for i in range(13)],
            "delta": [getattr(metrics, f"delta_{i+1}", 0) for i in range(13)],
            "delta2": [getattr(metrics, f"delta2_{i+1}", 0) for i in range(13)]
        },
        "chroma_features": {
            "chroma": [getattr(metrics, f"chroma_{i+1}", 0) for i in range(12)]
        },
        "tonnetz_features": {
            "tonnetz": [getattr(metrics, f"tonnetz_{i+1}", 0) for i in range(6)]
        },
        "other_features": {
            "contrast": metrics.contrast
        },
        "analysis": {
            "prediction": metrics.model_prediction,
            "confidence": metrics.model_confidence
        }
    }"""
        
        # 替换代码
        updated_content = content.replace(old_code, new_code)
        
        # 检查是否进行了替换
        if updated_content == content:
            logger.warning("没有找到匹配的代码块进行替换，尝试手动操作")
            
            # 尝试更新complete_diagnosis函数
            old_report = """    final_report = {
        "user_id": current_user.id,
        "username": current_user.username,
        "session_id": session_id,
        "diagnosis_time": session.created_at.isoformat(),
        "completed_time": session.completed_at.isoformat(),
        "voice_metrics": {
            "prediction": metrics.model_prediction,
            "confidence": metrics.model_confidence,
            "key_features": {
                "f0": metrics.f0,
                "hnr": metrics.hnr,
                "short_time_energy": metrics.short_time_energy,
                "zero_crossing_rate": metrics.zero_crossing_rate
            }
        },
        "llm_analysis": session.llm_suggestion if session.llm_suggestion else "未提供LLM分析",
        "llm_conversation": json.loads(session.llm_raw_result) if session.llm_raw_result else {}
    }"""
            
            new_report = """    final_report = {
        "user_id": current_user.id,
        "username": current_user.username,
        "session_id": session_id,
        "diagnosis_time": session.created_at.isoformat(),
        "completed_time": session.completed_at.isoformat(),
        "voice_metrics": {
            "prediction": metrics.model_prediction,
            "confidence": metrics.model_confidence,
            "key_features": {
                "centroid": metrics.centroid,
                "bandwidth": metrics.bandwidth,
                "rms": metrics.rms,
                "zcr": metrics.zcr
            }
        },
        "llm_analysis": session.llm_suggestion if session.llm_suggestion else "未提供LLM分析",
        "llm_conversation": []
    }"""
            
            # 替换完成诊断代码
            updated_content = updated_content.replace(old_report, new_report)
            
            # 检查是否替换成功
            if updated_content == content:
                logger.warning("自动更新失败，请手动检查并更新代码")
                return False
        
        # 写回文件
        with open(diagnosis_api_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
        
        logger.info("已成功更新可视化API端点")
        return True
    except Exception as e:
        logger.error(f"更新可视化API端点失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("=== 开始更新可视化API ===")
    
    # 更新可视化API端点
    if update_visualization_endpoint():
        logger.info("更新成功完成！")
        return True
    else:
        logger.error("更新失败，请检查日志查看详情")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 