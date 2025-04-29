from pydantic import BaseSettings, Field
from typing import Optional

class Settings(BaseSettings):
    # 项目基本设置
    PROJECT_NAME: str = "声肺康"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # JWT设置
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # 数据库设置
    MYSQL_USER: str = Field(..., env="MYSQL_USER")
    MYSQL_PASSWORD: str = Field(..., env="MYSQL_PASSWORD")
    MYSQL_HOST: str = Field("localhost", env="MYSQL_HOST")
    MYSQL_PORT: int = Field(3306, env="MYSQL_PORT")
    MYSQL_DB: str = Field(..., env="MYSQL_DB")
    
    # AI模型设置
    MODEL_PATH: str = Field("models/voice_model.pt", env="MODEL_PATH")
    
    # LLM设置
    LLM_API_KEY: Optional[str] = Field(None, env="LLM_API_KEY")
    
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@"
            f"{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
        )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings() 