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
│   ├── src/
│   │   ├── views/         # 页面组件
│   │   ├── stores/        # 状态管理
│   │   ├── router/        # 路由配置
│   │   └── components/    # 通用组件
│   ├── public/
│   └── package.json
├── ml_models/            # 机器学习模型
│   ├── trained/          # 训练好的模型
│   └── training/         # 训练脚本
├── requirements.txt      # Python依赖
└── README.md            # 项目文档
```

## 功能特性

- 用户认证系统
  - 用户注册
  - 用户登录
  - 权限控制
- 语音数据采集和处理
  - 语音上传
  - 实时录音
  - 音频预处理
- AI模型诊断
  - 声音特征提取
  - 机器学习分析
  - 诊断结果生成
- 大语言模型分析
  - 诊断报告生成
  - 专业建议提供
- 历史记录管理
  - 诊断历史查询
  - 数据统计分析
- 数据可视化面板
  - 语音波形显示
  - 诊断指标展示
  - 趋势分析图表

## 安装说明

1. 克隆项目
```bash
git clone https://github.com/Z0X8Z/voice_diagnosis_project
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
创建 `.env` 文件并设置必要的环境变量：
```
# 数据库配置
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=voice_diagnosis

# JWT配置
SECRET_KEY=your_secret_key
```

5. 启动服务
- 后端：`uvicorn main:app --reload`
- 前端：`npm run dev`

## 技术栈

- 前端：Vue.js, Element Plus, Echarts
- 后端：FastAPI, SQLAlchemy
- 数据库：MySQL
- AI模型：PyTorch
- 部署：Docker, Nginx

## 开发团队

- 后端开发：[开发者名字]
- 前端开发：[开发者名字]
- AI模型：[开发者名字]

## 开源协议

MIT License
