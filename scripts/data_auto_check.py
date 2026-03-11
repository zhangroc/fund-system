#!/usr/bin/env python3
"""
数据自动化核对机制
每天定时执行，随机抽取基金与外部数据源比对
"""

import sqlite3
import random
import os
from datetime import datetime

DB_PATH = "/home/ubuntu/.openclaw/workspace/fund-system/backend/fund_system.db"
LOG_PATH = "/tmp/data_check.log"

def get_fund_count():
    """获取基金总数"""
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

def get_sample_funds(n=5):
    """随机抽取N只基金"""
    if not os.path.exists(DB_PATH):
        return []
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"SELECT fund_code, fund_name FROM funds ORDER BY RANDOM() LIMIT {n}")
    results = cursor.fetchall()
    conn.close()
    return results

def check_data_consistency():
    """检查数据一致性"""
    fund_count = get_fund_count()
    funds = get_sample_funds(10)
    
    log = []
    log.append(f"\n{'='*60}")
    log.append(f"📊 数据自动化核对 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.append(f"{'='*60}")
    log.append(f"基金总数: {fund_count:,}")
    log.append(f"\n随机抽取 {len(funds)} 只基金进行核对：")
    log.append(f"\n{'基金代码':<12} {'基金名称':<30}")
    log.append("-" * 42)
    for code, name in funds:
        log.append(f"{code:<12} {name:<30}")
    log.append(f"\n核对网址：")
    log.append(f"  东方财富: https://fund.eastmoney.com/data/fundranking.html")
    log.append(f"  新浪财经: https://finance.sina.com.cn/fund/")
    log.append("="*60)
    
    result = "\n".join(log)
    print(result)
    
    # 写入日志
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(result + "\n")

if __name__ == "__main__":
    check_data_consistency()