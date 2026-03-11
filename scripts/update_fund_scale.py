#!/usr/bin/env python3
"""更新基金规模数据 - 逐步版本"""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:////home/ubuntu/.openclaw/workspace/fund-system/backend/fund_system.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)

from app.models.fund import Fund

import akshare as ak
import pandas as pd

# 强制刷新输出
import sys
sys.stdout.reconfigure(line_buffering=True)


def parse_scale(scale_str):
    if not scale_str or scale_str == '--' or pd.isna(scale_str):
        return 0.0
    scale_str = str(scale_str).strip()
    try:
        if '亿' in scale_str:
            return float(scale_str.replace('亿', ''))
        elif '万' in scale_str:
            return float(scale_str.replace('万', '')) / 10000
        elif '千万' in scale_str:
            return float(scale_str.replace('千万', '')) / 10
        else:
            return float(scale_str)
    except:
        return 0.0


def update_fund(fund_code):
    """更新单个基金"""
    session = Session()
    try:
        info_df = ak.fund_individual_basic_info_xq(symbol=fund_code)
        
        if info_df is not None and not info_df.empty:
            info_dict = {}
            for _, row in info_df.iterrows():
                item = row.get('item', '')
                value = row.get('value', '')
                if item:
                    info_dict[item] = value
            
            scale_str = info_dict.get('最新规模', '0')
            scale = parse_scale(scale_str)
            
            fund = session.query(Fund).filter(Fund.fund_code == fund_code).first()
            if fund:
                fund.scale = scale
                fund.updated_at = datetime.now()
                session.commit()
                return scale > 0
        return False
    except Exception as e:
        return False
    finally:
        session.close()


def main():
    session = Session()
    
    try:
        # 获取规模为0的基金
        funds = session.query(Fund).filter(Fund.scale == 0).all()
        total = len(funds)
        print(f"需要更新 {total} 只基金", flush=True)
        
        updated = 0
        zero = 0
        start = time.time()
        
        for i, fund in enumerate(funds):
            success = update_fund(fund.fund_code)
            
            if success:
                updated += 1
            else:
                zero += 1
            
            # 每100个打印进度
            if (i + 1) % 100 == 0:
                elapsed = time.time() - start
                rate = (i + 1) / elapsed
                remaining = (total - i - 1) / rate
                print(f"进度: {i+1}/{total} | 更新: {updated} | 为0: {zero} | 剩余: {remaining/60:.1f}分钟", flush=True)
            
            # 延迟
            time.sleep(0.2)
        
        elapsed = time.time() - start
        print(f"\n完成! 更新: {updated}, 为0: {zero}, 耗时: {elapsed/60:.1f}分钟", flush=True)
        
        # 验证结果
        total_with_scale = session.query(Fund).filter(Fund.scale > 0).count()
        ge_2 = session.query(Fund).filter(Fund.scale >= 2).count()
        print(f"总计规模>0: {total_with_scale}, 规模>=2亿: {ge_2}", flush=True)
        
    finally:
        session.close()


if __name__ == "__main__":
    main()