"""基金相关 Pydantic 模型"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.fund import FundType


# ============ 基金基础信息 Schema ============

class FundBase(BaseModel):
    """基金基础信息"""
    fund_code: str = Field(..., description="基金代码")
    fund_name: str = Field(..., description="基金名称")
    fund_type: FundType = Field(..., description="基金类型")
    manager: Optional[str] = Field(None, description="基金管理公司")
    scale: Optional[float] = Field(None, description="基金规模(亿元)")
    fund_manager: Optional[str] = Field(None, description="基金经理")
    custodian: Optional[str] = Field(None, description="托管银行")
    status: str = Field("在售", description="基金状态")
    risk_level: Optional[str] = Field(None, description="风险等级")
    management_fee: Optional[float] = Field(None, description="管理费率")
    custodian_fee: Optional[float] = Field(None, description="托管费率")
    sales_service_fee: Optional[float] = Field(None, description="销售服务费率")


class FundCreate(FundBase):
    """创建基金请求"""
    pass


class FundUpdate(BaseModel):
    """更新基金请求"""
    fund_name: Optional[str] = None
    manager: Optional[str] = None
    scale: Optional[float] = None
    fund_manager: Optional[str] = None
    custodian: Optional[str] = None
    status: Optional[str] = None
    risk_level: Optional[str] = None
    management_fee: Optional[float] = None
    custodian_fee: Optional[float] = None
    sales_service_fee: Optional[float] = None


class FundResponse(FundBase):
    """基金响应"""
    id: int
    establishment_date: Optional[datetime] = None
    investment_target: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============ 基金净值 Schema ============

class FundNavBase(BaseModel):
    """基金净值基础信息"""
    fund_code: str = Field(..., description="基金代码")
    nav_date: datetime = Field(..., description="净值日期")
    nav: float = Field(..., description="单位净值")
    accumulated_nav: Optional[float] = Field(None, description="累计净值")
    daily_growth: Optional[float] = Field(None, description="日增长率(%)")


class FundNavCreate(FundNavBase):
    """创建基金净值请求"""
    pass


class FundNavResponse(FundNavBase):
    """基金净值响应"""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============ 基金筛选 Schema ============

class FundFilter(BaseModel):
    """基金筛选条件"""
    fund_type: Optional[str] = Field(None, description="基金类型")
    min_scale: Optional[float] = Field(None, description="最小规模(亿元)")
    max_scale: Optional[float] = Field(None, description="最大规模(亿元)")
    manager: Optional[str] = Field(None, description="基金管理公司(模糊匹配)")
    status: Optional[str] = Field(None, description="基金状态")
    risk_level: Optional[str] = Field(None, description="风险等级")
    min_nav: Optional[float] = Field(None, description="最小净值")
    max_nav: Optional[float] = Field(None, description="最大净值")


class FundFilterRequest(BaseModel):
    """基金筛选请求"""
    filters: FundFilter = Field(default_factory=FundFilter, description="筛选条件")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


class FundFilterResponse(BaseModel):
    """基金筛选响应"""
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    data: List[FundResponse] = Field(..., description="基金列表")


# ============ 基金详情 Schema ============

class FundDetailResponse(FundResponse):
    """基金详情响应"""
    nav_history: Optional[List[FundNavResponse]] = Field(None, description="净值历史")
    recent_holdings: Optional[List[dict]] = Field(None, description="近期持仓")
    
    model_config = ConfigDict(from_attributes=True)


# ============ 基金排名 Schema ============

class FundRankRequest(BaseModel):
    """基金排名请求"""
    fund_type: Optional[FundType] = Field(None, description="基金类型")
    rank_by: str = Field("scale", description="排序字段: scale/risk/performance")
    order: str = Field("desc", description="排序方式: asc/desc")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")