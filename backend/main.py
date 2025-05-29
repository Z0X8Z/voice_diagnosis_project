from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.endpoints import auth, users, diagnosis, llm, dashboard
from app.db.session import engine, get_db
from app.db.models import Base
import uvicorn
import logging
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
import pymysql
import os
from fastapi.exception_handlers import RequestValidationError
from fastapi.exceptions import RequestValidationError
from fastapi import Request, status

# 配置日志
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'app.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 在应用启动时检查数据库连接
try:
    # 测试与MySQL的连接
    conn = pymysql.connect(
        host=settings.MYSQL_HOST,
        port=int(settings.MYSQL_PORT),
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        database=settings.MYSQL_DATABASE,
    )
    conn.close()
    logger.info(f"成功连接到MySQL数据库: {settings.MYSQL_DATABASE}")
except Exception as e:
    logger.error(f"无法连接到MySQL数据库: {e}")
    logger.warning("请确保MySQL服务正在运行并且已经初始化数据库")
    logger.info("可以使用 'python init_mysql_db.py' 初始化数据库")

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
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["用户管理"])
app.include_router(diagnosis.router, prefix=f"{settings.API_V1_STR}/diagnosis", tags=["诊断检测"])
app.include_router(llm.router, prefix=f"{settings.API_V1_STR}/llm", tags=["大模型调用"])
app.include_router(dashboard.router, prefix=f"{settings.API_V1_STR}/dashboard", tags=["仪表盘"])

@app.get("/")
def read_root():
    return JSONResponse(
        content={"message": "欢迎使用声肺康系统"},
        media_type="application/json; charset=utf-8"
    )

@app.get("/db-status")
def check_db_status(db: Session = Depends(get_db)):
    """检查数据库连接状态的端点"""
    try:
        # 执行简单查询以验证连接是否正常
        db.execute("SELECT 1")
        return {"status": "success", "message": "数据库连接正常"}
    except Exception as e:
        return {"status": "error", "message": f"数据库连接失败: {str(e)}"}

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error("====== 422 Unprocessable Entity Traceback ======")
    try:
        logger.error(f"URL: {request.method} {request.url}")
    except Exception as e:
        logger.error(f"无法获取URL: {e}")
    try:
        body = await request.body()
        logger.error(f"Body: {body.decode('utf-8')}")
    except Exception as e:
        logger.error(f"无法获取请求体: {e}")
    try:
        logger.error(f"Headers: {dict(request.headers)}")
    except Exception as e:
        logger.error(f"无法获取请求头: {e}")
    try:
        logger.error(f"Errors: {exc.errors()}")
    except Exception as e:
        logger.error(f"无法获取errors: {e}")
    try:
        logger.error(f"Error str: {str(exc)}")
    except Exception as e:
        logger.error(f"无法获取error str: {e}")
    logger.error("===============================================" )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )

if __name__ == "__main__":
    # 直接运行此文件时启动服务器
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )