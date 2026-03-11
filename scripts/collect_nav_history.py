#!/usr/bin/env python3
"""
基金净值历史数据采集脚本
目标: 为规模≥2亿的基金补采完整历史净值数据

功能:
- 查询需要补采历史的基金列表
- 遍历调用 AkShare 接口
- 存储到 fund_nav 表
- 断点续采机制 (记录采集状态)
- 进度实时显示

参数:
  --batch-size: 每批处理数量 (默认50)
  --delay: 请求间隔秒 (默认0.5)
  --retry: 失败重试次数 (默认3)
  --log-file: 日志文件路径
  --limit: 限制采集基金数量 (默认全部)
"""
import sys
import os
import time
import argparse
import logging
from datetime import datetime
from pathlib import Path
from sqlalchemy import func, text

# 添加项目路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
backend_path = os.path.join(project_root, 'backend')
sys.path.insert(0, backend_path)

# 切换到 backend 目录以确保 SQLite 路径正确
os.chdir(backend_path)

# 确保日志目录存在
log_dir = os.path.join(project_root, 'logs')
os.makedirs(log_dir, exist_ok=True)


def setup_logging(log_file=None):
    """配置日志"""
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    return logging.getLogger(__name__)


def init_collection_status(logger):
    """初始化采集状态表"""
    import sqlite3
    
    db_path = os.path.join(backend_path, 'fund_system.db')
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # 创建采集状态表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS nav_collection_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fund_code VARCHAR(10) NOT NULL UNIQUE,
            status VARCHAR(20) DEFAULT 'pending',
            records_count INTEGER DEFAULT 0,
            last_attempt DATETIME,
            error_msg TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    logger.info("采集状态表已初始化")


def get_funds_to_collect(db, limit=None):
    """获取需要采集的基金列表"""
    from app.models.fund import Fund, FundNav
    
    # 规模>=2亿，且没有完整历史数据的基金
    # 完整历史定义为有>=1000条记录
    
    # 先找出已经有不少数据的基金（暂不处理）
    funds_with_enough = db.query(FundNav.fund_code).\
        group_by(FundNav.fund_code).\
        having(func.count(FundNav.id) >= 1000).\
        subquery()
    
    # 找出完全没有数据或数据不足的基金
    query = db.query(Fund).filter(
        Fund.scale >= 2,
        ~Fund.fund_code.in_(funds_with_enough)
    ).order_by(Fund.scale.desc())
    
    if limit:
        query = query.limit(limit)
    
    return query.all()


def collect_fund_nav(fund_code, logger, retry=3, delay=0.5):
    """采集单只基金的净值历史"""
    import akshare as ak
    import pandas as pd
    from app.models.fund import FundNav
    
    for attempt in range(retry):
        try:
            nav_df = ak.fund_etf_fund_info_em(fund=fund_code)
            
            if nav_df is None or nav_df.empty:
                return 0, f"无数据"
            
            records = 0
            for _, row in nav_df.iterrows():
                try:
                    nav_date = row.get('净值日期')
                    if nav_date is None:
                        continue
                    
                    if isinstance(nav_date, str):
                        nav_date = pd.to_datetime(nav_date)
                    
                    nav = row.get('单位净值')
                    if nav is None or pd.isna(nav):
                        continue
                    
                    # 累计净值
                    accum_nav = row.get('累计净值')
                    if pd.isna(accum_nav):
                        accum_nav = None
                    
                    # 日增长率
                    daily_growth = row.get('日增长率')
                    if daily_growth is not None and not pd.isna(daily_growth):
                        if isinstance(daily_growth, str):
                            daily_growth = daily_growth.replace('%', '')
                        try:
                            daily_growth = float(daily_growth)
                        except:
                            daily_growth = None
                    
                    record = FundNav(
                        fund_code=fund_code,
                        nav_date=nav_date,
                        nav=float(nav),
                        accumulated_nav=float(accum_nav) if accum_nav else None,
                        daily_growth=daily_growth
                    )
                    
                    # 检查是否已存在
                    existing = db.query(FundNav).filter(
                        FundNav.fund_code == fund_code,
                        FundNav.nav_date == nav_date
                    ).first()
                    
                    if not existing:
                        db.add(record)
                        records += 1
                        
                except Exception as e:
                    logger.debug(f"处理行失败: {e}")
                    continue
            
            db.commit()
            return records, None
            
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"{fund_code} 第{attempt+1}次失败: {error_msg}")
            if attempt < retry - 1:
                time.sleep(delay * (attempt + 1))  # 指数退避
    
    return 0, error_msg


def update_collection_status(fund_code, status, records_count=0, error_msg=None):
    """更新采集状态"""
    import sqlite3
    from sqlalchemy import func
    
    db_path = os.path.join(backend_path, 'fund_system.db')
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cur.execute("""
        INSERT INTO nav_collection_status 
        (fund_code, status, records_count, last_attempt, error_msg, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(fund_code) DO UPDATE SET
            status = excluded.status,
            records_count = excluded.records_count,
            last_attempt = excluded.last_attempt,
            error_msg = excluded.error_msg,
            updated_at = excluded.updated_at
    """, (fund_code, status, records_count, now, error_msg, now))
    
    conn.commit()
    conn.close()


def run_collection(args, logger):
    """执行采集任务"""
    from app.core.database import SessionLocal
    from sqlalchemy import func
    
    # 初始化状态表
    init_collection_status(logger)
    
    db = SessionLocal()
    start_time = datetime.now()
    
    result = {
        "processed": 0,
        "success": 0,
        "failed": 0,
        "total_records": 0,
        "errors": []
    }
    
    try:
        # 获取需要采集的基金
        logger.info(f"查询需要采集的基金 (规模≥2亿, 历史数据<1000条)...")
        funds = get_funds_to_collect(db, args.limit)
        total_funds = len(funds)
        logger.info(f"共需采集 {total_funds} 只基金")
        
        # 获取已采集的进度
        completed = db.execute(text("""
            SELECT COUNT(*) FROM nav_collection_status 
            WHERE status = 'completed'
        """)).scalar() or 0
        
        logger.info(f"已完成: {completed} 只")
        
        # 遍历采集
        for idx, fund in enumerate(funds):
            fund_code = fund.fund_code
            
            # 检查是否已完成
            status_record = db.execute(text("""
                SELECT status FROM nav_collection_status 
                WHERE fund_code = :fund_code
            """), {"fund_code": fund_code}).fetchone()
            
            if status_record and status_record[0] == 'completed':
                logger.debug(f"{fund_code} 已完成, 跳过")
                continue
            
            # 更新状态为处理中
            update_collection_status(fund_code, 'processing')
            
            # 采集
            logger.info(f"[{idx+1}/{total_funds}] 采集 {fund_code} ({fund.fund_name[:20] if fund.fund_name else ''})...")
            
            records, error = collect_fund_nav(fund_code, logger, args.retry, args.delay)
            
            if error:
                update_collection_status(fund_code, 'failed', 0, error)
                result["failed"] += 1
                result["errors"].append(f"{fund_code}: {error}")
                logger.warning(f"{fund_code} 失败: {error}")
            else:
                update_collection_status(fund_code, 'completed', records)
                result["success"] += 1
                result["total_records"] += records
                logger.info(f"{fund_code} 完成, 新增 {records} 条记录")
            
            result["processed"] += 1
            
            # 进度报告
            if (idx + 1) % 10 == 0:
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = (idx + 1) / elapsed * 60  # 每分钟处理数
                remaining = (total_funds - idx - 1) / rate if rate > 0 else 0
                logger.info(f"=== 进度: {idx+1}/{total_funds} ({100*(idx+1)/total_funds:.1f}%) | 速率: {rate:.1f}/分 | 预计剩余: {remaining:.0f}分钟 ===")
            
            time.sleep(args.delay)
        
        # 最终统计
        logger.info("=" * 60)
        logger.info("采集完成!")
        logger.info(f"处理: {result['processed']} 只")
        logger.info(f"成功: {result['success']} 只")
        logger.info(f"失败: {result['failed']} 只")
        logger.info(f"新增记录: {result['total_records']} 条")
        
        # 显示当前数据库状态
        total_2y = db.query(func.count()).select_from(Fund).filter(Fund.scale >= 2).scalar()
        total_nav = db.query(func.count()).select_from(FundNav).scalar()
        with_nav = db.query(FundNav.fund_code).distinct().count()
        
        logger.info(f"=== 当前数据库状态 ===")
        logger.info(f"规模≥2亿基金: {total_2y}")
        logger.info(f"有净值数据: {with_nav}")
        logger.info(f"净值记录总数: {total_nav}")
        
        return result
        
    except KeyboardInterrupt:
        logger.info("用户中断")
        return result
        
    except Exception as e:
        logger.error(f"执行失败: {e}")
        import traceback
        traceback.print_exc()
        return result
        
    finally:
        db.close()
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"总耗时: {duration:.1f}秒 ({duration/60:.1f}分钟)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='采集基金净值历史数据')
    parser.add_argument('--batch-size', type=int, default=50, help='每批处理数量')
    parser.add_argument('--delay', type=float, default=0.5, help='请求间隔秒')
    parser.add_argument('--retry', type=int, default=3, help='失败重试次数')
    parser.add_argument('--log-file', type=str, default=None, help='日志文件路径')
    parser.add_argument('--limit', type=int, default=None, help='限制采集基金数量')
    
    args = parser.parse_args()
    
    # 默认日志文件
    if not args.log_file:
        args.log_file = os.path.join(log_dir, f'nav_collection_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    
    logger = setup_logging(args.log_file)
    
    logger.info("=" * 60)
    logger.info("基金净值历史采集任务开始")
    logger.info(f"参数: batch_size={args.batch_size}, delay={args.delay}, retry={args.retry}")
    logger.info("=" * 60)
    
    result = run_collection(args, logger)
    
    sys.exit(0 if result['failed'] == 0 else 1)