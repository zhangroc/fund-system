"""基金服务 - 业务逻辑层"""
import logging
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
import pandas as pd

from app.models.fund import Fund, FundNav, FundType
from app.schemas.fund import FundFilter, FundCreate

logger = logging.getLogger(__name__)


class FundService:
    """基金服务类"""
    
    @staticmethod
    def get_fund_list(db: Session, skip: int = 0, limit: int = 20) -> Tuple[List[Fund], int]:
        """获取基金列表"""
        query = db.query(Fund)
        total = query.count()
        funds = query.offset(skip).limit(limit).all()
        return funds, total
    
    @staticmethod
    def get_fund_by_code(db: Session, fund_code: str) -> Optional[Fund]:
        """根据基金代码获取基金"""
        return db.query(Fund).filter(Fund.fund_code == fund_code).first()
    
    @staticmethod
    def create_fund(db: Session, fund_data: FundCreate) -> Fund:
        """创建基金"""
        fund = Fund(**fund_data.model_dump())
        db.add(fund)
        db.commit()
        db.refresh(fund)
        return fund
    
    @staticmethod
    def update_fund(db: Session, fund_code: str, fund_data: dict) -> Optional[Fund]:
        """更新基金"""
        fund = FundService.get_fund_by_code(db, fund_code)
        if fund:
            for key, value in fund_data.items():
                if value is not None:
                    setattr(fund, key, value)
            db.commit()
            db.refresh(fund)
        return fund
    
    @staticmethod
    def delete_fund(db: Session, fund_code: str) -> bool:
        """删除基金"""
        fund = FundService.get_fund_by_code(db, fund_code)
        if fund:
            db.delete(fund)
            db.commit()
            return True
        return False
    
    @staticmethod
    def filter_funds(
        db: Session, 
        filters: FundFilter, 
        page: int = 1, 
        page_size: int = 20
    ) -> Tuple[List[Fund], int]:
        """筛选基金"""
        query = db.query(Fund)
        
        # 基金类型筛选
        if filters.fund_type:
            query = query.filter(Fund.fund_type == filters.fund_type)
        
        # 规模筛选
        if filters.min_scale is not None:
            query = query.filter(Fund.scale >= filters.min_scale)
        if filters.max_scale is not None:
            query = query.filter(Fund.scale <= filters.max_scale)
        
        # 管理公司筛选
        if filters.manager:
            query = query.filter(Fund.manager.like(f"%{filters.manager}%"))
        
        # 状态筛选
        if filters.status:
            query = query.filter(Fund.status == filters.status)
        
        # 风险等级筛选
        if filters.risk_level:
            query = query.filter(Fund.risk_level == filters.risk_level)
        
        # 净值筛选
        if filters.min_nav is not None or filters.max_nav is not None:
            # 需要关联净值表
            nav_subquery = db.query(
                FundNav.fund_code,
                func.max(FundNav.nav_date).label("latest_date")
            ).group_by(FundNav.fund_code).subquery()
            
            latest_nav = db.query(
                FundNav.fund_code,
                FundNav.nav
            ).join(
                nav_subquery,
                and_(
                    FundNav.fund_code == nav_subquery.c.fund_code,
                    FundNav.nav_date == nav_subquery.c.latest_date
                )
            ).subquery()
            
            query = query.join(latest_nav, Fund.fund_code == latest_nav.c.fund_code)
            
            if filters.min_nav is not None:
                query = query.filter(latest_nav.c.nav >= filters.min_nav)
            if filters.max_nav is not None:
                query = query.filter(latest_nav.c.nav <= filters.max_nav)
        
        # 获取总数
        total = query.count()
        
        # 分页
        skip = (page - 1) * page_size
        funds = query.offset(skip).limit(page_size).all()
        
        return funds, total
    
    @staticmethod
    def get_fund_nav_history(
        db: Session, 
        fund_code: str, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[FundNav]:
        """获取基金净值历史"""
        query = db.query(FundNav).filter(FundNav.fund_code == fund_code)
        
        if start_date:
            query = query.filter(FundNav.nav_date >= start_date)
        if end_date:
            query = query.filter(FundNav.nav_date <= end_date)
        
        return query.order_by(FundNav.nav_date.desc()).limit(limit).all()
    
    @staticmethod
    def add_fund_nav(db: Session, fund_code: str, nav_data: dict) -> FundNav:
        """添加基金净值"""
        # 检查基金是否存在
        fund = FundService.get_fund_by_code(db, fund_code)
        if not fund:
            raise ValueError(f"基金 {fund_code} 不存在")
        
        nav = FundNav(fund_code=fund_code, **nav_data)
        db.add(nav)
        db.commit()
        db.refresh(nav)
        return nav
    
    @staticmethod
    def get_fund_rank(
        db: Session,
        fund_type: Optional[FundType] = None,
        rank_by: str = "scale",
        order: str = "desc",
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Fund], int]:
        """基金排名"""
        query = db.query(Fund)
        
        # 筛选类型
        if fund_type:
            query = query.filter(Fund.fund_type == fund_type)
        
        # 排序
        order_func = desc if order == "desc" else asc
        if rank_by == "scale":
            query = query.order_by(order_func(Fund.scale))
        elif rank_by == "risk":
            query = query.order_by(order_func(Fund.risk_level))
        
        # 获取总数
        total = query.count()
        
        # 分页
        skip = (page - 1) * page_size
        funds = query.offset(skip).limit(page_size).all()
        
        return funds, total
    
    @staticmethod
    def get_funds_by_scale(db: Session, min_scale: float = 2.0) -> List[Fund]:
        """获取规模大于指定值的基金"""
        return db.query(Fund).filter(Fund.scale >= min_scale).all()


# ============ AkShare 数据同步 ============

class AkShareSync:
    """AkShare 数据同步类"""
    
    @staticmethod
    def sync_fund_list(db: Session, min_scale: float = 2.0) -> int:
        """同步基金列表（规模大于指定值）"""
        try:
            import akshare as ak
            
            # 获取基金列表
            logger.info("正在从 AkShare 获取基金列表...")
            fund_df = ak.fund_info_a_code_name()
            
            if fund_df is None or fund_df.empty:
                logger.warning("未获取到基金数据")
                return 0
            
            synced_count = 0
            for _, row in fund_df.iterrows():
                try:
                    fund_code = str(row.get('code', '')).zfill(6)
                    fund_name = row.get('name', '')
                    
                    if not fund_code or not fund_name:
                        continue
                    
                    # 检查是否已存在
                    existing = FundService.get_fund_by_code(db, fund_code)
                    if existing:
                        continue
                    
                    # 尝试获取基金详情
                    fund_type = FundType.其他
                    try:
                        detail_df = ak.fund_info_a_em(fund=fund_code)
                        if detail_df is not None and not detail_df.empty:
                            # 解析基金类型
                            type_str = detail_df.iloc[0].get('type', '')
                            for ft in FundType:
                                if ft.value in type_str:
                                    fund_type = ft
                                    break
                    except Exception:
                        pass
                    
                    # 创建基金记录
                    fund = Fund(
                        fund_code=fund_code,
                        fund_name=fund_name,
                        fund_type=fund_type,
                        status="在售"
                    )
                    db.add(fund)
                    synced_count += 1
                    
                except Exception as e:
                    logger.warning(f"同步基金失败: {e}")
                    continue
            
            db.commit()
            logger.info(f"成功同步 {synced_count} 个基金")
            return synced_count
            
        except ImportError:
            logger.error("请安装 akshare: pip install akshare")
            return 0
        except Exception as e:
            logger.error(f"同步基金列表失败: {e}")
            db.rollback()
            return 0
    
    @staticmethod
    def sync_fund_nav(db: Session, fund_code: str, days: int = 30) -> int:
        """同步基金净值"""
        try:
            import akshare as ak
            
            # 获取净值数据
            nav_df = ak.fund_nav_em(fund=fund_code)
            
            if nav_df is None or nav_df.empty:
                return 0
            
            synced_count = 0
            for _, row in nav_df.tail(days).iterrows():
                try:
                    nav_date = row.get('净值日期')
                    if isinstance(nav_date, str):
                        nav_date = pd.to_datetime(nav_date)
                    
                    nav = row.get('单位净值')
                    accumulated_nav = row.get('累计净值')
                    daily_growth = row.get('日增长率')
                    
                    if nav:
                        nav_record = FundNav(
                            fund_code=fund_code,
                            nav_date=nav_date,
                            nav=float(nav),
                            accumulated_nav=float(accumulated_nav) if accumulated_nav else None,
                            daily_growth=float(daily_growth.replace('%', '')) if daily_growth else None
                        )
                        db.add(nav_record)
                        synced_count += 1
                        
                except Exception as e:
                    logger.warning(f"同步净值失败: {e}")
                    continue
            
            db.commit()
            return synced_count
            
        except ImportError:
            logger.error("请安装 akshare: pip install akshare")
            return 0
        except Exception as e:
            logger.error(f"同步基金净值失败: {e}")
            db.rollback()
            return 0