# 环境变量配置说明

## 快速开始

1. 复制环境变量模板：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入你的实际配置：

### OpenAI 配置
```
OPENAI_API_KEY=你的API密钥
OPENAI_MODEL=Pro/deepseek-ai/DeepSeek-V3
OPENAI_API_BASE=https://api.siliconflow.cn/v1
```

### 数据库配置
```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=你的MySQL密码
MYSQL_DATABASE=project
```

### 安全配置
```
SECRET_KEY=你的密钥_生产环境请更改
```

## 安全注意事项

⚠️ **重要提醒：**
- `.env` 文件包含敏感信息，已被 `.gitignore` 忽略
- 不要将 `.env` 文件提交到 Git 仓库
- 生产环境中请使用强密码和随机生成的密钥
- 定期更换 API 密钥和数据库密码

## 如何使用

应用会自动从 `.env` 文件中读取配置。如果 `.env` 文件不存在或配置不完整，应用可能无法正常启动。

## 配置验证

启动应用时，请检查日志确保所有配置项都正确加载。 