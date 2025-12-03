import logging
import sys
from typing import TextIO

from loguru import logger

class InterceptHandler(logging.Handler):
    """
    该类的写法来自于 https://doupoa.site/archives/727，感谢文章作者提供的代码

    日志拦截处理器：将所有 Python 标准日志重定向到 Loguru （用于处理uvicorn / fastapi 等自带的日志）
    工作原理：
    1. 继承自 logging.Handler
    2. 重写 emit 方法处理日志记录
    3. 将标准库日志转换为 Loguru 格式
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(
            depth=depth,
            exception=record.exc_info
            ).log(
                level,
                record.getMessage()
            )


def setup_logger(
        output_path: str | TextIO,
        level: int | str
) -> None:
    logger.configure(extra={"request_id": ''})
    logger.remove()

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        # 日志级别，居中对齐
        "<level>{level: ^8}</level> | "
        # 进程和线程信息
        "process [<cyan>{process}</cyan>]:<cyan>{thread}</cyan> | "
        # 文件、函数和行号
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        # 日志消息
        "<level>{message}</level>"
    )

    # 控制台输出
    logger.add(
        sys.stdout,
        format=log_format,
        # colorize=True,
        level=level,
        backtrace=False,
        enqueue=True,
    )

    # 文件输出
    if not isinstance(output_path, TextIO):
        logger.add(
            output_path,
            format=log_format,
            # colorize=True,
            level=level,
            backtrace=True,
            enqueue=True,
        )

    # 配置第三方日志库
    logger_name_list = [name for name in logging.root.manager.loggerDict]
    for logger_name in logger_name_list:
        _logger = logging.getLogger(logger_name)
        _logger.setLevel(level)
        _logger.handlers.clear()
        if '.' not in logger_name:
            _logger.addHandler(InterceptHandler())
