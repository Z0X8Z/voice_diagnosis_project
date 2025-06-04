#!/usr/bin/env python3
"""
环境变量设置脚本
用于创建和配置 .env 文件
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_env_file(auto_mysql=False):
    """创建 .env 文件"""
    try:
        # 获取项目根目录
        root_dir = Path(__file__).parent.parent
        env_file = root_dir / '.env'
        
        # 如果文件已存在，询问是否覆盖（除非是自动模式）
        if env_file.exists() and not auto_mysql:
            response = input(".env 文件已存在，是否覆盖？(y/n): ")
            if response.lower() != 'y':
                logger.info("操作已取消")
                return False
        
        # 自动模式或用户输入
        if auto_mysql:
            # 自动配置MySQL数据库
            logger.info("使用MySQL自动配置...")
            project_name = "声肺康智能分析系统"
            version = "1.0.0"
            api_v1_str = "/api/v1"
            secret_key = "auto-generated-secret-key-for-voice-diagnosis-system"
            algorithm = "HS256"
            token_expire = "11520"
            # MySQL配置
            mysql_host = "localhost"
            mysql_port = "3306"
            mysql_user = "root"
            mysql_password = "12345678"
            mysql_database = "project"
            # OpenAI配置
            openai_api_key = ""
            openai_model = ""
            openai_api_base = ""
            # CORS配置
            cors_origins = "http://localhost:5173,http://127.0.0.1:5173"
        else:
            # 获取用户输入
            print("\n=== 声肺康智能分析系统环境配置 ===")
            print("请输入以下配置信息（直接回车使用默认值）：\n")
            
            # 项目配置
            project_name = input("项目名称 [声肺康智能分析系统]: ") or "声肺康智能分析系统"
            version = input("版本号 [1.0.0]: ") or "1.0.0"
            api_v1_str = input("API前缀 [/api/v1]: ") or "/api/v1"
            
            # 安全配置
            secret_key = input("密钥 [your-secret-key-here]: ") or "your-secret-key-here"
            algorithm = input("算法 [HS256]: ") or "HS256"
            token_expire = input("令牌过期时间(分钟) [11520]: ") or "11520"
            
            # MySQL配置
            mysql_host = input("MySQL主机 [localhost]: ") or "localhost"
            mysql_port = input("MySQL端口 [3306]: ") or "3306"
            mysql_user = input("MySQL用户名 [root]: ") or "root"
            mysql_password = input("MySQL密码 [12345678]: ") or "12345678"
            mysql_database = input("MySQL数据库名 [project]: ") or "project"
            
            # OpenAI配置
            print("\n=== OpenAI API 配置 ===")
            openai_api_key = input("OpenAI API Key []: ") or ""
            openai_model = input("OpenAI 模型 []: ") or ""
            openai_api_base = input("OpenAI API Base []: ") or ""
            
            # CORS配置
            cors_origins = input("CORS允许的源 [http://localhost:5173,http://127.0.0.1:5173]: ") or "http://localhost:5173,http://127.0.0.1:5173"
        
        # 写入文件 - 包含OpenAI配置
        env_content = f"""# 项目配置
PROJECT_NAME="{project_name}"
VERSION="{version}"
API_V1_STR="{api_v1_str}"

# 安全配置
SECRET_KEY="{secret_key}"
ALGORITHM="{algorithm}"
ACCESS_TOKEN_EXPIRE_MINUTES={token_expire}

# 数据库配置
MYSQL_HOST={mysql_host}
MYSQL_PORT={mysql_port}
MYSQL_USER={mysql_user}
MYSQL_PASSWORD={mysql_password}
MYSQL_DATABASE={mysql_database}

# OpenAI配置
OPENAI_API_KEY="{openai_api_key}"
OPENAI_MODEL="{openai_model}"
OPENAI_API_BASE="{openai_api_base}"

# CORS配置
BACKEND_CORS_ORIGINS=["{cors_origins.replace(',', '","')}"]
"""
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        logger.info(f".env 文件已创建: {env_file}")
        return True
        
    except Exception as e:
        logger.error(f"创建 .env 文件时出错: {e}")
        return False

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='设置环境变量')
    parser.add_argument('--auto-mysql', action='store_true', help='自动配置MySQL数据库')
    args = parser.parse_args()
    
    logger.info("开始设置环境变量...")
    
    if create_env_file(auto_mysql=args.auto_mysql):
        logger.info("环境变量设置完成！")
        logger.info("请确保已安装所有依赖：pip install -r requirements.txt")
        logger.info("然后运行数据库初始化脚本：python scripts/init_mysql_db.py")
        return True
    else:
        logger.error("环境变量设置失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 