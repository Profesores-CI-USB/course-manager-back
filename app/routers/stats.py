from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas.ai_config import AIModelConfigCreate, AIModelConfigOut, AIModelConfigUpdate, TrainResponse
from app.schemas.stats import CourseStatsResponse, PredictRequest, PredictResponse
from app.services import ai_config_service, stats_service

router = APIRouter(prefix="/stats", tags=["stats"])


# ── Dashboard de estadísticas ─────────────────────────────────────────────────

@router.get("/courses", response_model=CourseStatsResponse)
async def get_course_stats(
    course_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await stats_service.get_course_stats(
        db=db, current_user=current_user, course_id=course_id
    )


# ── Predicciones ──────────────────────────────────────────────────────────────

@router.post("/predict", response_model=PredictResponse)
async def predict_grades(
    payload: PredictRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await stats_service.predict_grades(
        db=db, current_user=current_user, payload=payload
    )


# ── Configuraciones de modelos IA ─────────────────────────────────────────────

@router.get("/ai-model-configs", response_model=list[AIModelConfigOut])
async def list_ai_model_configs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ai_config_service.list_configs(db=db, current_user=current_user)


@router.post(
    "/ai-model-configs",
    response_model=AIModelConfigOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_ai_model_config(
    payload: AIModelConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ai_config_service.create_config(
        db=db, current_user=current_user, payload=payload
    )


@router.get("/ai-model-configs/{config_id}", response_model=AIModelConfigOut)
async def get_ai_model_config(
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ai_config_service.get_config(
        db=db, current_user=current_user, config_id=config_id
    )


@router.put("/ai-model-configs/{config_id}", response_model=AIModelConfigOut)
async def update_ai_model_config(
    config_id: UUID,
    payload: AIModelConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ai_config_service.update_config(
        db=db, current_user=current_user, config_id=config_id, payload=payload
    )


@router.delete("/ai-model-configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ai_model_config(
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await ai_config_service.delete_config(
        db=db, current_user=current_user, config_id=config_id
    )


@router.post(
    "/ai-model-configs/{config_id}/train",
    response_model=TrainResponse,
)
async def train_ai_model(
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ai_config_service.train_model(
        db=db, current_user=current_user, config_id=config_id
    )
