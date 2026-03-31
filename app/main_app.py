from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import (
    AppException,
    BadGatewayException,
    BadRequestException,
    ConflictException,
    ForbiddenException,
    InternalException,
    NotFoundException,
    UnauthorizedException,
)
from app.db.session import close_redis, init_models, redis_client
from app.routers import academic_router, ai_router, auth_router, health_router, mail_router, users_router

_STATUS_MAP: dict[type[AppException], int] = {
    NotFoundException: 404,
    ForbiddenException: 403,
    ConflictException: 409,
    BadRequestException: 400,
    UnauthorizedException: 401,
    InternalException: 500,
    BadGatewayException: 502,
}


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


@app.exception_handler(AppException)
async def app_exception_handler(request, exc: AppException) -> JSONResponse:
    status_code = _STATUS_MAP.get(type(exc), 500)
    return JSONResponse(status_code=status_code, content={"detail": exc.detail})

app.include_router(health_router)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(users_router, prefix=settings.api_v1_prefix)
app.include_router(mail_router, prefix=settings.api_v1_prefix)
app.include_router(ai_router, prefix=settings.api_v1_prefix)
app.include_router(academic_router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root():
    return {
        "name": settings.project_name,
        "docs": "/docs",
        "api_prefix": settings.api_v1_prefix,
    }
