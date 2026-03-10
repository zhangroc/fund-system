"""策略管理 API"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.models import Strategy

router = APIRouter(prefix="/api/v1/strategies", tags=["策略管理"])


# Schema
class StrategyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    strategy_type: str
    parameters: dict = {}
    fund_codes: Optional[str] = None


class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    strategy_type: Optional[str] = None
    parameters: Optional[dict] = None
    fund_codes: Optional[str] = None


class StrategyResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    strategy_type: str
    parameters: dict
    fund_codes: Optional[str]
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


def strategy_to_dict(strategy: Strategy) -> dict:
    return {
        "id": strategy.id,
        "name": strategy.name,
        "description": strategy.description,
        "strategy_type": strategy.strategy_type,
        "parameters": strategy.parameters or {},
        "fund_codes": strategy.fund_codes,
        "created_at": strategy.created_at.strftime("%Y-%m-%d %H:%M:%S") if strategy.created_at else None,
        "updated_at": strategy.updated_at.strftime("%Y-%m-%d %H:%M:%S") if strategy.updated_at else None
    }


@router.get("", response_model=List[StrategyResponse])
def list_strategies(db: Session = Depends(get_db)):
    """获取策略列表"""
    strategies = db.query(Strategy).order_by(Strategy.created_at.desc()).all()
    return [strategy_to_dict(s) for s in strategies]


@router.get("/{strategy_id}", response_model=StrategyResponse)
def get_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """获取策略详情"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    return strategy_to_dict(strategy)


@router.post("", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
def create_strategy(strategy: StrategyCreate, db: Session = Depends(get_db)):
    """创建策略"""
    db_strategy = Strategy(
        name=strategy.name,
        description=strategy.description,
        strategy_type=strategy.strategy_type,
        parameters=strategy.parameters,
        fund_codes=strategy.fund_codes
    )
    db.add(db_strategy)
    db.commit()
    db.refresh(db_strategy)
    return strategy_to_dict(db_strategy)


@router.put("/{strategy_id}", response_model=StrategyResponse)
def update_strategy(strategy_id: int, strategy: StrategyUpdate, db: Session = Depends(get_db)):
    """更新策略"""
    db_strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not db_strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    if strategy.name is not None:
        db_strategy.name = strategy.name
    if strategy.description is not None:
        db_strategy.description = strategy.description
    if strategy.strategy_type is not None:
        db_strategy.strategy_type = strategy.strategy_type
    if strategy.parameters is not None:
        db_strategy.parameters = strategy.parameters
    if strategy.fund_codes is not None:
        db_strategy.fund_codes = strategy.fund_codes
    
    db.commit()
    db.refresh(db_strategy)
    return strategy_to_dict(db_strategy)


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """删除策略"""
    db_strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not db_strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    db.delete(db_strategy)
    db.commit()
    return None