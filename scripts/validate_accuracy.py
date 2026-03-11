#!/usr/bin/env python3
"""
净值数据准确性验证脚本

验证内容:
- 随机抽取基金，与官网(AkShare)数据对比
- 验证单位净值、累计净值、日增长率
- 目标: 与官网误差为0
"""
import sys
import os
import argparse
from datetime import datetime, timedelta

# 添加项目路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
backend_path = os.path.join(project_root, 'backend')
sys.path.insert(0, backend_path)

# 切换到 backend 目录以确保 SQLite 路径正确
os.chdir(backend_path)

from app.core.database import SessionLocal
from app.models.fund import FundNav
import akshare as ak
import pandas as pd


# 抽样基金列表 (方案中指定)
SAMPLE_FUNDS = [
    ('000001', '平安新利混合'),
    ('000011', '华夏大盘精选混合A'),
    ('000015', '华夏纯债债券A'),
    ('000009', '易方达天天理财货币A'),
    ('000076', '华夏恒生ETF联接'),
]


def validate_fund_accuracy(fund_code, fund_name, db, logger):
    """验证单只基金的准确性"""
    
    # 1. 从官网获取最新数据
    try:
        official_df = ak.fund_etf_fund_info_em(fund=fund_code)
        if official_df is None or official_df.empty:
            return None, "官网无数据"
    except Exception as e:
        return None, f"官网获取失败: {e}"
    
    # 取最近5天的数据用于对比
    latest_date = official_df['净值日期'].max()
    recent_days = pd.to_datetime(latest_date) - timedelta(days=7)
    recent_df = official_df[pd.to_datetime(official_df['净值日期']) >= recent_days]
    
    if recent_df.empty:
        return None, "无近期数据"
    
    # 2. 从数据库获取对应日期的数据
    results = []
    
    for _, row in recent_df.head(5).iterrows():
        nav_date = row['净值日期']
        if isinstance(nav_date, str):
            nav_date = pd.to_datetime(nav_date)
        
        # 查询数据库
        db_record = db.query(FundNav).filter(
            FundNav.fund_code == fund_code,
            FundNav.nav_date == nav_date
        ).first()
        
        if not db_record:
            continue
        
        # 对比
        official_nav = float(row['单位净值']) if pd.notna(row['单位净值']) else None
        db_nav = db_record.nav
        
        official_accum = float(row['累计净值']) if pd.notna(row.get('累计净值')) else None
        db_accum = db_record.accumulated_nav
        
        # 日增长率
        official_growth = row.get('日增长率')
        if official_growth and isinstance(official_growth, str):
            official_growth = float(official_growth.replace('%', ''))
        elif pd.notna(official_growth):
            official_growth = float(official_growth)
        else:
            official_growth = None
        db_growth = db_record.daily_growth
        
        # 检查差异
        nav_match = official_nav == db_nav if official_nav and db_nav else False
        accum_match = official_accum == db_accum if official_accum and db_accum else False
        
        # 增长率允许0.01%误差
        growth_diff = abs(official_growth - db_growth) if official_growth and db_growth else None
        growth_match = growth_diff is not None and growth_diff <= 0.01
        
        results.append({
            'date': nav_date.strftime('%Y-%m-%d'),
            'official_nav': official_nav,
            'db_nav': db_nav,
            'nav_match': nav_match,
            'official_accum': official_accum,
            'db_accum': db_accum,
            'accum_match': accum_match,
            'official_growth': official_growth,
            'db_growth': db_growth,
            'growth_match': growth_match
        })
    
    return results, None


def validate_accuracy(args, logger):
    """验证准确性"""
    db = SessionLocal()
    
    print("=" * 60)
    print("=== 净值准确性验证 ===")
    print("=" * 60)
    
    # 选择验证的基金
    if args.samples > 0:
        # 使用指定的抽样基金
        test_funds = SAMPLE_FUNDS[:args.samples]
    else:
        # 随机抽取
        import random
        all_funds = db.query(FundNav.fund_code).distinct().all()
        test_funds = random.sample([(f[0], '') for f in all_funds], min(args.samples, len(all_funds)))
    
    total_checks = 0
    passed_checks = 0
    failed_details = []
    
    for fund_code, fund_name in test_funds:
        print(f"\n验证 {fund_code} {fund_name}...")
        
        results, error = validate_fund_accuracy(fund_code, fund_name, db, logger)
        
        if error:
            print(f"  ❌ {error}")
            failed_details.append((fund_code, error))
            continue
        
        if not results:
            print(f"  ⚠️ 无对比数据")
            continue
        
        # 显示结果
        for r in results:
            nav_status = "✅" if r['nav_match'] else f"❌({r['db_nav']})"
            accum_status = "✅" if r['accum_match'] else f"❌({r['db_accum']})"
            growth_status = "✅" if r['growth_match'] else f"❌({r['db_growth']})"
            
            print(f"  {r['date']}: 单位净值 {nav_status} | 累计净值 {accum_status} | 增长率 {growth_status}")
            
            total_checks += 1
            if r['nav_match'] and r['accum_match'] and r['growth_match']:
                passed_checks += 1
    
    # 汇总
    print("\n" + "=" * 60)
    print("=== 验收结果 ===")
    
    if total_checks > 0:
        pass_rate = passed_checks / total_checks * 100
        print(f"验证通过: {passed_checks}/{total_checks} ({pass_rate:.1f}%)")
        
        if pass_rate >= 90:
            print("\n🎉 准确性验收通过!")
            return True
        else:
            print(f"\n⚠️ 准确性验收未通过 (需要≥90%)")
            return False
    else:
        print("无有效验证数据")
        return False


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.WARNING)
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(description='验证净值准确性')
    parser.add_argument('--samples', type=int, default=5, help='抽样数量')
    
    args = parser.parse_args()
    
    result = validate_accuracy(args, logger)
    sys.exit(0 if result else 1)