from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class SubjectOrderBy(str, Enum):
    code = "code"
    name = "name"
    credits = "credits"


class CourseOrderBy(str, Enum):
    year = "year"
    term = "term"
    subject_id = "subject_id"
    professor_id = "professor_id"


class StudentOrderBy(str, Enum):
    full_name = "full_name"
    student_card = "student_card"
    email = "email"


class EvaluationOrderBy(str, Enum):
    due_date = "due_date"
    percentage = "percentage"
    evaluation_type = "evaluation_type"


class EnrollmentOrderBy(str, Enum):
    id = "id"
    final_grade = "final_grade"


class EvaluationGradeOrderBy(str, Enum):
    id = "id"
    grade = "grade"


class SubjectCreate(BaseModel):
    code: str
    name: str
    credits: int


class SubjectUpdate(BaseModel):
    code: str
    name: str
    credits: int


class SubjectOut(BaseModel):
    id: UUID
    code: str
    name: str
    credits: int


class CourseCreate(BaseModel):
    subject_id: UUID
    professor_id: UUID
    term: Literal["april-july", "january-march", "september-december", "summer"]
    year: int


class CourseUpdate(BaseModel):
    subject_id: UUID
    professor_id: UUID
    term: Literal["april-july", "january-march", "september-december", "summer"]
    year: int


class CourseOut(BaseModel):
    id: UUID
    subject_id: UUID
    professor_id: UUID
    term: Literal["april-july", "january-march", "september-december", "summer"]
    year: int


class StudentCreate(BaseModel):
    full_name: str
    student_card: str
    email: EmailStr | None = None


class StudentUpdate(BaseModel):
    full_name: str
    student_card: str
    email: EmailStr | None = None


class StudentOut(BaseModel):
    id: UUID
    full_name: str
    student_card: str
    email: EmailStr


class EvaluationCreate(BaseModel):
    course_id: UUID
    description: str
    percentage: Decimal = Field(..., ge=0, le=100)
    evaluation_type: Literal["exam", "homework", "workshop", "project", "report", "presentation", "video"]
    due_date: date


class EvaluationUpdate(BaseModel):
    course_id: UUID
    description: str
    percentage: Decimal = Field(..., ge=0, le=100)
    evaluation_type: Literal["exam", "homework", "workshop", "project", "report", "presentation", "video"]
    due_date: date


class EvaluationOut(BaseModel):
    id: UUID
    course_id: UUID
    description: str
    percentage: Decimal
    evaluation_type: Literal["exam", "homework", "workshop", "project", "report", "presentation", "video"]
    due_date: date


class EnrollmentCreate(BaseModel):
    course_id: UUID
    student_id: UUID


class EnrollmentUpdate(BaseModel):
    course_id: UUID
    student_id: UUID
    final_grade: Decimal | None = Field(default=None, ge=0, le=100)


class EnrollmentOut(BaseModel):
    id: UUID
    course_id: UUID
    student_id: UUID
    final_grade: Decimal | None


class EvaluationGradeCreate(BaseModel):
    evaluation_id: UUID
    enrollment_id: UUID
    grade: Decimal = Field(..., ge=0)


class EvaluationGradeUpdate(BaseModel):
    evaluation_id: UUID
    enrollment_id: UUID
    grade: Decimal = Field(..., ge=0)


class EvaluationGradeOut(BaseModel):
    id: UUID
    evaluation_id: UUID
    enrollment_id: UUID
    grade: Decimal


class BulkEnrollmentRowError(BaseModel):
    line: int
    student_card: str | None = None
    detail: str


class BulkEnrollmentResult(BaseModel):
    course_id: UUID
    rows_total: int
    students_created: int
    students_existing: int
    enrollments_created: int
    enrollments_existing: int
    errors: list[BulkEnrollmentRowError]
