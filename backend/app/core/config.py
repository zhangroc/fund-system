"""应用配置"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置类"""
    
    # 数据库配置（开发用SQLite，生产用MySQL）
    database_url: str = "sqlite:///./fund_system.db"
    
    # Redis 配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    
    # API 配置
    api_title: str = "公募基金筛选与策略回测系统"
    api_version: str = "1.0.0"
    api_description: str = "提供基金筛选、行情数据、策略回测等功能"
    
    class Config:
        env_file = ".env"
        extra = "allow"


# 创建全局配置实例
settings = Settings()