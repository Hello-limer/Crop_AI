"""
工具函数集
包含数据下载、预处理、可视化等功能
"""

import os
import json
import random
import shutil
import datetime
from pathlib import Path
from urllib.request import urlretrieve
from tqdm import tqdm

import cv2
import numpy as np
from PIL import Image, ImageEnhance


def download_sample_data(output_dir: str = "data/samples", num_per_class: int = 10):
    """
    下载示例图片（用于快速测试）
    注意：实际使用时请替换为真实农业数据

    Args:
        output_dir: 输出目录
        num_per_class: 每类下载数量
    """
    # 使用Unsplash等免费图库的关键词（实际应为农业图片）
    # 这里用通用自然图片作为占位，用户需替换为真实作物图片

    print("⚠️  注意：当前下载的是示例自然图片，非真实作物数据！")
    print("   请访问以下资源获取真实农业数据集：")
    print("   - PlantVillage: https://github.com/spMohanty/PlantVillage-Dataset")
    print("   - AI Challenger: http://https://github.com/AIChallenger/AI_Challenger_2018")
    print("   - 或自行拍摄本地作物照片")
    print()

    # 创建目录结构
    classes = ["thirsty", "hungry", "sunburn", "leggy", "aging", "healthy"]
    base_path = Path(output_dir)

    for cls in classes:
        (base_path / "train" / cls).mkdir(parents=True, exist_ok=True)
        (base_path / "val" / cls).mkdir(parents=True, exist_ok=True)

    # 生成彩色占位图（带类别特征模拟）
    print(f"🎨 生成示例图片到 {output_dir}...")

    for cls in classes:
        for i in tqdm(range(num_per_class), desc=f"生成 {cls}"):
            # 根据类别生成不同特征的模拟图
            img = generate_mock_leaf(cls, size=(224, 224))

            # 保存
            save_path = base_path / "train" / cls / f"{cls}_{i:03d}.jpg"
            img.save(save_path, quality=90)

            # 复制20%到验证集
            if i < num_per_class * 0.2:
                val_path = base_path / "val" / cls / f"{cls}_{i:03d}.jpg"
                shutil.copy(save_path, val_path)

    print(f"✅ 示例数据生成完成: {output_dir}")
    print(f"   训练集: {num_per_class * len(classes)} 张")
    print(f"   验证集: {int(num_per_class * 0.2) * len(classes)} 张")
    print("\n💡 下一步: 运行 python scripts/train.py --data {output_dir}")


def generate_mock_leaf(emotion: str, size: tuple = (224, 224)) -> Image.Image:
    """
    生成模拟叶片图片（用于占位测试）

    Args:
        emotion: 情绪类别
        size: 图片尺寸

    Returns:
        PIL Image
    """
    w, h = size

    # 基础颜色（根据情绪）
    color_map = {
        "thirsty": (139, 125, 80),    # 土黄（缺水）
        "hungry": (200, 180, 50),     # 黄绿（缺肥）
        "sunburn": (160, 82, 45),     # 褐斑（晒伤）
        "leggy": (150, 200, 150),     # 浅绿（徒长）
        "aging": (139, 90, 43),       # 枯黄（早衰）
        "healthy": (34, 139, 34)      # 翠绿（健康）
    }

    base_color = color_map.get(emotion, (100, 150, 100))

    # 创建基础图像
    img_array = np.zeros((h, w, 3), dtype=np.uint8)

    # 添加渐变背景
    for y in range(h):
        for x in range(w):
            # 中心亮边缘暗的椭圆渐变
            dx = (x - w/2) / (w/2)
            dy = (y - h/2) / (h/2)
            dist = np.sqrt(dx*dx + dy*dy)

            # 基础颜色 + 随机扰动 + 光照
            brightness = 1 - dist * 0.3 + random.uniform(-0.1, 0.1)
            pixel = [min(255, max(0, int(c * brightness))) for c in base_color]
            img_array[y, x] = pixel

    # 添加叶脉纹理（简化模拟）
    img = Image.fromarray(img_array)

    # 添加随机噪声模拟纹理
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.2 + random.uniform(-0.2, 0.3))

    return img


def enhance_image(image_path: str, output_path: str = None):
    """
    图像增强（用于数据预处理）

    Args:
        image_path: 输入图片路径
        output_path: 输出路径（默认覆盖原图）
    """
    img = Image.open(image_path)

    # 自动对比度
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)

    # 锐化
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(2.0)

    # 色彩平衡（针对叶片）
    img = color_balance_for_leaves(img)

    save_path = output_path or image_path
    img.save(save_path)
    print(f"✅ 增强完成: {save_path}")


def color_balance_for_leaves(img: Image.Image) -> Image.Image:
    """
    针对叶片的色彩平衡（增强绿色通道）
    """
    img_array = np.array(img)

    # 简单色彩增强：提升绿色通道，抑制红蓝
    img_array[:, :, 1] = np.clip(img_array[:, :, 1] * 1.1, 0, 255)  # G
    img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 0.95, 0, 255)  # R
    img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 0.95, 0, 255)  # B

    return Image.fromarray(img_array.astype(np.uint8))


def split_dataset(source_dir: str, train_ratio: float = 0.8):
    """
    将图片集划分为训练集和验证集

    Args:
        source_dir: 源目录（包含各类别子文件夹）
        train_ratio: 训练集比例
    """
    source = Path(source_dir)

    for class_dir in source.iterdir():
        if not class_dir.is_dir():
            continue

        images = list(class_dir.glob("*.jpg")) + list(class_dir.glob("*.png"))
        random.shuffle(images)

        split_idx = int(len(images) * train_ratio)
        train_imgs = images[:split_idx]
        val_imgs = images[split_idx:]

        # 创建新目录结构
        train_dir = Path("data/train") / class_dir.name
        val_dir = Path("data/val") / class_dir.name
        train_dir.mkdir(parents=True, exist_ok=True)
        val_dir.mkdir(parents=True, exist_ok=True)

        # 复制文件
        for img in train_imgs:
            shutil.copy(img, train_dir / img.name)
        for img in val_imgs:
            shutil.copy(img, val_dir / img.name)

        print(f"{class_dir.name}: 训练{len(train_imgs)}张, 验证{len(val_imgs)}张")


def check_environment():
    """检查运行环境"""
    print("🔍 环境检查...")

    # Python版本
    import sys
    print(f"   Python: {sys.version}")

    # 关键依赖
    try:
        import torch
        print(f"   PyTorch: {torch.__version__}")
        print(f"   CUDA可用: {torch.cuda.is_available()}")
    except ImportError:
        print("   ⚠️ PyTorch未安装")

    try:
        import ultralytics
        print(f"   Ultralytics: {ultralytics.__version__}")
    except ImportError:
        print("   ⚠️ Ultralytics未安装")

    try:
        import ollama
        print("   Ollama: 已安装")
    except ImportError:
        print("   ⚠️ Ollama Python库未安装")

    # 检查Ollama服务
    try:
        import subprocess
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if result.returncode == 0:
            print("   Ollama服务: 运行中")
            print(f"   可用模型: {result.stdout[:200]}...")
        else:
            print("   ⚠️ Ollama服务未运行，请启动Ollama")
    except FileNotFoundError:
        print("   ⚠️ Ollama命令未找到，请安装Ollama")

    # 目录结构
    print("\n📁 目录结构:")
    for d in ["data", "models", "outputs"]:
        exists = "✅" if Path(d).exists() else "❌"
        print(f"   {exists} {d}/")


def save_diagnosis(
    image,
    emotion: str,
    scores: dict,
    report: dict,
    model_name: str = "unknown"
) -> str:
    """保存诊断记录

    Args:
        image: PIL图片对象
        emotion: 情绪标签
        scores: 置信度分数
        report: 诊断报告
        model_name: 使用的模型名称

    Returns:
        记录ID
    """
    from ..config.settings import config

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    record_id = f"diag_{timestamp}"

    # 保存图片
    output_dir = Path("../../outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    img_path = output_dir / f"{record_id}.jpg"
    image.save(img_path, quality=90)

    # 保存JSON
    data = {
        "id": record_id,
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "emotion": emotion,
        "scores": scores,
        "report": report,
        "model": model_name,
        "image": str(img_path)
    }

    json_path = output_dir / f"{record_id}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return record_id


def load_recent_records(limit: int = None) -> list:
    """加载最近的诊断记录

    Args:
        limit: 最多返回多少条记录

    Returns:
        记录列表
    """
    if limit is None:
        limit = 10

    records = []
    output_dir = Path("../../outputs")
    json_files = sorted(
        output_dir.glob("diag_*.json"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    for jf in json_files[:limit]:
        try:
            with open(jf, 'r', encoding='utf-8') as f:
                records.append(json.load(f))
        except Exception:
            continue

    return records
