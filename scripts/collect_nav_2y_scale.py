#!/usr/bin/env python3
"""
采集规模>=2亿基金的净值历史数据

用途: 采集5122只规模>=2亿基金的完整净值历史数据
"""
import sys
import os
import time
import logging
from datetime import datetime
from typing import List, Dict, Any

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def collect_nav_for_2y_scale_funds():
    """采集规模>=2亿基金的净值历史数据"""
    import akshare as ak
    import pandas as pd
    from app.core.database import SessionLocal
    from app.models.fund import Fund, FundNav
    
    db = SessionLocal()
    
    try:
        # 1. 查询规模>=2亿但未采集净值的基金
        logger.info("查询规模>=2亿但未采集净值的基金...")
        no_nav_funds = db.query(Fund).filter(
            Fund.scale >= 2,
            ~Fund.fund_code.in_(
                db.query(FundNav.fund_code).distinct()
            )
        ).all()
        
        logger.info(f"找到 {len(no_nav_funds)} 只规模>=2亿但未采集净值的基金")
        
        # 2. 查询规模>=2亿但已有部分净值的基金
        logger.info("查询规模>=2亿但已有净值的基金...")
        has_nav_funds = db.query(Fund).filter(
            Fund.scale >= 2,
            Fund.fund_code.in_(
                db.query(FundNav.fund_code).distinct()
            )
        ).all()
        
        logger.info(f"规模>=2亿已采集净值的基金: {len(has_nav_funds)} 只")
        
        # 3. 采集未采集净值的基金
        result = {
            "new_funds_processed": 0,
            "new_nav_records": 0,
            "errors": []
        }
        
        total_to_process = len(no_nav_funds)
        
        for idx, fund in enumerate(no_nav_funds):
            try:
                logger.info(f"[{idx+1}/{total_to_process}] 采集 {fund.fund_code} {fund.fund_name} 的净值数据...")
                
                # 获取净值历史
                nav_df = ak.fund_etf_fund_info_em(fund=fund.fund_code)
                
                if nav_df is None or nav_df.empty:
                    logger.warning(f"  {fund.fund_code} 无净值数据")
                    continue
                
                # 插入所有历史净值（不限制条数）
                count = 0
                for _, row in nav_df.iterrows():
                    try:
                        nav_date = row.get('净值日期')
                        if isinstance(nav_date, str):
                            nav_date = pd.to_datetime(nav_date)
                        
                        # 检查是否已存在
                        existing = db.query(FundNav).filter(
                            FundNav.fund_code == fund.fund_code,
                            FundNav.nav_date == nav_date
                        ).first()
                        
                        if existing:
                            continue
                        
                        nav = row.get('单位净值')
                        accumulated_nav = row.get('累计净值')
                        daily_growth = row.get('日增长率')
                        
                        if nav:
                            nav_record = FundNav(
                                fund_code=fund.fund_code,
                                nav_date=nav_date,
                                nav=float(nav),
                                accumulated_nav=float(accumulated_nav) if pd.notna(accumulated_nav) else None,
                                daily_growth=float(str(daily_growth).replace('%', '')) if pd.notna(daily_growth) else None
                            )
                            db.add(nav_record)
                            count += 1
                            
                    except Exception as e:
                        logger.warning(f"  处理净值记录失败: {e}")
                        continue
                
                db.commit()
                result["new_funds_processed"] += 1
                result["new_nav_records"] += count
                logger.info(f"  新增 {count} 条净值记录")
                
                # 避免请求过快
                time.sleep(0.3)
                
            except Exception as e:
                logger.error(f"  采集 {fund.fund_code} 失败: {e}")
                result["errors"].append(f"{fund.fund_code}: {str(e)}")
                continue
        
        # 4. 对于已有净值的基金，补充最新净值
        logger.info(f"\n开始更新 {len(has_nav_funds)} 只已有净值基金的最新数据...")
        
        # 获取今日日期
        today = datetime.now()
        
        try:
            daily_df = ak.fund_open_fund_daily_em()
            
            if daily_df is not None and not daily_df.empty:
                cols = daily_df.columns.tolist()
                nav_col = [c for c in cols if '单位净值' in c]
                accum_nav_col = [c for c in cols if '累计净值' in c]
                growth_col = [c for c in cols if '增长率' in c]
                
                for fund in has_nav_funds:
                    try:
                        # 查找基金代码
                        fund_code = fund.fund_code
                        row_data = daily_df[daily_df['基金代码'] == fund_code]
                        
                        if row_data.empty:
                            continue
                        
                        row = row_data.iloc[0]
                        nav = row.get(nav_col[0]) if nav_col else None
                        
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
                            daily_growth=float(daily_growth) if daily_growth else None
                        )
                        db.add(nav_record)
                        result["new_nav_records"] += 1
                        
                    except Exception as e:
                        continue
                
                db.commit()
                logger.info(f"今日净值更新完成")
                
        except Exception as e:
            logger.error(f"批量更新今日净值失败: {e}")
        
        # 5. 汇总统计
        logger.info("\n" + "=" * 50)
        logger.info("采集完成!")
        logger.info("=" * 50)
        
        # 最终统计
        total_2y_funds = db.query(Fund).filter(Fund.scale >= 2).count()
        funds_with_nav = db.query(FundNav.fund_code).filter(
            FundNav.fund_code.in_(
                db.query(Fund.fund_code).filter(Fund.scale >= 2)
            )
        ).distinct().count()
        total_nav_records = db.query(FundNav).filter(
            FundNav.fund_code.in_(
                db.query(Fund.fund_code).filter(Fund.scale >= 2)
            )
        ).count()
        
        logger.info(f"规模>=2亿基金总数: {total_2y_funds}")
        logger.info(f"已采集净值基金数: {funds_with_nav}")
        logger.info(f"净值记录总数: {total_nav_records}")
        logger.info(f"本次新增处理基金: {result['new_funds_processed']}")
        logger.info(f"本次新增净值记录: {result['new_nav_records']}")
        
        if result["errors"]:
            logger.warning(f"失败基金数: {len(result['errors'])}")
        
        return result
        
    except Exception as e:
        logger.error(f"采集失败: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
        
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("开始采集规模>=2亿基金的净值数据...")
    start_time = datetime.now()
    
    result = collect_nav_for_2y_scale_funds()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    logger.info(f"总耗时: {duration:.2f}秒 ({duration/60:.2f}分钟)")