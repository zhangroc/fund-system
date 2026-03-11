#!/usr/bin/env python3
"""
净值数据覆盖率验证脚本

验证内容:
- 有数据基金比例 (目标≥80%)
- 有≥1年数据基金比例 (目标≥50%)
- 有完整历史(≥2年)比例 (目标≥30%)
- 总记录数和平均记录数
"""
import sys
import os
from datetime import datetime, timedelta

# 添加项目路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
backend_path = os.path.join(project_root, 'backend')
sys.path.insert(0, backend_path)

# 切换到 backend 目录以确保 SQLite 路径正确
os.chdir(backend_path)

from app.core.database import SessionLocal
from app.models.fund import Fund, FundNav
from sqlalchemy import func, text


def validate_coverage():
    """验证数据覆盖率"""
    db = SessionLocal()
    
    print("=" * 60)
    print("=== 净值数据覆盖率报告 ===")
    print("=" * 60)
    
    try:
        # 规模≥2亿基金总数
        total_2y = db.query(func.count()).select_from(Fund).filter(Fund.scale >= 2).scalar()
        print(f"\n规模≥2亿基金总数: {total_2y}")
        
        if total_2y == 0:
            print("警告: 没有规模≥2亿的基金数据")
            return
        
        # 有净值数据的基金
        funds_with_nav = db.query(FundNav.fund_code).distinct().count()
        print(f"已有净值数据: {funds_with_nav} ({100*funds_with_nav/total_2y:.1f}%)")
        
        # 计算日期分布
        one_year_ago = datetime.now() - timedelta(days=365)
        two_years_ago = datetime.now() - timedelta(days=730)
        
        # 有≥1年数据的基金
        funds_1y = db.query(FundNav.fund_code).filter(
            FundNav.nav_date >= one_year_ago
        ).distinct().count()
        
        # 有≥2年数据的基金
        funds_2y = db.query(FundNav.fund_code).filter(
            FundNav.nav_date >= two_years_ago
        ).distinct().count()
        
        print(f"有≥1年数据: {funds_1y} ({100*funds_1y/total_2y:.1f}%)")
        print(f"有≥2年数据: {funds_2y} ({100*funds_2y/total_2y:.1f}%)")
        
        # 总记录数
        total_nav = db.query(func.count()).select_from(FundNav).scalar()
        print(f"\n净值记录总数: {total_nav:,}")
        
        # 平均记录数
        avg_records = total_nav / funds_with_nav if funds_with_nav > 0 else 0
        print(f"平均记录数/基金: {avg_records:.0f}条")
        
        # 按记录数分布
        print("\n--- 记录数分布 ---")
        
        # 获取每只基金的记录数
        stats = db.execute(text("""
            SELECT 
                CASE 
                    WHEN cnt >= 1000 THEN '≥1000'
                    WHEN cnt >= 500 THEN '500-999'
                    WHEN cnt >= 365 THEN '365-499'
                    WHEN cnt >= 180 THEN '180-364'
                    WHEN cnt >= 90 THEN '90-179'
                    ELSE '<90'
                END as range,
                COUNT(*) as funds
            FROM (
                SELECT fund_code, COUNT(*) as cnt
                FROM fund_nav
                GROUP BY fund_code
            )
            GROUP BY range
            ORDER BY 
                CASE range
                    WHEN '≥1000' THEN 1
                    WHEN '500-999' THEN 2
                    WHEN '365-499' THEN 3
                    WHEN '180-364' THEN 4
                    WHEN '90-179' THEN 5
                    ELSE 6
                END
        """)).fetchall()
        
        for row in stats:
            print(f"  {row[0]:>10}条: {row[1]:>5} 只基金")
        
        # 验收结果
        print("\n" + "=" * 60)
        print("=== 验收结果 ===")
        
        pass_coverage = funds_with_nav / total_2y >= 0.80
        pass_1y = funds_1y / total_2y >= 0.50
        pass_2y = funds_2y / total_2y >= 0.30
        
        print(f"覆盖率 (≥80%): {'✅ 通过' if pass_coverage else '❌ 未通过'} ({100*funds_with_nav/total_2y:.1f}%)")
        print(f"1年数据 (≥50%): {'✅ 通过' if pass_1y else '❌ 未通过'} ({100*funds_1y/total_2y:.1f}%)")
        print(f"2年数据 (≥30%): {'✅ 通过' if pass_2y else '❌ 未通过'} ({100*funds_2y/total_2y:.1f}%)")
        
        if pass_coverage and pass_1y and pass_2y:
            print("\n🎉 所有覆盖率验收标准通过!")
            return True
        else:
            print("\n⚠️ 部分验收标准未通过，需要继续采集")
            return False
        
    except Exception as e:
        print(f"验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    result = validate_coverage()
    sys.exit(0 if result else 1)