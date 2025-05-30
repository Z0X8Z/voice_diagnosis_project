# 机器学习代码重组说明

本文档说明项目中机器学习代码的重组过程和最终结构。

## 重组背景

之前的项目结构中，机器学习相关代码分散在不同目录：

1. `ml_models/`: 存放模型文件和训练代码
2. `backend/app/models/`: 存放模型实现类如特征提取器

这种结构导致了以下问题：
- 机器学习代码分散，不利于集中管理
- 职责边界不清晰
- 数据科学家和后端开发者的协作不便

## 重组后的结构

现在，我们将所有机器学习相关代码统一放在`ml_models`目录下：

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
└── training/                 # 训练脚本和数据
```

后端应用通过导入`ml_models`包来使用这些功能：

```python
from ml_models.src.feature_extractors import VoiceFeatureExtractor
```

## 兼容性处理

为保持与现有代码的兼容性，我们在`backend/app/models/__init__.py`中添加了导入重定向：

```python
# 为了向后兼容，从ml_models中导入
from ml_models.src.feature_extractors import VoiceFeatureExtractor

__all__ = ["VoiceFeatureExtractor"]
```

这样，现有代码中的`from app.models import VoiceFeatureExtractor`导入仍然有效。

## 服务层适配

`backend/app/services/model_service.py`已更新为使用`ml_models`包：

```python
# 添加项目根目录到系统路径，以便导入ml_models
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    # 从ml_models导入模型和特征提取器
    from ml_models.src.feature_extractors import VoiceFeatureExtractor
except ImportError:
    # 回退到旧路径
    from app.models import VoiceFeatureExtractor
```

## 重组带来的好处

1. **集中管理**：所有机器学习代码在一个目录下，便于管理和维护
2. **清晰职责**：数据科学家专注于`ml_models`目录，后端开发者通过导入使用功能
3. **扩展性**：可以轻松添加新的特征提取器和预测模型
4. **版本控制**：可以对机器学习代码进行独立版本控制
5. **文档清晰**：每个部分都有明确的README说明

## 大型模型支持

重组后的结构对大型模型有更好的支持：

- `ml_models/trained/large_models/`专门存放大型模型
- 提供了模型下载和版本管理的支持
- 清晰的文档说明如何管理大型模型文件

## 后续步骤

1. 优化导入路径，确保所有代码都使用新的导入方式
2. 将更多机器学习功能迁移到`ml_models/src/`目录
3. 开发更多机器学习模型，存放在对应目录中
4. 对`ml_models`包进行版本管理，并考虑发布为独立包
