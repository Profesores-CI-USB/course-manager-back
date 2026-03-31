"""
Servicio de estadísticas y predicciones de cursos.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.models import Course, Enrollment, EvaluationGrade, Student, Subject
from app.models import Evaluation
from app.models.ai_config import AIModelConfig
from app.schemas.stats import (
    CourseStatItem,
    CourseStatsResponse,
    EvaluationCoverage,
    GradeDistribution,
    PredictRequest,
    PredictionItem,
    PredictResponse,
    StatsSummary,
)
from app.services.common import _is_admin

PASS_THRESHOLD = 50.0
WEIGHTS_DIR = Path(__file__).parent.parent.parent / "models_weights"


# ── Helpers ────────────────────────────────────────────────────────────────────

def grade_to_scale(grade: float) -> int:
    """Convierte nota 0–100 a escala 1–5."""
    if grade >= 85:
        return 5
    if grade >= 70:
        return 4
    if grade >= 50:
        return 3
    if grade >= 30:
        return 2
    return 1


def _grade_bucket(grade: float) -> str:
    if grade >= 85:
        return "five"
    if grade >= 70:
        return "four"
    if grade >= 50:
        return "three"
    if grade >= 30:
        return "two"
    return "one"


def _empty_distribution() -> GradeDistribution:
    return GradeDistribution(five=0, four=0, three=0, two=0, one=0, pending=0)


def _build_feature_vector(
    evaluations: list,
    graded_map: dict[UUID, float],
    max_features: int,
) -> list[float]:
    """Vector de features: grade/percentage por evaluación (orden por due_date), pad con -1."""
    features: list[float] = []
    for ev in evaluations[:max_features]:
        features.append(graded_map.get(ev.id, -1.0))
    while len(features) < max_features:
        features.append(-1.0)
    return features


# ── Statistics ─────────────────────────────────────────────────────────────────

async def get_course_stats(
    db: AsyncSession,
    current_user,
    course_id: UUID | None = None,
) -> CourseStatsResponse:
    # Obtener cursos según RBAC
    query = select(Course)
    if not _is_admin(current_user):
        query = query.where(Course.professor_id == current_user.id)
    if course_id:
        query = query.where(Course.id == course_id)

    courses_result = await db.execute(query)
    courses = courses_result.scalars().all()

    course_stats: list[CourseStatItem] = []
    total_enrolled = 0
    total_graded = 0
    grade_sum = 0.0
    scale_sum = 0.0
    pass_count = 0
    overall_dist = _empty_distribution()

    for course in courses:
        # Subject info
        subject_result = await db.execute(select(Subject).where(Subject.id == course.subject_id))
        subject = subject_result.scalar_one_or_none()

        # Enrollments
        enroll_result = await db.execute(
            select(Enrollment).where(Enrollment.course_id == course.id)
        )
        enrollments = enroll_result.scalars().all()

        # Evaluations
        eval_result = await db.execute(
            select(Evaluation).where(Evaluation.course_id == course.id)
        )
        evaluations = eval_result.scalars().all()

        # Count evaluation grades registered
        eg_result = await db.execute(
            select(EvaluationGrade)
            .join(Evaluation, EvaluationGrade.evaluation_id == Evaluation.id)
            .where(Evaluation.course_id == course.id)
        )
        all_eg = eg_result.scalars().all()

        # Per-course aggregation
        dist = _empty_distribution()
        graded_in_course = 0
        grade_total = 0.0
        scale_total = 0.0
        pass_in_course = 0

        for enr in enrollments:
            if enr.final_grade is not None:
                fg = float(enr.final_grade)
                sg = grade_to_scale(fg)
                graded_in_course += 1
                grade_total += fg
                scale_total += sg
                bucket = _grade_bucket(fg)
                setattr(dist, bucket, getattr(dist, bucket) + 1)
                if fg >= PASS_THRESHOLD:
                    pass_in_course += 1
                # Overall
                setattr(overall_dist, bucket, getattr(overall_dist, bucket) + 1)
                grade_sum += fg
                scale_sum += sg
                pass_count += 1 if fg >= PASS_THRESHOLD else 0
            else:
                dist.pending += 1
                overall_dist.pending += 1

        total_enrolled += len(enrollments)
        total_graded += graded_in_course

        # Evaluation completion rate
        max_possible_grades = len(evaluations) * len(enrollments)
        completion_rate = (len(all_eg) / max_possible_grades) if max_possible_grades > 0 else 0.0

        # Fully graded evaluations (at least one grade registered)
        graded_eval_ids = {eg.evaluation_id for eg in all_eg}

        course_stats.append(
            CourseStatItem(
                course_id=course.id,
                subject_code=subject.code if subject else "—",
                subject_name=subject.name if subject else "—",
                term=course.term,
                year=course.year,
                professor_id=course.professor_id,
                total_enrolled=len(enrollments),
                graded_count=graded_in_course,
                avg_final_grade=round(grade_total / graded_in_course, 2) if graded_in_course > 0 else None,
                avg_scale_grade=round(scale_total / graded_in_course, 4) if graded_in_course > 0 else None,
                pass_rate=round(pass_in_course / graded_in_course, 4) if graded_in_course > 0 else None,
                grade_distribution=dist,
                evaluations=EvaluationCoverage(
                    total=len(evaluations),
                    fully_graded=len(graded_eval_ids),
                    completion_rate=round(completion_rate, 4),
                ),
            )
        )

    global_avg = round(grade_sum / total_graded, 2) if total_graded > 0 else None
    global_avg_scale = round(scale_sum / total_graded, 4) if total_graded > 0 else None
    global_pass = round(pass_count / total_graded, 4) if total_graded > 0 else None

    summary = StatsSummary(
        total_courses=len(courses),
        total_enrolled=total_enrolled,
        graded_students=total_graded,
        pending_students=total_enrolled - total_graded,
        global_avg_grade=global_avg,
        global_avg_scale_grade=global_avg_scale,
        global_pass_rate=global_pass,
        overall_grade_distribution=overall_dist,
    )

    return CourseStatsResponse(summary=summary, courses=course_stats)


# ── Prediction ─────────────────────────────────────────────────────────────────

async def predict_grades(
    db: AsyncSession,
    current_user,
    payload: PredictRequest,
) -> PredictResponse:
    from app.services.tf_inference import run_prediction

    # Load model config
    cfg_result = await db.execute(
        select(AIModelConfig).where(AIModelConfig.id == payload.model_config_id)
    )
    config = cfg_result.scalar_one_or_none()
    if config is None:
        raise NotFoundException("Configuración de modelo no encontrada")
    if not config.is_trained or not config.weights_path:
        raise BadRequestException("El modelo aún no ha sido entrenado. Ejecuta POST /train primero.")

    # RBAC on course
    course_result = await db.execute(select(Course).where(Course.id == payload.course_id))
    course = course_result.scalar_one_or_none()
    if course is None:
        raise NotFoundException("Curso no encontrado")
    if not _is_admin(current_user) and course.professor_id != current_user.id:
        raise ForbiddenException("No tienes permiso para predecir en este curso")

    # Evaluations (sorted by due_date)
    eval_result = await db.execute(
        select(Evaluation)
        .where(Evaluation.course_id == payload.course_id)
        .order_by(Evaluation.due_date)
    )
    evaluations = eval_result.scalars().all()

    max_features: int = config.hyperparams.get("max_features", 10)

    # Enrollments to predict
    enroll_query = select(Enrollment).where(Enrollment.course_id == payload.course_id)
    if payload.enrollment_id:
        enroll_query = enroll_query.where(Enrollment.id == payload.enrollment_id)
    enroll_result = await db.execute(enroll_query)
    enrollments = enroll_result.scalars().all()

    if not enrollments:
        raise NotFoundException("No se encontraron inscripciones para predecir")

    X: list[list[float]] = []
    partial_grades: list[float] = []
    coverage_list: list[float] = []

    for enr in enrollments:
        # Get grades for this enrollment
        grades_result = await db.execute(
            select(EvaluationGrade, Evaluation)
            .join(Evaluation, EvaluationGrade.evaluation_id == Evaluation.id)
            .where(EvaluationGrade.enrollment_id == enr.id)
        )
        rows = grades_result.all()

        graded_map: dict[UUID, float] = {}
        partial_sum = 0.0
        graded_pct = 0.0

        for eg, ev in rows:
            if float(ev.percentage) > 0:
                normalized = float(eg.grade) / float(ev.percentage)
                graded_map[ev.id] = normalized
                partial_sum += float(eg.grade)
                graded_pct += float(ev.percentage)

        X.append(_build_feature_vector(evaluations, graded_map, max_features))
        partial_grades.append(round(partial_sum, 2))
        coverage_list.append(round(graded_pct, 2))

    # Run inference in executor (TF is blocking)
    loop = asyncio.get_event_loop()
    preds: list[float] = await loop.run_in_executor(
        None,
        run_prediction,
        config.weights_path,
        X,
        config.target,
    )

    # Fetch students for card info
    student_ids = [enr.student_id for enr in enrollments]
    students_result = await db.execute(select(Student).where(Student.id.in_(student_ids)))
    students_map = {s.id: s for s in students_result.scalars().all()}

    predictions: list[PredictionItem] = []
    for enr, pred, partial, cov in zip(enrollments, preds, partial_grades, coverage_list):
        student = students_map.get(enr.student_id)
        is_final_grade = config.target == "final_grade"
        predictions.append(
            PredictionItem(
                enrollment_id=enr.id,
                student_id=enr.student_id,
                student_card=student.student_card if student else "N/A",
                current_partial_grade=partial,
                graded_pct_coverage=cov,
                predicted_final_grade=round(pred, 2) if is_final_grade else None,
                predicted_scale_grade=grade_to_scale(pred) if is_final_grade else None,
                pass_probability=round(pred, 4) if not is_final_grade else None,
            )
        )

    return PredictResponse(
        model_config_id=config.id,
        model_name=config.name,
        model_type=config.model_type,
        target=config.target,
        predictions=predictions,
    )
