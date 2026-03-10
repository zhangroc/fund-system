#!/usr/bin/env python3
"""
定时数据采集脚本

用法:
    python scheduled_collector.py [--mode {full|nav|details}]
    
模式:
    - full: 完整采集（基金列表 + 净值 + 详情）
    - nav: 仅增量更新净值
    - details: 仅更新基金详情

定时任务配置示例 (crontab):
    # 每天下午6点执行净值更新
    0 18 * * * cd /home/ubuntu/.openclaw/workspace/fund-system/backend && python3 ../scripts/scheduled_collector.py --mode nav
    
    # 每天凌晨2点执行完整采集
    0 2 * * * cd /home/ubuntu/.openclaw/workspace/fund-system/backend && python3 ../scripts/scheduled_collector.py --mode full
"""
import sys
import os
import argparse
import logging
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_collector(mode: str = "nav"):
    """运行采集器"""
    from app.core.database import SessionLocal
    from app.services.data_collector import DataCollector, ScheduledCollector
    
    db = SessionLocal()
    
    try:
        if mode == "full":
            logger.info("=" * 50)
            logger.info("开始执行完整数据采集")
            logger.info("=" * 50)
            
            collector = DataCollector(db)
            
            # 1. 采集基金列表
            logger.info("[1/3] 采集基金列表...")
            result1 = collector.collect_fund_list(min_scale=1.0)
            logger.info(f"基金列表采集结果: {result1}")
            
            # 2. 采集净值
            logger.info("[2/3] 采集净值数据...")
            result2 = collector.collect_fund_nav(days=30)
            logger.info(f"净值采集结果: {result2}")
            
            # 3. 更新基金详情
            logger.info("[3/3] 更新基金详情...")
            result3 = collector.update_fund_details()
            logger.info(f"基金详情更新结果: {result3}")
            
            logger.info("完整数据采集完成!")
            
        elif mode == "nav":
            logger.info("=" * 50)
            logger.info("开始增量更新净值")
            logger.info("=" * 50)
            
            collector = DataCollector(db)
            result = collector.update_latest_nav()
            logger.info(f"净值更新结果: {result}")
            
        elif mode == "details":
            logger.info("=" * 50)
            logger.info("开始更新基金详情")
            logger.info("=" * 50)
            
            collector = DataCollector(db)
            result = collector.update_fund_details()
            logger.info(f"基金详情更新结果: {result}")
            
        else:
            logger.error(f"未知模式: {mode}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"采集执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="定时数据采集脚本")
    parser.add_argument(
        "--mode", 
        choices=["full", "nav", "details"],
        default="nav",
        help="采集模式"
    )
    
    args = parser.parse_args()
    
    logger.info(f"定时采集任务开始 - 模式: {args.mode}")
    start_time = datetime.now()
    
    success = run_collector(args.mode)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    if success:
        logger.info(f"任务完成! 耗时: {duration:.2f}秒")
        sys.exit(0)
    else:
        logger.error(f"任务失败! 耗时: {duration:.2f}秒")
        sys.exit(1)


if __name__ == "__main__":
    main()