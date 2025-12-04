from pydantic import BaseModel, Field


class ArticleAndSeriesFilterParams(BaseModel):
    """
    :param category_name: 文章category名，可选，默认"all"，表示查询所有文章
    :param is_series: 系列文章过滤器，True表示只返回系列文章的入口信息，False表示返回单个文章和系列文章的信息，默认False
    :param skip: 文章分页时的第几页，默认1
    :param limit: 每页的返回文章信息数量，默认9
    """
    category_name: str = "all"
    is_series: bool = False
    skip: int = Field(1, ge=1)
    limit: int = Field(9, ge=1)

class ArticleInfo(BaseModel):
    article_id: int
    article_title: str
    article_series: str
    update_time: str
    article_cover: str
    article_category: int



class ArticleCreatorParams(BaseModel):
    """
    :param article_title: 文章标题
    :param series_name: 文章所属系列名
    :param article_cover: 封面URL
    :param article_abstract: 文章摘要
    :param article_content: 文章内容
    :param category_name: 文章所属类别名
    """
    article_title: str
    series_name: str = None
    article_cover: str
    article_abstract: str
    article_content: str
    category_name: str

class ArticleCategoryCreatorParams(BaseModel):
    """
    :param article_category_name: 文章类别名
    """
    article_category_name: str

class ArticleDeleteParams(BaseModel):
    article_id: int
    is_force: bool = False
