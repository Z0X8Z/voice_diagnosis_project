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
- React
- TypeScript
- Ant Design
- ECharts

## 安装步骤

1. 克隆项目
```bash
git clone git@github.com:Z0X8Z/voice_diagnosis_project.git
cd <项目目录>
```

2. 安装后端依赖
```bash
cd backend
pip install -r requirements.txt
```

3. 安装前端依赖
```bash
cd frontend
npm install
```

4. 配置环境变量
```bash
cd backend
python scripts/setup_env.py
```
按照提示输入配置信息，或直接使用默认值。

5. 初始化数据库
```bash
cd backend
python scripts/init_mysql_db.py
```

## 运行项目

1. 启动后端服务
```bash
cd backend
uvicorn main:app --reload
```

2. 启动前端服务
```bash
cd frontend
npm start
```

3. 访问应用
- 后端API文档：http://localhost:8000/docs
- 前端应用：http://localhost:3000

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
│   └── tests/            # 测试文件
├── frontend/              # 前端代码
│   ├── src/              # 源代码
│   │   ├── components/   # 组件
│   │   ├── pages/        # 页面
│   │   ├── services/     # 服务
│   │   └── utils/        # 工具
│   └── public/           # 静态资源
└── docs/                 # 文档
```

## 开发指南

### 后端开发

1. 创建新的API端点
- 在 `app/api/v1/endpoints/` 下创建新的路由文件
- 在 `app/api/v1/api.py` 中注册路由

2. 添加新的数据模型
- 在 `app/models/` 下创建新的模型文件
- 运行数据库迁移：
   ```bash
cd backend
alembic revision --autogenerate -m "描述"
alembic upgrade head
```

### 前端开发

1. 创建新的组件
- 在 `src/components/` 下创建新的组件文件
- 在 `src/pages/` 下创建新的页面文件

2. 添加新的API服务
- 在 `src/services/` 下创建新的服务文件

## 测试

### 后端测试
   ```bash
cd backend
pytest
```

### 前端测试
```bash
cd frontend
npm test
```

## 部署

### 后端部署
1. 构建Docker镜像
```bash
cd backend
docker build -t voice-analysis-backend .
   ```

2. 运行容器
   ```bash
docker run -d -p 8000:8000 voice-analysis-backend
   ```

### 前端部署
1. 构建生产版本
   ```bash
cd frontend
npm run build
```

2. 部署到Web服务器
将 `build` 目录下的文件部署到Web服务器。

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

如有问题或建议，请提交 Issue 或联系项目维护者。
