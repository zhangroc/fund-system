#!/usr/bin/env python3
"""数据库初始化脚本"""
import os
import sys
import logging
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.database import Base, init_db
from app.models.fund import Fund, FundNav, FundHolding
from app.services.fund_service import AkShareSync

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_database():
    """创建数据库"""
    logger.info("正在创建数据库...")
    
    # 连接 MySQL 服务器（不指定数据库）
    engine = create_engine(
        f"mysql+pymysql://{settings.mysql_user}:{settings.mysql_password}@{settings.mysql_host}:{settings.mysql_port}",
        pool_pre_ping=True
    )
    
    try:
        with engine.connect() as conn:
            # 创建数据库（如果不存在）
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {settings.mysql_database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            conn.commit()
        logger.info(f"数据库 {settings.mysql_database} 创建成功")
    except Exception as e:
        logger.error(f"创建数据库失败: {e}")
        raise
    finally:
        engine.dispose()


def create_tables():
    """创建数据表"""
    logger.info("正在创建数据表...")
    init_db()
    logger.info("数据表创建成功")


def sync_fund_data():
    """同步基金数据"""
    logger.info("正在从 AkShare 同步基金数据...")
    
    # 重新创建引擎（指定数据库）
    from app.core.database import SessionLocal
    db = SessionLocal()
    
    try:
        # 同步基金列表（规模 > 2亿）
        synced_count = AkShareSync.sync_fund_list(db, min_scale=2.0)
        logger.info(f"成功同步 {synced_count} 个基金")
        
        # 显示统计信息
        from sqlalchemy import func
        total = db.query(func.count(Fund.id)).scalar()
        logger.info(f"数据库中共有 {total} 个基金")
        
        # 显示规模大于2亿的基金数量
        large_funds = db.query(func.count(Fund.id)).filter(Fund.scale >= 2.0).scalar()
        logger.info(f"规模大于2亿的基金: {large_funds} 个")
        
    except Exception as e:
        logger.error(f"同步基金数据失败: {e}")
        raise
    finally:
        db.close()


def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("开始初始化数据库")
    logger.info("=" * 50)
    
    try:
        # 1. 创建数据库
        create_database()
        
        # 2. 创建数据表
        create_tables()
        
        # 3. 同步基金数据
        sync_fund_data()
        
        logger.info("=" * 50)
        logger.info("数据库初始化完成!")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()