#!/usr/bin/env python3
"""
数据库初始化脚本
用于创建所有必要的表结构，适用于全新安装
"""

import os
import sys
import logging
from sqlalchemy import inspect

# 添加父目录到系统路径，使脚本可以导入app模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.db import Base, engine
from app.core.config import settings
from app.db.models import User, DiagnosisSession, VoiceMetrics

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_tables():
    """
    创建所有数据库表
    """
    try:
        # 获取当前已存在的表
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"当前数据库中已有的表: {tables}")
        
        # 创建未存在的表
        Base.metadata.create_all(engine)
        logger.info("所有表已成功创建或更新")
        
        # 验证表是否创建成功
        new_tables = inspect(engine).get_table_names()
        logger.info(f"创建后的表: {new_tables}")
        
        return True
    except Exception as e:
        logger.error(f"创建表时出错: {e}")
        return False

def main():
    """主函数"""
    logger.info("=== 开始初始化数据库 ===")
    logger.info(f"数据库配置: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}")
    
    # 创建表
    if create_tables():
        logger.info("数据库初始化成功！")
        return True
    else:
        logger.error("数据库初始化失败，请检查日志")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 