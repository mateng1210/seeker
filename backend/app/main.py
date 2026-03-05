from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.database import engine, Base
from app.routers import auth, documents, analysis, jobs, resumes
from app.config import settings
import logging
from app.log_config import setup_logging

setup_logging()

# 创建数据库表
def init_db():
    Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理器 - 处理认证相关的401错误
@app.exception_handler(status.HTTP_401_UNAUTHORIZED)
async def unauthorized_exception_handler(request: Request, exc):
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "code": 401,
            "msg": "请登录",
            "data": []
        }
    )

# 包含路由
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(analysis.router)
app.include_router(jobs.router)
app.include_router(resumes.router)

@app.on_event("startup")
async def on_startup():
    init_db()

@app.get("/")
async def root():
    # 在视图里愉快地记录日志吧
    log = logging.getLogger(__name__)  # 推荐用`__name__`获取logger
    log.info("有人访问了根路径！")
    return {"message": "Welcome to AI Talent Assistant API"}
