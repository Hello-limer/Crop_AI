"""
数据库模型
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Diagnosis(Base):
    """诊断记录表"""
    __tablename__ = "diagnoses"
    
    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String(255))  # 图片路径
    emotion = Column(String(50))  # 主要情绪/状态
    scores = Column(JSON)  # 所有状态分数
    report = Column(JSON)  # 诊断报告
    model_used = Column(String(255))  # 使用的模型
    diagnosis_time = Column(Float)  # 诊断耗时（秒）
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 环境数据
    humidity = Column(Float)
    temperature = Column(Float)
    light = Column(Float)
    
    # 关系
    chat_messages = relationship("ChatMessage", back_populates="diagnosis")


class ChatMessage(Base):
    """聊天记录表"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    diagnosis_id = Column(Integer, ForeignKey("diagnoses.id"), nullable=True)
    role = Column(String(20))  # "user" 或 "assistant"
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    diagnosis = relationship("Diagnosis", back_populates="chat_messages")


class SensorData(Base):
    """传感器数据表（用于预测趋势）"""
    __tablename__ = "sensor_data"
    
    id = Column(Integer, primary_key=True, index=True)
    humidity = Column(Float)  # 湿度
    temperature = Column(Float)  # 温度
    light = Column(Float)  # 光照
    recorded_at = Column(DateTime, default=datetime.utcnow)
