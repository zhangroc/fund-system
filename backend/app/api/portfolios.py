"""组合 API 路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.portfolio import (
    PortfolioCreate, PortfolioUpdate, 
    PortfolioResponse, PortfolioListResponse,
    PortfolioDetailResponse
)
from app.services.portfolio_service import PortfolioService

router = APIRouter(prefix="/api/v1/portfolios", tags=["组合管理"])


# ============ 组合 CRUD API ============

@router.get("", response_model=PortfolioListResponse)
async def get_portfolios(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="组合状态"),
    risk_level: Optional[str] = Query(None, description="风险等级"),
    db: Session = Depends(get_db)
):
    """获取组合列表（支持筛选）"""
    if status or risk_level:
        portfolios, total = PortfolioService.filter_portfolios(
            db, status, risk_level, page, page_size
        )
    else:
        skip = (page - 1) * page_size
        portfolios, total = PortfolioService.get_portfolio_list(db, skip, page_size)
    
    return PortfolioListResponse(
        total=total,
        page=page,
        page_size=page_size,
        data=portfolios
    )


@router.get("/{portfolio_id}", response_model=PortfolioDetailResponse)
async def get_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db)
):
    """获取组合详情"""
    portfolio = PortfolioService.get_portfolio_with_funds(db, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="组合不存在")
    
    # 获取关联基金
    funds_data = []
    if portfolio.funds:
        for fund in portfolio.funds:
            funds_data.append({
                "fund_code": fund.fund_code,
                "fund_name": fund.fund_name,
                "fund_type": fund.fund_type
            })
    
    response_data = PortfolioDetailResponse(
        id=portfolio.id,
        name=portfolio.name,
        description=portfolio.description,
        status=portfolio.status,
        risk_level=portfolio.risk_level,
        target_return=portfolio.target_return,
        notes=portfolio.notes,
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at,
        funds=funds_data
    )
    return response_data


@router.post("", response_model=PortfolioResponse, status_code=201)
async def create_portfolio(
    portfolio_data: PortfolioCreate,
    db: Session = Depends(get_db)
):
    """创建组合"""
    # 检查名称是否已存在
    existing = PortfolioService.get_portfolio_by_name(db, portfolio_data.name)
    if existing:
        raise HTTPException(status_code=400, detail="组合名称已存在")
    
    portfolio = PortfolioService.create_portfolio(db, portfolio_data)
    return portfolio


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: int,
    portfolio_data: PortfolioUpdate,
    db: Session = Depends(get_db)
):
    """更新组合信息"""
    # 检查组合是否存在
    existing = PortfolioService.get_portfolio_by_id(db, portfolio_id)
    if not existing:
        raise HTTPException(status_code=404, detail="组合不存在")
    
    # 如果更新名称，检查新名称是否已存在
    if portfolio_data.name and portfolio_data.name != existing.name:
        name_exists = PortfolioService.get_portfolio_by_name(db, portfolio_data.name)
        if name_exists:
            raise HTTPException(status_code=400, detail="组合名称已存在")
    
    portfolio = PortfolioService.update_portfolio(
        db, portfolio_id, portfolio_data.model_dump(exclude_unset=True)
    )
    return portfolio


@router.delete("/{portfolio_id}")
async def delete_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db)
):
    """删除组合"""
    success = PortfolioService.delete_portfolio(db, portfolio_id)
    if not success:
        raise HTTPException(status_code=404, detail="组合不存在")
    return {"message": "删除成功"}


# ============ 组合统计 API ============

@router.get("/stats/summary")
async def get_portfolio_stats(db: Session = Depends(get_db)):
    """获取组合统计信息"""
    from sqlalchemy import func
    from app.models.portfolio import Portfolio
    
    # 统计总数量
    total_count = db.query(func.count(Portfolio.id)).scalar() or 0
    
    # 统计各状态数量
    status_stats = db.query(
        Portfolio.status,
        func.count(Portfolio.id).label("count")
    ).group_by(Portfolio.status).all()
    
    # 统计各风险等级数量
    risk_stats = db.query(
        Portfolio.risk_level,
        func.count(Portfolio.id).label("count")
    ).group_by(Portfolio.risk_level).all()
    
    return {
        "total_count": total_count,
        "status_stats": [
            {
                "status": stat.status if stat.status else "未知",
                "count": stat.count
            }
            for stat in status_stats
        ],
        "risk_stats": [
            {
                "risk_level": stat.risk_level if stat.risk_level else "未知",
                "count": stat.count
            }
            for stat in risk_stats
        ]
    }