"""
诊断相关 API
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
import shutil
import datetime
import time
from pathlib import Path
from PIL import Image

from ..database.database import get_db
from ..database.models import Diagnosis
from ..config.settings import config
from ..core.llm import create_llm_client

router = APIRouter()

# 全局 LLM 客户端
llm_client = None

def get_llm_client():
    """懒加载 LLM 客户端"""
    global llm_client
    if llm_client is None:
        try:
            prompt_path = Path(__file__).parent.parent / "prompts" / "system_prompt.txt"
            llm_client = create_llm_client(
                provider=config.ACTIVE_LLM,
                system_prompt_path=str(prompt_path)
            )
            print("✅ LLM 客户端初始化成功")
        except Exception as e:
            print(f"⚠️  LLM 客户端初始化失败: {e}")
    return llm_client


@router.post("/upload")
async def upload_and_diagnose(
    file: UploadFile = File(...),
    use_sensor: bool = Form(False),
    humidity: Optional[float] = Form(None),
    temperature: Optional[float] = Form(None),
    light: Optional[float] = Form(None),
    db: Session = Depends(get_db)
):
    """
    上传图片并进行诊断
    """
    start_time = time.time()
    
    try:
        # 1. 保存上传的图片
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"diagnosis_{timestamp}.{file.filename.split('.')[-1]}"
        filepath = Path("uploads") / filename
        
        with filepath.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 2. 读取图片
        pil_image = Image.open(filepath).convert("RGB")
        
        # 3. 构建用户输入
        user_input = "请分析这张作物图片"
        if use_sensor and humidity is not None and temperature is not None and light is not None:
            user_input = f"""请分析这张作物图片，结合以下环境数据：
土壤湿度: {humidity}%
气温: {temperature}°C
光照强度: {light} Lux
"""
        
        # 4. 调用 LLM 进行诊断
        diagnosis_result = None
        model_used = config.DOUBAO_MODEL or "doubao-seed-2.0-pro-260215"
        has_crop = True
        error_message = None
        
        llm = get_llm_client()
        if llm:
            try:
                print("🔄 正在调用 LLM 进行诊断...")
                diagnosis_result = llm.chat(
                    user_input,
                    image=pil_image,
                    temperature=0.7,
                    max_tokens=1500
                )
                print("✅ LLM 诊断完成")
                
                # 检查是否有作物 - 处理JSON格式结果
                if isinstance(diagnosis_result, dict):
                    if "没有作物" in diagnosis_result.get("作物自述", "") or "无法诊断" in diagnosis_result.get("作物自述", "") or diagnosis_result.get("primary_state") == "无法诊断":
                        has_crop = False
                        error_message = "该图片中不包含农作物"
                
            except Exception as e:
                print(f"⚠️  LLM 调用失败: {e}")
                # 检查错误信息中是否包含无作物的提示
                error_str = str(e)
                if "该图片中不包含农作物" in error_str or "未识别到需要诊断的农田作物" in error_str or "没有作物" in error_str or "无法诊断" in error_str:
                    has_crop = False
                    error_message = "该图片中不包含农作物"
                else:
                    # 其他错误，直接返回错误信息
                    has_crop = False
                    error_message = f"诊断失败：{error_str}"
        else:
            # LLM 客户端初始化失败
            has_crop = False
            error_message = "LLM 服务不可用，请稍后再试"
        
        # 检查是否识别到作物或有错误
        if not has_crop:
            # 不保存到数据库，直接返回错误
            return {
                "success": False,
                "error": error_message,
                "diagnosis_id": None,
                "result": None,
                "diagnosis_time": round(time.time() - start_time, 2),
                "model_used": model_used
            }
        
        # 检查诊断结果是否有效
        if not diagnosis_result or not isinstance(diagnosis_result, dict):
            return {
                "success": False,
                "error": "诊断失败：无法获取有效的诊断结果",
                "diagnosis_id": None,
                "result": None,
                "diagnosis_time": round(time.time() - start_time, 2),
                "model_used": model_used
            }
        
        # 计算诊断耗时
        diagnosis_time = round(time.time() - start_time, 2)
        
        # 5. 保存到数据库（只有识别到作物时才保存）
        diagnosis_id = None
        try:
            db_diagnosis = Diagnosis(
                image_path=str(filepath),
                emotion=diagnosis_result.get("primary_state", "未知"),
                scores=diagnosis_result.get("all_confidences", {}),
                report=diagnosis_result,
                model_used=model_used,
                diagnosis_time=diagnosis_time,
                humidity=humidity,
                temperature=temperature,
                light=light
            )
            db.add(db_diagnosis)
            db.commit()
            db.refresh(db_diagnosis)
            diagnosis_id = db_diagnosis.id
        except Exception as db_error:
            print(f"⚠️  数据库保存失败: {db_error}")
        
        return {
            "success": True,
            "diagnosis_id": diagnosis_id,
            "result": diagnosis_result,
            "diagnosis_time": diagnosis_time,
            "model_used": model_used
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"诊断失败: {str(e)}")


@router.get("/result/{diagnosis_id}")
async def get_diagnosis_result(diagnosis_id: int, db: Session = Depends(get_db)):
    """
    获取诊断结果
    """
    try:
        diagnosis = db.query(Diagnosis).filter(Diagnosis.id == diagnosis_id).first()
        if not diagnosis:
            raise HTTPException(status_code=404, detail="诊断记录不存在")
        return {
            "success": True,
            "result": diagnosis.report
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取诊断结果失败: {str(e)}")