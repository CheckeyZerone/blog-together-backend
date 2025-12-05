from fastapi import APIRouter, Query, Path, HTTPException
from fastapi.params import Depends
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.article import (get_article_info,
                              get_article_info_page_count,
                              get_article,
                              get_series_id,
                              create_article, get_category_id, create_category, get_all_categories,
                              delete_article_by_id)
from app.database import get_database
from typing import Annotated
from app.api_responser import TodoResponse, OKResponse, ErrorResponse
from app.schemas.article import ArticleAndSeriesFilterParams, ArticleCreatorParams, ArticleCategoryCreatorParams, \
    ArticleDeleteParams

router = APIRouter(
    prefix="/articles",
    tags=["文章与系列查询"],
    responses={404: {"description": "Not found"}}
)

@router.get("",summary="分页查询文章/系列信息")
async def get_articles_by_category(
        filter_params: Annotated[ArticleAndSeriesFilterParams, Query()],
        # category: Annotated[str, Query(max_length=30)] = "all",
        # is_series: bool = False,
        # skip: Annotated[int, Path(title="skip", ge=1)] = 1,
        # limit: Annotated[int, Path(title="limit", ge=1)] = 9,
        session: AsyncSession = Depends(get_database)
) -> JSONResponse:
    """
    获取全部文章
    :param filter_params:
        category_name: 文章category，可选，默认"all"，表示查询所有文章
        is_series: 系列文章过滤器，True表示只返回系列文章的入口信息，False表示返回单个文章和系列文章的信息，默认False
         skip: 文章分页时的第几页，默认1
        limit: 每页的返回文章信息数量，默认9
    :param session:
    :return: 一个包含文章信息的列表，列表的每个元素是一个如下的JSON:
            ```
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
            ```
    """
    # logger.debug(items.limit)
    logger.info(f"查询：{filter_params}")
    if filter_params.is_series:
        return TodoResponse()
    else:
        try:
            total_page = await get_article_info_page_count(filter_params.category_name, filter_params.limit, session)
            if filter_params.skip > total_page:
                raise ValueError(f"最大页数为{total_page}，但是获取到的页数skip={filter_params.skip}")
            article_list = await get_article_info(category=filter_params.category_name,
                                                  skip=filter_params.skip,
                                                  limit=filter_params.limit,
                                                  is_recycled=False,
                                                  session=session)
            content = {
                "info": {
                    "page": filter_params.skip,
                    "total_page": total_page
                },
                "article_list": article_list
            }
            logger.info(
                f"查询到page={content['info']['page']}, "
                f"total_page={content['info']['total_page']}, "
                f"len={len(content['article_list'])}"
            )
            return OKResponse(content=content)
        except ValueError as e:
            logger.error(e)
            return ErrorResponse(e)
        except TypeError as e:
            logger.error(e)
            return ErrorResponse(e)
        except Exception as e:
            logger.exception(e)
            return ErrorResponse(e)


@router.get("/article", summary="查询文章信息")
async def get_article_by_id(
        article_id: Annotated[int, Query()],
        session: AsyncSession = Depends(get_database)
) -> JSONResponse:
    """
    根据id获取某一文章的全部信息
    :param article_id: 文章的id
    :param session: 会话工厂
    :return: 文章的完整信息Json，文章不存在或查询失败会返回404错误码和错误信息
            ```
            {
                "article_id": 文章id,
                "article_title": 文章标题,
                "article_series": 文章所属系列的id，可能为空,
                "update_time": 文章更新日期,
                "article_cover": 文章封面的URL,
                "article_abstract": 文章摘要（Markdown）,
                "article_content": 文章正文（Markdown）,
                "article_category": 文章所属category的id
            }
            ```
    """
    logger.info(f"查询article_id={article_id}")
    try:
        content = await get_article(article_id=article_id, session=session)
        if not content:
            raise HTTPException(status_code=404, detail=f"数据库中没有article_id = {article_id}的文章/系列")
        logger.info(f"查询到article_id={article_id}, article_title={content['article_title']}")
        return OKResponse(content=content)
    except Exception as e:
        logger.error(e)
        return ErrorResponse(e)

@router.get("/categories", summary="查询文章的所有的类别")
async def article_categories(
        session: AsyncSession = Depends(get_database)
) -> JSONResponse:
    """
    获取所有category的列表
    :return: 一个列表，其每个元素的值为如下
            ```
            {
                "article_category_id": 文章category的id
                "article_category_name": 文章category的名称
            }
            ```
    """
    logger.info(f"查询文章类别")
    try:
        content = await get_all_categories(session=session)
        logger.info(f"全部文章类别：{content}")
        return OKResponse(content=content)
    except Exception as e:
        logger.exception(e)
        return ErrorResponse(e)

@router.get("/series/{series_id}", summary="待实现")
async def series_by_id(series_id: int):
    """
    TODO: 未来实现，通过series_id查询系列
    :param series_id:
    :return: TODO: 未来实现，文章系列的信息
    """
    pass

@router.post("/post/article", summary="上传文章")
async def post_article(
        creator_params: Annotated[ArticleCreatorParams, Query()],
        session: AsyncSession = Depends(get_database)
) -> JSONResponse:
    """
    上传文章
    :param creator_params:
        article_title: 文章标题
        series_name: 文章所属系列名
        article_cover: 封面URL
        article_abstract: 文章摘要
        article_content: 文章内容
        category_name: 文章所属类别名
    :param session: 会话工厂
    :return: 如果正常上传返回包含True的一个JSONResponse，否则抛出异常并返回包含错误信息的JSONResponse
    """
    logger.info(f"正在创建文章 {creator_params.article_title}")
    try:
        content = await create_article(
            article_title=creator_params.article_title,
            article_cover=creator_params.article_cover,
            article_abstract=creator_params.article_abstract,
            article_content=creator_params.article_content,
            article_category_id=await get_category_id(creator_params.category_name, session=session),
            series_id=await get_series_id(creator_params.series_name, session=session),
            session=session
        )
        if content:
            logger.info(f"已创建文章 {creator_params.article_title}")
        return OKResponse(content=content)
    except Exception as e:
        logger.error(e)
        return ErrorResponse(e)

@router.post("/post/category", summary="上传文章类别")
async def post_categories(
        creator_params: Annotated[ArticleCategoryCreatorParams, Query()],
        session: AsyncSession = Depends(get_database)
) -> JSONResponse:
    """
    上传文章类别
    :param creator_params:
        - article_category_name: 文章类别名
    :param session: 会话工厂
    :return: 如果正常上传返回包含True的一个JSONResponse，否则抛出异常并返回包含错误信息的JSONResponse
    """
    try:
        content = await create_category(
            article_category_name=creator_params.article_category_name,
            session=session
        )
    except Exception as e:
        logger.error(e)
        return ErrorResponse(e)
    return OKResponse(content=content)

@router.delete("/delete/article", summary="根据article_id删除文章")
async def delete_article(
        article_delete_params: Annotated[ArticleDeleteParams, Query()],
        # article_id: Annotated[int, Query()],
        session: AsyncSession = Depends(get_database)
):
    # TODO: 之后改为逻辑删除
    logger.info(f"尝试删除article_id={article_delete_params.article_id}")
    try:
        content = await delete_article_by_id(
            article_id=article_delete_params.article_id,
            is_force=article_delete_params.is_force,
            session=session
        )
        if content:
            logger.info(f"已删除article_id={article_delete_params.article_id}")
        return OKResponse(content=content)
    except ValueError as e:
        logger.warning(e)
        return ErrorResponse(e)
    except Exception as e:
        logger.exception(e)
        return ErrorResponse(e)

@router.get("/recycle/articles", summary="待实现")
async def get_recycle_articles(
        filter_params: Annotated[ArticleAndSeriesFilterParams, Query()],
        session: AsyncSession = Depends(get_database)
):
    """
    查询被逻辑删除的文章
    :param filter_params:
        category_name: 文章category，可选，默认"all"，表示查询所有文章
        is_series: 系列文章过滤器，True表示只返回系列文章的入口信息，False表示返回单个文章和系列文章的信息，默认False
         skip: 文章分页时的第几页，默认1
        limit: 每页的返回文章信息数量，默认9
    :param session:
    :return: 一个包含文章信息的列表，列表的每个元素是一个如下的JSON:
            ```
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
    return TodoResponse()

