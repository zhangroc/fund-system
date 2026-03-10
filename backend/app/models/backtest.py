"""回测相关数据模型"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class StrategyType(enum.Enum):
    """策略类型"""
    DOLLAR_COST_AVERAGING = "定投"  # 定期定额
    LUMP_SUM = "一次性买入"  # 一次性买入
    CONDITIONAL_BUY = "条件买入"  # 条件买入
    REBALANCE = "再平衡"  # 仓位再平衡


class BacktestStatus(enum.Enum):
    """回测状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Strategy(Base):
    """策略表"""
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 策略名称
    name = Column(String(100), nullable=False, comment="策略名称")
    
    # 策略描述
    description = Column(Text, nullable=True, comment="策略描述")
    
    # 策略类型
    strategy_type = Column(String(50), nullable=False, comment="策略类型")
    
    # 策略参数 (JSON)
    # 定投策略: {"amount": 1000, "frequency": "monthly", "day": 1}
    # 一次性买入: {"amount": 100000}
    parameters = Column(JSON, nullable=True, comment="策略参数")
    
    # 关联基金代码 (可选，多个用逗号分隔)
    fund_codes = Column(String(500), nullable=True, comment="关联基金代码")
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    # 更新时间
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    # 关联回测记录
    backtests = relationship("Backtest", back_populates="strategy")
    
    def __repr__(self):
        return f"<Strategy {self.id} - {self.name}>"


class Backtest(Base):
    """回测记录表"""
    __tablename__ = "backtests"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 策略ID
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, comment="策略ID")
    
    # 回测名称
    name = Column(String(100), nullable=False, comment="回测名称")
    
    # 回测状态
    status = Column(String(20), default="pending", comment="状态: pending/running/completed/failed")
    
    # 回测开始日期
    start_date = Column(DateTime, nullable=False, comment="回测开始日期")
    
    # 回测结束日期
    end_date = Column(DateTime, nullable=False, comment="回测结束日期")
    
    # 初始资金
    initial_capital = Column(Float, nullable=False, comment="初始资金")
    
    # 回测配置 (JSON)
    config = Column(JSON, nullable=True, comment="回测配置")
    
    # 回测结果 (JSON)
    result = Column(JSON, nullable=True, comment="回测结果")
    
    # 进度百分比
    progress = Column(Integer, default=0, comment="进度百分比")
    
    # 错误信息
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # 开始时间
    started_at = Column(DateTime, nullable=True, comment="开始时间")
    
    # 完成时间
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    # 更新时间
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    # 关联策略
    strategy = relationship("Strategy", back_populates="backtests")
    
    # 关联交易记录
    trades = relationship("BacktestTrade", back_populates="backtest")
    
    def __repr__(self):
        return f"<Backtest {self.id} - {self.name}>"


class BacktestTrade(Base):
    """回测交易记录表"""
    __tablename__ = "backtest_trades"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 回测ID
    backtest_id = Column(Integer, ForeignKey("backtests.id"), nullable=False, comment="回测ID")
    
    # 交易日期
    trade_date = Column(DateTime, nullable=False, comment="交易日期")
    
    # 交易类型 (买入/卖出)
    trade_type = Column(String(10), nullable=False, comment="交易类型: buy/sell")
    
    # 基金代码
    fund_code = Column(String(10), nullable=False, comment="基金代码")
    
    # 交易金额
    amount = Column(Float, nullable=False, comment="交易金额")
    
    # 净值
    nav = Column(Float, nullable=False, comment="交易时净值")
    
    # 份额
    shares = Column(Float, nullable=False, comment="购买份额")
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    # 关联回测
    backtest = relationship("Backtest", back_populates="trades")
    
    def __repr__(self):
        return f"<BacktestTrade {self.id} - {self.trade_type} {self.fund_code}>"