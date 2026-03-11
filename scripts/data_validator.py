#!/usr/bin/env python3
"""
数据同步验证脚本
每30分钟执行一次，检查数据是否达到PRD指标
"""

import sqlite3
import os
from datetime import datetime

# PRD指标
TARGET_FUND_COUNT = 5000
TARGET_NAV_COUNT = 5000000

# 数据库路径
DB_PATH = "/home/ubuntu/.openclaw/workspace/fund-system/backend/fund_system.db"

def get_fund_count():
    """获取基金数量"""
    if not os.path.exists(DB_PATH):
        return 0
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM funds")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def get_nav_count():
    """获取净值数据条数"""
    if not os.path.exists(DB_PATH):
        return 0
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM fund_nav")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def check_data_sync():
    """检查数据同步状态"""
    fund_count = get_fund_count()
    nav_count = get_nav_count()
    
    fund_status = "✅" if fund_count >= TARGET_FUND_COUNT else "❌"
    nav_status = "✅" if nav_count >= TARGET_NAV_COUNT else "❌"
    
    print(f"\n{'='*50}")
    print(f"📊 数据同步验证报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")
    print(f"基金数量: {fund_count:,} / {TARGET_FUND_COUNT:,} {fund_status}")
    print(f"净值数据: {nav_count:,} / {TARGET_NAV_COUNT:,} {nav_status}")
    
    if fund_count >= TARGET_FUND_COUNT and nav_count >= TARGET_NAV_COUNT:
        print(f"\n🎉 数据同步已达标！")
        return True
    else:
        print(f"\n⚠️ 数据同步未达标，需要继续同步")
        return False

if __name__ == "__main__":
    check_data_sync()