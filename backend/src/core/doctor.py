"""
农田情绪诊断引擎
使用 LLM 生成个性化诊断报告
"""

import json
from typing import Dict, Optional
from PIL import Image

from .llm import create_llm_client
from ..utils.logger import get_logger

# 初始化 logger
logger = get_logger("doctor")


class FarmEmotionDoctor:
    """作物情绪诊断专家"""

    def __init__(self, llm_client=None):
        """
        初始化诊断师

        Args:
            llm_client: LLM 客户端实例（可选，自动创建）
        """
        logger.info("🔧 初始化 FarmEmotionDoctor...")
        self.llm = llm_client or create_llm_client()
        logger.info(f"✅ LLM 客户端已加载: {type(self.llm).__name__}")

    def generate_diagnosis(
        self,
        image: Image.Image,
        emotion: Optional[str] = None,
        scores: Optional[Dict] = None,
        sensor_data: Optional[Dict] = None
    ) -> Dict:
        """
        生成完整诊断报告

        Args:
            image: PIL 图片对象
            emotion: 视觉分类结果（可选）
            scores: 置信度分数（可选）
            sensor_data: 传感器数据（可选）

        Returns:
            诊断报告字典
        """
        logger.info("🧠 开始生成诊断报告...")
        
        if emotion:
            logger.info(f"📊 视觉分类输入: {emotion}")
        else:
            logger.info("📊 无视觉分类（纯 LLM 模式）")
            
        if sensor_data:
            logger.info(f"📈 传感器数据: {sensor_data}")

        # 构建用户输入（包含图片）
        user_input = self._build_user_input(image, emotion, scores, sensor_data)

        try:
            logger.info("🤖 调用 LLM...")
            result = self.llm.chat(
                user_input,
                image=image,
                temperature=0.8,
                max_tokens=800
            )
            logger.info("✅ LLM 响应成功")
            logger.debug(f"📨 LLM 返回: {json.dumps(result, ensure_ascii=False)}")
            return result

        except Exception as e:
            logger.error(f"❌ LLM 调用失败: {e}")
            return self._fallback_response(emotion)

    def _build_user_input(
        self,
        image: Image.Image,
        emotion: Optional[str],
        scores: Optional[Dict],
        sensor_data: Optional[Dict]
    ) -> str:
        """构建用户输入文本"""
        parts = []

        if emotion and scores:
            scores_str = ", ".join([f"{k}:{v:.0%}" for k, v in scores.items()])
            parts.append(f"【视觉分析结果】\n主要状态: {emotion}\n详细分数: {scores_str}")
        elif emotion:
            parts.append(f"【视觉分析结果】\n主要状态: {emotion}")
        else:
            parts.append("【视觉分析结果】\n无，请根据图片分析作物状态")

        if sensor_data:
            sensor_str = ", ".join([f"{k}:{v}" for k, v in sensor_data.items()])
            parts.append(f"\n【环境传感器数据】\n{sensor_str}")

        parts.append("\n请根据图片和以上信息，生成作物诊断报告。")
        return "\n".join(parts)

    def _fallback_response(self, emotion: Optional[str]) -> Dict:
        """备用响应（当 LLM 失败时）"""
        logger.warning("⚠️ 使用备用响应")
        
        emotion_name = emotion or "未知"
        
        # 英文状态 -> 中文状态映射
        state_map = {
            'thirsty': '缺水',
            'hungry': '缺肥',
            'sunburn': '晒伤',
            'aging': '早衰',
            'healthy': '健康',
            'leggy': '徒长',
            'pest': '病菌虫害'
        }
        
        primary_state = state_map.get(emotion_name, emotion_name)
        
        # 构建 all_confidences
        all_confidences = {
            "缺水": 14.29,
            "早衰": 14.29,
            "健康": 14.29,
            "缺肥": 14.29,
            "晒伤": 14.28,
            "徒长": 14.28,
            "病菌虫害": 14.28
        }
        all_confidences[primary_state] = 70.00
        # 调整总和为 100
        remaining = 30.00
        for state in all_confidences:
            if state != primary_state:
                all_confidences[state] = remaining / 6
        
        return {
            "primary_state": primary_state,
            "confidence": 70.00,
            "all_confidences": all_confidences,
            "作物自述": f"我现在感觉有点{primary_state}的样子... (｡•́︿•̀｡)",
            "农事建议": {
                "立即行动": "请检查作物状况",
                "日常养护": "保持适宜的环境条件",
                "预防措施": "定期观察作物状态"
            },
            "诊断说明": "LLM 服务暂时不可用，这是一个备用诊断。",
            "环境建议": {
                "适宜温度": "20-30°C",
                "适宜湿度": "60-80%",
                "适宜光照": "500-1500 Lux",
                "调整建议": "请根据作物状态调整环境"
            }
        }
