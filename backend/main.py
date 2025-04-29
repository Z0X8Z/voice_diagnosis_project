from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.endpoints import auth
from app.db.session import engine
from app.db.models import Base
import uvicorn
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    default_response_class=JSONResponse,  # 设置默认响应类
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["认证"])

@app.get("/")
def read_root():
    return JSONResponse(
        content={"message": "欢迎使用声肺康系统"},
        media_type="application/json; charset=utf-8"
    )

if __name__ == "__main__":
    # 直接运行此文件时启动服务器
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )