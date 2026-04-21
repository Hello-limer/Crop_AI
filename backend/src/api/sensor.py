"""
传感器数据和预测 API
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from ..database.database import get_db
from ..database.models import SensorData

router = APIRouter()


class SensorDataCreate(BaseModel):
    humidity: float
    temperature: float
    light: float


@router.post("/data")
async def save_sensor_data(
    data: SensorDataCreate,
    db: Session = Depends(get_db)
):
    """
    保存传感器数据
    """
    try:
        sensor_data = SensorData(
            humidity=data.humidity,
            temperature=data.temperature,
            light=data.light
        )
        db.add(sensor_data)
        db.commit()
        db.refresh(sensor_data)
        
        return {
            "success": True,
            "id": sensor_data.id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存传感器数据失败: {str(e)}")


@router.get("/data")
async def get_sensor_history(
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """
    获取传感器历史数据
    """
    start_time = datetime.utcnow() - timedelta(hours=hours)
    data_points = db.query(SensorData)\
        .filter(SensorData.recorded_at >= start_time)\
        .order_by(SensorData.recorded_at)\
        .all()
    
    return {
        "time_range_hours": hours,
        "data": [
            {
                "id": d.id,
                "humidity": d.humidity,
                "temperature": d.temperature,
                "light": d.light,
                "recorded_at": d.recorded_at
            }
            for d in data_points
        ]
    }


@router.get("/predict/temperature")
async def predict_temperature(
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """
    预测温度趋势
    """
    # TODO: 实现真实的预测逻辑
    # 这里返回模拟数据
    predictions = []
    base_time = datetime.utcnow()
    
    for i in range(hours):
        predictions.append({
            "time": base_time + timedelta(hours=i),
            "temperature": 20 + (i % 12) * 0.5
        })
    
    return {
        "predictions": predictions,
        "unit": "°C"
    }


@router.get("/predict/humidity")
async def predict_humidity(
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """
    预测湿度趋势
    """
    # TODO: 实现真实的预测逻辑
    predictions = []
    base_time = datetime.utcnow()
    
    for i in range(hours):
        predictions.append({
            "time": base_time + timedelta(hours=i),
            "humidity": 60 + (i % 12) * 2
        })
    
    return {
        "predictions": predictions,
        "unit": "%"
    }


@router.get("/predict/light")
async def predict_light(
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """
    预测光照趋势
    """
    # TODO: 实现真实的预测逻辑
    predictions = []
    base_time = datetime.utcnow()
    
    for i in range(hours):
        hour = (base_time.hour + i) % 24
        light = 0
        if 6 <= hour <= 18:
            light = 500 + (hour - 6) * 50
        predictions.append({
            "time": base_time + timedelta(hours=i),
            "light": light
        })
    
    return {
        "predictions": predictions,
        "unit": "Lux"
    }
