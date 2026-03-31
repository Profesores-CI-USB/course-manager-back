from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ── Grade distribution ────────────────────────────────────────────────────────

class GradeDistribution(BaseModel):
    """Distribución usando la escala 1–5 (calculada a partir de notas 0–100)."""
    five: int = Field(description="Escala 5 — Nota >= 85")
    four: int = Field(description="Escala 4 — 70 <= Nota < 85")
    three: int = Field(description="Escala 3 — 50 <= Nota < 70")
    two: int = Field(description="Escala 2 — 30 <= Nota < 50")
    one: int = Field(description="Escala 1 — Nota < 30")
    pending: int = Field(description="Sin nota final registrada")


# ── Per-course stats ──────────────────────────────────────────────────────────

class EvaluationCoverage(BaseModel):
    total: int
    fully_graded: int
    completion_rate: float = Field(description="Porcentaje de notas de evaluación registradas (0–1)")


class CourseStatItem(BaseModel):
    course_id: UUID
    subject_code: str
    subject_name: str
    term: str
    year: int
    professor_id: UUID
    total_enrolled: int
    graded_count: int = Field(description="Estudiantes con nota final registrada")
    avg_final_grade: float | None = Field(description="Promedio en escala 0–100")
    avg_scale_grade: float | None = Field(description="Promedio en escala 1–5")
    pass_rate: float | None = Field(description="Fracción de aprobados (escala >= 3, nota >= 50) entre los calificados (0–1)")
    grade_distribution: GradeDistribution
    evaluations: EvaluationCoverage


# ── Summary KPIs ──────────────────────────────────────────────────────────────

class StatsSummary(BaseModel):
    total_courses: int
    total_enrolled: int = Field(description="Total de inscripciones (puede repetir estudiantes entre cursos)")
    graded_students: int = Field(description="Inscripciones con nota final registrada")
    pending_students: int = Field(description="Inscripciones sin nota final")
    global_avg_grade: float | None = Field(description="Promedio global en escala 0–100")
    global_avg_scale_grade: float | None = Field(description="Promedio global en escala 1–5")
    global_pass_rate: float | None = Field(description="Fracción de aprobados (escala >= 3) sobre calificados")
    overall_grade_distribution: GradeDistribution


# ── Full response ─────────────────────────────────────────────────────────────

class CourseStatsResponse(BaseModel):
    summary: StatsSummary
    courses: list[CourseStatItem]


# ── AI Prediction ─────────────────────────────────────────────────────────────

class PredictRequest(BaseModel):
    model_config_id: UUID
    course_id: UUID
    enrollment_id: UUID | None = None


class PredictionItem(BaseModel):
    enrollment_id: UUID
    student_id: UUID
    student_card: str
    current_partial_grade: float = Field(description="Suma ponderada actual (0–100)")
    graded_pct_coverage: float = Field(description="Porcentaje de la nota total ya evaluado (0–100)")
    predicted_final_grade: float | None = Field(default=None, description="Nota predicha en escala 0–100. Solo si target=final_grade")
    predicted_scale_grade: int | None = Field(default=None, description="Nota predicha en escala 1–5. Solo si target=final_grade")
    pass_probability: float | None = Field(default=None, description="Probabilidad de aprobar (0–1). Solo si target=pass_probability")


class PredictResponse(BaseModel):
    model_config_id: UUID
    model_name: str
    model_type: str
    target: Literal["final_grade", "pass_probability"]
    predictions: list[PredictionItem]
