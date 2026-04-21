"""
日志配置模块
"""

import os
import logging
import sys
from pathlib import Path

from ..config.settings import config


def setup_logging():
    """配置日志系统"""
    
    # 创建 logger
    logger = logging.getLogger("farm_diagnosis")
    logger.setLevel(logging.DEBUG if config.LOG_LEVEL == "DEBUG" else logging.INFO)
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    # 控制台输出格式
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if config.LOG_LEVEL == "DEBUG" else logging.INFO)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器（如果配置了）
    log_file = os.getenv("LOG_FILE")
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


# 全局 logger 实例
logger = setup_logging()


def get_logger(name: str = None) -> logging.Logger:
    """获取 logger 实例

    Args:
        name: logger 名称（可选）

    Returns:
        logger 实例
    """
    if name:
        return logging.getLogger(f"farm_diagnosis.{name}")
    return logger
