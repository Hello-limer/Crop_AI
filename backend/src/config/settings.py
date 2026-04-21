"""
配置文件
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """应用配置"""
    # 服务器配置
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
    
    # 标题和描述
    TITLE = os.getenv("TITLE", "AI农田情绪诊断师")
    DESC = os.getenv("DESC", "对作物叶片图片，AI会告诉你作物的心情 - 支持摄像头实时诊断图片上传")
    
    # 数据库配置
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
    DB_NAME = os.getenv("DB_NAME", "farm_diagnosis")
    
    # 数据库连接 URL
    @property
    def DATABASE_URL(self):
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # 模型配置
    ACTIVE_LLM = os.getenv("ACTIVE_LLM", "doubao")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    DOUBAO_MODEL = os.getenv("DOUBAO_MODEL", "")
    DOUBAO_API_KEY = os.getenv("DOUBAO_API_KEY", "")
    DOUBAO_BASE_URL = os.getenv("DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    ENABLE_VISUAL_CLASSIFIER = os.getenv("ENABLE_VISUAL_CLASSIFIER", "false").lower() == "true"
    LLM_ONLY_MODE = os.getenv("LLM_ONLY_MODE", "true").lower() == "true"
    
    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "")
    
    # CORS配置
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


# 创建配置实例
config = Config()
