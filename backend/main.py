from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.core.database import init_db
from app.api.routes import router

logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="Awaken AI 生涯成长产品 MVP 后端服务",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info(f"{settings.APP_NAME} 服务启动成功")
    logger.info(f"环境: {settings.APP_ENV}")
    logger.info(f"SMTP 邮件服务: {'已启用' if settings.SMTP_ENABLED else 'Mock 模式'}")
    logger.info(f"飞书 Webhook: {'已启用' if settings.FEISHU_ENABLED else 'Mock 模式'}")


app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
