"""Redis 缓存服务"""
import json
import logging
from typing import Optional, Any
from datetime import timedelta

import redis
from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis 缓存工具类"""
    
    def __init__(self):
        self._client = None
    
    @property
    def client(self) -> Optional[redis.Redis]:
        """获取 Redis 客户端"""
        if self._client is None:
            try:
                self._client = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    decode_responses=True,
                    socket_connect_timeout=2
                )
                # 测试连接
                self._client.ping()
            except redis.ConnectionError:
                logger.warning(f"无法连接到 Redis ({settings.redis_host}:{settings.redis_port})")
                self._client = None
            except Exception as e:
                logger.warning(f"Redis 初始化失败: {e}")
                self._client = None
        return self._client
    
    def is_available(self) -> bool:
        """检查 Redis 是否可用"""
        return self.client is not None
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if not self.is_available():
            return None
        
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.warning(f"Redis get 失败: {e}")
        return None
    
    def set(self, key: str, value: Any, expire_seconds: int = 3600) -> bool:
        """设置缓存值"""
        if not self.is_available():
            return False
        
        try:
            serialized = json.dumps(value, default=str)
            return self.client.setex(key, expire_seconds, serialized)
        except Exception as e:
            logger.warning(f"Redis set 失败: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.is_available():
            return False
        
        try:
            return self.client.delete(key) > 0
        except Exception as e:
            logger.warning(f"Redis delete 失败: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self.is_available():
            return False
        
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            logger.warning(f"Redis exists 失败: {e}")
            return False
    
    def get_many(self, keys: list) -> dict:
        """批量获取缓存"""
        if not self.is_available():
            return {}
        
        result = {}
        try:
            values = self.client.mget(keys)
            for key, value in zip(keys, values):
                if value:
                    result[key] = json.loads(value)
        except Exception as e:
            logger.warning(f"Redis mget 失败: {e}")
        return result
    
    def set_many(self, data: dict, expire_seconds: int = 3600) -> bool:
        """批量设置缓存"""
        if not self.is_available():
            return False
        
        try:
            pipeline = self.client.pipeline()
            for key, value in data.items():
                serialized = json.dumps(value, default=str)
                pipeline.setex(key, expire_seconds, serialized)
            pipeline.execute()
            return True
        except Exception as e:
            logger.warning(f"Redis mset 失败: {e}")
            return False


# 全局缓存实例
cache = RedisCache()


# ============ 缓存键生成工具 ============

def cache_key(prefix: str, *args) -> str:
    """生成缓存键"""
    parts = [prefix] + [str(arg) for arg in args]
    return ":".join(parts)


# 缓存键前缀
CACHE_KEYS = {
    # 基金相关
    "fund_nav": "fund:nav",  # fund:nav:{fund_code}
    "fund_nav_batch": "fund:nav:batch",  # 批量净值
    "fund_list": "fund:list",
    "fund_detail": "fund:detail",  # fund:detail:{fund_code}
    
    # 基准相关
    "benchmark_nav": "benchmark:nav",  # benchmark:nav:{code}
    "benchmark_list": "benchmark:list",
    "benchmark_detail": "benchmark:detail",  # benchmark:detail:{code}
    
    # 分析相关
    "alpha_beta": "analysis:alpha_beta",  # analysis:alpha_beta:{fund_code}:{benchmark_code}
    
    # 回测相关
    "backtest_result": "backtest:result",
}


# ============ 缓存过期时间配置 ============

CACHE_EXPIRE = {
    "short": 300,      # 5分钟 - 频繁更新的数据
    "medium": 1800,    # 30分钟 - 一般数据
    "long": 3600,      # 1小时 - 稳定数据
    "very_long": 86400,  # 24小时 - 几乎不变的数据
}