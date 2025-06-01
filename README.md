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
git clone https://github.com/Z0X8Z/voice_diagnosis_project.git
cd voice_diagnosis_project
```

2. 安装 Anaconda/Miniconda
请确保本地已安装 [Anaconda](https://www.anaconda.com/products/distribution) 或 [Miniconda](https://docs.conda.io/en/latest/miniconda.html)。

3. 创建并激活后端环境
```bash
conda create -n voice_diagnosis_env python=3.10 -y
conda activate voice_diagnosis_env
```

4. 安装后端依赖（推荐方式）
```bash
pip install -r backend/requirements.txt
```

> **注意：** 绝大多数情况下，直接执行上述命令即可自动安装所有主依赖和二级依赖。

5. 安装前端依赖
```bash
cd frontend
npm install
```

6. 配置环境变量（可选）
```bash
cd ../backend
python scripts/setup_env.py
```
按提示输入配置信息，或直接使用默认值。

7. 初始化数据库（如首次部署）
```bash
python scripts/init_mysql_db.py
```

8. 启动后端服务
```bash
cd backend
uvicorn main:app --reload
```
后端API文档地址：http://localhost:8000/docs

9. 启动前端服务
```bash
cd frontend
npm run dev
```
前端访问地址：http://localhost:3000

---

## 常见问题与解决

- **依赖安装失败/构建报错（如 PyYAML、exceptiongroup 等）**：
  某些环境下，个别依赖（如 PyYAML）可能因兼容性或构建问题导致安装失败。此时可采用如下手动安装方案：
  ```bash
  pip install pyyaml==6.0.1
  pip install -r backend/requirements.txt --no-deps
  pip install exceptiongroup tomli
  ```
  这样可规避部分依赖冲突或构建失败问题。

- **依赖安装失败**：请确保已激活`voice_diagnosis_env`环境，并使用`pip`安装依赖。
- **缺少依赖**：如遇`ModuleNotFoundError`，请根据报错信息手动`pip install`缺失的包。
- **端口冲突**：如8000或3000端口被占用，请修改启动命令或释放端口。

---

如需进一步自动化，可考虑编写一键安装脚本（如`install.sh`），进一步提升易用性。

如有问题请查阅项目README或联系维护者。

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

## 贡献人及分工

| 姓名   | 角色/分工                     | 主要工作内容                         |
|--------|------------------------------|--------------------------------------|
| 牛志宇 | 项目负责人、文档撰写         | 选定题目、系统可行性与需求分析、文档撰写 |
| 张绪正 | 架构设计、数据库设计         | 系统概要设计、数据库设计、详细设计   |
| 张胜希 | 核心开发                     | 编程实现主要模块和功能               |
| 惠国轩 | 测试与调试                   | 系统调试与测试                       |
| 刘储瑜 | 项目优化、结题、文档完善     | 项目改进提升、结题准备、文档撰写     |

