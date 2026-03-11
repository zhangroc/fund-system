#!/usr/bin/env python3
"""
净值数据清洗脚本

功能:
- 删除重复记录（保留最新一条）
- 修复累计净值异常（累计净值 < 单位净值）
"""
import sys
import os

# 添加项目路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
backend_path = os.path.join(project_root, 'backend')
sys.path.insert(0, backend_path)

# 切换到 backend 目录
os.chdir(backend_path)

from sqlalchemy import text
from app.core.database import SessionLocal
from app.models.fund import FundNav


def clean_duplicates(db):
    """删除重复记录，保留最新一条"""
    print("检查重复记录...")
    
    # 找出所有重复的 (fund_code, nav_date) 组合
    duplicates = db.execute(text("""
        SELECT fund_code, DATE(nav_date) as nav_date, COUNT(*) as cnt, MAX(id) as max_id
        FROM fund_nav
        GROUP BY fund_code, DATE(nav_date)
        HAVING COUNT(*) > 1
    """)).fetchall()
    
    if not duplicates:
        print("  无重复记录")
        return 0
    
    print(f"  发现 {len(duplicates)} 组重复记录")
    
    # 删除重复的，保留id最大的（即最新插入的）
    # 使用原生SQL避免text()包装问题
    import sqlite3
    conn = sqlite3.connect('fund_system.db')
    cur = conn.cursor()
    
    deleted = 0
    for fund_code, nav_date, cnt, max_id in duplicates:
        cur.execute("""
            DELETE FROM fund_nav 
            WHERE fund_code = ? 
            AND DATE(nav_date) = ?
            AND id != ?
        """, (fund_code, nav_date, max_id))
        deleted += cur.rowcount
    
    conn.commit()
    conn.close()
    
    print(f"  已删除 {deleted} 条重复记录")
    return deleted


def fix_accumulated_nav(db):
    """修复累计净值异常（累计净值 < 单位净值）"""
    print("\n检查累计净值异常...")
    
    # 找出累计净值 < 单位净值的记录
    invalid = db.query(FundNav).filter(
        FundNav.accumulated_nav.isnot(None),
        FundNav.accumulated_nav < FundNav.nav
    ).all()
    
    if not invalid:
        print("  无异常记录")
        return 0
    
    print(f"  发现 {len(invalid)} 条异常记录")
    
    # 修复：将累计净值设为单位净值
    for record in invalid:
        record.accumulated_nav = record.nav
    
    db.commit()
    print(f"  已修复 {len(invalid)} 条记录")
    return len(invalid)


def main():
    db = SessionLocal()
    
    print("=" * 60)
    print("=== 净值数据清洗 ===")
    print("=" * 60)
    
    try:
        deleted = clean_duplicates(db)
        fixed = fix_accumulated_nav(db)
        
        print("\n" + "=" * 60)
        print("清洗完成!")
        print(f"  删除重复: {deleted} 条")
        print(f"  修复异常: {fixed} 条")
        print("=" * 60)
        
    except Exception as e:
        print(f"清洗失败: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()


if __name__ == "__main__":
    main()