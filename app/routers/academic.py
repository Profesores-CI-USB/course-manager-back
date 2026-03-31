import uuid
from datetime import date

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas.academic import (
    BulkEnrollmentResult,
    CourseCreate,
    CourseOrderBy,
    CourseOut,
    CourseUpdate,
    EnrollmentCreate,
    EnrollmentOrderBy,
    EnrollmentOut,
    EnrollmentUpdate,
    EvaluationCreate,
    EvaluationGradeCreate,
    EvaluationGradeOrderBy,
    EvaluationGradeOut,
    EvaluationGradeUpdate,
    EvaluationOrderBy,
    EvaluationOut,
    EvaluationUpdate,
    StudentCreate,
    StudentOrderBy,
    StudentOut,
    StudentUpdate,
    SubjectCreate,
    SubjectOrderBy,
    SubjectOut,
    SubjectUpdate,
)
from app.services import academic_service


router = APIRouter(prefix="/academic", tags=["academic"])


@router.get("/subjects", response_model=list[SubjectOut])
async def list_subjects(
    code: str | None = None,
    name: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    order_by: SubjectOrderBy = Query(default=SubjectOrderBy.code),
    order_dir: str = Query(default="asc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.list_subjects(
        db=db,
        current_user=current_user,
        code=code,
        name=name,
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_dir=order_dir,
    )


@router.get("/courses", response_model=list[CourseOut])
async def list_courses(
    subject_id: uuid.UUID | None = None,
    term: str | None = None,
    year: int | None = None,
    professor_id: uuid.UUID | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    order_by: CourseOrderBy = Query(default=CourseOrderBy.year),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.list_courses(
        db=db,
        current_user=current_user,
        subject_id=subject_id,
        term=term,
        year=year,
        professor_id=professor_id,
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_dir=order_dir,
    )


@router.get("/students", response_model=list[StudentOut])
async def list_students(
    course_id: uuid.UUID | None = None,
    student_card: str | None = None,
    email: str | None = None,
    full_name: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    order_by: StudentOrderBy = Query(default=StudentOrderBy.full_name),
    order_dir: str = Query(default="asc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.list_students(
        db=db,
        current_user=current_user,
        course_id=course_id,
        student_card=student_card,
        email=email,
        full_name=full_name,
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_dir=order_dir,
    )


@router.get("/evaluations", response_model=list[EvaluationOut])
async def list_evaluations(
    course_id: uuid.UUID | None = None,
    evaluation_type: str | None = None,
    due_date_from: date | None = None,
    due_date_to: date | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    order_by: EvaluationOrderBy = Query(default=EvaluationOrderBy.due_date),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.list_evaluations(
        db=db,
        current_user=current_user,
        course_id=course_id,
        evaluation_type=evaluation_type,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_dir=order_dir,
    )


@router.get("/enrollments", response_model=list[EnrollmentOut])
async def list_enrollments(
    course_id: uuid.UUID | None = None,
    student_id: uuid.UUID | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    order_by: EnrollmentOrderBy = Query(default=EnrollmentOrderBy.id),
    order_dir: str = Query(default="asc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.list_enrollments(
        db=db,
        current_user=current_user,
        course_id=course_id,
        student_id=student_id,
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_dir=order_dir,
    )


@router.get("/evaluation-grades", response_model=list[EvaluationGradeOut])
async def list_evaluation_grades(
    course_id: uuid.UUID | None = None,
    evaluation_id: uuid.UUID | None = None,
    enrollment_id: uuid.UUID | None = None,
    student_id: uuid.UUID | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    order_by: EvaluationGradeOrderBy = Query(default=EvaluationGradeOrderBy.id),
    order_dir: str = Query(default="asc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.list_evaluation_grades(
        db=db,
        current_user=current_user,
        course_id=course_id,
        evaluation_id=evaluation_id,
        enrollment_id=enrollment_id,
        student_id=student_id,
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_dir=order_dir,
    )


@router.post("/subjects", response_model=SubjectOut, status_code=status.HTTP_201_CREATED)
async def create_subject(
    payload: SubjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.create_subject(db=db, payload=payload, current_user=current_user)


@router.post("/courses", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
async def create_course(
    payload: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.create_course(db=db, payload=payload, current_user=current_user)


@router.post("/students", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
async def create_student(
    payload: StudentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.create_student(db=db, payload=payload, current_user=current_user)


@router.post("/evaluations", response_model=EvaluationOut, status_code=status.HTTP_201_CREATED)
async def create_evaluation(
    payload: EvaluationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.create_evaluation(db=db, payload=payload, current_user=current_user)


@router.post("/enrollments", response_model=EnrollmentOut, status_code=status.HTTP_201_CREATED)
async def create_enrollment(
    payload: EnrollmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.create_enrollment(db=db, payload=payload, current_user=current_user)


@router.post("/evaluation-grades", response_model=EvaluationGradeOut, status_code=status.HTTP_201_CREATED)
async def create_evaluation_grade(
    payload: EvaluationGradeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.create_evaluation_grade(db=db, payload=payload, current_user=current_user)


@router.post("/enrollments/bulk-csv", response_model=BulkEnrollmentResult, status_code=status.HTTP_201_CREATED)
async def bulk_enroll_students_csv(
    course_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.bulk_enroll_students_csv(
        db=db,
        current_user=current_user,
        course_id=course_id,
        file=file,
    )


@router.put("/subjects/{subject_id}", response_model=SubjectOut)
async def update_subject(
    subject_id: uuid.UUID,
    payload: SubjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.update_subject(db=db, subject_id=subject_id, payload=payload, current_user=current_user)


@router.put("/courses/{course_id}", response_model=CourseOut)
async def update_course(
    course_id: uuid.UUID,
    payload: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.update_course(
        db=db,
        current_user=current_user,
        course_id=course_id,
        payload=payload,
    )


@router.put("/students/{student_id}", response_model=StudentOut)
async def update_student(
    student_id: uuid.UUID,
    payload: StudentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.update_student(db=db, student_id=student_id, payload=payload, current_user=current_user)


@router.put("/evaluations/{evaluation_id}", response_model=EvaluationOut)
async def update_evaluation(
    evaluation_id: uuid.UUID,
    payload: EvaluationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.update_evaluation(
        db=db,
        current_user=current_user,
        evaluation_id=evaluation_id,
        payload=payload,
    )


@router.put("/enrollments/{enrollment_id}", response_model=EnrollmentOut)
async def update_enrollment(
    enrollment_id: uuid.UUID,
    payload: EnrollmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.update_enrollment(
        db=db,
        current_user=current_user,
        enrollment_id=enrollment_id,
        payload=payload,
    )


@router.put("/evaluation-grades/{evaluation_grade_id}", response_model=EvaluationGradeOut)
async def update_evaluation_grade(
    evaluation_grade_id: uuid.UUID,
    payload: EvaluationGradeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_service.update_evaluation_grade(
        db=db,
        current_user=current_user,
        evaluation_grade_id=evaluation_grade_id,
        payload=payload,
    )
