"""回测管理 API"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.models import Backtest, Strategy
from app.core.backtest_engine import run_backtest

router = APIRouter(prefix="/api/v1/backtests", tags=["回测管理"])


# Schema
class BacktestCreate(BaseModel):
    name: str
    strategy_id: int
    start_date: str  # "2020-01-01"
    end_date: str    # "2025-01-01"
    initial_capital: float = 100000


class BacktestUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None


class BacktestResponse(BaseModel):
    id: int
    name: str
    strategy_id: int
    strategy_name: Optional[str] = None
    status: str
    start_date: str
    end_date: str
    initial_capital: float
    config: Optional[dict] = None
    result: Optional[dict] = None
    progress: int
    error_message: Optional[str] = None
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


def backtest_to_dict(backtest: Backtest, include_strategy_name: bool = True) -> dict:
    result = {
        "id": backtest.id,
        "name": backtest.name,
        "strategy_id": backtest.strategy_id,
        "status": backtest.status,
        "start_date": backtest.start_date.strftime("%Y-%m-%d") if backtest.start_date else None,
        "end_date": backtest.end_date.strftime("%Y-%m-%d") if backtest.end_date else None,
        "initial_capital": backtest.initial_capital,
        "config": backtest.config,
        "result": backtest.result,
        "progress": backtest.progress,
        "error_message": backtest.error_message,
        "created_at": backtest.created_at.strftime("%Y-%m-%d %H:%M:%S") if backtest.created_at else None,
        "updated_at": backtest.updated_at.strftime("%Y-%m-%d %H:%M:%S") if backtest.updated_at else None
    }
    if include_strategy_name and backtest.strategy:
        result["strategy_name"] = backtest.strategy.name
    return result


@router.get("", response_model=List[BacktestResponse])
def list_backtests(
    status_filter: Optional[str] = None,
    strategy_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取回测列表"""
    query = db.query(Backtest).order_by(Backtest.created_at.desc())
    
    if status_filter:
        query = query.filter(Backtest.status == status_filter)
    if strategy_id:
        query = query.filter(Backtest.strategy_id == strategy_id)
    
    backtests = query.all()
    return [backtest_to_dict(b) for b in backtests]


@router.get("/{backtest_id}", response_model=BacktestResponse)
def get_backtest(backtest_id: int, db: Session = Depends(get_db)):
    """获取回测详情"""
    backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
    if not backtest:
        raise HTTPException(status_code=404, detail="回测不存在")
    return backtest_to_dict(backtest)


@router.post("", response_model=BacktestResponse, status_code=status.HTTP_201_CREATED)
def create_backtest(backtest: BacktestCreate, db: Session = Depends(get_db)):
    """创建回测"""
    # 验证策略存在
    strategy = db.query(Strategy).filter(Strategy.id == backtest.strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    # 解析日期
    try:
        start_date = datetime.strptime(backtest.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(backtest.end_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
    
    if end_date <= start_date:
        raise HTTPException(status_code=400, detail="结束日期必须大于开始日期")
    
    db_backtest = Backtest(
        name=backtest.name,
        strategy_id=backtest.strategy_id,
        start_date=start_date,
        end_date=end_date,
        initial_capital=backtest.initial_capital,
        status="pending"
    )
    db.add(db_backtest)
    db.commit()
    db.refresh(db_backtest)
    return backtest_to_dict(db_backtest)


@router.post("/{backtest_id}/run", response_model=BacktestResponse)
def run_backtest_api(backtest_id: int, db: Session = Depends(get_db)):
    """执行回测"""
    backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
    if not backtest:
        raise HTTPException(status_code=404, detail="回测不存在")
    
    if backtest.status == "running":
        raise HTTPException(status_code=400, detail="回测正在运行中")
    
    try:
        result = run_backtest(db, backtest_id)
        db.refresh(backtest)
        return backtest_to_dict(backtest)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回测执行失败: {str(e)}")


@router.delete("/{backtest_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_backtest(backtest_id: int, db: Session = Depends(get_db)):
    """删除回测"""
    backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
    if not backtest:
        raise HTTPException(status_code=404, detail="回测不存在")
    
    db.delete(backtest)
    db.commit()
    return None