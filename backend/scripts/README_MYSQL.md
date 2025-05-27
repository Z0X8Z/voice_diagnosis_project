# MySQL 数据库配置和使用指南

本文档介绍如何在声音诊断系统中配置和使用 MySQL 数据库。

## 先决条件

1. 已安装 MySQL 服务器（5.7+ 或 8.0+）
2. Python 3.8+
3. 项目依赖已安装 (`pip install -r requirements.txt`)

## 配置 MySQL 连接

项目支持两种方式配置 MySQL 连接参数：

### 1. 通过环境变量

系统会按以下优先级查找 MySQL 连接参数：
1. 环境变量
2. 配置文件默认值

可用的环境变量：
- `MYSQL_USER` - MySQL 用户名（默认：root）
- `MYSQL_PASSWORD` - MySQL 密码（默认：空）
- `MYSQL_HOST` - MySQL 主机地址（默认：localhost）
- `MYSQL_PORT` - MySQL 端口（默认：3306）
- `MYSQL_DATABASE` - 数据库名称（默认：voice_diagnosis_db）

### 2. 使用配置助手脚本

我们提供了一个脚本简化环境变量设置：

```bash
# 进入项目目录
cd 项目根目录

# 给脚本执行权限
chmod +x backend/setup_mysql_env.sh

# 运行配置脚本
source backend/setup_mysql_env.sh
```

## 初始化数据库

首次使用 MySQL 前，需要创建数据库和表结构：

```bash
# 确保当前处于项目根目录
cd 项目根目录

# 运行初始化脚本
python backend/init_mysql_db.py
```

初始化脚本将：
1. 创建数据库（如果不存在）
2. 创建所有必要的表
3. 设置表关系和索引

## 故障排除

### 连接错误

如果遇到类似 `Access denied for user 'root'@'localhost'` 的错误，请尝试：

1. 检查您的 MySQL 用户密码配置
2. 确认用户具有创建数据库的权限
3. 尝试从命令行登录 MySQL 验证凭据：`mysql -u root -p`

### 表结构更新

如果您修改了数据模型，需要更新表结构：

1. 使用 MySQL 工具手动更新表（推荐用于生产环境）
2. 删除并重新创建数据库（仅用于开发环境）：
   ```bash
   mysql -u root -p -e "DROP DATABASE IF EXISTS voice_diagnosis_db; CREATE DATABASE voice_diagnosis_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
   python backend/init_mysql_db.py
   ```

## 生产环境最佳实践

1. 创建专用数据库用户，而不是使用 root
2. 设置强密码
3. 限制数据库用户权限
4. 使用环境变量管理敏感配置
5. 定期备份数据库 