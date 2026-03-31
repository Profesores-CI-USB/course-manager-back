"""
CRUD y entrenamiento de configuraciones de modelos IA.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ConflictException, ForbiddenException, NotFoundException
from app.models import Course, Enrollment, Evaluation, EvaluationGrade
from app.models.ai_config import AIModelConfig
from app.schemas.ai_config import AIModelConfigCreate, AIModelConfigOut, AIModelConfigUpdate, TrainResponse
from app.services.common import _is_admin

WEIGHTS_DIR = Path(__file__).parent.parent.parent / "models_weights"
PASS_THRESHOLD = 50.0


def _weights_path(config_id: UUID) -> Path:
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    return WEIGHTS_DIR / f"{config_id}.pkl"


def _to_out(config: AIModelConfig) -> AIModelConfigOut:
    return AIModelConfigOut.model_validate(config)


# ── CRUD ───────────────────────────────────────────────────────────────────────

async def list_configs(db: AsyncSession, current_user) -> list[AIModelConfigOut]:
    query = select(AIModelConfig).order_by(AIModelConfig.created_at.desc())
    if not _is_admin(current_user):
        query = query.where(AIModelConfig.created_by == current_user.id)
    result = await db.execute(query)
    return [_to_out(c) for c in result.scalars().all()]


async def get_config(db: AsyncSession, current_user, config_id: UUID) -> AIModelConfigOut:
    result = await db.execute(select(AIModelConfig).where(AIModelConfig.id == config_id))
    config = result.scalar_one_or_none()
    if config is None:
        raise NotFoundException("Configuración de modelo no encontrada")
    if not _is_admin(current_user) and config.created_by != current_user.id:
        raise ForbiddenException("No tienes permiso para ver esta configuración")
    return _to_out(config)


async def create_config(
    db: AsyncSession, current_user, payload: AIModelConfigCreate
) -> AIModelConfigOut:
    # Any authenticated user can create; ownership (created_by) is set to current_user.id.
    # RBAC on reads/updates/deletes is enforced via created_by ownership check.
    # Check unique name
    existing = await db.execute(select(AIModelConfig).where(AIModelConfig.name == payload.name))
    if existing.scalar_one_or_none() is not None:
        raise ConflictException("Ya existe una configuración con ese nombre")

    config = AIModelConfig(
        name=payload.name,
        description=payload.description,
        model_type=payload.model_type,
        target=payload.target,
        hyperparams=payload.hyperparams,
        created_by=current_user.id,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return _to_out(config)


async def update_config(
    db: AsyncSession, current_user, config_id: UUID, payload: AIModelConfigUpdate
) -> AIModelConfigOut:
    result = await db.execute(select(AIModelConfig).where(AIModelConfig.id == config_id))
    config = result.scalar_one_or_none()
    if config is None:
        raise NotFoundException("Configuración de modelo no encontrada")
    if not _is_admin(current_user) and config.created_by != current_user.id:
        raise ForbiddenException("No tienes permiso para modificar esta configuración")

    if payload.name is not None:
        dup = await db.execute(
            select(AIModelConfig).where(
                AIModelConfig.name == payload.name,
                AIModelConfig.id != config_id,
            )
        )
        if dup.scalar_one_or_none() is not None:
            raise ConflictException("Ya existe una configuración con ese nombre")
        config.name = payload.name

    if payload.description is not None:
        config.description = payload.description
    if payload.hyperparams is not None:
        config.hyperparams = payload.hyperparams
        # Al cambiar hiperparámetros el modelo deja de ser válido
        config.is_trained = False
        config.weights_path = None
        config.trained_at = None

    db.add(config)
    await db.commit()
    await db.refresh(config)
    return _to_out(config)


async def delete_config(db: AsyncSession, current_user, config_id: UUID) -> None:
    result = await db.execute(select(AIModelConfig).where(AIModelConfig.id == config_id))
    config = result.scalar_one_or_none()
    if config is None:
        raise NotFoundException("Configuración de modelo no encontrada")
    if not _is_admin(current_user) and config.created_by != current_user.id:
        raise ForbiddenException("No tienes permiso para eliminar esta configuración")

    # Borrar pesos si existen
    if config.weights_path:
        try:
            Path(config.weights_path).unlink(missing_ok=True)
        except OSError:
            pass

    await db.delete(config)
    await db.commit()


# ── Training ───────────────────────────────────────────────────────────────────

async def train_model(db: AsyncSession, current_user, config_id: UUID) -> TrainResponse:
    from app.services.tf_inference import build_and_train

    result = await db.execute(select(AIModelConfig).where(AIModelConfig.id == config_id))
    config = result.scalar_one_or_none()
    if config is None:
        raise NotFoundException("Configuración de modelo no encontrada")
    if not _is_admin(current_user) and config.created_by != current_user.id:
        raise ForbiddenException("No tienes permiso para entrenar este modelo")

    max_features: int = config.hyperparams.get("max_features", 10)

    # ── Recopilar datos de entrenamiento ──────────────────────────────────────
    # Usamos TODAS las inscripciones con nota final (de todos los cursos)
    enroll_result = await db.execute(
        select(Enrollment).where(Enrollment.final_grade.is_not(None))
    )
    enrollments = enroll_result.scalars().all()

    X: list[list[float]] = []
    y: list[float] = []

    for enr in enrollments:
        # Evaluaciones del curso (ordenadas por fecha)
        evals_result = await db.execute(
            select(Evaluation)
            .where(Evaluation.course_id == enr.course_id)
            .order_by(Evaluation.due_date)
        )
        evaluations = evals_result.scalars().all()
        if not evaluations:
            continue

        # Notas registradas para esta inscripción
        grades_result = await db.execute(
            select(EvaluationGrade, Evaluation)
            .join(Evaluation, EvaluationGrade.evaluation_id == Evaluation.id)
            .where(EvaluationGrade.enrollment_id == enr.id)
        )
        rows = grades_result.all()

        graded_map: dict[UUID, float] = {
            eg.evaluation_id: float(eg.grade) / float(ev.percentage)
            for eg, ev in rows
            if float(ev.percentage) > 0
        }

        features = _build_feature_vector(evaluations, graded_map, max_features)
        X.append(features)

        if config.target == "final_grade":
            y.append(float(enr.final_grade) / 100.0)
        else:
            y.append(1.0 if float(enr.final_grade) >= PASS_THRESHOLD else 0.0)

    # ── Entrenar en executor ──────────────────────────────────────────────────
    wp = _weights_path(config_id)
    loop = asyncio.get_event_loop()

    samples_used: int = await loop.run_in_executor(
        None,
        build_and_train,
        X, y,
        config.model_type,
        config.target,
        config.hyperparams,
        str(wp),
    )

    # ── Actualizar registro ───────────────────────────────────────────────────
    config.weights_path = str(wp)
    config.is_trained = True
    config.trained_at = datetime.now(timezone.utc)
    db.add(config)
    await db.commit()

    return TrainResponse(
        config_id=config.id,
        is_trained=True,
        trained_at=config.trained_at,
        samples_used=samples_used,
        message=f"Modelo entrenado con {samples_used} muestras.",
    )


# ── Shared helper (reused by stats_service) ───────────────────────────────────

def _build_feature_vector(
    evaluations: list,
    graded_map: dict[UUID, float],
    max_features: int,
) -> list[float]:
    features: list[float] = []
    for ev in evaluations[:max_features]:
        features.append(graded_map.get(ev.id, -1.0))
    while len(features) < max_features:
        features.append(-1.0)
    return features
