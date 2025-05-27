#!/usr/bin/env python3
"""
数据库结构迁移脚本
用于更新数据库表结构以支持新的声音指标
"""

import os
import sys
import logging
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

# 添加父目录到系统路径，使脚本可以导入app模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.db import Base, engine, SessionLocal
from app.core.config import settings
from app.db.models import User, DiagnosisSession, VoiceMetrics

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def backup_database():
    """
    备份当前数据库（如果有重要数据）
    """
    logger.info("请在继续前手动备份您的数据库，以防数据丢失。")
    confirmation = input("是否已完成备份? (y/n): ")
    if confirmation.lower() != 'y':
        logger.error("用户未确认备份，退出迁移")
        sys.exit(1)
    logger.info("继续进行迁移...")

def update_schema():
    """
    更新数据库表结构
    """
    try:
        logger.info("开始更新数据库表结构...")
        
        # 创建会话工厂
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:            
            # 更新VoiceMetrics表结构
            inspector = sa.inspect(engine)
            voice_metrics_columns = [col["name"] for col in inspector.get_columns("voice_metrics")]
            
            # 添加或更新列，使用事务方式
            conn = engine.connect()
            transaction = conn.begin()
            
            try:
                # 移除旧列
                old_columns = [
                    "short_time_energy", "zero_crossing_rate", "waveform_kurtosis",
                    "f0", "hnr", "gammatone_spectrum", "wavelet_entropy",
                    "breath_ratio", "energy_ratio_40_600hz", "cough_detection",
                    "chest_audionet_embedding"
                ]
                
                for col in old_columns:
                    if col in voice_metrics_columns:
                        logger.info(f"移除列: {col}")
                        conn.execute(f"ALTER TABLE voice_metrics DROP COLUMN {col}")
                
                # 添加新列
                new_columns = {
                    # MFCC的一阶差分
                    "delta_1": "FLOAT", "delta_2": "FLOAT", "delta_3": "FLOAT",
                    "delta_4": "FLOAT", "delta_5": "FLOAT", "delta_6": "FLOAT",
                    "delta_7": "FLOAT", "delta_8": "FLOAT", "delta_9": "FLOAT",
                    "delta_10": "FLOAT", "delta_11": "FLOAT", "delta_12": "FLOAT",
                    "delta_13": "FLOAT",
                    
                    # MFCC的二阶差分
                    "delta2_1": "FLOAT", "delta2_2": "FLOAT", "delta2_3": "FLOAT",
                    "delta2_4": "FLOAT", "delta2_5": "FLOAT", "delta2_6": "FLOAT",
                    "delta2_7": "FLOAT", "delta2_8": "FLOAT", "delta2_9": "FLOAT",
                    "delta2_10": "FLOAT", "delta2_11": "FLOAT", "delta2_12": "FLOAT",
                    "delta2_13": "FLOAT",
                    
                    # 色度特征
                    "chroma_1": "FLOAT", "chroma_2": "FLOAT", "chroma_3": "FLOAT",
                    "chroma_4": "FLOAT", "chroma_5": "FLOAT", "chroma_6": "FLOAT",
                    "chroma_7": "FLOAT", "chroma_8": "FLOAT", "chroma_9": "FLOAT",
                    "chroma_10": "FLOAT", "chroma_11": "FLOAT", "chroma_12": "FLOAT",
                    
                    # 梅尔频谱特征
                    "log_mel": "TEXT",
                    
                    # 频谱对比度
                    "contrast": "FLOAT",
                    
                    # 调性特征
                    "tonnetz_1": "FLOAT", "tonnetz_2": "FLOAT", "tonnetz_3": "FLOAT",
                    "tonnetz_4": "FLOAT", "tonnetz_5": "FLOAT", "tonnetz_6": "FLOAT",
                    
                    # 时域特征和频谱形状特征
                    "rms": "FLOAT", "zcr": "FLOAT",
                    "bandwidth": "FLOAT", "centroid": "FLOAT", "rolloff": "FLOAT"
                }
                
                for col_name, col_type in new_columns.items():
                    if col_name not in voice_metrics_columns:
                        logger.info(f"添加列: {col_name} ({col_type})")
                        conn.execute(f"ALTER TABLE voice_metrics ADD COLUMN {col_name} {col_type}")
                
                transaction.commit()
                logger.info("数据库结构更新成功")
                
            except Exception as e:
                transaction.rollback()
                logger.error(f"更新表结构时出错: {e}")
                raise
            finally:
                conn.close()
            
        finally:
            db.close()
        
        return True
    except Exception as e:
        logger.error(f"更新数据库结构失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("=== 开始数据库结构迁移 ===")
    logger.info(f"数据库配置: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}")
    
    # 备份数据库
    backup_database()
    
    # 更新表结构
    if update_schema():
        logger.info("迁移成功完成！")
        return True
    else:
        logger.error("迁移失败，请检查日志查看详情")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 