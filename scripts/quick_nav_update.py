#!/usr/bin/env python3
"""
快速更新规模>=2亿基金的净值数据
1. 批量更新今日净值
2. 补充历史净值（尽可能多）
"""
import sys
import os
import time
import logging
from datetime import datetime
from typing import List, Dict, Any

# 添加项目路径
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
sys.path.insert(0, backend_path)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def update_nav_batch():
    """批量更新净值"""
    import akshare as ak
    import pandas as pd
    from app.core.database import SessionLocal
    from app.models.fund import Fund, FundNav
    
    db = SessionLocal()
    today = datetime.now()
    
    result = {
        "today_nav_updated": 0,
        "history_nav_records": 0,
        "history_funds_processed": 0,
        "errors": []
    }
    
    try:
        # 步骤1: 批量获取今日净值
        logger.info("步骤1: 批量获取今日净值...")
        daily_df = ak.fund_open_fund_daily_em()
        
        if daily_df is None or daily_df.empty:
            logger.error("无法获取今日净值数据")
            return result
        
        # 获取列名
        cols = daily_df.columns.tolist()
        nav_col = [c for c in cols if '单位净值' in c and '2026' in c]
        accum_nav_col = [c for c in cols if '累计净值' in c and '2026' in c]
        growth_col = [c for c in cols if '日增长率' in c]
        
        if not nav_col:
            nav_col = [c for c in cols if '单位净值' in c]
            accum_nav_col = [c for c in cols if '累计净值' in c]
        
        logger.info(f"使用列: {nav_col}, {accum_nav_col}")
        
        # 只处理规模>=2亿的基金
        fund_codes_2y = [f[0] for f in db.query(Fund.fund_code).filter(Fund.scale >= 2).all()]
        fund_codes_set = set(fund_codes_2y)
        
        logger.info(f"规模>=2亿基金数量: {len(fund_codes_set)}")
        
        for _, row in daily_df.iterrows():
            try:
                fund_code = str(row.get('基金代码', '')).zfill(6)
                
                # 只处理规模>=2亿的基金
                if fund_code not in fund_codes_set:
                    continue
                
                nav = row.get(nav_col[0])
                if nav is None:
                    continue
                
                # 检查是否已存在今日净值
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
                result["today_nav_updated"] += 1
                
            except Exception as e:
                continue
        
        db.commit()
        logger.info(f"今日净值更新完成: {result['today_nav_updated']} 条记录")
        
        # 步骤2: 补充历史净值 - 优先处理完全没有数据的基金
        logger.info("步骤2: 补充历史净值...")
        
        # 找出规模>=2亿但完全没有净值数据的基金
        no_nav_funds = db.query(Fund).filter(
            Fund.scale >= 2,
            ~Fund.fund_code.in_(
                db.query(FundNav.fund_code).distinct()
            )
        ).limit(50).all()  # 限制每次处理数量
        
        logger.info(f"找到 {len(no_nav_funds)} 只完全没有净值数据的基金")
        
        for fund in no_nav_funds:
            try:
                logger.info(f"采集 {fund.fund_code} {fund.fund_name[:10]} 的历史净值...")
                
                nav_df = ak.fund_etf_fund_info_em(fund=fund.fund_code)
                
                if nav_df is None or nav_df.empty:
                    logger.warning(f"  无数据")
                    continue
                
                # 插入所有历史数据
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
                            
                    except Exception as e:
                        continue
                
                db.commit()
                result["history_funds_processed"] += 1
                result["history_nav_records"] += count
                logger.info(f"  新增 {count} 条记录")
                
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"  失败: {e}")
                result["errors"].append(f"{fund.fund_code}: {str(e)}")
                continue
        
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
        
        logger.info("=" * 50)
        logger.info("采集完成!")
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
    start = datetime.now()
    result = update_nav_batch()
    duration = (datetime.now() - start).total_seconds()
    logger.info(f"总耗时: {duration:.1f}秒")