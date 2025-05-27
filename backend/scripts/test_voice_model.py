import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

from app.utils.voice_models_utils import create_model

def test_with_sample_audio():
    """使用示例音频文件测试模型"""
    print("开始测试语音模型...")
    
    # 创建模型实例
    try:
        model = create_model()
        print("✓ 模型初始化成功")
    except Exception as e:
        print(f"✗ 模型初始化失败: {str(e)}")
        return
    
    # 测试音频文件路径
    test_audio_path = project_root / "ml_models" / "trained" / "voice_models" / "test_audio.wav"
    
    # 检查测试音频文件是否存在
    if not test_audio_path.exists():
        print(f"✗ 测试音频文件不存在: {test_audio_path}")
        print("请将测试音频文件放在以下位置：")
        print(f"  {test_audio_path}")
        return
    
    # 测试特征提取
    try:
        features = model.get_features(str(test_audio_path))
        print(f"✓ 特征提取成功，特征向量长度: {len(features)}")
    except Exception as e:
        print(f"✗ 特征提取失败: {str(e)}")
        return
    
    # 测试预测
    try:
        result = model.get_prediction(str(test_audio_path))
        print("\n预测结果:")
        print(f"  状态: {result['status']}")
        print(f"  预测值: {result['prediction']}")
        if result['confidence'] is not None:
            print(f"  置信度: {result['confidence']:.2%}")
        if result['status'] == 'error':
            print(f"  错误信息: {result['error']}")
    except Exception as e:
        print(f"✗ 预测失败: {str(e)}")
        return
    
    print("\n测试完成！")

if __name__ == "__main__":
    test_with_sample_audio() 