"""数据采集 API"""
import logging
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.data_collector import DataCollector, ScheduledCollector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/data", tags=["数据采集"])


@router.post("/collect/funds")
async def collect_fund_list(
    min_scale: float = 1.0,
    db: Session = Depends(get_db)
):
    """
    采集基金列表
    
    - min_scale: 最小规模(亿元)
    """
    collector = DataCollector(db)
    result = collector.collect_fund_list(min_scale=min_scale)
    return {
        "code": 200,
        "message": "基金列表采集完成",
        "data": result
    }


@router.post("/collect/nav")
async def collect_fund_nav(
    fund_codes: Optional[List[str]] = None,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    采集基金净值
    
    - fund_codes: 基金代码列表，None 表示所有基金
    - days: 采集天数
    """
    collector = DataCollector(db)
    result = collector.collect_fund_nav(fund_codes=fund_codes, days=days)
    return {
        "code": 200,
        "message": "基金净值采集完成",
        "data": result
    }


@router.post("/collect/details")
async def update_fund_details(
    fund_codes: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    """
    更新基金详细信息
    
    - fund_codes: 基金代码列表，None 表示所有基金
    """
    collector = DataCollector(db)
    result = collector.update_fund_details(fund_codes=fund_codes)
    return {
        "code": 200,
        "message": "基金详情更新完成",
        "data": result
    }


@router.post("/collect/holdings/{fund_code}")
async def collect_fund_holdings(
    fund_code: str,
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    采集基金持仓
    
    - fund_code: 基金代码
    - year: 年份，默认最新
    """
    collector = DataCollector(db)
    result = collector.collect_fund_holdings(fund_code=fund_code, year=year)
    
    if result["error"]:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return {
        "code": 200,
        "message": "基金持仓采集完成",
        "data": result
    }


@router.get("/collect/etf/{symbol}")
async def get_etf_hist(
    symbol: str,
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db)
):
    """
    获取 ETF 历史数据
    
    - symbol: ETF 代码
    - start_date: 开始日期 (YYYYMMDD)
    - end_date: 结束日期 (YYYYMMDD)
    """
    collector = DataCollector(db)
    df = collector.collect_etf_hist(symbol, start_date, end_date)
    
    if df.empty:
        raise HTTPException(status_code=404, detail="无数据")
    
    # 转换为列表格式
    data = df.to_dict(orient='records')
    
    return {
        "code": 200,
        "message": "成功",
        "data": data
    }


@router.get("/collect/rank")
async def get_fund_rank(
    fund_type: str = "全部",
    top_n: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取基金业绩排名
    
    - fund_type: 基金类型 (全部/股票型/混合型/债券型/指数型等)
    - top_n: 返回前 N 名
    """
    collector = DataCollector(db)
    df = collector.collect_fund_rank(fund_type=fund_type, top_n=top_n)
    
    if df.empty:
        raise HTTPException(status_code=404, detail="无数据")
    
    # 转换为列表格式
    data = df.to_dict(orient='records')
    
    return {
        "code": 200,
        "message": "成功",
        "data": data
    }


@router.post("/update/nav")
async def update_latest_nav(
    db: Session = Depends(get_db)
):
    """
    增量更新基金净值（用于定时任务）
    """
    collector = DataCollector(db)
    result = collector.update_latest_nav()
    
    return {
        "code": 200,
        "message": "净值更新完成",
        "data": result
    }


@router.post("/scheduled")
async def run_scheduled(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    执行定时采集任务
    
    在后台执行数据采集任务
    """
    # 使用后台任务执行
    background_tasks.add_task(ScheduledCollector.run_scheduled_collection, db)
    
    return {
        "code": 200,
        "message": "定时任务已启动"
    }


@router.get("/scheduled")
async def get_scheduled_status(
    db: Session = Depends(get_db)
):
    """
    获取定时任务状态和最近执行结果
    """
    # 返回最近的数据统计
    from app.models.fund import Fund, FundNav
    
    total_funds = db.query(Fund).count()
    total_nav_records = db.query(FundNav).count()
    
    # 最近更新的净值
    latest_nav = db.query(FundNav).order_by(FundNav.nav_date.desc()).first()
    
    return {
        "code": 200,
        "data": {
            "total_funds": total_funds,
            "total_nav_records": total_nav_records,
            "latest_nav_date": latest_nav.nav_date.isoformat() if latest_nav else None,
            "latest_nav_fund": latest_nav.fund_code if latest_nav else None
        }
    }