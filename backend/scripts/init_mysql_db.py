#!/usr/bin/env python3
"""
数据库初始化脚本
用于创建数据库和表
"""
import os
import sys
import logging
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import subprocess

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config():
    """加载环境变量配置"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if not os.path.exists(env_path):
        logger.error(f"找不到环境配置文件: {env_path}")
        sys.exit(1)
    
    load_dotenv(env_path)
    
    return {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', '3306')),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', 'project')
    }

def create_database(config):
    """创建数据库"""
    try:
        # 连接到MySQL服务器
        conn = mysql.connector.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password']
        )
        
        if conn.is_connected():
            cursor = conn.cursor()
                
            # 创建数据库（如果不存在）
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            logger.info(f"数据库 {config['database']} 创建成功或已存在")
            
            cursor.close()
        conn.close()
            
    except Error as e:
        logger.error(f"创建数据库时出错: {e}")
        sys.exit(1)

def create_tables(config):
    """创建数据库表"""
    try:
        # 直接导入模型和创建引擎
        from sqlalchemy import create_engine
        from app.db.models import Base
        
        # 创建数据库连接URL
        database_url = f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
        
        # 创建引擎
        engine = create_engine(database_url)
        
        # 先删除所有表
        logger.info("删除所有现有表...")
        Base.metadata.drop_all(bind=engine)
        logger.info("所有表已删除")
        
        # 创建新表
        logger.info("开始创建数据库表...")
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建完成")
        
    except Exception as e:
        logger.error(f"创建数据库表时出错: {e}")
        sys.exit(1)

def init_database():
    """初始化数据库"""
    try:
        # 加载配置
        config = load_config()
        
        # 创建数据库
        create_database(config)
        
        # 创建表
        create_tables(config)
        
        # 运行数据库迁移
        # 注释掉迁移步骤，因为我们直接创建表
        # logger.info("开始运行数据库迁移...")
        # subprocess.run(["alembic", "upgrade", "heads"], check=True)
        # logger.info("数据库迁移完成")
        
    except Exception as e:
        logger.error(f"初始化数据库时出错: {e}")
        sys.exit(1)

def main():
    """主函数"""
    logger.info("开始初始化数据库...")
    init_database()
    logger.info("数据库初始化完成")

if __name__ == "__main__":
    main() 