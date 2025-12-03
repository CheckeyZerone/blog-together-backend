import sys
from functools import lru_cache
from typing import TypedDict, AsyncIterator, Any, AsyncGenerator, TextIO
from app.core.config import Settings
from fastapi.params import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
import app.database as db
from loguru import logger
import app.models as models
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import app.routers as routers
from contextlib import asynccontextmanager

from app.config import get_logger_config
from app.core.logger import setup_logger


class AppState(TypedDict):
    engine: AsyncEngine
    session_factory: AsyncSession

@lru_cache
async def get_settings() -> Settings:
    settings = Settings()
    return settings

@asynccontextmanager
async def lifespan(api: FastAPI) -> AsyncGenerator[dict[str, AsyncEngine | async_sessionmaker[AsyncSession]], None]:
    logger.info("程序启动中……")

    settings = await get_settings()

    # 配置日志库
    # logger.remove()
    # output_path, log_level = get_logger_config()
    output_path, log_level, log_rotation, log_retention = settings.logger_config
    # logger.add(output_path, level=log_level)
    # logger.info(f"已设置日志输出路径为{output_path}，输出等级为{log_level}")
    # if not isinstance(output_path, TextIO):
    #     logger.add(sys.stderr, level=log_level)
    setup_logger(output_path, log_level, log_rotation, log_retention)
    logger.info(f"已设置日志输出路径为{output_path}，输出等级为{log_level}")

    # 初始化数据库
    engine, session_factory = await db.setup_database_connection(settings.database_url)
    await db.init_database_tables(engine)
    # await db.create_db()
    logger.info("程序启动成功！")

    yield {"engine": engine, "session_factory": session_factory}

    # await db.async_engine.dispose()
    logger.info("程序关闭中……")
    await db.close_database(engine)
    logger.info("程序关闭成功！")


app = FastAPI(
    title="Blog Together Backend",
    lifespan=lifespan,
    version="0.0.3-Alpha"
)

# 白名单url
origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
)


# 文章查询的路由/article/*
app.include_router(routers.articles.router)


@app.get("/db-check")
async def db_check(database: AsyncSession = Depends(db.get_database)):
    """
    用于测试后端数据库是否连接异常
    """
    try:
        result = await database.execute(text("SELECT 1"))
        if result.scalar_one() == 1:
            return {"status": "success", "message": "数据库连接成功！"}
    except Exception as error:
        return {"status": "error", "message": f"数据库连接失败：{error}"}


"""
    blog-together-backend  Copyright (C) 2025  Checkey_01
    This program comes with ABSOLUTELY NO WARRANTY; for details type `show w'.
    This is free software, and you are welcome to redistribute it
    under certain conditions; type `show c' for details.
"""

if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True, log_config=None)

