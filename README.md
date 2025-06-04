# 声肺康智能分析系统

声肺康智能分析系统是一个基于声音分析的肺部健康评估系统，通过分析用户的声音特征来评估肺部健康状况。

## ⚡ 新用户快速部署

**🚀 一键部署脚本（推荐）：**

```bash
# macOS/Linux用户
git clone https://github.com/Z0X8Z/voice_diagnosis_project.git
cd voice_diagnosis_project
chmod +x quick_setup.sh  # 确保脚本有执行权限
./quick_setup.sh

# Windows用户
git clone https://github.com/Z0X8Z/voice_diagnosis_project.git
cd voice_diagnosis_project
quick_setup.bat
```

**⚠️ 前提条件：**
- 已安装 [Anaconda/Miniconda](https://www.anaconda.com/products/distribution)
- 已安装 [Node.js](https://nodejs.org/) (LTS版本，推荐16+)
- Git (用于克隆项目)

### 🔄 克隆项目常见问题

#### 克隆速度慢或连接超时
如果从GitHub克隆速度较慢，可以尝试以下方法：

```bash
# 方法1：使用国内镜像（如Gitee）
git clone https://gitee.com/mirrors/voice_diagnosis_project.git

# 方法2：设置Git代理（如果有代理服务器）
git config --global http.proxy http://127.0.0.1:7890
git clone https://github.com/Z0X8Z/voice_diagnosis_project.git
# 完成后可以取消代理
git config --global --unset http.proxy
```

#### 权限问题
在Linux/macOS系统中，如果脚本无法执行，请确保设置了执行权限：

```bash
chmod +x quick_setup.sh
```

---

## 功能特点

- 声音特征分析
- 肺部健康评估
- 历史数据追踪
- 趋势分析
- 用户管理
- 数据可视化

## 技术栈

### 后端
- Python 3.8+
- FastAPI
- SQLAlchemy
- MySQL
- Alembic
- JWT认证

### 前端
- Vue 3
- TypeScript
- Ant Design Vue
- ECharts

## 🚀 快速开始

### 系统要求
- **操作系统**：Windows 10+、macOS 10.15+、Ubuntu 18.04+
- **内存**：至少4GB RAM，推荐8GB+
- **存储**：至少2GB可用空间
- **处理器**：现代多核处理器（推荐Intel i5/AMD Ryzen 5或更高）

### 软件前提条件
- [Anaconda](https://www.anaconda.com/products/distribution) 或 [Miniconda](https://docs.conda.io/en/latest/miniconda.html) (Python环境管理)
- [Node.js](https://nodejs.org/) (推荐 16+ 版本)
- [MySQL](https://dev.mysql.com/downloads/) (可选，系统默认使用SQLite)
- [Git](https://git-scm.com/downloads) (用于克隆项目)

### 版本兼容性说明
- Python: 3.8-3.10 (推荐3.10)
- Node.js: 14-18 (推荐16 LTS)
- npm: 6+ (通常随Node.js安装)
- MySQL: 5.7+ 或 8.0+ (如果选择使用MySQL)

## 📦 安装步骤

### 1. 获取项目代码
```bash
git clone https://github.com/Z0X8Z/voice_diagnosis_project.git
cd voice_diagnosis_project
```

### 2. 后端环境配置

#### 2.1 创建并激活Conda环境
```bash
conda create -n voice_diagnosis_env python=3.10 -y
conda activate voice_diagnosis_env
```

#### 2.2 验证环境激活成功
```bash
conda env list
# 应该看到voice_diagnosis_env前面有*标记
```

#### 2.3 安装后端依赖
```bash
cd backend
# 使用更可靠的安装方法，避免依赖安装失败问题
pip install pyyaml==6.0.1
pip install -r requirements.txt --no-deps
pip install exceptiongroup tomli
```

### 3. 前端环境配置

#### 3.1 安装前端依赖
```bash
cd frontend
npm install
```

### 4. 数据库配置（可选）

```bash
cd ../backend  # 如果已经在backend目录，则不需要cd ../backend
# 自动配置SQLite数据库（推荐新手）
python scripts/setup_env.py --auto-sqlite

# 或按提示手动配置
python scripts/setup_env.py
```

#### 4.1 数据库选择说明
本项目支持两种数据库配置：
- **SQLite**（默认）：无需额外安装，适合开发和测试
- **MySQL**：需要额外安装MySQL服务器，适合生产环境

#### 4.2 初始化数据库
```bash
# 初始化数据库结构和基础数据
python scripts/init_mysql_db.py
```

#### 4.3 数据库配置文件
配置会生成在`backend/.env`文件中，包含以下主要内容：
- 项目基本配置
- 安全配置（密钥等）
- 数据库连接信息
- CORS配置

## 🏃‍♂️ 运行系统

### 启动后端服务

⚠️ **重要：必须在backend目录下运行后端服务**

```bash
# 确保在项目根目录
cd backend

# 方法1：直接运行（推荐）
python main.py

# 方法2：使用uvicorn
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

✅ **后端启动成功标志：**
- 看到 "Will watch for changes" 信息
- 访问 http://127.0.0.1:8000 显示欢迎信息
- API文档：http://127.0.0.1:8000/docs

### 启动前端服务

```bash
# 在新的终端窗口中
cd frontend
npm run dev
```

✅ **前端启动成功标志：**
- 显示本地访问地址（通常是 http://localhost:5173）
- 浏览器自动打开或手动访问显示登录页面

## 🔧 环境验证

### 验证后端环境
```bash
# 激活环境后测试
conda activate voice_diagnosis_env
python -c "import fastapi; print('FastAPI版本:', fastapi.__version__)"
python -c "import sqlalchemy; print('SQLAlchemy版本:', sqlalchemy.__version__)"
```

### 验证前端环境
```bash
cd frontend
npm run build  # 测试构建是否成功
```

### 验证API连接
```bash
# 后端启动后测试
curl http://127.0.0.1:8000/
# 应该返回：{"message":"欢迎使用声肺康系统"}
```

### 验证数据库连接
```bash
curl http://127.0.0.1:8000/db-status
```

## 🐛 常见问题与解决方案

### 后端问题

#### ❌ ModuleNotFoundError: No module named 'fastapi'

**原因：** 环境未正确激活或依赖未安装

**解决方案：**
1. 确认环境激活：`conda env list` 查看*标记
2. 重新激活：`conda activate voice_diagnosis_env`
3. 重新安装依赖：`pip install -r backend/requirements.txt`
4. **关键：在backend目录下运行**

#### ❌ 导入错误：from app.core.config import settings

**原因：** 不在正确的工作目录

**解决方案：**
```bash
# 必须在backend目录下运行
cd backend
python main.py
# 不要使用Python解释器的完整路径
```

#### ❌ 依赖安装失败/构建报错

**常见报错：** PyYAML、exceptiongroup、tomli等包安装失败

**解决方案：**

某些环境下，个别依赖（如 PyYAML）可能因兼容性或构建问题导致安装失败。此时可采用如下手动安装方案：

```bash
# 方案1：指定版本安装
pip install pyyaml==6.0.1
pip install -r backend/requirements.txt --no-deps
pip install exceptiongroup tomli

# 方案2：逐个安装关键依赖
pip install fastapi==0.68.2
pip install sqlalchemy==1.4.54
pip install uvicorn==0.15.0
pip install python-dotenv==1.1.0
```

**说明：**
- `--no-deps` 跳过依赖检查，避免冲突
- 这样可规避部分依赖冲突或构建失败问题
- 如遇 `ModuleNotFoundError`，请根据报错信息手动 `pip install` 缺失的包

#### ❌ MySQL连接失败

**解决方案：**
1. 确保MySQL服务运行：`sudo service mysql start`
2. 或使用SQLite（默认）：无需额外配置
3. 初始化数据库：`python scripts/init_mysql_db.py`

#### ❌ 端口冲突

**症状：** 8000端口被占用，启动失败

**解决方案：**
```bash
# 查看端口占用
lsof -i :8000

# 释放端口或更改端口
uvicorn main:app --port 8001  # 更改后端端口
# 或在main.py中修改端口号
```

### 前端问题

#### ❌ 网络错误：timeout of 10000ms exceeded

**原因：** 前端API配置错误或后端未启动

**解决方案：**
1. 确认后端服务运行：`lsof -i :8000` 或访问 http://127.0.0.1:8000
2. 重启前端服务：`npm run dev`

#### ❌ 跨域问题 (CORS)

**解决方案：**
后端已配置CORS，如仍有问题，检查API地址是否正确

#### ❌ 前端端口冲突

**症状：** 3000或5173端口被占用

**解决方案：**
```bash
# 查看端口占用
lsof -i :5173

# 更改前端端口
npm run dev -- --port 3001
```

#### ❌ IDE显示"无法解析导入"错误

**症状：** IDE显示类似"无法解析导入'fastapi'"等错误，但代码可以正常运行

**原因：** IDE未正确识别Python解释器环境

**解决方案：**

1. **VS Code配置：**
   - 按 `Cmd + Shift + P`（Mac）或 `Ctrl + Shift + P`（Windows）
   - 输入 "Python: Select Interpreter"
   - 选择 `voice_diagnosis_env` 环境中的Python解释器
   - 路径通常为：`/opt/anaconda3/envs/voice_diagnosis_env/bin/python`

2. **PyCharm配置：**
   - 打开 `Preferences/Settings` -> `Project` -> `Python Interpreter`
   - 点击齿轮图标 -> `Add`
   - 选择 `Conda Environment` -> `Existing Environment`
   - 选择 `voice_diagnosis_env` 环境中的Python解释器

3. **验证配置：**
   ```bash
   # 确认环境激活
   conda activate voice_diagnosis_env
   
   # 验证fastapi安装
   pip list | grep fastapi
   ```

4. **如果问题仍然存在：**
   - 重启IDE
   - 重新安装fastapi：`pip uninstall fastapi -y && pip install fastapi==0.68.2`
   - 清除IDE缓存并重新加载窗口

**注意：** 此错误仅影响IDE的代码提示和错误检查，不影响实际代码运行。

### 环境问题

#### ❌ conda命令未找到

**解决方案：**
1. 安装Anaconda/Miniconda
2. 重启终端或执行：`source ~/.bashrc`

#### ❌ 端口占用

**解决方案：**
```bash
# 查看端口占用
lsof -i :8000  # 后端
lsof -i :5173  # 前端

# 释放端口或更改端口
uvicorn main:app --port 8001  # 更改后端端口
npm run dev -- --port 3001   # 更改前端端口
```

## 🧪 开发调试

### 开发模式运行
```bash
# 后端开发模式（自动重载）
cd backend
uvicorn main:app --reload

# 前端开发模式
cd frontend
npm run dev
```

### 日志查看
```bash
# 后端日志
tail -f backend/logs/app.log

# 前端网络请求
浏览器F12 -> Network 标签页
```

### API测试
- Swagger文档：http://127.0.0.1:8000/docs
- Postman/Insomnia 导入OpenAPI规范

## 🔍 故障排除流程

### 故障排除流程图

```
┌─────────────────┐
│ 项目启动失败    │
└────────┬────────┘
         ▼
┌─────────────────┐     ┌─────────────────┐
│ 后端启动失败    │─────▶ 1. 检查环境激活 │
└────────┬────────┘     │ 2. 检查依赖安装 │
         │              │ 3. 检查工作目录 │
         │              │ 4. 检查端口占用 │
         │              └─────────────────┘
         ▼
┌─────────────────┐     ┌─────────────────┐
│ 前端启动失败    │─────▶ 1. 检查npm安装  │
└────────┬────────┘     │ 2. 检查依赖安装 │
         │              │ 3. 检查端口占用 │
         │              └─────────────────┘
         ▼
┌─────────────────┐     ┌─────────────────┐
│ 运行时错误      │─────▶ 1. 查看日志     │
└────────┬────────┘     │ 2. 检查API连接  │
         │              │ 3. 检查数据库   │
         │              └─────────────────┘
         ▼
┌─────────────────┐
│ 提交GitHub Issue│
└─────────────────┘
```

### 1. 环境检查
```bash
# 检查Python环境
which python
python --version

# 检查包安装
pip list | grep fastapi
pip list | grep sqlalchemy
```

### 2. 服务状态检查
```bash
# 检查后端服务
ps aux | grep python
lsof -i :8000

# 检查前端服务
ps aux | grep node
lsof -i :5173
```

### 3. 网络连接测试
```bash
# 测试后端API
curl -v http://127.0.0.1:8000/
curl -v http://127.0.0.1:8000/api/v1/auth/status

# 测试数据库连接
curl http://127.0.0.1:8000/db-status
```

### 4. 完整故障排除清单

如果遇到问题，请按照以下步骤进行排查：

1. **确认环境激活**
   - 确认conda环境已正确激活 (`conda activate voice_diagnosis_env`)
   - 检查Python版本是否为3.8-3.10 (`python --version`)

2. **检查依赖安装**
   - 后端依赖是否正确安装 (`pip list`)
   - 前端依赖是否正确安装 (`npm list --depth=0`)

3. **检查配置文件**
   - 后端配置文件(.env)是否存在且正确
   - 数据库连接是否正确配置

4. **检查网络和端口**
   - 确认所需端口未被占用 (8000, 5173)
   - 确认网络连接正常

5. **检查日志**
   - 查看后端日志 (`tail -f backend/logs/app.log`)
   - 查看浏览器控制台错误

6. **尝试重新安装**
   - 如持续失败，尝试使用一键部署脚本重新安装

## 项目结构

```
.
├── backend/                # 后端代码
│   ├── app/               # 应用代码
│   │   ├── api/          # API路由
│   │   │   └── v1/       # API v1版本
│   │   │       ├── endpoints/  # 各功能端点
│   │   │       └── deps.py     # 依赖项（认证等）
│   │   ├── core/         # 核心配置
│   │   │   ├── config.py       # 配置加载
│   │   │   └── security.py     # 安全相关
│   │   ├── db/           # 数据库
│   │   │   ├── base.py         # 基础模型
│   │   │   └── session.py      # 数据库会话
│   │   ├── models/       # 数据模型（ORM）
│   │   │   ├── user.py         # 用户模型
│   │   │   └── voice_record.py # 声音记录模型
│   │   ├── schemas/      # 数据模式（Pydantic）
│   │   │   ├── user.py         # 用户模式
│   │   │   └── voice.py        # 声音数据模式
│   │   └── services/     # 业务服务
│   │       ├── auth.py         # 认证服务
│   │       └── voice_analysis.py # 声音分析服务
│   ├── scripts/          # 脚本文件
│   │   ├── setup_env.py        # 环境配置脚本
│   │   └── init_mysql_db.py    # 数据库初始化
│   ├── logs/             # 日志文件
│   ├── main.py           # 应用入口
│   ├── requirements.txt  # 依赖列表
│   ├── .env              # 环境变量（自动生成）
│   └── tests/            # 测试文件
├── frontend/              # 前端代码
│   ├── src/              # 源代码
│   │   ├── components/   # 组件
│   │   │   ├── common/         # 通用组件
│   │   │   └── voice/          # 声音相关组件
│   │   ├── pages/        # 页面
│   │   │   ├── dashboard/      # 仪表盘页面
│   │   │   └── analysis/       # 分析页面
│   │   ├── services/     # 服务
│   │   │   ├── api.js          # API调用
│   │   │   └── auth.js         # 认证服务
│   │   ├── composables/  # 组合式API
│   │   └── utils/        # 工具
│   ├── public/           # 静态资源
│   ├── package.json      # 依赖配置
│   └── vite.config.js    # Vite配置
├── ml_models/             # 机器学习模型
│   ├── voice_classifier/  # 声音分类模型
│   └── feature_extractor/ # 特征提取模型
├── docs/                  # 文档
│   └── API.md             # API文档
├── quick_setup.sh         # Linux/macOS快速部署脚本
├── quick_setup.bat        # Windows快速部署脚本
├── environment.yml        # Conda环境配置
└── README.md              # 项目说明
```

### 关键文件说明

#### 后端核心文件
- `backend/main.py` - 应用入口点，包含FastAPI实例创建和路由注册
- `backend/app/core/config.py` - 配置加载，从.env文件读取环境变量
- `backend/app/db/session.py` - 数据库会话管理
- `backend/app/api/v1/endpoints/` - API端点实现

#### 前端核心文件
- `frontend/src/main.js` - 应用入口点
- `frontend/src/router/index.js` - 路由配置
- `frontend/src/store/index.js` - 状态管理
- `frontend/src/services/api.js` - 后端API调用

#### 配置文件
- `backend/.env` - 后端环境变量（运行setup_env.py生成）
- `environment.yml` - Conda环境配置
- `frontend/vite.config.js` - 前端构建配置

## 开发指南

### 后端开发

1. **创建新的API端点**
   ```bash
   # 在 app/api/v1/endpoints/ 下创建新文件
   # 在 main.py 中注册路由
   ```

2. **添加新的数据模型**
   ```bash
   cd backend
   alembic revision --autogenerate -m "描述"
   alembic upgrade head
   ```

### 前端开发

1. **创建新组件**
   ```bash
   # 在 src/components/ 下创建Vue组件
   # 使用Composition API风格
   ```

2. **添加新的API服务**
   ```bash
   # 在 src/composables/ 下创建API调用函数
   ```

## 测试

### 后端测试
```bash
cd backend
pytest -v
pytest tests/test_api.py  # 测试特定模块
```

### 前端测试
```bash
cd frontend
npm test
npm run test:coverage  # 覆盖率测试
```

## 部署

### 后端部署
```bash
cd backend
# 生产环境配置
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 前端部署
```bash
cd frontend
npm run build
# 将dist目录部署到Web服务器
```

### Docker部署
```bash
# 后端
cd backend
docker build -t voice-analysis-backend .
docker run -d -p 8000:8000 voice-analysis-backend

# 前端
cd frontend
docker build -t voice-analysis-frontend .
docker run -d -p 80:80 voice-analysis-frontend
```

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 代码规范
- Python: 遵循PEP 8规范
- Vue: 遵循Vue 3 Composition API规范
- 提交信息: 使用语义化提交格式

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📞 技术支持

- 🐛 **Bug报告**: [GitHub Issues](https://github.com/Z0X8Z/voice_diagnosis_project/issues)
- 💡 **功能建议**: [GitHub Discussions](https://github.com/Z0X8Z/voice_diagnosis_project/discussions)
- 📧 **技术咨询**: 联系项目维护者

## 👥 贡献者

| 姓名   | 角色/分工                     | 主要工作内容                         |
|--------|------------------------------|--------------------------------------|
| LoOp | 项目负责人、文档撰写         | 选定题目、系统可行性与需求分析、文档撰写 |
| 丁一 | 架构设计、数据库设计         | 系统概要设计、数据库设计、后端架构  |
| 塑料 | 核心开发                     | 编程模型训练、详细设计             |
| 风信然 | 测试与调试                   | 系统调试与测试                       |
| 荣筝 | 项目优化、结题、文档完善     | 项目改进提升、结题准备、文档撰写     |

---

⭐ **如果这个项目对您有帮助，请给我们一个Star！**

🎯 **项目状态**: 积极维护中

📈 **版本**: v1.0.0