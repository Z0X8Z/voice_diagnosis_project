# 语音诊断系统

这是一个基于语音分析的诊断系统，集成了机器学习模型和大语言模型，用于提供专业的诊断建议。

## 项目结构

```
project/
├── backend/                # 后端代码
│   ├── app/
│   │   ├── api/           # API路由
│   │   ├── core/          # 核心配置
│   │   ├── db/            # 数据库模型
│   │   ├── models/        # AI模型
│   │   └── services/      # 业务逻辑
│   └── main.py            # 后端入口
├── frontend/              # 前端代码
│   ├── public/
│   ├── src/
│   └── package.json
├── requirements.txt       # Python依赖
└── README.md             # 项目文档
```

## 功能特性

- 用户认证系统
- 语音数据采集和处理
- AI模型诊断
- 大语言模型分析
- 历史记录管理
- 数据可视化面板

## 安装说明

1. 克隆项目
```bash
git clone [项目地址]
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
创建 `.env` 文件并设置必要的环境变量

5. 启动服务
- 后端：`uvicorn main:app --reload`
- 前端：`npm start`

## 技术栈

- 前端：React.js, Ant Design, Echarts
- 后端：FastAPI, SQLAlchemy
- 数据库：MySQL
- AI模型：PyTorch
- 部署：Docker, Nginx 