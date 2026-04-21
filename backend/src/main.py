"""
AI农田情绪诊断师 - FastAPI 后端入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .config.settings import config
from .database.database import init_db
from .api import diagnosis, chat, history, sensor

# 创建上传目录
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 初始化数据库
print("🗄️  初始化数据库...")
try:
    # 安全地初始化数据库（失败不影响启动
    try:
        init_db()
    except Exception as db_error:
        print(f"⚠️  数据库初始化失败: {db_error}")
        print("应用将继续启动，但数据库功能可能不可用")
except Exception as e:
    print(f"⚠️  数据库初始化失败: {e}")
    print("应用将继续启动，但数据库功能可能不可用")

# 创建 FastAPI 应用
app = FastAPI(
    title=config.TITLE,
    description=config.DESC,
    version="2.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        config.FRONTEND_URL,
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# 注册路由
app.include_router(diagnosis.router, prefix="/api/diagnosis", tags=["诊断"])
app.include_router(chat.router, prefix="/api/chat", tags=["聊天"])
app.include_router(history.router, prefix="/api/history", tags=["历史记录"])
app.include_router(sensor.router, prefix="/api/sensor", tags=["传感器数据"])

# 健康检查端点
@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "message": "AI农田情绪诊断师后端运行正常！"}

# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用 AI农田情绪诊断师 API",
        "docs": "/docs",
        "health": "/api/health"
    }

if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # 添加 src 父目录到路径
    src_parent = Path(__file__).parent.parent
    sys.path.insert(0, str(src_parent))
    
    import uvicorn
    
    print("🚀 启动 FastAPI 服务器...")
    print(f"📍 地址: http://{config.SERVER_HOST}:{config.SERVER_PORT}")
    print(f"📚 文档: http://{config.SERVER_HOST}:{config.SERVER_PORT}/docs")
    print("=" * 60)
    
    uvicorn.run(
        "src.main:app",
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        reload=True
    )
