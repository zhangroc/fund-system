"""组合服务 - 业务逻辑层"""
import logging
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio
from app.schemas.portfolio import PortfolioCreate, PortfolioUpdate

logger = logging.getLogger(__name__)


class PortfolioService:
    """组合服务类"""
    
    @staticmethod
    def get_portfolio_list(
        db: Session, 
        skip: int = 0, 
        limit: int = 20
    ) -> Tuple[List[Portfolio], int]:
        """获取组合列表"""
        query = db.query(Portfolio)
        total = query.count()
        portfolios = query.offset(skip).limit(limit).all()
        return portfolios, total
    
    @staticmethod
    def get_portfolio_by_id(db: Session, portfolio_id: int) -> Optional[Portfolio]:
        """根据ID获取组合"""
        return db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    
    @staticmethod
    def get_portfolio_by_name(db: Session, name: str) -> Optional[Portfolio]:
        """根据名称获取组合"""
        return db.query(Portfolio).filter(Portfolio.name == name).first()
    
    @staticmethod
    def create_portfolio(db: Session, portfolio_data: PortfolioCreate) -> Portfolio:
        """创建组合"""
        portfolio = Portfolio(**portfolio_data.model_dump())
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
        return portfolio
    
    @staticmethod
    def update_portfolio(
        db: Session, 
        portfolio_id: int, 
        portfolio_data: dict
    ) -> Optional[Portfolio]:
        """更新组合"""
        portfolio = PortfolioService.get_portfolio_by_id(db, portfolio_id)
        if portfolio:
            for key, value in portfolio_data.items():
                if value is not None:
                    setattr(portfolio, key, value)
            db.commit()
            db.refresh(portfolio)
        return portfolio
    
    @staticmethod
    def delete_portfolio(db: Session, portfolio_id: int) -> bool:
        """删除组合"""
        portfolio = PortfolioService.get_portfolio_by_id(db, portfolio_id)
        if portfolio:
            db.delete(portfolio)
            db.commit()
            return True
        return False
    
    @staticmethod
    def filter_portfolios(
        db: Session,
        status: Optional[str] = None,
        risk_level: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Portfolio], int]:
        """筛选组合"""
        query = db.query(Portfolio)
        
        if status:
            query = query.filter(Portfolio.status == status)
        
        if risk_level:
            query = query.filter(Portfolio.risk_level == risk_level)
        
        total = query.count()
        skip = (page - 1) * page_size
        portfolios = query.offset(skip).limit(page_size).all()
        
        return portfolios, total
    
    @staticmethod
    def get_portfolio_with_funds(
        db: Session, 
        portfolio_id: int
    ) -> Optional[Portfolio]:
        """获取组合详情（含关联基金）"""
        return db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()