import os
import sys
import logging
from sqlalchemy.exc import ProgrammingError

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def remove_user_settings_table():
    """
    删除用户设置表
    """
    try:
        # 创建数据库连接
        engine = create_engine(settings.SQLALCHEMY_DATABASE_URL)
        
        # 开始事务
        with engine.begin() as conn:
            # 获取外键约束名称
            logger.info("获取外键约束名称...")
            result = conn.execute(text("""
                SELECT CONSTRAINT_NAME 
                FROM information_schema.TABLE_CONSTRAINTS 
                WHERE TABLE_NAME = 'users' 
                AND CONSTRAINT_TYPE = 'FOREIGN KEY'
            """))
            foreign_keys = [row[0] for row in result]
            
            # 删除外键约束
            for fk in foreign_keys:
                logger.info(f"删除外键约束 {fk}...")
                conn.execute(text(f"ALTER TABLE users DROP FOREIGN KEY {fk}"))
            
            # 删除用户设置表
            logger.info("删除用户设置表...")
            conn.execute(text("DROP TABLE IF EXISTS user_settings"))
            
            # 删除用户表中的settings_id列（如果存在）
            logger.info("尝试删除用户表中的settings_id列...")
            try:
                conn.execute(text("ALTER TABLE users DROP COLUMN settings_id"))
            except ProgrammingError as e:
                logger.warning(f"忽略删除settings_id列时的错误: {e}")
        
        logger.info("用户设置表删除成功！")
        
    except Exception as e:
        logger.error(f"删除用户设置表时发生错误: {str(e)}")
        raise

if __name__ == "__main__":
    remove_user_settings_table() 