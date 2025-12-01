from typing import Tuple, AsyncGenerator, cast
from loguru import logger
from sqlalchemy import Column, Unicode, Integer, String, UnicodeText, URL
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine
from app.models.base import Base
from app.config import get_database_url
from fastapi import Request

class Projects(Base):
    """
    项目表
    """
    __tablename__ = 'projects'
    project_id: Integer = Column('project_id', Integer, primary_key=True)
    project_name: Unicode = Column('project_name', Unicode(30), nullable=False)
    project_description: Unicode = Column('project_description', UnicodeText, nullable=False)
    project_cover: String = Column('project_cover', String(1024), nullable=False)


async def setup_database_connection(database_url: str | URL) -> Tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """
    创建数据库引擎和会话工厂
    FastAPI启动时在lifespan中调用
    """
    logger.info("创建数据库（异步）引擎中……")
    # engine = create_async_engine(get_database_url())
    engine = create_async_engine(url=database_url)
    logger.info("创建数据库（异步）引擎成功！")
    logger.info("创建数据库（异步）会话工厂中……")
    session_factory = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        class_=AsyncSession
    )
    logger.info("创建数据库（异步）会话工厂成功")
    return engine, session_factory

async def init_database_tables(engine: AsyncEngine) -> None:
    """
    初始化所有的表
    FastAPI启动时在lifespan中调用，应当在`setup_database_connection()`调用之后使用
    :param engine: 数据库引擎
    :return: None
    """
    async with engine.connect() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_database(engine: AsyncEngine) -> None:
    """
    关闭数据库引擎
    FastAPI关闭时在lifespan中调用
    :param engine:
    :return:
    """
    logger.info("数据库引擎关闭中……")
    await engine.dispose()
    logger.info("数据库引擎关闭成功！")

# database_url = get_database_url()
# engine = create_engine(database_url)
# async_engine = create_async_engine(database_url)

# Base.metadata.create_all(engine)

async def get_database(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    为每个请求任务提供数据库会话
    依赖于lifespan中初始化的session_factory
    :param request:
    :return:
    """
    session_factory = cast(
        async_sessionmaker[AsyncSession], request.state.session_factory
    )  # 显式告诉检查器`setup_database_connection`是`async_sessionmaker[AsyncSession]`
    async with session_factory() as session:
        yield session

