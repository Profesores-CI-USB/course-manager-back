import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Literal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    credits: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("credits > 0", name="ck_subjects_credits_positive"),
    )

    courses: Mapped[list["Course"]] = relationship(back_populates="subject")


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    professor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    term: Mapped[Literal["april-july", "january-march", "september-december", "summer"]] = mapped_column(
        String(30),
        nullable=False,
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "term IN ('april-july', 'january-march', 'september-december', 'summer')",
            name="ck_courses_term_allowed",
        ),
        CheckConstraint("year >= 2000", name="ck_courses_year_min"),
    )

    subject: Mapped["Subject"] = relationship(back_populates="courses")
    professor: Mapped["User"] = relationship(back_populates="courses_taught")
    evaluations: Mapped[list["Evaluation"]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
    )
    enrollments: Mapped[list["Enrollment"]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
    )


class Student(Base):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    student_card: Mapped[str] = mapped_column(String(8), unique=True, nullable=False, index=True)

    __table_args__ = (
        CheckConstraint("student_card ~ '^[0-9]{2}-[0-9]{5}$'", name="ck_students_student_card_format"),
    )

    enrollments: Mapped[list["Enrollment"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
    )


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    evaluation_type: Mapped[
        Literal["exam", "homework", "workshop", "project", "report", "presentation", "video"]
    ] = mapped_column(String(100), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)

    __table_args__ = (
        CheckConstraint("percentage >= 0 AND percentage <= 100", name="ck_evaluations_percentage_range"),
        CheckConstraint(
            "evaluation_type IN ('exam', 'homework', 'workshop', 'project', 'report', 'presentation', 'video')",
            name="ck_evaluations_type_allowed",
        ),
    )

    course: Mapped["Course"] = relationship(back_populates="evaluations")
    grades: Mapped[list["EvaluationGrade"]] = relationship(
        back_populates="evaluation",
        cascade="all, delete-orphan",
    )


class Enrollment(Base):
    __tablename__ = "enrollments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    final_grade: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    __table_args__ = (
        UniqueConstraint("course_id", "student_id", name="uq_enrollments_course_student"),
        CheckConstraint("final_grade IS NULL OR (final_grade >= 0 AND final_grade <= 100)", name="ck_enrollments_final_grade_range"),
    )

    course: Mapped["Course"] = relationship(back_populates="enrollments")
    student: Mapped["Student"] = relationship(back_populates="enrollments")
    evaluation_grades: Mapped[list["EvaluationGrade"]] = relationship(
        back_populates="enrollment",
        cascade="all, delete-orphan",
    )


class EvaluationGrade(Base):
    __tablename__ = "evaluation_grades"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evaluations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("enrollments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    grade: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    __table_args__ = (
        UniqueConstraint("evaluation_id", "enrollment_id", name="uq_evaluation_grades_eval_enrollment"),
        CheckConstraint("grade >= 0 AND grade <= 100", name="ck_evaluation_grades_grade_range"),
    )

    evaluation: Mapped["Evaluation"] = relationship(back_populates="grades")
    enrollment: Mapped["Enrollment"] = relationship(back_populates="evaluation_grades")
