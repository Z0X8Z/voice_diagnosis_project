# 机器学习模型

本目录包含项目使用的机器学习模型相关文件。

## 目录结构

- `trained/`: 存放训练好的模型文件
  - 声音特征提取模型
  - 语音诊断模型
  - 其他相关模型

- `training/`: 存放模型训练相关脚本
  - 数据预处理脚本
  - 模型训练脚本
  - 模型评估脚本

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