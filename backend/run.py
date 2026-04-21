"""
启动脚本
"""

import sys
from pathlib import Path

# 将 backend 目录添加到 Python 路径
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 启动 AI农田情绪诊断师 后端服务...")
    print("📚 API 文档: http://localhost:8000/docs")
    print("=" * 60)
    
    uvicorn.run(
        "src.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
