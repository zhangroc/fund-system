"""组合模型"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class Portfolio(Base):
    """组合模型"""
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True, comment="组合名称")
    description = Column(Text, nullable=True, comment="组合描述")
    
    # 组合配置 - 存储基金及其权重
    # 格式: [{"fund_code": "000001", "fund_name": "xxx", "weight": 0.3}, ...]
    holdings = Column(JSON, nullable=True, default=list, comment="持仓明细")
    
    # 总资产、现金等
    total_assets = Column(Float, nullable=True, default=0, comment="总资产(元)")
    cash = Column(Float, nullable=True, default=0, comment="现金(元)")
    
    # 状态
    status = Column(String(20), nullable=False, default="active", comment="状态: active, archived")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")