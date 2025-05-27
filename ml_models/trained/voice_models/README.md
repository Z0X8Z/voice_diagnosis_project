# 语音模型目录

本目录用于存放项目使用的各种语音相关模型，包括但不限于：
- 语音特征提取模型
- 声音健康评估模型
- 语音分类模型
- 语音情感分析模型

## 模型目录结构

```
voice_models/
├── feature_extractor/            # 特征提取模型
│   ├── model.pkl                 # 模型文件
│   └── config.json               # 配置文件
├── health_classifier/            # 声音健康分类器
│   ├── model.h5                  # 模型文件
│   └── labels.json               # 标签映射
├── emotion_detector/             # 情感检测模型
│   └── model.pt                  # PyTorch模型
└── ...
```

## 模型加载和使用

语音模型通常由`backend/app/services/model_service.py`中的服务类加载和使用。例如：

```python
# 在VoiceModelService中加载模型
def _load_models(self):
    """加载训练好的模型"""
    try:
        model_path = os.path.join(
            os.path.dirname(__file__), 
            '..', '..', '..', 
            'ml_models', 'trained', 'voice_models', 
            'health_classifier', 'model.h5'
        )
        # 加载模型
        self.models['health_classifier'] = load_model(model_path)
        
    except Exception as e:
        logger.error(f"加载模型失败: {str(e)}")
```

## 模型更新流程

1. 在`ml_models/training/`中开发和训练新模型
2. 对模型进行评估和验证
3. 将训练好的模型保存到对应的子目录
4. 更新模型的配置文件和文档
5. 更新服务层代码以使用新模型

## 版本管理

每个模型应包含版本信息，并在更新时记录变更：

```
feature_extractor_v1.0/
feature_extractor_v1.1/
```

## 模型元数据

每个模型目录应包含配置文件（如config.json），记录以下信息：

```json
{
  "name": "健康声音分类器",
  "version": "1.0",
  "created_at": "2023-05-15",
  "framework": "tensorflow",
  "input_shape": [26],
  "output_shape": [2],
  "accuracy": 0.92,
  "labels": ["健康", "异常"],
  "features": ["短时能量", "过零率", "谐噪比", "..."]
}
``` 