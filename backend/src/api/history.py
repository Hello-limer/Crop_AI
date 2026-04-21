"""
历史记录 API
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database.database import get_db
from ..database.models import Diagnosis

router = APIRouter()


@router.get("/diagnoses")
async def get_diagnoses_list(
    skip: int = 0,
    limit: int = 50,
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    获取诊断历史列表
    """
    try:
        query = db.query(Diagnosis)
        
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Diagnosis.created_at >= start_dt)
        
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            query = query.filter(Diagnosis.created_at <= end_dt)
        
        total = query.count()
        diagnoses = query.order_by(Diagnosis.created_at.desc()).offset(skip).limit(limit).all()
        
        return {
            "total": total,
            "items": [
                {
                    "id": d.id,
                    "image_path": d.image_path,
                    "emotion": d.emotion,
                    "model_used": d.model_used,
                    "diagnosis_time": d.diagnosis_time,
                    "humidity": d.humidity,
                    "temperature": d.temperature,
                    "light": d.light,
                    "created_at": d.created_at
                }
                for d in diagnoses
            ]
        }
    except Exception as e:
        print(f"⚠️  数据库查询失败: {e}")
        return {
            "total": 0,
            "items": [],
            "message": "数据库不可用，返回空列表"
        }


@router.get("/diagnoses/{id}")
async def get_diagnosis_detail(
    id: int,
    db: Session = Depends(get_db)
):
    """
    获取单条诊断详情
    """
    try:
        diagnosis = db.query(Diagnosis).filter(Diagnosis.id == id).first()
        if not diagnosis:
            raise HTTPException(status_code=404, detail="诊断记录不存在")
        
        return {
            "id": diagnosis.id,
            "image_path": diagnosis.image_path,
            "emotion": diagnosis.emotion,
            "scores": diagnosis.scores,
            "report": diagnosis.report,
            "model_used": diagnosis.model_used,
            "diagnosis_time": diagnosis.diagnosis_time,
            "humidity": diagnosis.humidity,
            "temperature": diagnosis.temperature,
            "light": diagnosis.light,
            "created_at": diagnosis.created_at
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")


@router.delete("/diagnoses/{id}")
async def delete_diagnosis(
    id: int,
    db: Session = Depends(get_db)
):
    """
    删除诊断记录
    """
    try:
        diagnosis = db.query(Diagnosis).filter(Diagnosis.id == id).first()
        if not diagnosis:
            raise HTTPException(status_code=404, detail="诊断记录不存在")
        
        db.delete(diagnosis)
        db.commit()
        
        return {"success": True, "message": "删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库操作失败: {str(e)}")


@router.post("/diagnoses/batch-delete")
async def batch_delete_diagnoses(
    ids: List[int],
    db: Session = Depends(get_db)
):
    """
    批量删除诊断记录
    """
    try:
        if not ids:
            raise HTTPException(status_code=400, detail="请选择要删除的记录")
        
        diagnoses = db.query(Diagnosis).filter(Diagnosis.id.in_(ids)).all()
        if not diagnoses:
            raise HTTPException(status_code=404, detail="未找到要删除的记录")
        
        for diagnosis in diagnoses:
            db.delete(diagnosis)
        
        db.commit()
        
        return {"success": True, "message": f"成功删除 {len(diagnoses)} 条记录"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库操作失败: {str(e)}")
