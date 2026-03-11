"""
基准指数数据采集脚本
使用 AkShare 获取沪深300、中证500、创业板指、上证指数、中证100的历史数据
"""
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 直接定义模型，避免导入 app 模块
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
import pandas as pd
import akshare as ak

# 创建基类
Base = declarative_base()


class BenchmarkNav(Base):
    """基准指数净值表"""
    __tablename__ = "benchmark_nav"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 指数代码 (如 000300, 399006)
    benchmark_code = Column(String(10), index=True, nullable=False, comment="指数代码")
    
    # 指数名称
    benchmark_name = Column(String(50), nullable=False, comment="指数名称")
    
    # 交易日期
    trade_date = Column(DateTime, nullable=False, comment="交易日期")
    
    # 收盘价
    close = Column(Float, nullable=False, comment="收盘价")
    
    # 涨跌幅 (%)
    pct_chg = Column(Float, nullable=True, comment="涨跌幅(%)")
    
    # 开盘价
    open = Column(Float, nullable=True, comment="开盘价")
    
    # 最高价
    high = Column(Float, nullable=True, comment="最高价")
    
    # 最低价
    low = Column(Float, nullable=True, comment="最低价")
    
    # 成交量
    volume = Column(Float, nullable=True, comment="成交量")
    
    # 成交额
    amount = Column(Float, nullable=True, comment="成交额")
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    def __repr__(self):
        return f"<BenchmarkNav {self.benchmark_code} - {self.trade_date}>"


# 数据库配置
DATABASE_URL = "sqlite:///./fund_system.db"

# 创建数据库引擎和会话
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建表（如果不存在）
Base.metadata.create_all(bind=engine)

# 基准指数配置 (akshare 需要带 sh/sz 前缀)
BENCHMARKS = {
    "sh000300": "沪深300",
    "sh000905": "中证500",
    "sz399006": "创业板指",
    "sh000001": "上证指数",
    "sz399300": "中证100"
}

# 存储时使用的纯数字代码
BENCHMARK_CODES = {
    "sh000300": "000300",
    "sh000905": "000905",
    "sz399006": "399006",
    "sh000001": "000001",
    "sz399300": "399300"
}


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BenchmarkCollector:
    """基准指数数据采集器"""
    
    def __init__(self, db):
        self.db = db
        self.request_delay = 0.5  # 请求间隔(秒)
    
    def collect_benchmark_nav(
        self, 
        benchmark_codes: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 365
    ) -> Dict[str, Any]:
        """
        采集基准指数数据
        
        Args:
            benchmark_codes: 指数代码列表，None 表示采集所有配置的指数
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            days: 默认采集天数
            
        Returns:
            dict: 采集结果统计
        """
        result = {
            "benchmarks_processed": 0,
            "total_records": 0,
            "failed": 0,
            "errors": []
        }
        
        # 确定要采集的指数
        if benchmark_codes is None:
            benchmark_codes = list(BENCHMARKS.keys())
        
        # 计算日期范围
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
        
        logger.info(f"开始采集基准指数数据: {start_date} - {end_date}")
        
        for code in benchmark_codes:
            try:
                name = BENCHMARKS.get(code, code)
                logger.info(f"采集 {code} ({name})...")
                
                records = self._collect_single_benchmark(code, name, start_date, end_date)
                result["total_records"] += records
                result["benchmarks_processed"] += 1
                
                logger.info(f"{code} ({name}) 采集完成: {records} 条记录")
                
                # 请求间隔，避免被封
                import time
                time.sleep(self.request_delay)
                
            except Exception as e:
                result["failed"] += 1
                result["errors"].append(f"{code}: {str(e)}")
                logger.error(f"采集 {code} 失败: {e}")
                continue
        
        self.db.commit()
        logger.info(f"基准指数数据采集完成: 处理 {result['benchmarks_processed']} 个指数，新增 {result['total_records']} 条记录")
        
        return result
    
    def _collect_single_benchmark(
        self, 
        code: str, 
        name: str, 
        start_date: str, 
        end_date: str
    ) -> int:
        """
        采集单个指数的历史数据
        
        Args:
            code: 指数代码
            name: 指数名称
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            int: 新增记录数
        """
        count = 0
        
        try:
            # 使用 akshare 获取指数数据
            df = ak.stock_zh_index_daily(symbol=code)
            
            if df is None or df.empty:
                logger.warning(f"未获取到 {code} 的数据")
                return 0
            
            # 筛选日期范围
            df['date'] = pd.to_datetime(df['date'])
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]
            
            if df.empty:
                logger.warning(f"{code} 在指定日期范围内无数据")
                return 0
            
            # 获取存储用的纯数字代码
            store_code = BENCHMARK_CODES.get(code, code)
            
            # 获取最新的记录数
            latest_count = self.db.query(BenchmarkNav).filter(
                BenchmarkNav.benchmark_code == store_code
            ).count()

            logger.info(f"{code} 当前已有 {latest_count} 条记录，将新增 {len(df)} 条")

            for _, row in df.iterrows():
                try:
                    trade_date = row['date']

                    # 检查是否已存在
                    existing = self.db.query(BenchmarkNav).filter(
                        BenchmarkNav.benchmark_code == store_code,
                        BenchmarkNav.trade_date == trade_date
                    ).first()

                    if existing:
                        continue
                    
                    # 获取涨跌幅
                    pct_chg = row.get('pct_chg') if 'pct_chg' in df.columns else None
                    if pd.notna(pct_chg):
                        pct_chg = float(pct_chg)
                    
                    # 获取收盘价
                    close = row.get('close')
                    
                    benchmark_nav = BenchmarkNav(
                        benchmark_code=store_code,  # 使用纯数字代码
                        benchmark_name=name,
                        trade_date=trade_date,
                        close=float(close) if pd.notna(close) else 0,
                        pct_chg=pct_chg,
                        open=float(row.get('open', 0)) if pd.notna(row.get('open')) else None,
                        high=float(row.get('high', 0)) if pd.notna(row.get('high')) else None,
                        low=float(row.get('low', 0)) if pd.notna(row.get('low')) else None,
                        volume=float(row.get('volume', 0)) if pd.notna(row.get('volume')) else None,
                        amount=float(row.get('amount', 0)) if pd.notna(row.get('amount')) else None
                    )
                    self.db.add(benchmark_nav)
                    count += 1
                    
                except Exception as e:
                    logger.warning(f"处理 {code} 记录失败: {e}")
                    continue
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"获取指数 {code} 数据失败: {e}")
            self.db.rollback()
        
        return count
    
    def update_latest(self) -> Dict[str, Any]:
        """
        增量更新最新数据
        
        Returns:
            dict: 更新结果统计
        """
        result = {
            "benchmarks_updated": 0,
            "new_records": 0,
            "errors": []
        }
        
        today = datetime.now().strftime("%Y%m%d")
        
        for code, name in BENCHMARKS.items():
            try:
                # 获取该指数的最新日期 - 使用纯数字代码
                store_code = BENCHMARK_CODES.get(code, code)
                latest = self.db.query(BenchmarkNav).filter(
                    BenchmarkNav.benchmark_code == store_code
                ).order_by(BenchmarkNav.trade_date.desc()).first()
                
                start_date = (latest.trade_date + timedelta(days=1)).strftime("%Y%m%d") if latest else (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
                end_date = today
                
                # 采集增量数据
                records = self._collect_single_benchmark(code, name, start_date, end_date)
                
                if records > 0:
                    result["benchmarks_updated"] += 1
                    result["new_records"] += records
                    logger.info(f"{code} 增量更新: {records} 条新记录")
                
            except Exception as e:
                result["errors"].append(f"{code}: {str(e)}")
                logger.error(f"更新 {code} 失败: {e}")
        
        self.db.commit()
        logger.info(f"增量更新完成: 更新 {result['benchmarks_updated']} 个指数，新增 {result['new_records']} 条记录")
        
        return result


def get_benchmark_codes() -> List[str]:
    """获取所有配置的基准指数代码"""
    return list(BENCHMARKS.keys())


def main():
    """主函数 - 用于命令行执行"""
    db = SessionLocal()
    
    try:
        collector = BenchmarkCollector(db)
        
        # 解析命令行参数
        import argparse
        parser = argparse.ArgumentParser(description="采集基准指数数据")
        parser.add_argument("--days", type=int, default=365, help="采集天数")
        parser.add_argument("--update", action="store_true", help="增量更新模式")
        parser.add_argument("--codes", nargs="+", help="指定指数代码")
        
        args = parser.parse_args()
        
        if args.update:
            # 增量更新
            logger.info("执行增量更新...")
            result = collector.update_latest()
        else:
            # 全量采集
            logger.info(f"执行全量采集，采集最近 {args.days} 天数据...")
            result = collector.collect_benchmark_nav(
                benchmark_codes=args.codes,
                days=args.days
            )
        
        logger.info(f"采集结果: {result}")
        return result
        
    except Exception as e:
        logger.error(f"采集失败: {e}")
        return {"error": str(e)}
    finally:
        db.close()


if __name__ == "__main__":
    main()