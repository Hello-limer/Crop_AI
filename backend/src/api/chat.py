"""
聊天相关 API
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path

from ..database.database import get_db
from ..database.models import ChatMessage, Diagnosis
from ..config.settings import config
from ..core.llm import create_llm_client

router = APIRouter()

# 全局 LLM 客户端
chat_llm_client = None

def get_chat_llm_client():
    """懒加载聊天用 LLM 客户端"""
    global chat_llm_client
    if chat_llm_client is None:
        try:
            prompt_path = Path(__file__).parent.parent / "prompts" / "chat_prompt.txt"
            chat_llm_client = create_llm_client(
                provider=config.ACTIVE_LLM,
                system_prompt_path=str(prompt_path)
            )
            print("✅ 聊天 LLM 客户端初始化成功")
        except Exception as e:
            print(f"⚠️  聊天 LLM 客户端初始化失败: {e}")
    return chat_llm_client


def get_mock_reply(message: str) -> str:
    """获取模拟回复（备用）"""
    # 简单的关键词匹配
    if any(keyword in message for keyword in ['浇水', '水', '缺水']):
        return "关于浇水：建议早晨或傍晚浇水，避免中午高温时浇水。浇水要浇透，但不要积水！💧"
    elif any(keyword in message for keyword in ['虫', '病', '虫害', '病害']):
        return "关于病虫害：建议先识别病虫害类型，然后选择合适的防治方法，注意农药要安全使用！🌿"
    elif any(keyword in message for keyword in ['肥', '施肥', '养分']):
        return "关于施肥：建议根据作物生长期选择合适的肥料，薄肥勤施！🌱"
    elif any(keyword in message for keyword in ['光照', '阳光', '晒太阳']):
        return "关于光照：大多数作物需要充足的光照，但要注意避免暴晒！☀️"
    elif any(keyword in message for keyword in ['温度', '气温', '冷', '热']):
        return "关于温度：不同作物对温度要求不同，请根据具体作物调整！🌡️"
    else:
        return "您好！我是农作物顾问，很高兴为您服务。请问您有什么关于农作物种植、养护、病虫害防治等方面的问题吗？🌱"


class ChatRequest(BaseModel):
    diagnosis_id: Optional[int] = None
    message: str
    history: Optional[List[dict]] = []


@router.post("/message")
async def send_chat_message(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    发送聊天消息
    """
    try:
        print(f"[聊天] 收到用户消息: {request.message}")
        print(f"[聊天] history长度: {len(request.history) if request.history else 0}")
        
        # 1. 保存用户消息
        user_message = ChatMessage(
            diagnosis_id=request.diagnosis_id,
            role="user",
            content=request.message
        )
        db.add(user_message)
        
        # 2. 获取诊断信息（如果有diagnosis_id）
        diagnosis_info = None
        if request.diagnosis_id:
            try:
                diagnosis = db.query(Diagnosis).filter(Diagnosis.id == request.diagnosis_id).first()
                if diagnosis:
                    diagnosis_info = diagnosis.report
                    print(f"[聊天] 找到诊断信息: {diagnosis_info.get('primary_state', '未知') if diagnosis_info else 'N/A'}")
            except Exception as e:
                print(f"[聊天] 获取诊断信息失败: {e}")
        
        # 3. 调用 LLM 生成回复
        assistant_reply = None
        llm = get_chat_llm_client()
        
        if llm:
            try:
                print(f"[聊天] 正在调用LLM...")
                # 构建历史对话
                history_messages = []
                for msg in request.history:
                    history_messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
                
                # 构建增强的用户消息（包含诊断信息）
                enhanced_message = request.message
                if diagnosis_info:
                    diagnosis_context = f"""
【当前诊断信息】
- 作物状态: {diagnosis_info.get('primary_state', '未知')}
- 置信度: {diagnosis_info.get('confidence', '未知')}%
- 作物自述: {diagnosis_info.get('作物自述', '无')}
- 诊断说明: {diagnosis_info.get('诊断说明', '无')}
"""
                    enhanced_message = f"{diagnosis_context}\n\n用户问题: {request.message}"
                
                assistant_reply = llm.chat_text(
                    enhanced_message,
                    history=history_messages,
                    temperature=0.7,
                    max_tokens=1000
                )
                print(f"[聊天] LLM返回: {assistant_reply[:100] if assistant_reply else 'None'}...")
            except Exception as e:
                print(f"⚠️  LLM 调用失败: {e}")
        
        # 如果 LLM 失败，使用模拟回复
        if not assistant_reply:
            print(f"[聊天] 使用模拟回复")
            assistant_reply = get_mock_reply(request.message)
        
        print(f"[聊天] 最终回复: {assistant_reply}")
        
        # 4. 保存助手回复
        assistant_message = ChatMessage(
            diagnosis_id=request.diagnosis_id,
            role="assistant",
            content=assistant_reply
        )
        db.add(assistant_message)
        
        try:
            db.commit()
        except Exception as db_error:
            print(f"⚠️  数据库保存失败: {db_error}")
            # 即使数据库保存失败，也返回回复
        
        return {
            "success": True,
            "reply": assistant_reply
        }
        
    except Exception as e:
        print(f"⚠️ 聊天请求异常: {e}")
        raise HTTPException(status_code=500, detail=f"聊天失败: {str(e)}")


@router.get("/history/{diagnosis_id}")
async def get_chat_history(
    diagnosis_id: int,
    db: Session = Depends(get_db)
):
    """
    获取聊天历史
    """
    try:
        messages = db.query(ChatMessage)\
            .filter(ChatMessage.diagnosis_id == diagnosis_id)\
            .order_by(ChatMessage.created_at)\
            .all()
        
        return {
            "diagnosis_id": diagnosis_id,
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "created_at": m.created_at
                }
                for m in messages
            ]
        }
    except Exception as e:
        # 数据库失败时返回空历史
        return {
            "diagnosis_id": diagnosis_id,
            "messages": []
        }


@router.delete("/history/{diagnosis_id}")
async def clear_chat_history(
    diagnosis_id: int,
    db: Session = Depends(get_db)
):
    """
    清除聊天历史
    """
    try:
        messages = db.query(ChatMessage)\
            .filter(ChatMessage.diagnosis_id == diagnosis_id)\
            .all()
        
        for message in messages:
            db.delete(message)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"成功清除 {len(messages)} 条聊天记录"
        }
    except Exception as e:
        print(f"⚠️  清除聊天历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"清除聊天历史失败: {str(e)}")
