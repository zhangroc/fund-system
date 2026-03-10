"""组合 Schema"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class HoldingItem(BaseModel):
    """持仓项"""
    fund_code: str = Field(..., description="基金代码")
    fund_name: Optional[str] = Field(None, description="基金名称")
    weight: float = Field(..., ge=0, le=1, description="权重(0-1)")


class PortfolioBase(BaseModel):
    """组合基础字段"""
    name: str = Field(..., min_length=1, max_length=100, description="组合名称")
    description: Optional[str] = Field(None, description="组合描述")
    holdings: List[HoldingItem] = Field(default=[], description="持仓明细")
    status: str = Field(default="active", description="状态")


class PortfolioCreate(PortfolioBase):
    """创建组合请求"""
    total_assets: Optional[float] = Field(0, description="总资产")
    cash: Optional[float] = Field(0, description="现金")


class PortfolioUpdate(BaseModel):
    """更新组合请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    holdings: Optional[List[HoldingItem]] = None
    total_assets: Optional[float] = None
    cash: Optional[float] = None
    status: Optional[str] = None


class PortfolioResponse(PortfolioBase):
    """组合响应"""
    id: int
    total_assets: float
    cash: float
    status: str
    risk_level: Optional[str] = None
    target_return: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PortfolioListResponse(BaseModel):
    """组合列表响应"""
    total: int
    page: int
    page_size: int
    data: List[PortfolioResponse]


class PortfolioDetailResponse(BaseModel):
    """组合详情响应"""
    id: int
    name: str
    description: Optional[str] = None
    status: str
    risk_level: Optional[str] = None
    target_return: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    funds: List[dict] = []