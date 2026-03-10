"""公募基金筛选与策略回测系统 - 主入口"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.api.funds import router as funds_router
from app.api.strategies import router as strategies_router
from app.api.backtests import router as backtests_router
from app.api.portfolios import router as portfolios_router
from app.api.data_collection import router as data_collection_router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("正在初始化数据库...")
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, init_db)  # 在线程池中执行同步数据库操作
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
    
    yield
    
    # 关闭时
    logger.info("应用关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(funds_router)
app.include_router(strategies_router)
app.include_router(backtests_router)
app.include_router(portfolios_router)
app.include_router(data_collection_router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用公募基金筛选与策略回测系统",
        "version": settings.api_version,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)