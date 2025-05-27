#!/bin/bash
# MySQL数据库环境变量设置脚本

# 默认值
DEFAULT_USER="root"
DEFAULT_PASSWORD=""  # 默认空密码
DEFAULT_HOST="localhost"
DEFAULT_PORT="3306"
DEFAULT_DATABASE="voice_diagnosis_db"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # 无颜色

echo -e "${GREEN}声音诊断系统 MySQL 配置工具${NC}"
echo "===========================================" 
echo "此脚本将帮助您设置MySQL数据库连接参数"
echo "===========================================" 

# 提示用户输入MySQL配置信息
read -p "MySQL用户名 [默认: $DEFAULT_USER]: " MYSQL_USER
MYSQL_USER=${MYSQL_USER:-$DEFAULT_USER}

read -s -p "MySQL密码 [默认: 空密码]: " MYSQL_PASSWORD
echo ""
MYSQL_PASSWORD=${MYSQL_PASSWORD:-$DEFAULT_PASSWORD}

read -p "MySQL主机 [默认: $DEFAULT_HOST]: " MYSQL_HOST
MYSQL_HOST=${MYSQL_HOST:-$DEFAULT_HOST}

read -p "MySQL端口 [默认: $DEFAULT_PORT]: " MYSQL_PORT
MYSQL_PORT=${MYSQL_PORT:-$DEFAULT_PORT}

read -p "数据库名称 [默认: $DEFAULT_DATABASE]: " MYSQL_DATABASE
MYSQL_DATABASE=${MYSQL_DATABASE:-$DEFAULT_DATABASE}

echo ""
echo -e "${YELLOW}将使用以下配置:${NC}"
echo "用户名: $MYSQL_USER"
echo "密码: ***" # 不显示实际密码
echo "主机: $MYSQL_HOST" 
echo "端口: $MYSQL_PORT"
echo "数据库: $MYSQL_DATABASE"
echo ""

# 导出为环境变量
echo "正在设置环境变量..."
export MYSQL_USER=$MYSQL_USER
export MYSQL_PASSWORD=$MYSQL_PASSWORD
export MYSQL_HOST=$MYSQL_HOST
export MYSQL_PORT=$MYSQL_PORT
export MYSQL_DATABASE=$MYSQL_DATABASE

echo -e "${GREEN}环境变量已设置!${NC}"
echo "" 
echo "可以使用以下命令初始化数据库:"
echo "cd backend && python init_mysql_db.py"
echo ""
echo "注意: 这些环境变量只在当前终端会话中有效"
echo "如果要永久保存，请将它们添加到您的 .bashrc 或 .zshrc 文件中" 