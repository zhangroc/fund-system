"""基准指数服务 - 业务逻辑层"""
import logging
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import numpy as np
import pandas as pd

from app.models.benchmark import Benchmark, BenchmarkNav, DEFAULT_BENCHMARKS

logger = logging.getLogger(__name__)


class BenchmarkService:
    """基准指数服务类"""
    
    @staticmethod
    def get_all_benchmarks(db: Session) -> List[Benchmark]:
        """获取所有可用基准指数"""
        return db.query(Benchmark).order_by(Benchmark.name).all()
    
    @staticmethod
    def get_benchmark_by_code(db: Session, code: str) -> Optional[Benchmark]:
        """根据代码获取基准指数"""
        return db.query(Benchmark).filter(Benchmark.code == code).first()
    
    @staticmethod
    def create_benchmark(db: Session, code: str, name: str, 
                         index_type: str = None, base_point: float = 1000) -> Benchmark:
        """创建基准指数"""
        benchmark = Benchmark(
            code=code,
            name=name,
            index_type=index_type,
            base_point=base_point
        )
        db.add(benchmark)
        db.commit()
        db.refresh(benchmark)
        return benchmark
    
    @staticmethod
    def init_default_benchmarks(db: Session) -> int:
        """初始化默认基准指数"""
        count = 0
        for bm_data in DEFAULT_BENCHMARKS:
            try:
                existing = BenchmarkService.get_benchmark_by_code(db, bm_data["code"])
                if not existing:
                    benchmark = Benchmark(**bm_data)
                    db.add(benchmark)
                    count += 1
            except Exception as e:
                logger.warning(f"添加基准 {bm_data['code']} 失败: {e}")
                db.rollback()
                continue
        
        if count > 0:
            try:
                db.commit()
            except Exception as e:
                logger.warning(f"提交基准数据失败: {e}")
                db.rollback()
        
        logger.info(f"已初始化 {count} 个默认基准指数")
        return count
    
    @staticmethod
    def get_benchmark_nav_history(
        db: Session,
        code: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 365
    ) -> List[BenchmarkNav]:
        """获取基准指数历史数据"""
        query = db.query(BenchmarkNav).filter(BenchmarkNav.benchmark_code == code)
        
        if start_date:
            query = query.filter(BenchmarkNav.trade_date >= start_date)
        if end_date:
            query = query.filter(BenchmarkNav.trade_date <= end_date)
        
        return query.order_by(BenchmarkNav.trade_date.asc()).limit(limit).all()
    
    @staticmethod
    def add_benchmark_nav(db: Session, code: str, trade_date: datetime, 
                          close: float, pct_chg: float = None) -> BenchmarkNav:
        """添加基准指数净值"""
        nav_record = BenchmarkNav(
            benchmark_code=code,
            trade_date=trade_date,
            close=close,
            pct_chg=pct_chg
        )
        db.add(nav_record)
        db.commit()
        db.refresh(nav_record)
        return nav_record
    
    @staticmethod
    def get_latest_nav(db: Session, code: str) -> Optional[BenchmarkNav]:
        """获取最新净值"""
        return db.query(BenchmarkNav).filter(
            BenchmarkNav.benchmark_code == code
        ).order_by(BenchmarkNav.trade_date.desc()).first()


class AlphaBetaCalculator:
    """Alpha/Beta/信息比率计算器"""
    
    @staticmethod
    def calculate_returns(prices: List[float]) -> List[float]:
        """计算收益率序列"""
        if len(prices) < 2:
            return []
        returns = []
        for i in range(1, len(prices)):
            ret = (prices[i] - prices[i-1]) / prices[i-1]
            returns.append(ret * 100)  # 转换为百分比
        return returns
    
    @staticmethod
    def calculate_alpha_beta(
        strategy_returns: List[float], 
        benchmark_returns: List[float]
    ) -> dict:
        """
        计算 Alpha 和 Beta
        策略收益率 = α + β × 基准收益率 + ε
        
        使用最小二乘法 (OLS) 回归计算
        """
        # 确保数据长度一致
        min_len = min(len(strategy_returns), len(benchmark_returns))
        if min_len < 2:
            return {
                "alpha": 0.0,
                "beta": 1.0,
                "r_squared": 0.0,
                "correlation": 0.0
            }
        
        strategy_ret = np.array(strategy_returns[:min_len])
        benchmark_ret = np.array(benchmark_returns[:min_len])
        
        # 计算均值
        strategy_mean = np.mean(strategy_ret)
        benchmark_mean = np.mean(benchmark_ret)
        
        # 计算协方差和方差
        covariance = np.cov(strategy_ret, benchmark_ret)[0, 1]
        benchmark_variance = np.var(benchmark_ret)
        
        # 计算 Beta
        if benchmark_variance > 0:
            beta = covariance / benchmark_variance
        else:
            beta = 1.0
        
        # 计算 Alpha (年化)
        # Alpha = 策略年化收益 - Beta × 基准年化收益
        # 假设252个交易日
        strategy_annual = strategy_mean * 252
        benchmark_annual = benchmark_mean * 252
        alpha = strategy_annual - beta * benchmark_annual
        
        # 计算相关系数
        correlation = np.corrcoef(strategy_ret, benchmark_ret)[0, 1]
        
        # 计算 R² (决定系数)
        if correlation is not None and not np.isnan(correlation):
            r_squared = correlation ** 2
        else:
            r_squared = 0.0
        
        return {
            "alpha": round(float(alpha), 4),
            "beta": round(float(beta), 4),
            "r_squared": round(float(r_squared), 4),
            "correlation": round(float(correlation), 4) if not np.isnan(correlation) else 0.0,
            "strategy_annual_return": round(float(strategy_annual), 4),
            "benchmark_annual_return": round(float(benchmark_annual), 4)
        }
    
    @staticmethod
    def calculate_information_ratio(
        strategy_returns: List[float],
        benchmark_returns: List[float]
    ) -> dict:
        """
        计算信息比率
        信息比率 = 超额收益 / 跟踪误差
        """
        min_len = min(len(strategy_returns), len(benchmark_returns))
        if min_len < 2:
            return {
                "information_ratio": 0.0,
                "excess_return": 0.0,
                "tracking_error": 0.0
            }
        
        strategy_ret = np.array(strategy_returns[:min_len])
        benchmark_ret = np.array(benchmark_returns[:min_len])
        
        # 超额收益 = 策略收益 - 基准收益
        excess_returns = strategy_ret - benchmark_ret
        
        # 平均超额收益 (年化)
        mean_excess = np.mean(excess_returns) * 252
        
        # 跟踪误差 (超额收益的标准差, 年化)
        tracking_error = np.std(excess_returns) * np.sqrt(252)
        
        # 信息比率
        if tracking_error > 0:
            information_ratio = mean_excess / tracking_error
        else:
            information_ratio = 0.0
        
        return {
            "information_ratio": round(float(information_ratio), 4),
            "excess_return": round(float(mean_excess), 4),
            "tracking_error": round(float(tracking_error), 4),
            "excess_returns_std": round(float(np.std(excess_returns)), 4)
        }
    
    @staticmethod
    def calculate_full_analysis(
        strategy_prices: List[float],
        benchmark_prices: List[float]
    ) -> dict:
        """完整分析：计算所有指标"""
        strategy_returns = AlphaBetaCalculator.calculate_returns(strategy_prices)
        benchmark_returns = AlphaBetaCalculator.calculate_returns(benchmark_prices)
        
        # Alpha/Beta
        alpha_beta = AlphaBetaCalculator.calculate_alpha_beta(
            strategy_returns, benchmark_returns
        )
        
        # 信息比率
        info_ratio = AlphaBetaCalculator.calculate_information_ratio(
            strategy_returns, benchmark_returns
        )
        
        # 合并结果
        return {
            **alpha_beta,
            **info_ratio,
            "data_points": len(strategy_returns)
        }


class BenchmarkSync:
    """基准指数数据同步类"""
    
    @staticmethod
    def sync_benchmark_nav(db: Session, code: str, days: int = 30) -> int:
        """从 AkShare 同步基准指数数据"""
        try:
            import akshare as ak
            
            # 获取指数数据
            if code == "000300":
                index_df = ak.stock_zh_index_daily(symbol="sh000300")
            elif code == "000001":
                index_df = ak.stock_zh_index_daily(symbol="sh000001")
            elif code == "399001":
                index_df = ak.stock_zh_index_daily(symbol="sz399001")
            elif code == "000905":
                index_df = ak.stock_zh_index_daily(symbol="sh000905")
            elif code == "000016":
                index_df = ak.stock_zh_index_daily(symbol="sh000016")
            elif code == "399006":
                index_df = ak.stock_zh_index_daily(symbol="sz399006")
            else:
                logger.warning(f"不支持的指数代码: {code}")
                return 0
            
            if index_df is None or index_df.empty:
                return 0
            
            synced_count = 0
            for _, row in index_df.tail(days).iterrows():
                try:
                    date = row.get('date')
                    if isinstance(date, str):
                        date = pd.to_datetime(date)
                    
                    close = row.get('close')
                    if close:
                        # 计算日收益率
                        existing = db.query(BenchmarkNav).filter(
                            BenchmarkNav.benchmark_code == code,
                            BenchmarkNav.trade_date == date
                        ).first()
                        
                        if not existing:
                            # 获取前一天的收盘价来计算日收益率
                            prev_nav = BenchmarkService.get_latest_nav(db, code)
                            daily_return = None
                            if prev_nav:
                                daily_return = ((close - prev_nav.close) / prev_nav.close) * 100
                            
                            nav_record = BenchmarkNav(
                                benchmark_code=code,
                                trade_date=date,
                                close=float(close),
                                pct_chg=daily_return
                            )
                            db.add(nav_record)
                            synced_count += 1
                            
                except Exception as e:
                    logger.warning(f"同步指数数据失败: {e}")
                    continue
            
            db.commit()
            return synced_count
            
        except ImportError:
            logger.error("请安装 akshare: pip install akshare")
            return 0
        except Exception as e:
            logger.error(f"同步基准指数数据失败: {e}")
            db.rollback()
            return 0

