"""基金 API 路由"""
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.fund import FundType
from app.schemas.fund import (
    FundCreate, FundUpdate, FundResponse, 
    FundFilter, FundFilterRequest, FundFilterResponse,
    FundNavResponse, FundDetailResponse, FundRankRequest
)
from app.services.fund_service import FundService, AkShareSync

router = APIRouter(prefix="/api/v1/funds", tags=["基金"])


# ============ 基金基本信息 API ============

@router.get("", response_model=FundFilterResponse)
async def get_funds(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    fund_type: Optional[str] = Query(None, description="基金类型"),
    manager: Optional[str] = Query(None, description="管理公司"),
    min_scale: Optional[float] = Query(None, description="最小规模(亿)"),
    max_scale: Optional[float] = Query(None, description="最大规模(亿)"),
    status: Optional[str] = Query(None, description="基金状态"),
    db: Session = Depends(get_db)
):
    """获取基金列表（支持筛选）"""
    # 构建筛选条件
    filters_dict = {}
    if fund_type:
        filters_dict['fund_type'] = fund_type
    if manager:
        filters_dict['manager'] = manager
    if min_scale is not None:
        filters_dict['min_scale'] = min_scale
    if max_scale is not None:
        filters_dict['max_scale'] = max_scale
    if status:
        filters_dict['status'] = status
    
    # 如果有筛选条件，使用筛选服务
    if filters_dict:
        filters = FundFilter(**filters_dict)
        funds, total = FundService.filter_funds(db, filters, page, page_size)
    else:
        skip = (page - 1) * page_size
        funds, total = FundService.get_fund_list(db, skip, page_size)
    
    return FundFilterResponse(
        total=total,
        page=page,
        page_size=page_size,
        data=funds
    )


@router.get("/{fund_code}", response_model=FundResponse)
async def get_fund(
    fund_code: str,
    db: Session = Depends(get_db)
):
    """获取基金详情"""
    fund = FundService.get_fund_by_code(db, fund_code)
    if not fund:
        raise HTTPException(status_code=404, detail="基金不存在")
    return fund


@router.post("", response_model=FundResponse, status_code=201)
async def create_fund(
    fund_data: FundCreate,
    db: Session = Depends(get_db)
):
    """创建基金"""
    # 检查是否已存在
    existing = FundService.get_fund_by_code(db, fund_data.fund_code)
    if existing:
        raise HTTPException(status_code=400, detail="基金已存在")
    
    fund = FundService.create_fund(db, fund_data)
    return fund


@router.put("/{fund_code}", response_model=FundResponse)
async def update_fund(
    fund_code: str,
    fund_data: FundUpdate,
    db: Session = Depends(get_db)
):
    """更新基金信息"""
    fund = FundService.update_fund(db, fund_code, fund_data.model_dump(exclude_unset=True))
    if not fund:
        raise HTTPException(status_code=404, detail="基金不存在")
    return fund


@router.delete("/{fund_code}")
async def delete_fund(
    fund_code: str,
    db: Session = Depends(get_db)
):
    """删除基金"""
    success = FundService.delete_fund(db, fund_code)
    if not success:
        raise HTTPException(status_code=404, detail="基金不存在")
    return {"message": "删除成功"}


# ============ 基金筛选 API ============

@router.post("/filter", response_model=FundFilterResponse)
async def filter_funds(
    request: FundFilterRequest,
    db: Session = Depends(get_db)
):
    """筛选基金"""
    funds, total = FundService.filter_funds(
        db, 
        request.filters, 
        request.page, 
        request.page_size
    )
    
    return FundFilterResponse(
        total=total,
        page=request.page,
        page_size=request.page_size,
        data=funds
    )


# ============ 基金排名 API ============

@router.get("/rank/list", response_model=FundFilterResponse)
async def get_fund_rank(
    fund_type: Optional[FundType] = Query(None, description="基金类型"),
    rank_by: str = Query("scale", description="排序字段: scale/risk"),
    order: str = Query("desc", description="排序方式: asc/desc"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取基金排名"""
    funds, total = FundService.get_fund_rank(
        db, fund_type, rank_by, order, page, page_size
    )
    
    return FundFilterResponse(
        total=total,
        page=page,
        page_size=page_size,
        data=funds
    )


# ============ 基金净值 API ============

@router.get("/{fund_code}/nav")
async def get_fund_nav(
    fund_code: str,
    days: int = Query(30, ge=1, le=365, description="查询天数"),
    db: Session = Depends(get_db)
):
    """获取基金净值历史"""
    fund = FundService.get_fund_by_code(db, fund_code)
    if not fund:
        raise HTTPException(status_code=404, detail="基金不存在")
    
    start_date = datetime.now() - timedelta(days=days)
    nav_history = FundService.get_fund_nav_history(db, fund_code, start_date)
    
    return {
        "fund_code": fund_code,
        "fund_name": fund.fund_name,
        "data": nav_history
    }


# ============ 数据同步 API ============

@router.post("/sync/list")
async def sync_fund_list(
    min_scale: float = Query(2.0, description="最小规模(亿元)"),
    db: Session = Depends(get_db)
):
    """从 AkShare 同步基金列表"""
    # 检查基金是否存在
    count = db.query(FundService.get_fund_by_code(db, "000001")).count() if False else 0
    
    synced_count = AkShareSync.sync_fund_list(db, min_scale)
    
    return {
        "message": "同步完成",
        "synced_count": synced_count
    }


@router.post("/{fund_code}/sync/nav")
async def sync_fund_nav(
    fund_code: str,
    days: int = Query(30, ge=1, le=365, description="同步天数"),
    db: Session = Depends(get_db)
):
    """从 AkShare 同步基金净值"""
    fund = FundService.get_fund_by_code(db, fund_code)
    if not fund:
        raise HTTPException(status_code=404, detail="基金不存在")
    
    synced_count = AkShareSync.sync_fund_nav(db, fund_code, days)
    
    return {
        "message": "同步完成",
        "synced_count": synced_count
    }


# ============ 基金统计 API ============

@router.get("/stats/summary")
async def get_fund_stats(db: Session = Depends(get_db)):
    """获取基金统计信息"""
    from sqlalchemy import func
    from app.models.fund import Fund
    
    # 统计各类型基金数量
    type_stats = db.query(
        Fund.fund_type,
        func.count(Fund.id).label("count"),
        func.avg(Fund.scale).label("avg_scale")
    ).group_by(Fund.fund_type).all()
    
    # 统计总规模
    total_scale = db.query(func.sum(Fund.scale)).scalar() or 0
    
    # 统计总数量
    total_count = db.query(func.count(Fund.id)).scalar() or 0
    
    return {
        "total_count": total_count,
        "total_scale": total_scale,
        "type_stats": [
            {
                "type": stat.fund_type if stat.fund_type else "未知",
                "count": stat.count,
                "avg_scale": stat.avg_scale or 0
            }
            for stat in type_stats
        ]
    }