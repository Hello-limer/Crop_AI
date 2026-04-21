"""
数据库连接和会话管理
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from ..config.settings import config
from .models import Base
import time

# 创建数据库引擎
engine = create_engine(
    config.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """初始化数据库，创建所有表"""
    # 尝试连接数据库，失败则等待重试
    max_retries = 2
    retry_count = 0
    while retry_count < max_retries:
        try:
            # 测试连接
            conn = engine.connect()
            conn.close()
            print("✅ 数据库连接成功！")
            break
        except OperationalError:
            retry_count += 1
            if retry_count < max_retries:
                print(f"⚠️  数据库连接失败，等待重试... ({retry_count}/{max_retries})")
                time.sleep(1)
            else:
                print("❌ 数据库连接失败，请检查配置！")
                print("💡 提示：如果没有MySQL，可以忽略此错误，应用仍可运行")
                return  # 不抛出异常，让应用继续运行
    
    # 创建所有表
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表创建成功！")
    except Exception as e:
        print(f"⚠️  数据库表创建失败: {e}")


def get_db():
    """获取数据库会话（FastAPI 依赖项）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
