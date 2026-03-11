#!/usr/bin/env python3
"""
净值数据合理性验证脚本

验证内容:
- 净值范围检查 (单位净值 > 0)
- 日增长率检查 (-15% ~ +15%)
- 累计净值检查 (累计净值 ≥ 单位净值)
- 货币基金增长率检查
"""
import sys
import os
from datetime import datetime

# 添加项目路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
backend_path = os.path.join(project_root, 'backend')
sys.path.insert(0, backend_path)

# 切换到 backend 目录以确保 SQLite 路径正确
os.chdir(backend_path)

from app.core.database import SessionLocal
from app.models.fund import FundNav, Fund
from sqlalchemy import func, or_, text


def validate_reasonableness():
    """验证数据合理性"""
    db = SessionLocal()
    
    print("=" * 60)
    print("=== 净值合理性检查 ===")
    print("=" * 60)
    
    try:
        # 1. 异常净值检查 (单位净值 <= 0)
        print("\n[1] 检查异常净值 (单位净值 <= 0)...")
        invalid_nav = db.query(FundNav).filter(FundNav.nav <= 0).count()
        print(f"  异常净值记录: {invalid_nav} 条")
        
        # 2. 累计净值异常 (累计净值 < 单位净值)
        print("\n[2] 检查累计净值异常 (累计净值 < 单位净值)...")
        invalid_accum = db.query(FundNav).filter(
            FundNav.accumulated_nav.isnot(None),
            FundNav.accumulated_nav < FundNav.nav
        ).count()
        print(f"  异常记录: {invalid_accum} 条")
        
        # 3. 日增长率异常
        print("\n[3] 检查日增长率异常 (-15% ~ +15% 之外)...")
        extreme_growth = db.query(FundNav).filter(
            or_(
                FundNav.daily_growth < -15,
                FundNav.daily_growth > 15
            )
        ).count()
        print(f"  极端增长率记录: {extreme_growth} 条")
        
        # 显示一些异常记录
        if extreme_growth > 0 and extreme_growth <= 10:
            extreme_records = db.query(FundNav).filter(
                or_(
                    FundNav.daily_growth < -15,
                    FundNav.daily_growth > 15
                )
            ).limit(10).all()
            
            print("  异常记录示例:")
            for r in extreme_records:
                print(f"    {r.fund_code} {r.nav_date}: {r.daily_growth}%")
        
        # 4. 日期连续性检查
        print("\n[4] 检查数据缺失情况...")
        
        # SQLite不支持在聚合函数中使用MIN/MAX，需用子查询
        gap_stats = db.execute(text("""
            SELECT 
                CASE 
                    WHEN gap_days > 30 THEN '>30天'
                    WHEN gap_days > 14 THEN '15-30天'
                    WHEN gap_days > 7 THEN '8-14天'
                    ELSE '<=7天'
                END as gap_range,
                COUNT(*) as funds
            FROM (
                SELECT 
                    fund_code,
                    MAX(nav_date) - MIN(nav_date) as gap_days
                FROM fund_nav
                GROUP BY fund_code
                HAVING COUNT(*) > 1
            )
            GROUP BY gap_range
            ORDER BY 
                CASE gap_range
                    WHEN '<=7天' THEN 1
                    WHEN '8-14天' THEN 2
                    WHEN '15-30天' THEN 3
                    ELSE 4
                END
        """)).fetchall()
        
        print("  数据时间跨度分布:")
        for row in gap_stats:
            print(f"    {row[0]}: {row[1]} 只基金")
        
        # 5. 重复记录检查
        print("\n[5] 检查重复记录...")
        duplicates = db.execute(text("""
            SELECT fund_code, nav_date, COUNT(*) as cnt
            FROM fund_nav
            GROUP BY fund_code, DATE(nav_date)
            HAVING COUNT(*) > 1
        """)).fetchall()
        
        print(f"  有重复的日期数: {len(duplicates)}")
        
        if duplicates:
            print("  示例:")
            for d in duplicates[:5]:
                print(f"    {d[0]} {d[1]}: {d[2]}条重复")
        
        # 6. 字段缺失检查
        print("\n[6] 检查字段缺失...")
        missing_nav = db.query(FundNav).filter(FundNav.nav.is_(None)).count()
        print(f"  单位净值为空: {missing_nav} 条")
        
        # 汇总
        print("\n" + "=" * 60)
        print("=== 验收结果 ===")
        
        total_records = db.query(func.count()).select_from(FundNav).scalar()
        total_issues = invalid_nav + invalid_accum + extreme_growth + len(duplicates) + missing_nav
        issue_rate = total_issues / total_records * 100 if total_records > 0 else 0
        
        print(f"总记录数: {total_records:,}")
        print(f"总异常数: {total_issues}")
        print(f"异常率: {issue_rate:.3f}%")
        
        print(f"\n  异常净值: {invalid_nav} 条")
        print(f"  累计净值异常: {invalid_accum} 条")
        print(f"  极端增长率: {extreme_growth} 条")
        print(f"  重复记录: {len(duplicates)} 条")
        print(f"  字段缺失: {missing_nav} 条")
        
        # 验收标准: 异常率 < 0.1%
        if issue_rate < 0.1:
            print("\n🎉 合理性验收通过! (异常率 < 0.1%)")
            return True
        else:
            print(f"\n⚠️ 合理性验收未通过 (需要 < 0.1%)")
            return False
        
    except Exception as e:
        print(f"验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    result = validate_reasonableness()
    sys.exit(0 if result else 1)