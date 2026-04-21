"""
情绪分类器封装
"""

from pathlib import Path
import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO

from ..config.settings import config


class EmotionClassifier:
    """情绪分类器封装"""

    def __init__(self):
        self.model = None
        self.model_path = None
        self.load_model()

    def load_model(self):
        """加载模型"""
        # 获取正确的模型路径
        base_dir = Path(__file__).parent.parent.parent.parent
        model_path = base_dir / "models" / "farm_emotion_v1" / "weights" / "best.pt"
        fallback_model = base_dir / "models" / "yolov8n-cls.pt"
        
        if model_path.exists():
            self.model_path = model_path
            print(f"✅ 加载自定义模型: {self.model_path}")
        elif fallback_model.exists():
            self.model_path = fallback_model
            print(f"⚠️ 使用备用模型: {self.model_path}")
        else:
            print(f"❌ 模型文件不存在: {model_path}")
            self.model = None
            return

        try:
            self.model = YOLO(self.model_path)
            print(f"   类别: {self.model.names}")
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            self.model = None

    def predict(self, image):
        """
        预测单张图片

        Args:
            image: PIL.Image 或 numpy数组

        Returns:
            (label, confidence, all_probs) 标签、置信度、所有类别概率
        """
        if self.model is None:
            return "error", 0.0, {}

        # 确保是RGB
        if isinstance(image, np.ndarray):
            if image.shape[-1] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(image)

        # 预测
        results = self.model.predict(image, verbose=False)
        probs = results[0].probs

        # 获取Top1
        top1_idx = probs.top1
        label = results[0].names[top1_idx]
        confidence = float(probs.top1conf)

        # 获取所有概率
        all_probs = {
            results[0].names[i]: float(probs.data[i])
            for i in range(len(probs.data))
        }

        return label, confidence, all_probs
