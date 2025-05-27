# 声肺康后端服务

声肺康是一个基于声音分析的肺部健康检测系统，采用FastAPI框架开发。系统通过分析用户的语音特征，结合AI模型和大型语言模型(LLM)，提供肺部健康状况的评估和建议。

## 项目结构

```
backend/
├── app/                    # 应用核心代码
│   ├── api/                # API路由
│   │   └── v1/             # API版本1
│   │       └── endpoints/  # API端点
│   │           ├── auth.py         # 认证相关接口
│   │           ├── dashboard.py    # 仪表盘相关接口
│   │           ├── diagnosis.py    # 诊断分析相关接口
│   │           ├── llm.py          # 大语言模型相关接口
│   │           └── users.py        # 用户管理相关接口
│   ├── core/               # 核心配置
│   ├── db/                 # 数据库相关
│   ├── models/             # 数据模型
│   ├── schemas/            # 请求/响应模式
│   └── services/           # 业务服务
│       ├── llm_service.py         # LLM服务
│       └── model_service.py       # 模型服务
├── ml_models/              # 机器学习模型
│   ├── src/                # 模型源代码
│   │   ├── feature_extractors/  # 特征提取器
│   │   └── predictors/          # 预测模型
│   └── configs/            # 模型配置
├── tests/                  # 测试
│   └── outputs/            # 测试输出目录
├── uploads/                # 用户上传文件目录
├── main.py                 # 主程序入口
└── requirements.txt        # 依赖包列表
```

## API路由结构

系统的API路由结构如下：

### 1. 认证路由 (/api/v1/auth)
- `POST /login` - 用户登录，获取访问令牌
- `POST /register` - 新用户注册

### 2. 用户管理路由 (/api/v1/users)
- `GET /me` - 获取当前用户信息
- `PUT /me` - 更新当前用户信息
- `GET /{user_id}` - 获取指定用户信息
- `PUT /{user_id}` - 更新指定用户信息
- `DELETE /{user_id}` - 删除指定用户

### 3. 诊断分析路由 (/api/v1/diagnosis)
- `POST /upload` - 上传语音文件
- `POST /features/{session_id}` - 从语音文件提取特征
- `POST /analyze/{session_id}` - 对语音进行AI模型分析
- `GET /visualization/{session_id}` - 获取诊断可视化数据
- `POST /complete/{session_id}` - 完成诊断会话并生成最终报告

### 4. LLM路由 (/api/v1/llm)
- `GET /summary` - 获取用于显示的摘要数据
- `GET /realtime` - 获取实时监控数据
- `POST /analyze/{session_id}` - 使用LLM分析语音诊断结果
- `POST /followup/{session_id}` - 向LLM提出后续问题
- `GET /conversation/{session_id}` - 获取与LLM的对话历史

### 5. 仪表盘路由 (/api/v1/dashboard)
- `GET /spectrum` - 获取频谱分析数据
- `GET /clustering` - 获取聚类分析数据
- `GET /trends` - 获取指定指标的趋势分析
- `POST /settings` - 更新用户的仪表盘设置
- `GET /settings` - 获取用户的仪表盘设置
- `GET /recent-sessions` - 获取用户最近的诊断会话

## 诊断流程

1. 用户上传语音文件 (`POST /diagnosis/upload`)
2. 系统从语音文件中提取特征 (`POST /diagnosis/features/{session_id}`)
3. 使用AI模型分析语音特征 (`POST /diagnosis/analyze/{session_id}`)
4. 使用LLM对分析结果进行解读 (`POST /llm/analyze/{session_id}`)
5. 用户可以向LLM提出后续问题 (`POST /llm/followup/{session_id}`)
6. 完成诊断会话并生成最终报告 (`POST /diagnosis/complete/{session_id}`)

## 安装与启动

1. 克隆项目
```bash
git clone <repository_url>
cd backend
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 设置环境变量
```bash
cp .env.example .env
# 编辑.env文件，设置必要的环境变量
```

4. 启动服务
```bash
uvicorn main:app --reload
```

API文档将在 `http://localhost:8000/docs` 可用。

## 模型与服务

本系统使用多层架构组织与模型相关的代码：

1. `app/models/` - 实现底层功能，如特征提取器
2. `app/services/` - 提供业务服务，桥接模型和API

系统使用的训练好的机器学习模型存放在项目根目录的`ml_models/trained/`目录中。
服务层负责加载这些模型并使用它们来处理请求。

详细的模型相关目录说明请参见 [docs/models_explanation.md](../docs/models_explanation.md)。

## 测试

项目包含多种测试脚本，位于`tests`目录下。

### 运行语音特征提取测试

```bash
# 生成测试音频并提取特征
python tests/test_feature_extractor.py --generate --visualize

# 使用已有音频文件测试
python tests/test_feature_extractor.py --file path/to/audio.wav

# 生成模拟咳嗽音频并测试
python tests/test_feature_extractor.py --generate --simulate-cough --visualize
```

所有测试输出（音频文件、特征数据、可视化图表）会保存在`tests/outputs/`目录中。

## 数据库配置

详细的数据库配置信息请参见 [scripts/README_MYSQL.md](./scripts/README_MYSQL.md)。

## 辅助脚本

项目包含多个辅助脚本，位于`scripts`目录下：

1. `setup_mysql_env.sh` - 交互式设置MySQL环境变量的脚本
2. `init_mysql_db.py` - 初始化数据库和表结构的脚本
3. `generate_er.py` - 生成数据库ER图的工具

## API文档

系统提供两种API文档：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc` 