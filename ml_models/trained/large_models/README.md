# 大型模型存储目录

本目录用于存放项目使用的大型模型，包括但不限于：
- 语音分析大模型
- 定制化语音识别模型
- 定制化大语言模型
- 其他占用空间较大的模型

## 模型目录结构

建议每个大型模型使用独立的子目录，并遵循以下结构：

```
large_models/
├── voice_analysis_llm/           # 语音分析大模型
│   ├── model.bin                 # 模型文件
│   ├── config.json               # 配置文件
│   └── README.md                 # 模型说明文档
├── custom_speech_model/          # 定制语音识别模型
│   ├── model/                    # 模型目录
│   ├── tokenizer/                # 分词器
│   └── README.md                 # 模型说明文档
└── ...
```

## 模型版本管理

为有效管理大型模型文件，建议：

1. 使用Git LFS来管理大型文件
   ```
   git lfs track "*.bin" "*.pt" "*.h5"
   ```

2. 为每个模型提供版本信息和检查点，例如：
   ```
   voice_analysis_llm_v1.0/
   voice_analysis_llm_v1.1/
   ```

3. 在不需要保留多个版本时，只保留最新版本，减少存储空间占用

## 外部存储集成

对于特别大的模型（>1GB），建议：

1. 将模型存储在云存储服务中（如阿里云OSS、AWS S3等）
2. 在本地保留模型的配置文件和小型元数据
3. 在代码中使用配置指定模型的远程URL，需要时自动下载

```python
# 示例代码：动态加载大型模型
from app.services.model_loader import download_model_if_needed

model_path = download_model_if_needed("voice_analysis_llm", "v1.0")
model = load_model(model_path)
```

## 模型文档要求

每个模型目录应包含README.md文件，至少包含以下信息：

1. 模型名称和版本
2. 训练数据描述
3. 性能指标
4. 输入/输出格式
5. 使用示例
6. 训练/微调说明
7. 许可信息 