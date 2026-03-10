"""基金数据模型"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class FundType(enum.Enum):
    """基金类型枚举"""
    STOCK = "股票型"
    MIXED = "混合型"
    BOND = "债券型"
    INDEX = "指数型"
    QDII = "QDII"
    MONEY = "货币型"
    FOF = "FOF"
    OTHER = "其他"


class Fund(Base):
    """基金基本信息表"""
    __tablename__ = "funds"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 基金代码 (6位数字)
    fund_code = Column(String(10), unique=True, index=True, nullable=False, comment="基金代码")
    
    # 基金名称
    fund_name = Column(String(200), nullable=False, comment="基金名称")
    
    # 基金类型
    fund_type = Column(String(20), nullable=False, comment="基金类型")
    
    # 管理公司
    manager = Column(String(200), comment="基金管理公司")
    
    # 基金规模 (单位: 亿元)
    scale = Column(Float, default=0, comment="基金规模(亿元)")
    
    # 成立日期
    establishment_date = Column(DateTime, nullable=True, comment="成立日期")
    
    # 基金经理
    fund_manager = Column(String(100), comment="基金经理")
    
    # 托管银行
    custodian = Column(String(100), comment="托管银行")
    
    # 基金状态 (在售/停售/募集)
    status = Column(String(20), default="在售", comment="基金状态")
    
    # 风险等级
    risk_level = Column(String(20), comment="风险等级")
    
    # 投资目标
    investment_target = Column(Text, nullable=True, comment="投资目标")
    
    # 费率信息
    management_fee = Column(Float, nullable=True, comment="管理费率")
    custodian_fee = Column(Float, nullable=True, comment="托管费率")
    sales_service_fee = Column(Float, nullable=True, comment="销售服务费率")
    
    # 创建和更新时间
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    # 关联组合 - 暂时注释，等Portfolio模型完善后再启用
    # portfolios = relationship("Portfolio", secondary="portfolio_funds", back_populates="funds")
    
    def __repr__(self):
        return f"<Fund {self.fund_code} - {self.fund_name}>"


class FundNav(Base):
    """基金净值表"""
    __tablename__ = "fund_nav"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 基金代码
    fund_code = Column(String(10), index=True, nullable=False, comment="基金代码")
    
    # 净值日期
    nav_date = Column(DateTime, nullable=False, comment="净值日期")
    
    # 单位净值
    nav = Column(Float, nullable=False, comment="单位净值")
    
    # 累计净值
    accumulated_nav = Column(Float, nullable=True, comment="累计净值")
    
    # 日增长率 (%)
    daily_growth = Column(Float, nullable=True, comment="日增长率(%)")
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    def __repr__(self):
        return f"<FundNav {self.fund_code} - {self.nav_date}>"


class FundHolding(Base):
    """基金持仓表"""
    __tablename__ = "fund_holdings"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 基金代码
    fund_code = Column(String(10), index=True, nullable=False, comment="基金代码")
    
    # 持仓日期
    holding_date = Column(DateTime, nullable=False, comment="持仓日期")
    
    # 股票代码
    stock_code = Column(String(20), nullable=True, comment="股票代码")
    
    # 股票名称
    stock_name = Column(String(100), nullable=True, comment="股票名称")
    
    # 占净值比例 (%)
    holding_ratio = Column(Float, nullable=True, comment="占净值比例(%)")
    
    # 持仓市值 (万元)
    holding_market_value = Column(Float, nullable=True, comment="持仓市值(万元)")
    
    # 持股数 (股)
    shares = Column(Float, nullable=True, comment="持股数")
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    def __repr__(self):
        return f"<FundHolding {self.fund_code} - {self.stock_code}>"