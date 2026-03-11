#!/usr/bin/env python3
"""
数据抽样核对脚本
从数据库随机抽取基金，与东方财富/新浪财经数据对比
"""

import sqlite3
import random
import os

DB_PATH = "/home/ubuntu/.openclaw/workspace/fund-system/backend/fund_system.db"

def get_sample_funds(n=5):
    """随机抽取N只基金"""
    if not os.path.exists(DB_PATH):
        print("数据库不存在")
        return []
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 随机抽取
    cursor.execute(f"SELECT fund_code, fund_name FROM funds ORDER BY RANDOM() LIMIT {n}")
    results = cursor.fetchall()
    conn.close()
    return results

def main():
    print("\n" + "="*60)
    print("📊 数据抽样核对 - 基金列表")
    print("="*60)
    print("\n请打开以下网址核对数据：")
    print("  东方财富: https://fund.eastmoney.com/data/fundranking.html")
    print("  新浪财经: https://finance.sina.com.cn/fund/")
    print("\n" + "="*60)
    
    funds = get_sample_funds(10)
    
    print(f"\n随机抽取 {len(funds)} 只基金进行核对：\n")
    print(f"{'基金代码':<12} {'基金名称':<30}")
    print("-" * 42)
    for code, name in funds:
        print(f"{code:<12} {name:<30}")
    
    print("\n" + "="*60)
    print("核对步骤：")
    print("1. 打开上述网址")
    print("2. 搜索以上基金代码")
    print("3. 对比基金名称、规模、净值等")
    print("4. 如有差异记录并反馈")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()