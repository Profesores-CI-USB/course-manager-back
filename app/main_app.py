from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.db.session import close_redis, init_models, redis_client
from app.routers import ai_router, auth_router, health_router, mail_router, users_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_models()
    await redis_client.ping()
    yield
    await close_redis()


app = FastAPI(
    title=settings.project_name,
    version="1.0.0",
    description="Plantilla backend: FastAPI + Neon(Postgres) + Redis + SMTP + IA",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(users_router, prefix=settings.api_v1_prefix)
app.include_router(mail_router, prefix=settings.api_v1_prefix)
app.include_router(ai_router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root():
    return {
        "name": settings.project_name,
        "docs": "/docs",
        "api_prefix": settings.api_v1_prefix,
    }
