# 声肺康智能分析系统 - 新用户部署指南

## 📋 概述

本指南面向需要在全新环境中部署声肺康智能分析系统的新用户。包含完整的环境搭建、项目配置和部署流程。

## 🛠️ 系统要求

### 操作系统
- **macOS**: 10.14+ 
- **Windows**: 10/11
- **Linux**: Ubuntu 18.04+ / CentOS 7+

### 硬件要求
- **RAM**: 最低 8GB，推荐 16GB+
- **存储**: 至少 5GB 可用空间
- **网络**: 稳定的互联网连接（用于下载依赖）

## 📥 第一步：获取项目代码

### 1.1 安装Git（如果未安装）

**macOS:**
```bash
# 使用Homebrew安装
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install git
```

**Windows:**
- 下载并安装 [Git for Windows](https://gitforwindows.org/)

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install git -y
```

### 1.2 克隆项目
```bash
# 克隆项目到本地
git clone https://github.com/Z0X8Z/voice_diagnosis_project.git
cd voice_diagnosis_project
```

## 🐍 第二步：Python环境配置

### 2.1 安装Anaconda

**下载地址：** https://www.anaconda.com/products/distribution

**macOS/Linux安装:**
```bash
# 下载后安装
bash Anaconda3-2023.xx-MacOSX-x86_64.sh  # macOS
bash Anaconda3-2023.xx-Linux-x86_64.sh   # Linux
```

**Windows安装:**
- 双击下载的 `.exe` 文件，按提示安装

### 2.2 验证Anaconda安装
```bash
conda --version
# 应该显示conda版本号
```

### 2.3 创建项目专用Python环境
```bash
# 创建新的conda环境
conda create -n voice_diagnosis_env python=3.10 -y

# 激活环境
conda activate voice_diagnosis_env

# 验证环境
which python  # macOS/Linux
where python  # Windows
# 应该显示包含voice_diagnosis_env的路径
```

## 🔧 第三步：后端环境配置

### 3.1 安装后端依赖
```bash
# 确保在项目根目录且环境已激活
conda activate voice_diagnosis_env
cd backend
pip install -r requirements.txt
```

### 3.2 处理依赖安装问题（如遇到）

**常见问题1：PyYAML安装失败**
```bash
# 指定版本安装
pip install PyYAML==6.0.1
```

**常见问题2：构建工具缺失**
```bash
# macOS
xcode-select --install

# Ubuntu/Debian
sudo apt install build-essential python3-dev

# CentOS/RHEL
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel
```

### 3.3 数据库配置

**选项1：使用SQLite（推荐新手）**
```bash
# 无需额外配置，系统会自动创建SQLite数据库
python scripts/setup_env.py
# 选择使用SQLite（选项2）
```

**选项2：使用MySQL**
```bash
# 安装MySQL
# macOS: brew install mysql
# Ubuntu: sudo apt install mysql-server
# Windows: 下载MySQL Installer

# 启动MySQL服务
# macOS: brew services start mysql
# Linux: sudo systemctl start mysql

# 创建数据库
mysql -u root -p
CREATE DATABASE voice_diagnosis;
CREATE USER 'voice_user'@'localhost' IDENTIFIED BY 'voice_password';
GRANT ALL PRIVILEGES ON voice_diagnosis.* TO 'voice_user'@'localhost';
FLUSH PRIVILEGES;
exit;

# 配置环境
python scripts/setup_env.py
# 选择MySQL并输入连接信息
```

### 3.4 初始化数据库
```bash
# 在backend目录下执行
python scripts/init_mysql_db.py
```

## 🌐 第四步：前端环境配置

### 4.1 安装Node.js

**下载地址：** https://nodejs.org/

**推荐版本：** LTS版本（当前推荐18.x）

**验证安装:**
```bash
node --version  # 应显示v18.x.x
npm --version   # 应显示npm版本
```

### 4.2 安装前端依赖
```bash
cd frontend
npm install

# 如果npm安装慢，可以使用国内镜像
npm config set registry https://registry.npm.taobao.org
npm install
```

### 4.3 配置前端环境
```bash
# 在frontend目录下创建环境配置文件
echo "VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1" > .env
```

## 🚀 第五步：启动系统

### 5.1 启动后端服务

**在第一个终端窗口:**
```bash
# 激活环境
conda activate voice_diagnosis_env

# 切换到backend目录
cd voice_diagnosis_project/backend

# 启动后端
python main.py
```

**成功标志:**
- 看到 "INFO:     Will watch for changes in these directories"
- 访问 http://127.0.0.1:8000 显示欢迎消息
- API文档可访问：http://127.0.0.1:8000/docs

### 5.2 启动前端服务

**在第二个终端窗口:**
```bash
cd voice_diagnosis_project/frontend
npm run dev
```

**成功标志:**
- 显示本地访问地址（通常是 http://localhost:5173）
- 浏览器显示登录页面

## ✅ 第六步：系统验证

### 6.1 验证后端API
```bash
# 测试基础API
curl http://127.0.0.1:8000/
# 期望输出：{"message":"欢迎使用声肺康系统"}

# 测试健康检查
curl http://127.0.0.1:8000/health
# 期望输出：{"status":"healthy"}
```

### 6.2 验证前端功能
1. 访问 http://localhost:5173
2. 看到登录页面
3. 点击"注册"创建新账户
4. 登录后能看到主页面

### 6.3 验证数据库连接
```bash
# 在backend目录下运行
python -c "
from app.core.database import get_db, engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('数据库连接成功:', result.fetchone())
"
```

## 🔒 第七步：生产环境部署（可选）

### 7.1 环境变量配置
```bash
# 创建生产环境配置
cp backend/.env.example backend/.env

# 编辑配置文件，设置：
# - SECRET_KEY: 随机密钥
# - DATABASE_URL: 生产数据库地址
# - CORS_ORIGINS: 允许的前端域名
```

### 7.2 构建前端
```bash
cd frontend
npm run build
# 生成的dist目录包含静态文件
```

### 7.3 使用反向代理（推荐）
```nginx
# Nginx配置示例
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # 后端API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🐛 常见问题解决

### 问题1：conda命令找不到
**解决方案：**
```bash
# 添加conda到PATH
echo 'export PATH="$HOME/anaconda3/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### 问题2：后端启动失败 - ModuleNotFoundError
**解决方案：**
```bash
# 确保环境激活
conda activate voice_diagnosis_env
# 确保在backend目录下
cd backend
# 重新安装依赖
pip install -r requirements.txt
```

### 问题3：前端npm install失败
**解决方案：**
```bash
# 清理缓存
npm cache clean --force
# 删除node_modules重新安装
rm -rf node_modules package-lock.json
npm install
```

### 问题4：数据库连接失败
**解决方案：**
```bash
# 检查MySQL服务状态
# macOS: brew services list | grep mysql
# Linux: systemctl status mysql

# 重新配置数据库
python scripts/setup_env.py
```

### 问题5：端口被占用
**解决方案：**
```bash
# 查找占用端口的进程
# macOS/Linux: lsof -i :8000
# Windows: netstat -ano | findstr :8000

# 杀死进程或更换端口
python main.py --port 8001
```

## 📞 技术支持

### 获取帮助
1. **查看日志：** `backend/logs/` 目录下的日志文件
2. **GitHub Issues：** https://github.com/Z0X8Z/voice_diagnosis_project/issues
3. **文档：** 项目根目录下的README.md

### 开发环境重置
```bash
# 完全重置环境
conda deactivate
conda env remove -n voice_diagnosis_env
# 然后重新按照指南操作
```

## 🎯 下一步

项目部署成功后，您可以：

1. **学习使用：** 探索系统各功能模块
2. **定制开发：** 根据需求修改代码
3. **数据备份：** 定期备份数据库
4. **监控运维：** 设置日志监控和性能监控

---

**祝您部署顺利！** 🎉

如有问题，请参考常见问题部分或提交Issue获取帮助。 