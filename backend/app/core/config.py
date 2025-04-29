from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # 项目基本设置
    PROJECT_NAME: str = "声肺康"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # JWT设置
    SECRET_KEY: str = Field(default="your-super-secret-key-please-change-it")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # 数据库设置
    MYSQL_USER: str = Field(default="root")
    MYSQL_PASSWORD: str = Field(default="12345678")
    MYSQL_HOST: str = Field(default="localhost")
    MYSQL_PORT: int = Field(default=3306)
    MYSQL_DB: str = Field(default="project")
    
    # AI模型设置
    MODEL_PATH: str = Field(default="models/voice_model.pt")
    
    # LLM设置
    LLM_API_KEY: Optional[str] = None
    
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@"
            f"{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
        )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()