"""基准指数 API 路由"""
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.services.benchmark_service import (
    BenchmarkService, AlphaBetaCalculator, BenchmarkSync
)
from app.services.cache_service import cache, cache_key, CACHE_KEYS, CACHE_EXPIRE

router = APIRouter(prefix="/api/v1/benchmark", tags=["基准指数"])


# ============ Schema 定义 ============

class BenchmarkResponse(BaseModel):
    """基准指数响应"""
    code: str
    name: str
    index_type: Optional[str] = None
    base_point: float = 1000
    description: Optional[str] = None


class BenchmarkListResponse(BaseModel):
    """基准指数列表响应"""
    total: int
    data: List[BenchmarkResponse]


class BenchmarkNavResponse(BaseModel):
    """基准净值响应"""
    code: str
    name: str
    nav_date: datetime
    nav: float
    daily_return: Optional[float] = None


class BenchmarkHistoryResponse(BaseModel):
    """基准历史数据响应"""
    code: str
    name: str
    data: List[dict]


class AlphaBetaRequest(BaseModel):
    """Alpha/Beta 计算请求"""
    strategy_code: str
    benchmark_code: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class AlphaBetaResponse(BaseModel):
    """Alpha/Beta 计算响应"""
    strategy_code: str
    benchmark_code: str
    alpha: float
    beta: float
    r_squared: float
    correlation: float
    information_ratio: float
    excess_return: float
    tracking_error: float
    strategy_annual_return: float
    benchmark_annual_return: float
    data_points: int


# ============ 基准列表 API ============

@router.get("/list", response_model=BenchmarkListResponse)
async def get_benchmark_list(
    db: Session = Depends(get_db)
):
    """获取所有可用基准指数列表"""
    # 尝试从缓存获取
    cache_key_str = CACHE_KEYS["benchmark_list"]
    cached = cache.get(cache_key_str)
    if cached:
        return cached
    
    # 从数据库获取
    benchmarks = BenchmarkService.get_all_benchmarks(db)
    
    # 如果数据库为空，初始化默认基准
    if not benchmarks:
        BenchmarkService.init_default_benchmarks(db)
        benchmarks = BenchmarkService.get_all_benchmarks(db)
    
    result = {
        "total": len(benchmarks),
        "data": [
            BenchmarkResponse(
                code=bm.code,
                name=bm.name,
                index_type=bm.index_type,
                base_point=bm.base_point,
                description=bm.description
            )
            for bm in benchmarks
        ]
    }
    
    # 缓存结果
    cache.set(cache_key_str, result, CACHE_EXPIRE["long"])
    
    return result


# ============ 基准历史数据 API ============

@router.get("/{code}/history", response_model=BenchmarkHistoryResponse)
async def get_benchmark_history(
    code: str,
    days: int = Query(30, ge=1, le=365, description="查询天数"),
    db: Session = Depends(get_db)
):
    """获取基准指数历史数据"""
    # 检查基准是否存在
    benchmark = BenchmarkService.get_benchmark_by_code(db, code)
    if not benchmark:
        raise HTTPException(status_code=404, detail=f"基准指数 {code} 不存在")
    
    # 尝试从缓存获取
    cache_key_str = f"{CACHE_KEYS['benchmark_nav']}:{code}:{days}"
    cached = cache.get(cache_key_str)
    if cached:
        return cached
    
    # 获取历史数据
    start_date = datetime.now() - timedelta(days=days)
    nav_history = BenchmarkService.get_benchmark_nav_history(
        db, code, start_date=start_date, limit=days
    )
    
    result = {
        "code": code,
        "name": benchmark.name,
        "data": [
            {
                "nav_date": nav.nav_date.isoformat() if hasattr(nav.nav_date, 'isoformat') else str(nav.nav_date),
                "nav": nav.nav,
                "daily_return": nav.daily_return
            }
            for nav in nav_history
        ]
    }
    
    # 缓存结果
    cache.set(cache_key_str, result, CACHE_EXPIRE["medium"])
    
    return result


# ============ Alpha/Beta 计算 API ============

@router.post("/alpha-beta", response_model=AlphaBetaResponse)
async def calculate_alpha_beta(
    request: AlphaBetaRequest,
    db: Session = Depends(get_db)
):
    """计算 Alpha、Beta 和信息比率"""
    # 验证策略代码 (基金代码)
    from app.services.fund_service import FundService
    strategy_fund = FundService.get_fund_by_code(db, request.strategy_code)
    if not strategy_fund:
        raise HTTPException(status_code=404, detail=f"策略基金 {request.strategy_code} 不存在")
    
    # 验证基准代码
    benchmark = BenchmarkService.get_benchmark_by_code(db, request.benchmark_code)
    if not benchmark:
        raise HTTPException(status_code=404, detail=f"基准指数 {request.benchmark_code} 不存在")
    
    # 尝试从缓存获取
    cache_key_str = f"{CACHE_KEYS['alpha_beta']}:{request.strategy_code}:{request.benchmark_code}"
    if request.start_date:
        cache_key_str += f":{request.start_date.date()}"
    cached = cache.get(cache_key_str)
    if cached:
        return AlphaBetaResponse(
            strategy_code=request.strategy_code,
            benchmark_code=request.benchmark_code,
            **cached
        )
    
    # 确定日期范围
    end_date = request.end_date or datetime.now()
    start_date = request.start_date or (end_date - timedelta(days=365))
    
    # 获取策略 (基金) 净值数据
    strategy_navs = FundService.get_fund_nav_history(
        db, request.strategy_code, start_date=start_date, end_date=end_date, limit=365
    )
    
    # 获取基准净值数据
    benchmark_navs = BenchmarkService.get_benchmark_nav_history(
        db, request.benchmark_code, start_date=start_date, end_date=end_date, limit=365
    )
    
    # 转换为价格序列 (按日期对齐)
    strategy_prices = {}
    for nav in strategy_navs:
        date_key = nav.nav_date.date() if hasattr(nav.nav_date, 'date') else nav.nav_date
        strategy_prices[date_key] = nav.nav
    
    benchmark_prices = {}
    for nav in benchmark_navs:
        date_key = nav.nav_date.date() if hasattr(nav.nav_date, 'date') else nav.nav_date
        benchmark_prices[date_key] = nav.nav
    
    # 找到共同的日期
    common_dates = sorted(set(strategy_prices.keys()) & set(benchmark_prices.keys()))
    
    if len(common_dates) < 2:
        raise HTTPException(
            status_code=400, 
            detail="数据点不足，无法计算 Alpha/Beta（需要至少2个共同交易日）"
        )
    
    # 提取价格序列
    strategy_price_list = [strategy_prices[d] for d in common_dates]
    benchmark_price_list = [benchmark_prices[d] for d in common_dates]
    
    # 计算 Alpha/Beta 和信息比率
    analysis = AlphaBetaCalculator.calculate_full_analysis(
        strategy_price_list, benchmark_price_list
    )
    
    result = {
        "strategy_code": request.strategy_code,
        "benchmark_code": request.benchmark_code,
        **analysis
    }
    
    # 缓存结果 (30分钟)
    cache.set(cache_key_str, analysis, CACHE_EXPIRE["medium"])
    
    return AlphaBetaResponse(**result)


# ============ 数据同步 API ============

@router.post("/sync/{code}")
async def sync_benchmark_nav(
    code: str,
    days: int = Query(30, ge=1, le=365, description="同步天数"),
    db: Session = Depends(get_db)
):
    """同步基准指数数据"""
    benchmark = BenchmarkService.get_benchmark_by_code(db, code)
    if not benchmark:
        # 尝试初始化默认基准
        BenchmarkService.init_default_benchmarks(db)
        benchmark = BenchmarkService.get_benchmark_by_code(db, code)
        if not benchmark:
            raise HTTPException(status_code=404, detail=f"基准指数 {code} 不存在")
    
    # 检查基金是否存在
    from app.models.benchmark import DEFAULT_BENCHMARKS
    benchmark_info = next((b for b in DEFAULT_BENCHMARKS if b["code"] == code), None)
    
    if not benchmark_info:
        raise HTTPException(status_code=404, detail=f"不支持同步基准指数 {code}")
    
    # 清除缓存
    cache.delete(CACHE_KEYS["benchmark_list"])
    cache.delete(f"{CACHE_KEYS['benchmark_nav']}:{code}")
    
    synced_count = BenchmarkSync.sync_benchmark_nav(db, code, days)
    
    return {
        "message": "同步完成",
        "code": code,
        "name": benchmark.name,
        "synced_count": synced_count
    }


@router.post("/init")
async def init_benchmarks(db: Session = Depends(get_db)):
    """初始化默认基准指数"""
    count = BenchmarkService.init_default_benchmarks(db)
    
    # 清除缓存
    cache.delete(CACHE_KEYS["benchmark_list"])
    
    return {
        "message": "初始化完成",
        "count": count
    }