# app/core/config.py
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    # 以下字段会从环境变量自动加载
    mysql_user:     str = Field(..., env="MYSQL_USER")
    mysql_password: str = Field(..., env="MYSQL_PASSWORD")
    mysql_host:     str = Field("localhost", env="MYSQL_HOST")
    mysql_port:     int = Field(3306, env="MYSQL_PORT")
    mysql_db:       str = Field(..., env="MYSQL_DB")

    @property
    def database_url(self) -> str:
        """
        构造 SQLAlchemy 所需的数据库 URL，
        这里使用 PyMySQL 驱动，并设定 utf8mb4 编码
        """
        return (
            f"mysql+pymysql://"
            f"{self.mysql_user}:{self.mysql_password}@"
            f"{self.mysql_host}:{self.mysql_port}/"
            f"{self.mysql_db}"
            "?charset=utf8mb4"
        )

    class Config:
        # 指定 env 文件路径及编码
        env_file = ".env"
        env_file_encoding = "utf-8"


# 在整个项目里都 import 这一个实例
settings = Settings()
