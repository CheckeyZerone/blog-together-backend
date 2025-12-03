import os.path
import sys
from typing import Literal, Annotated, Optional, TextIO, Tuple

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL, create_engine, text


class Settings(BaseSettings):
    # class Config:
    #     env_file = ".env"
    #     env_file_encoding = "utf-8"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
    def __init__(self):
        if not os.path.exists(os.path.join(self.root_url, self.model_config["env_file"])):
            with open(os.path.join(self.root_url, self.model_config["env_file"]), "w", encoding="utf-8") as file:
                config_default: str = \
                ("DB_TYPE=sqlite\nDB_NAME=blog_data\n\n"
                 "# MySQL专用，不使用MySQL时不生效\nDB_USERNAME=root\nDB_PASSWORD=password\nDB_HOST=localhost\nDB_PORT\n\n"
                 "# sqlite专用，不适用sqlite时不生效\nDB_PATH\n\n"
                 "# 日志设置\nLOG_OUTPUT_PATH\nLOG_LEVEL=INFO")
                file.writelines(config_default)
        super().__init__()

    app_name: str = "Blog Together Backend"
    db_type: Annotated[Literal["sqlite", "mysql"], Field(default="sqlite")]
    db_name: Annotated[str, Field(default="blog_data")]

    # MySQL专用，不使用MySQL时不生效
    db_username: Annotated[str, Field(default="root")]
    db_password: Annotated[Optional[str], Field(default="")]
    db_host: Annotated[Optional[str], Field(default="localhost")]
    db_port: Annotated[Optional[int], Field(default=None)]

    # sqlite专用，不适用sqlite时不生效
    db_path: Annotated[Optional[str], Field(default="./")]

    # 日志设置
    log_output_path: Optional[str] = None
    log_level: Annotated[Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], Field(default="INFO")]

    @computed_field
    @property
    def database_url(self) -> str | URL:
        if self.db_type.lower() == "sqlite":
            url = f"sqlite+aiosqlite:///{self.root_url}/{self.db_path}/{self.db_name}.db"
        elif self.db_type.lower() == "mysql":
            url = URL.create(
                self.db_type,
                host=self.db_host,
                port=self.db_port,
                username=self.db_username,
                password=self.db_password,
                query={"charset": "utf8mb4"}
            )
            engine = create_engine(url)

            # 若数据库不存在则创建数据库
            try:
                with engine.connect() as connection:
                    create_database: str = f'CREATE DATABASE IF NOT EXISTS {self.db_name};'
                    connection.execute(text(create_database))
                    connection.commit()
            except Exception as e:
                print(e)
                exit(-1)
            finally:
                engine.dispose()
            url = url.set(
                drivername=self.db_type+'+asyncmy',
                database=self.db_name
            )
        else:
            raise ValueError(f"Unknown database type: {self.db_type}")
        return url

    @computed_field
    @property
    def root_url(self) -> str:
        root_url = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        return root_url

    @computed_field
    @property
    def logger_config(self) -> Tuple[str | TextIO, str]:
        output_path: TextIO | str = sys.stderr
        if self.log_output_path is not None and len(self.log_output_path) != 0:
            output_path: str = self.log_output_path
        log_level: str = self.log_level.upper()
        return output_path, log_level



