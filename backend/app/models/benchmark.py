"""基准指数数据模型"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from app.core.database import Base


class Benchmark(Base):
    """基准指数信息表"""
    __tablename__ = "benchmarks"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 指数代码 (如: 000300 代表沪深300)
    code = Column(String(20), unique=True, index=True, nullable=False, comment="指数代码")
    
    # 指数名称
    name = Column(String(100), nullable=False, comment="指数名称")
    
    # 指数类型 (如: 股票指数, 债券指数)
    index_type = Column(String(50), comment="指数类型")
    
    # 发布日期
    publish_date = Column(DateTime, nullable=True, comment="发布日期")
    
    # 基准点数
    base_point = Column(Float, default=1000, comment="基准点数")
    
    # 描述
    description = Column(Text, nullable=True, comment="指数描述")
    
    # 创建和更新时间
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    def __repr__(self):
        return f"<Benchmark {self.code} - {self.name}>"


class BenchmarkNav(Base):
    """基准指数净值表"""
    __tablename__ = "benchmark_nav"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 指数代码
    code = Column(String(20), index=True, nullable=False, comment="指数代码")
    
    # 净值日期
    nav_date = Column(DateTime, nullable=False, comment="净值日期")
    
    # 指数点位
    nav = Column(Float, nullable=False, comment="指数点位")
    
    # 日收益率 (%)
    daily_return = Column(Float, nullable=True, comment="日收益率(%)")
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    def __repr__(self):
        return f"<BenchmarkNav {self.code} - {self.nav_date}>"


# 预设常用基准指数
DEFAULT_BENCHMARKS = [
    {"code": "000300", "name": "沪深300", "index_type": "股票指数", "base_point": 1000},
    {"code": "000001", "name": "上证指数", "index_type": "股票指数", "base_point": 100},
    {"code": "399001", "name": "深证成指", "index_type": "股票指数", "base_point": 1000},
    {"code": "000905", "name": "中证500", "index_type": "股票指数", "base_point": 1000},
    {"code": "000016", "name": "上证50", "index_type": "股票指数", "base_point": 1000},
    {"code": "399006", "name": "创业板指", "index_type": "股票指数", "base_point": 1000},
    {"code": "000012", "name": "中证国债指数", "index_type": "债券指数", "base_point": 100},
    {"code": "000826", "name": "中证800", "index_type": "股票指数", "base_point": 1000},
    {"code": "HSI", "name": "恒生指数", "index_type": "股票指数", "base_point": 100},
    {"code": "SPX", "name": "标普500", "index_type": "股票指数", "base_point": 1000},
]