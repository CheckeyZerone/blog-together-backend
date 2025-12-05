import datetime
import math
from typing import Optional, Sequence

import pytz
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, RowMapping, delete, and_, update
from sqlalchemy.sql.elements import ColumnElement
from app.models.article import Articles, ArticleSeries, ArticleCategories
from app.tools import get_now_datetime_async

async def get_article_info_condition(
        category: str,
        is_recycled: bool,
        session: AsyncSession,
) -> ColumnElement[bool]:
    """
    返回文章查询条件
    :param category: 类别
    :param is_recycled: 查询内容是否为回收站内容
    :param session: 会话工厂
    :return: 一个查询条件，该条件为.where()方法的参数
    """
    if is_recycled:
        recycled_filter: ColumnElement[bool] = or_(Articles.article_delete_time != None)
    else:
        recycled_filter: ColumnElement[bool] = or_(Articles.article_delete_time == None)

    category_filter: Optional[ColumnElement[bool] | bool] = None
    if category != "all":
        article_category_id = await get_category_id(category_name=category, session=session)
        category_filter = ArticleCategories.article_category_id == article_category_id

    ret = recycled_filter
    if category_filter is not None:
        ret = and_(ret, category_filter)

    return ret


async def get_article_info(
        category: str,
        skip: int,
        limit: int,
        is_recycled: bool,
        session: AsyncSession
) -> Sequence[RowMapping]:
    """
    根据类别返回查询列表
    :param category: 类别
    :param skip: 查询页数
    :param limit: 每页最大查询数
    :param is_recycled: bool 查询内容是否为回收站内容，为True时查询回收站内的文章
    :param session: 会话工厂
    :return: 一个包含文章信息的列表，列表的每个元素是一个如下的JSON:
            {
                "info": {
                    "page": 当前页数,
                    "total_page": 总页数
                }
                "article_list": 文章列表
            }
            其中，"article_list"是一个文章列表，其每个元素为如下JSON:
            {
                article_id: 文章id,
                article_title: 文章标题,
                article_series: 文章所属系列的id，可能为空,
                update_time: 文章更新日期,
                article_cover: 文章封面的URL,
                article_category_id: 文章所属category的id,
            }
    """
    condition: ColumnElement[bool] = await get_article_info_condition(category=category,
                                                                      is_recycled=is_recycled,
                                                                      session=session)
    select_columns: list = [
        Articles.article_id,
        Articles.article_title,
        Articles.series_id,
        Articles.update_time,
        Articles.article_cover,
        Articles.article_category_id
    ]
    if is_recycled:
        select_columns.append(Articles.article_delete_time)
    stmt = (
        select(
            *select_columns
        )
        .where(condition)
        .order_by(Articles.update_time)
        .limit(limit)
        .offset((skip - 1) * limit)
    )
    result = await session.execute(stmt)
    content = result.mappings().fetchall()
    return content

async def get_article_info_page_count(
        article_category_name: str,
        limit: int,
        session: AsyncSession
) -> int:
    if article_category_name == "all":
        stmt = (
            select(func.count(Articles.article_id))
            .where(and_(Articles.article_delete_time == None))
        )
    else:
        article_category_id = await get_category_id(article_category_name, session)
        stmt = (
            select(func.count(Articles.article_id).label("articles_count"))
            .where(and_(Articles.article_category_id == article_category_id, Articles.article_delete_time == None))
        )
    result = await session.scalars(stmt)
    total_page = math.ceil(result.first() / limit)
    total_page = max(1, total_page)
    logger.debug(f"article_category_name={article_category_name}, SQL: {stmt}, 总页数{total_page}")
    return total_page

async def get_article(
        article_id: int,
        session: AsyncSession
):
    stmt = (
        select(
            Articles.article_id,
            Articles.article_title,
            Articles.series_id,
            Articles.update_time,
            Articles.article_cover,
            Articles.article_abstract,
            Articles.article_content,
            Articles.article_category_id
        )
        .where(and_(Articles.article_id == article_id, Articles.article_delete_time == None))
    )
    result = await session.execute(stmt)
    content = result.mappings().fetchone()
    logger.debug(f"content={content}")
    return content

async def create_article(
        article_title: str,
        article_cover: str,
        article_abstract: str,
        article_content: str,
        article_category_id: Optional[int],
        series_id: int,
        session: AsyncSession,
) -> bool:
    """
    创建一个文章，如果创建失败会抛出异常并终止，该异常的抛出依赖于AsyncSession.add()方法，注意，文章的更新时间使用的是东八区时间
    :param article_title: 文章标题
    :param article_cover: 封面URL
    :param article_abstract: 文章摘要
    :param article_content: 文章内容
    :param article_category_id: 文章所属类别id
    :param series_id: 文章所属系列id
    :param session: 会话工厂
    :return: 如果创建成功，返回True
    """
    update_time = await get_now_datetime_async()
    if series_id is None:
        article = Articles(
            article_title=article_title,
            article_cover=article_cover,
            article_abstract=article_abstract,
            article_content=article_content,
            update_time=update_time,
            article_category_id=article_category_id,
        )
    else:
        article = Articles(
            article_title=article_title,
            article_cover=article_cover,
            article_abstract=article_abstract,
            article_content=article_content,
            update_time=update_time,
            article_category_id=article_category_id,
            series_id=series_id
        )
    session.add(article)
    await session.commit()
    return True

async def get_series_id(
        series_name: str,
        session: AsyncSession
) -> Optional[int]:
    """
    根据系列名查询系列id
    :param series_name: 系列名
    :param session: 会话工厂
    :return: 如果系列存在返回系列id，如果系列不存在或series_name为None返回None
    """
    if series_name is not None:
        stmt = (
            select(ArticleSeries.series_id)
            .where(or_(ArticleSeries.series_name == series_name))
        )
        result = await session.scalars(stmt)
        try:
            series_id = result.first()
        except TypeError as e:
            raise Exception(f"series_name={series_name}，该series_name可能并不存在，因而触发异常{e}")
    else:
        series_id = None
    return series_id

async def get_category_id(
        category_name: str,
        session: AsyncSession
) -> Optional[int]:
    if category_name is not None:
        stmt = (select(ArticleCategories.article_category_id)
                .where(or_(ArticleCategories.article_category_name == category_name)))
        result = await session.scalars(stmt)
        try:
            article_category_id = result.first()
            if article_category_id is None and category_name != "all":
                raise ValueError(f"{category_name}不存在！")
        except ValueError as e:
            raise ValueError(f"category_name={category_name}，该category_name可能并不存在，因而触发异常{e}")
        except Exception as e:
            raise e
        return article_category_id
    else:
        raise Exception("category_name不能为空")

async def create_category(
        article_category_name: str,
        session: AsyncSession
) -> bool:
    """
    创建一个类别，如果创建失败会抛出异常并终止，该异常的抛出依赖于AsyncSession方法
    :param article_category_name: 文章类别名
    :param session: 会话工厂
    :return: 如果创建成功，返回True
    """
    category = ArticleCategories(
        article_category_name=article_category_name
    )
    session.add(category)
    await session.commit()
    return True

async def get_all_categories(
        session: AsyncSession,
):
    stmt = (
        select(ArticleCategories.article_category_id,
               ArticleCategories.article_category_name)
    )
    result = await session.execute(stmt)
    content = result.mappings().fetchall()
    logger.debug(f"content={content}")
    return content

async def delete_article_by_id(
        article_id: int,
        is_force: bool,
        session: AsyncSession,
):
    if is_force:
        stmt = (
            select(Articles.article_id)
            .where(or_(Articles.article_id == article_id))
        )
        result = await session.scalars(stmt)
        if result.first() is None:
            raise ValueError(f"article_id={article_id}不存在！")
        stmt = (delete(Articles)
                .where(or_(Articles.article_id == article_id)))
    else:
        stmt = (
            update(Articles)
            .where(and_(Articles.article_id == article_id, Articles.article_delete_time is None))
            .values(article_delete_time=await get_now_datetime_async())
        )
    await session.execute(stmt)
    await session.commit()
    return True


