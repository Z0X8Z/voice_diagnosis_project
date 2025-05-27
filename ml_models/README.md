# 机器学习模型

本目录包含项目中使用的所有机器学习模型和算法。

## 目录结构

```
ml_models/
├── src/                      # 源代码目录
│   ├── feature_extractors/   # 特征提取器
│   │   └── voice_feature_extractor.py  # 语音特征提取
│   ├── predictors/           # 预测模型
│   └── utils/                # 工具函数
├── trained/                  # 训练好的模型
│   ├── voice_models/         # 语音相关模型
│   └── large_models/         # 大型模型
├── training/                 # 训练脚本和数据
│   ├── data/                 # 训练数据
│   └── scripts/              # 训练脚本
└── test_import.py            # 测试脚本
```

## 模块说明

### src/ 目录

这里包含所有机器学习功能的源代码实现：

- **feature_extractors/**: 从原始数据中提取特征的组件
  - `voice_feature_extractor.py`: 提取音频文件的各种声学特征

- **predictors/**: 预测模型的具体实现
  - 负责利用特征进行预测和分类

### trained/ 目录

存放训练好的模型文件：

- **voice_models/**: 存放语音相关的较小模型
- **large_models/**: 存放大型模型，如定制化大语言模型

### training/ 目录

包含训练模型所需的脚本和数据：

- **data/**: 训练和验证数据
- **scripts/**: 模型训练和评估脚本

## 使用方法

### 导入模块

```python
# 导入特征提取器
from ml_models.src.feature_extractors import VoiceFeatureExtractor

# 创建特征提取器实例
extractor = VoiceFeatureExtractor()

# 提取特征
features = extractor.extract_features("path/to/audio.wav")

# 分析声音健康
prediction, confidence = extractor.analyze_voice_health(features)
```

### 运行测试

验证模块导入和功能:

```bash
python ml_models/test_import.py
```

## 开发指南

1. 所有机器学习相关的代码都应放在本目录下
2. 新增特征提取器应放在 `src/feature_extractors/` 目录
3. 新增预测模型应放在 `src/predictors/` 目录
4. 训练好的模型文件应存放在 `trained/` 对应目录下
5. 保持功能模块化，便于复用和测试

## 模型说明

1. 声音特征提取模型
   - 输入：原始音频文件
   - 输出：音频特征向量
   - 特征：音高、音量、频谱等

2. 语音诊断模型
   - 输入：音频特征向量
   - 输出：诊断结果和置信度
   - 评估指标：准确率、召回率等

## 使用说明

1. 模型训练
```bash
cd training
python train_model.py
```

2. 模型评估
```bash
cd training
python evaluate_model.py
```

3. 模型使用
```python
from models import VoiceDiagnosisModel

model = VoiceDiagnosisModel.load('trained/model.pt')
result = model.predict(audio_data)
```

## 注意事项

- 模型文件较大，请使用Git LFS管理
- 训练需要GPU支持
- 请定期更新模型版本 