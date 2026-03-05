"""add academic entities

Revision ID: 3c12f0b7d1aa
Revises: 0a6d9d4e3b8f
Create Date: 2026-03-04 23:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3c12f0b7d1aa"
down_revision: Union[str, Sequence[str], None] = "0a6d9d4e3b8f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "subjects",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("credits", sa.Integer(), nullable=False),
        sa.CheckConstraint("credits > 0", name="ck_subjects_credits_positive"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_subjects_code"), "subjects", ["code"], unique=True)

    op.create_table(
        "students",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("student_card", sa.String(length=8), nullable=False),
        sa.CheckConstraint("student_card ~ '^[0-9]{2}-[0-9]{5}$'", name="ck_students_student_card_format"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_students_student_card"), "students", ["student_card"], unique=True)

    op.create_table(
        "courses",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("subject_id", sa.UUID(), nullable=False),
        sa.Column("professor_id", sa.UUID(), nullable=False),
        sa.Column("term", sa.String(length=30), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "term IN ('april-july', 'january-march', 'september-december', 'summer')",
            name="ck_courses_term_allowed",
        ),
        sa.CheckConstraint("year >= 2000", name="ck_courses_year_min"),
        sa.ForeignKeyConstraint(["professor_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_courses_professor_id"), "courses", ["professor_id"], unique=False)
    op.create_index(op.f("ix_courses_subject_id"), "courses", ["subject_id"], unique=False)

    op.create_table(
        "evaluations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("course_id", sa.UUID(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("percentage", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("evaluation_type", sa.String(length=100), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.CheckConstraint("percentage >= 0 AND percentage <= 100", name="ck_evaluations_percentage_range"),
        sa.CheckConstraint(
            "evaluation_type IN ('exam', 'homework', 'workshop', 'project', 'report', 'presentation', 'video')",
            name="ck_evaluations_type_allowed",
        ),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_evaluations_course_id"), "evaluations", ["course_id"], unique=False)

    op.create_table(
        "enrollments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("course_id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("final_grade", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.CheckConstraint(
            "final_grade IS NULL OR (final_grade >= 0 AND final_grade <= 100)",
            name="ck_enrollments_final_grade_range",
        ),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id", "student_id", name="uq_enrollments_course_student"),
    )
    op.create_index(op.f("ix_enrollments_course_id"), "enrollments", ["course_id"], unique=False)
    op.create_index(op.f("ix_enrollments_student_id"), "enrollments", ["student_id"], unique=False)

    op.create_table(
        "evaluation_grades",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("evaluation_id", sa.UUID(), nullable=False),
        sa.Column("enrollment_id", sa.UUID(), nullable=False),
        sa.Column("grade", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.CheckConstraint("grade >= 0 AND grade <= 100", name="ck_evaluation_grades_grade_range"),
        sa.ForeignKeyConstraint(["enrollment_id"], ["enrollments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evaluation_id"], ["evaluations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("evaluation_id", "enrollment_id", name="uq_evaluation_grades_eval_enrollment"),
    )
    op.create_index(op.f("ix_evaluation_grades_enrollment_id"), "evaluation_grades", ["enrollment_id"], unique=False)
    op.create_index(op.f("ix_evaluation_grades_evaluation_id"), "evaluation_grades", ["evaluation_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_evaluation_grades_evaluation_id"), table_name="evaluation_grades")
    op.drop_index(op.f("ix_evaluation_grades_enrollment_id"), table_name="evaluation_grades")
    op.drop_table("evaluation_grades")

    op.drop_index(op.f("ix_enrollments_student_id"), table_name="enrollments")
    op.drop_index(op.f("ix_enrollments_course_id"), table_name="enrollments")
    op.drop_table("enrollments")

    op.drop_index(op.f("ix_evaluations_course_id"), table_name="evaluations")
    op.drop_table("evaluations")

    op.drop_index(op.f("ix_courses_subject_id"), table_name="courses")
    op.drop_index(op.f("ix_courses_professor_id"), table_name="courses")
    op.drop_table("courses")

    op.drop_index(op.f("ix_students_student_card"), table_name="students")
    op.drop_table("students")

    op.drop_index(op.f("ix_subjects_code"), table_name="subjects")
    op.drop_table("subjects")
