"""基准对比功能单元测试"""
import pytest
import sys
import os
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.benchmark_service import AlphaBetaCalculator, BenchmarkService


class TestAlphaBetaCalculator:
    """Alpha/Beta 计算器测试"""
    
    def test_calculate_returns(self):
        """测试收益率计算"""
        prices = [100, 105, 102, 110, 108]
        returns = AlphaBetaCalculator.calculate_returns(prices)
        
        assert len(returns) == 4
        assert abs(returns[0] - 5.0) < 0.01  # (105-100)/100 * 100
        assert abs(returns[1] - (-2.857)) < 0.01  # (102-105)/105 * 100
        assert abs(returns[2] - 7.843) < 0.01  # (110-102)/102 * 100
        assert abs(returns[3] - (-1.818)) < 0.01  # (108-110)/110 * 100
    
    def test_calculate_alpha_beta_basic(self):
        """测试基本 Alpha/Beta 计算"""
        strategy_returns = [1.0, 2.0, 3.0, 4.0, 5.0]
        benchmark_returns = [0.5, 1.0, 1.5, 2.0, 2.5]
        
        result = AlphaBetaCalculator.calculate_alpha_beta(
            strategy_returns, benchmark_returns
        )
        
        assert result["beta"] > 0
        assert "alpha" in result
        assert "r_squared" in result
        assert "correlation" in result
    
    def test_calculate_alpha_beta_perfect_correlation(self):
        """测试完全相关的情况"""
        # 使用相同的数据确保完全相关
        strategy_returns = [1.0, 2.0, 3.0, 4.0, 5.0]
        benchmark_returns = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        result = AlphaBetaCalculator.calculate_alpha_beta(
            strategy_returns, benchmark_returns
        )
        
        # 完全正相关，相关系数应该接近1
        assert result["correlation"] == 1.0
        # R平方应该为1
        assert result["r_squared"] == 1.0
        # Beta应该为正且合理
        assert result["beta"] > 0
    
    def test_calculate_alpha_beta_negative_correlation(self):
        """测试负相关情况"""
        strategy_returns = [1.0, -1.0, 1.0, -1.0, 1.0]
        benchmark_returns = [1.0, 1.0, -1.0, -1.0, 1.0]
        
        result = AlphaBetaCalculator.calculate_alpha_beta(
            strategy_returns, benchmark_returns
        )
        
        # 相关系数应该接近0（不相关）或负相关
        assert result["correlation"] < 0.5
    
    def test_calculate_alpha_beta_insufficient_data(self):
        """测试数据不足的情况"""
        strategy_returns = [1.0]
        benchmark_returns = [0.5]
        
        result = AlphaBetaCalculator.calculate_alpha_beta(
            strategy_returns, benchmark_returns
        )
        
        assert result["alpha"] == 0.0
        assert result["beta"] == 1.0
    
    def test_calculate_information_ratio(self):
        """测试信息比率计算"""
        strategy_returns = [1.0, 2.0, 3.0, 4.0, 5.0]
        benchmark_returns = [0.5, 1.0, 1.5, 2.0, 2.5]
        
        result = AlphaBetaCalculator.calculate_information_ratio(
            strategy_returns, benchmark_returns
        )
        
        assert "information_ratio" in result
        assert "excess_return" in result
        assert "tracking_error" in result
    
    def test_calculate_information_ratio_zero_tracking_error(self):
        """测试跟踪误差为0的情况"""
        strategy_returns = [1.0, 2.0, 3.0]
        benchmark_returns = [1.0, 2.0, 3.0]
        
        result = AlphaBetaCalculator.calculate_information_ratio(
            strategy_returns, benchmark_returns
        )
        
        # 当跟踪误差为0时，信息比率应该为0（避免除以0）
        assert result["tracking_error"] == 0.0
    
    def test_calculate_full_analysis(self):
        """测试完整分析"""
        strategy_prices = [100, 105, 102, 110, 108, 115]
        benchmark_prices = [100, 102, 101, 104, 103, 107]
        
        result = AlphaBetaCalculator.calculate_full_analysis(
            strategy_prices, benchmark_prices
        )
        
        # 验证所有关键字段
        assert "alpha" in result
        assert "beta" in result
        assert "r_squared" in result
        assert "correlation" in result
        assert "information_ratio" in result
        assert "excess_return" in result
        assert "tracking_error" in result
        assert "data_points" in result
        assert result["data_points"] == 5  # 6个价格 = 5个收益率


class TestBenchmarkModel:
    """基准模型测试"""
    
    def test_default_benchmarks_count(self):
        """测试默认基准数量"""
        from app.models.benchmark import DEFAULT_BENCHMARKS
        
        # 验证没有重复代码
        codes = [b["code"] for b in DEFAULT_BENCHMARKS]
        assert len(codes) == len(set(codes)), "存在重复的基准代码"
        
        # 验证基准数量
        assert len(DEFAULT_BENCHMARKS) > 0


class TestCacheService:
    """缓存服务测试"""
    
    def test_cache_key_generation(self):
        """测试缓存键生成"""
        from app.services.cache_service import cache_key, CACHE_KEYS
        
        key = cache_key(CACHE_KEYS["fund_nav"], "000001", 30)
        assert key == "fund:nav:000001:30"
        
        key = cache_key(CACHE_KEYS["benchmark_nav"], "000300")
        assert key == "benchmark:nav:000300"
    
    def test_cache_key_prefixes(self):
        """测试缓存键前缀"""
        from app.services.cache_service import CACHE_KEYS
        
        assert CACHE_KEYS["fund_nav"] == "fund:nav"
        assert CACHE_KEYS["benchmark_nav"] == "benchmark:nav"
        assert CACHE_KEYS["benchmark_list"] == "benchmark:list"
        assert CACHE_KEYS["alpha_beta"] == "analysis:alpha_beta"


class TestCacheExpire:
    """缓存过期时间测试"""
    
    def test_cache_expire_values(self):
        """测试缓存过期时间配置"""
        from app.services.cache_service import CACHE_EXPIRE
        
        assert CACHE_EXPIRE["short"] == 300  # 5分钟
        assert CACHE_EXPIRE["medium"] == 1800  # 30分钟
        assert CACHE_EXPIRE["long"] == 3600  # 1小时
        assert CACHE_EXPIRE["very_long"] == 86400  # 24小时


class TestBenchmarkService:
    """基准服务测试"""
    
    def test_calculate_returns_edge_cases(self):
        """测试收益率计算的边界情况"""
        # 单个价格
        prices = [100]
        returns = AlphaBetaCalculator.calculate_returns(prices)
        assert returns == []
        
        # 两个价格
        prices = [100, 105]
        returns = AlphaBetaCalculator.calculate_returns(prices)
        assert len(returns) == 1
        
        # 空列表
        prices = []
        returns = AlphaBetaCalculator.calculate_returns(prices)
        assert returns == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])