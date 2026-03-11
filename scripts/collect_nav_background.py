#!/usr/bin/env python3
"""
后台持续采集规模>=2亿基金的净值历史数据
"""
import sys
import os
import time
import logging
from datetime import datetime

# 添加项目路径
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
sys.path.insert(0, backend_path)

# 确保日志目录存在
log_dir = '/home/ubuntu/.openclaw/workspace/fund-system/logs'
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(log_dir, 'nav_collection.log'))
    ]
)
logger = logging.getLogger(__name__)


def collect_all_nav():
    """采集所有规模>=2亿基金的净值历史"""
    import akshare as ak
    import pandas as pd
    from app.core.database import SessionLocal
    from app.models.fund import Fund, FundNav
    
    db = SessionLocal()
    today = datetime.now()
    
    result = {
        "processed": 0,
        "nav_records": 0,
        "errors": []
    }
    
    try:
        # 步骤1: 先批量更新今日净值
        logger.info("批量更新今日净值...")
        try:
            daily_df = ak.fund_open_fund_daily_em()
            if daily_df is not None:
                cols = daily_df.columns.tolist()
                nav_col = [c for c in cols if '单位净值' in c and '2026' in c]
                accum_nav_col = [c for c in cols if '累计净值' in c and '2026' in c]
                growth_col = [c for c in cols if '日增长率' in c]
                
                if not nav_col:
                    nav_col = [c for c in cols if '单位净值' in c][:1]
                    accum_nav_col = [c for c in cols if '累计净值' in c][:1]
                
                fund_codes_2y = set([f[0] for f in db.query(Fund.fund_code).filter(Fund.scale >= 2).all()])
                
                for _, row in daily_df.iterrows():
                    fund_code = str(row.get('基金代码', '')).zfill(6)
                    if fund_code not in fund_codes_2y:
                        continue
                    
                    nav = row.get(nav_col[0])
                    if nav is None:
                        continue
                    
                    existing = db.query(FundNav).filter(
                        FundNav.fund_code == fund_code,
                        FundNav.nav_date == today
                    ).first()
                    
                    if existing:
                        continue
                    
                    accum_nav = row.get(accum_nav_col[0]) if accum_nav_col else None
                    daily_growth = row.get(growth_col[0]) if growth_col else None
                    if daily_growth and isinstance(daily_growth, str):
                        daily_growth = daily_growth.replace('%', '')
                    
                    nav_record = FundNav(
                        fund_code=fund_code,
                        nav_date=today,
                        nav=float(nav),
                        accumulated_nav=float(accum_nav) if accum_nav else None,
                        daily_growth=float(daily_growth) if daily_growth and daily_growth not in [None, ''] else None
                    )
                    db.add(nav_record)
                
                db.commit()
                logger.info("今日净值更新完成")
        except Exception as e:
            logger.error(f"批量更新失败: {e}")
        
        # 步骤2: 采集完全没有数据的基金
        logger.info("采集完全没有净值数据的基金...")
        
        # 每次获取一小批处理
        batch_size = 10
        max_batches = 100  # 最多处理100批
        
        for batch_idx in range(max_batches):
            no_nav_funds = db.query(Fund).filter(
                Fund.scale >= 2,
                ~Fund.fund_code.in_(
                    db.query(FundNav.fund_code).distinct()
                )
            ).limit(batch_size).all()
            
            if not no_nav_funds:
                logger.info("所有基金都已采集完成!")
                break
            
            logger.info(f"批次 {batch_idx+1}: 处理 {len(no_nav_funds)} 只基金")
            
            for fund in no_nav_funds:
                try:
                    nav_df = ak.fund_etf_fund_info_em(fund=fund.fund_code)
                    
                    if nav_df is None or nav_df.empty:
                        logger.warning(f"{fund.fund_code} 无数据")
                        continue
                    
                    count = 0
                    for _, row in nav_df.iterrows():
                        try:
                            nav_date = row.get('净值日期')
                            if isinstance(nav_date, str):
                                nav_date = pd.to_datetime(nav_date)
                            
                            existing = db.query(FundNav).filter(
                                FundNav.fund_code == fund.fund_code,
                                FundNav.nav_date == nav_date
                            ).first()
                            
                            if existing:
                                continue
                            
                            nav = row.get('单位净值')
                            if nav:
                                nav_record = FundNav(
                                    fund_code=fund.fund_code,
                                    nav_date=nav_date,
                                    nav=float(nav),
                                    accumulated_nav=float(row.get('累计净值')) if pd.notna(row.get('累计净值')) else None,
                                    daily_growth=float(str(row.get('日增长率')).replace('%', '')) if pd.notna(row.get('日增长率')) else None
                                )
                                db.add(nav_record)
                                count += 1
                                
                        except Exception:
                            continue
                    
                    db.commit()
                    result["processed"] += 1
                    result["nav_records"] += count
                    logger.info(f"{fund.fund_code} 新增 {count} 条")
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"{fund.fund_code} 失败: {e}")
                    result["errors"].append(f"{fund.fund_code}: {str(e)}")
                    time.sleep(2)  # 失败后等待更长时间
                    continue
            
            # 每批次完成后检查进度
            remaining = db.query(Fund).filter(
                Fund.scale >= 2,
                ~Fund.fund_code.in_(
                    db.query(FundNav.fund_code).distinct()
                )
            ).count()
            
            logger.info(f"剩余未采集: {remaining} 只基金")
            
            if remaining == 0:
                break
        
        # 最终统计
        total_2y = db.query(Fund).filter(Fund.scale >= 2).count()
        with_nav = db.query(FundNav.fund_code).filter(
            FundNav.fund_code.in_(
                db.query(Fund.fund_code).filter(Fund.scale >= 2)
            )
        ).distinct().count()
        total_nav = db.query(FundNav).filter(
            FundNav.fund_code.in_(
                db.query(Fund.fund_code).filter(Fund.scale >= 2)
            )
        ).count()
        
        logger.info("=" * 60)
        logger.info(f"采集完成!")
        logger.info(f"规模>=2亿基金总数: {total_2y}")
        logger.info(f"已采集净值基金数: {with_nav}")
        logger.info(f"净值记录总数: {total_nav}")
        
        return result
        
    except Exception as e:
        logger.error(f"执行失败: {e}")
        import traceback
        traceback.print_exc()
        return result
        
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("开始采集规模>=2亿基金净值...")
    start = datetime.now()
    
    try:
        result = collect_all_nav()
    except KeyboardInterrupt:
        logger.info("用户中断")
    
    duration = (datetime.now() - start).total_seconds()
    logger.info(f"总耗时: {duration:.1f}秒 ({duration/60:.1f}分钟)")