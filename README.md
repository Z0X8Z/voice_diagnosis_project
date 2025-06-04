# 声肺康智能分析系统

声肺康智能分析系统是一个基于声音分析的肺部健康评估系统，通过分析用户的声音特征来评估肺部健康状况。

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

### 前提条件
- [Anaconda](https://www.anaconda.com/products/distribution) 或 [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
- [Node.js](https://nodejs.org/) (推荐 16+ 版本)
- [MySQL](https://dev.mysql.com/downloads/) (可选，系统可使用内置SQLite)

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
pip install -r backend/requirements.txt
```

### 3. 前端环境配置

#### 3.1 安装前端依赖
```bash
cd frontend
npm install
```

#### 3.2 配置API地址
创建前端环境配置文件：
```bash
# 在frontend目录下创建.env文件
echo "VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1" > .env
```

### 4. 数据库配置（可选）
```bash
cd ../backend
python scripts/setup_env.py
# 按提示配置，或直接使用默认SQLite数据库
```

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

#### ❌ MySQL连接失败

**解决方案：**
1. 确保MySQL服务运行：`sudo service mysql start`
2. 或使用SQLite（默认）：无需额外配置
3. 初始化数据库：`python scripts/init_mysql_db.py`

### 前端问题

#### ❌ 网络错误：timeout of 10000ms exceeded

**原因：** 前端API配置错误或后端未启动

**解决方案：**
1. 确认后端服务运行：`lsof -i :8000` 或访问 http://127.0.0.1:8000
2. 检查前端.env文件：
   ```bash
   # frontend/.env
   VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
   ```
3. 重启前端服务：`npm run dev`

#### ❌ 跨域问题 (CORS)

**解决方案：**
后端已配置CORS，如仍有问题，检查API地址是否正确

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

## 项目结构

```
.
├── backend/                # 后端代码
│   ├── app/               # 应用代码
│   │   ├── api/          # API路由
│   │   ├── core/         # 核心配置
│   │   ├── db/           # 数据库
│   │   ├── models/       # 数据模型
│   │   ├── schemas/      # 数据模式
│   │   └── services/     # 业务服务
│   ├── scripts/          # 脚本文件
│   ├── logs/             # 日志文件
│   ├── uploads/          # 上传文件
│   └── tests/            # 测试文件
├── frontend/              # 前端代码
│   ├── src/              # 源代码
│   │   ├── components/   # 组件
│   │   ├── pages/        # 页面
│   │   ├── services/     # 服务
│   │   ├── composables/  # 组合式API
│   │   └── utils/        # 工具
│   ├── public/           # 静态资源
│   └── .env             # 环境配置
├── ml_models/             # 机器学习模型
└── docs/                 # 文档
```

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
| 牛志宇 | 项目负责人、文档撰写         | 选定题目、系统可行性与需求分析、文档撰写 |
| 张绪正 | 架构设计、数据库设计         | 系统概要设计、数据库设计、详细设计   |
| 张胜希 | 核心开发                     | 编程实现主要模块和功能               |
| 惠国轩 | 测试与调试                   | 系统调试与测试                       |
| 刘储瑜 | 项目优化、结题、文档完善     | 项目改进提升、结题准备、文档撰写     |

---

⭐ **如果这个项目对您有帮助，请给我们一个Star！**

🎯 **项目状态**: 积极维护中

📈 **版本**: v1.0.0

