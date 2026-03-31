import csv
import io
import uuid
from datetime import date

from fastapi import UploadFile
from sqlalchemy import asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ConflictException, ForbiddenException, NotFoundException
from app.models import Course, Enrollment, Evaluation, EvaluationGrade, Student, Subject, User
from app.services.common import _apply_pagination, _is_admin, _resolve_order_column
from app.schemas.academic import (
    BulkEnrollmentResult,
    BulkEnrollmentRowError,
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


async def list_subjects(
    db: AsyncSession,
    current_user: User,
    code: str | None,
    name: str | None,
    limit: int,
    offset: int,
    order_by: SubjectOrderBy,
    order_dir: str,
) -> list[SubjectOut]:
    query = select(Subject)

    if not _is_admin(current_user):
        query = query.join(Course, Course.subject_id == Subject.id).where(Course.professor_id == current_user.id)

    if code:
        query = query.where(Subject.code.ilike(f"%{code}%"))
    if name:
        query = query.where(Subject.name.ilike(f"%{name}%"))

    order_column = _resolve_order_column(
        order_by.value,
        {
            "code": Subject.code,
            "name": Subject.name,
            "credits": Subject.credits,
        },
        Subject.code,
    )
    order_expression = asc(order_column) if order_dir == "asc" else desc(order_column)
    query = _apply_pagination(query.order_by(order_expression), limit=limit, offset=offset)

    result = await db.execute(query)
    subjects = result.scalars().unique().all()
    return [SubjectOut(id=s.id, code=s.code, name=s.name, credits=s.credits) for s in subjects]


async def list_courses(
    db: AsyncSession,
    current_user: User,
    subject_id: uuid.UUID | None,
    term: str | None,
    year: int | None,
    professor_id: uuid.UUID | None,
    limit: int,
    offset: int,
    order_by: CourseOrderBy,
    order_dir: str,
) -> list[CourseOut]:
    query = select(Course)

    if _is_admin(current_user):
        if professor_id:
            query = query.where(Course.professor_id == professor_id)
    else:
        query = query.where(Course.professor_id == current_user.id)

    if subject_id:
        query = query.where(Course.subject_id == subject_id)
    if term:
        query = query.where(Course.term == term)
    if year:
        query = query.where(Course.year == year)

    order_column = _resolve_order_column(
        order_by.value,
        {
            "year": Course.year,
            "term": Course.term,
            "subject_id": Course.subject_id,
            "professor_id": Course.professor_id,
        },
        Course.year,
    )
    order_expression = asc(order_column) if order_dir == "asc" else desc(order_column)
    query = _apply_pagination(query.order_by(order_expression), limit=limit, offset=offset)

    result = await db.execute(query)
    courses = result.scalars().all()
    return [
        CourseOut(
            id=c.id,
            subject_id=c.subject_id,
            professor_id=c.professor_id,
            term=c.term,
            year=c.year,
        )
        for c in courses
    ]


async def list_students(
    db: AsyncSession,
    current_user: User,
    course_id: uuid.UUID | None,
    student_card: str | None,
    email: str | None,
    full_name: str | None,
    limit: int,
    offset: int,
    order_by: StudentOrderBy,
    order_dir: str,
) -> list[StudentOut]:
    query = select(Student)

    if not _is_admin(current_user) or course_id:
        query = query.join(Enrollment, Enrollment.student_id == Student.id).join(Course, Course.id == Enrollment.course_id)

    if not _is_admin(current_user):
        query = query.where(Course.professor_id == current_user.id)

    if course_id:
        query = query.where(Enrollment.course_id == course_id)
    if student_card:
        query = query.where(Student.student_card.ilike(f"%{student_card}%"))
    if email:
        query = query.where(Student.email.ilike(f"%{email}%"))
    if full_name:
        query = query.where(Student.full_name.ilike(f"%{full_name}%"))

    order_column = _resolve_order_column(
        order_by.value,
        {
            "full_name": Student.full_name,
            "student_card": Student.student_card,
            "email": Student.email,
        },
        Student.full_name,
    )
    order_expression = asc(order_column) if order_dir == "asc" else desc(order_column)
    query = _apply_pagination(query.order_by(order_expression), limit=limit, offset=offset)

    result = await db.execute(query)
    students = result.scalars().unique().all()
    return [
        StudentOut(
            id=s.id,
            full_name=s.full_name,
            student_card=s.student_card,
            email=s.email,
        )
        for s in students
    ]


async def list_evaluations(
    db: AsyncSession,
    current_user: User,
    course_id: uuid.UUID | None,
    evaluation_type: str | None,
    due_date_from: date | None,
    due_date_to: date | None,
    limit: int,
    offset: int,
    order_by: EvaluationOrderBy,
    order_dir: str,
) -> list[EvaluationOut]:
    query = select(Evaluation).join(Course, Course.id == Evaluation.course_id)

    if not _is_admin(current_user):
        query = query.where(Course.professor_id == current_user.id)

    if course_id:
        query = query.where(Evaluation.course_id == course_id)
    if evaluation_type:
        query = query.where(Evaluation.evaluation_type == evaluation_type)
    if due_date_from:
        query = query.where(Evaluation.due_date >= due_date_from)
    if due_date_to:
        query = query.where(Evaluation.due_date <= due_date_to)

    order_column = _resolve_order_column(
        order_by.value,
        {
            "due_date": Evaluation.due_date,
            "percentage": Evaluation.percentage,
            "evaluation_type": Evaluation.evaluation_type,
        },
        Evaluation.due_date,
    )
    order_expression = asc(order_column) if order_dir == "asc" else desc(order_column)
    query = _apply_pagination(query.order_by(order_expression), limit=limit, offset=offset)

    result = await db.execute(query)
    evaluations = result.scalars().all()
    return [
        EvaluationOut(
            id=e.id,
            course_id=e.course_id,
            description=e.description,
            percentage=e.percentage,
            evaluation_type=e.evaluation_type,
            due_date=e.due_date,
        )
        for e in evaluations
    ]


async def list_enrollments(
    db: AsyncSession,
    current_user: User,
    course_id: uuid.UUID | None,
    student_id: uuid.UUID | None,
    limit: int,
    offset: int,
    order_by: EnrollmentOrderBy,
    order_dir: str,
) -> list[EnrollmentOut]:
    query = select(Enrollment).join(Course, Course.id == Enrollment.course_id)

    if not _is_admin(current_user):
        query = query.where(Course.professor_id == current_user.id)

    if course_id:
        query = query.where(Enrollment.course_id == course_id)
    if student_id:
        query = query.where(Enrollment.student_id == student_id)

    order_column = _resolve_order_column(
        order_by.value,
        {
            "id": Enrollment.id,
            "final_grade": Enrollment.final_grade,
        },
        Enrollment.id,
    )
    order_expression = asc(order_column) if order_dir == "asc" else desc(order_column)
    query = _apply_pagination(query.order_by(order_expression), limit=limit, offset=offset)

    result = await db.execute(query)
    enrollments = result.scalars().all()
    return [
        EnrollmentOut(
            id=e.id,
            course_id=e.course_id,
            student_id=e.student_id,
            final_grade=e.final_grade,
        )
        for e in enrollments
    ]


async def list_evaluation_grades(
    db: AsyncSession,
    current_user: User,
    course_id: uuid.UUID | None,
    evaluation_id: uuid.UUID | None,
    enrollment_id: uuid.UUID | None,
    student_id: uuid.UUID | None,
    limit: int,
    offset: int,
    order_by: EvaluationGradeOrderBy,
    order_dir: str,
) -> list[EvaluationGradeOut]:
    query = (
        select(EvaluationGrade)
        .join(Evaluation, Evaluation.id == EvaluationGrade.evaluation_id)
        .join(Enrollment, Enrollment.id == EvaluationGrade.enrollment_id)
        .join(Course, Course.id == Evaluation.course_id)
    )

    if not _is_admin(current_user):
        query = query.where(Course.professor_id == current_user.id)

    if course_id:
        query = query.where(Evaluation.course_id == course_id)
    if evaluation_id:
        query = query.where(EvaluationGrade.evaluation_id == evaluation_id)
    if enrollment_id:
        query = query.where(EvaluationGrade.enrollment_id == enrollment_id)
    if student_id:
        query = query.where(Enrollment.student_id == student_id)

    order_column = _resolve_order_column(
        order_by.value,
        {
            "id": EvaluationGrade.id,
            "grade": EvaluationGrade.grade,
        },
        EvaluationGrade.id,
    )
    order_expression = asc(order_column) if order_dir == "asc" else desc(order_column)
    query = _apply_pagination(query.order_by(order_expression), limit=limit, offset=offset)

    result = await db.execute(query)
    grades = result.scalars().all()
    return [
        EvaluationGradeOut(
            id=g.id,
            evaluation_id=g.evaluation_id,
            enrollment_id=g.enrollment_id,
            grade=g.grade,
        )
        for g in grades
    ]


async def create_subject(db: AsyncSession, payload: SubjectCreate, current_user: User) -> SubjectOut:
    if not _is_admin(current_user):
        raise ForbiddenException("Solo un admin puede crear materias")

    existing = await db.execute(select(Subject).where(Subject.code == payload.code))
    if existing.scalar_one_or_none() is not None:
        raise ConflictException("Ya existe una materia con ese codigo")

    subject = Subject(code=payload.code, name=payload.name, credits=payload.credits)
    db.add(subject)
    await db.commit()
    await db.refresh(subject)

    return SubjectOut(id=subject.id, code=subject.code, name=subject.name, credits=subject.credits)


async def create_course(db: AsyncSession, payload: CourseCreate, current_user: User) -> CourseOut:
    subject_result = await db.execute(select(Subject).where(Subject.id == payload.subject_id))
    subject = subject_result.scalar_one_or_none()
    if subject is None:
        raise NotFoundException("Materia no encontrada")

    if _is_admin(current_user) and payload.professor_id is not None:
        professor_id = payload.professor_id
        professor_result = await db.execute(select(User).where(User.id == professor_id))
        professor = professor_result.scalar_one_or_none()
        if professor is None:
            raise NotFoundException("Profesor no encontrado")
        if professor.role != "professor":
            raise BadRequestException("El usuario indicado no tiene rol professor")
    else:
        professor_id = current_user.id

    course = Course(
        subject_id=payload.subject_id,
        professor_id=professor_id,
        term=payload.term,
        year=payload.year,
    )
    db.add(course)
    await db.commit()
    await db.refresh(course)

    return CourseOut(
        id=course.id,
        subject_id=course.subject_id,
        professor_id=course.professor_id,
        term=course.term,
        year=course.year,
    )


async def create_student(db: AsyncSession, payload: StudentCreate, current_user: User) -> StudentOut:
    if not _is_admin(current_user):
        raise ForbiddenException("Solo un admin puede crear estudiantes")

    existing_student_card = await db.execute(select(Student).where(Student.student_card == payload.student_card))
    if existing_student_card.scalar_one_or_none() is not None:
        raise ConflictException("Ya existe un estudiante con ese carnet")

    default_email = f"{payload.student_card}@usb.ve"
    student_email = payload.email or default_email

    existing_email = await db.execute(select(Student).where(Student.email == student_email))
    if existing_email.scalar_one_or_none() is not None:
        raise ConflictException("Ya existe un estudiante con ese correo")

    student = Student(full_name=payload.full_name, student_card=payload.student_card, email=student_email)
    db.add(student)
    await db.commit()
    await db.refresh(student)

    return StudentOut(
        id=student.id,
        full_name=student.full_name,
        student_card=student.student_card,
        email=student.email,
    )


async def create_evaluation(db: AsyncSession, payload: EvaluationCreate, current_user: User) -> EvaluationOut:
    course_result = await db.execute(select(Course).where(Course.id == payload.course_id))
    course = course_result.scalar_one_or_none()
    if course is None:
        raise NotFoundException("Curso no encontrado")

    if not _is_admin(current_user) and course.professor_id != current_user.id:
        raise ForbiddenException("No tienes permiso para crear evaluaciones en este curso")

    evaluation = Evaluation(
        course_id=payload.course_id,
        description=payload.description,
        percentage=payload.percentage,
        evaluation_type=payload.evaluation_type,
        due_date=payload.due_date,
    )
    db.add(evaluation)
    await db.commit()
    await db.refresh(evaluation)

    return EvaluationOut(
        id=evaluation.id,
        course_id=evaluation.course_id,
        description=evaluation.description,
        percentage=evaluation.percentage,
        evaluation_type=evaluation.evaluation_type,
        due_date=evaluation.due_date,
    )


async def create_enrollment(db: AsyncSession, payload: EnrollmentCreate, current_user: User) -> EnrollmentOut:
    course_result = await db.execute(select(Course).where(Course.id == payload.course_id))
    course = course_result.scalar_one_or_none()
    if course is None:
        raise NotFoundException("Curso no encontrado")

    if not _is_admin(current_user) and course.professor_id != current_user.id:
        raise ForbiddenException("No tienes permiso para inscribir estudiantes en este curso")

    student_result = await db.execute(select(Student).where(Student.id == payload.student_id))
    student = student_result.scalar_one_or_none()
    if student is None:
        raise NotFoundException("Estudiante no encontrado")

    existing = await db.execute(
        select(Enrollment).where(
            Enrollment.course_id == payload.course_id,
            Enrollment.student_id == payload.student_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictException("El estudiante ya esta inscrito en este curso")

    enrollment = Enrollment(course_id=payload.course_id, student_id=payload.student_id)
    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)

    return EnrollmentOut(
        id=enrollment.id,
        course_id=enrollment.course_id,
        student_id=enrollment.student_id,
        final_grade=enrollment.final_grade,
    )


async def create_evaluation_grade(db: AsyncSession, payload: EvaluationGradeCreate, current_user: User) -> EvaluationGradeOut:
    evaluation_result = await db.execute(select(Evaluation).where(Evaluation.id == payload.evaluation_id))
    evaluation = evaluation_result.scalar_one_or_none()
    if evaluation is None:
        raise NotFoundException("Evaluacion no encontrada")

    enrollment_result = await db.execute(select(Enrollment).where(Enrollment.id == payload.enrollment_id))
    enrollment = enrollment_result.scalar_one_or_none()
    if enrollment is None:
        raise NotFoundException("Inscripcion no encontrada")

    course_result = await db.execute(select(Course).where(Course.id == evaluation.course_id))
    course = course_result.scalar_one_or_none()
    if not _is_admin(current_user) and (course is None or course.professor_id != current_user.id):
        raise ForbiddenException("No tienes permiso para registrar notas en este curso")

    if enrollment.course_id != evaluation.course_id:
        raise BadRequestException("La evaluacion y la inscripcion deben pertenecer al mismo curso")

    if payload.grade > evaluation.percentage:
        raise BadRequestException("La nota no puede ser mayor que el porcentaje de la evaluacion")

    existing = await db.execute(
        select(EvaluationGrade).where(
            EvaluationGrade.evaluation_id == payload.evaluation_id,
            EvaluationGrade.enrollment_id == payload.enrollment_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictException("Ya existe una nota para esta evaluacion e inscripcion")

    evaluation_grade = EvaluationGrade(
        evaluation_id=payload.evaluation_id,
        enrollment_id=payload.enrollment_id,
        grade=payload.grade,
    )
    db.add(evaluation_grade)
    await db.commit()
    await db.refresh(evaluation_grade)

    return EvaluationGradeOut(
        id=evaluation_grade.id,
        evaluation_id=evaluation_grade.evaluation_id,
        enrollment_id=evaluation_grade.enrollment_id,
        grade=evaluation_grade.grade,
    )


async def bulk_enroll_students_csv(
    db: AsyncSession,
    current_user: User,
    course_id: uuid.UUID,
    file: UploadFile,
) -> BulkEnrollmentResult:
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    course = course_result.scalar_one_or_none()
    if course is None:
        raise NotFoundException("Curso no encontrado")

    if not _is_admin(current_user) and course.professor_id != current_user.id:
        raise ForbiddenException("Solo el profesor encargado o un admin puede hacer carga masiva en este curso")

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise BadRequestException("El archivo debe ser CSV")

    raw = await file.read()
    try:
        decoded = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise BadRequestException("No se pudo leer el CSV en UTF-8") from exc

    reader = csv.DictReader(io.StringIO(decoded))
    if reader.fieldnames is None:
        raise BadRequestException("CSV sin encabezados")

    normalized_headers = {h.strip().lower(): h for h in reader.fieldnames if h}
    student_card_header = normalized_headers.get("carnet") or normalized_headers.get("student_card")
    full_name_header = normalized_headers.get("nombre") or normalized_headers.get("full_name") or normalized_headers.get("name")

    if not student_card_header or not full_name_header:
        raise BadRequestException("CSV invalido: requiere columnas carnet y nombre")

    rows_total = 0
    students_created = 0
    students_existing = 0
    enrollments_created = 0
    enrollments_existing = 0
    errors: list[BulkEnrollmentRowError] = []

    line_number = 1
    for row in reader:
        line_number += 1
        rows_total += 1

        student_card = (row.get(student_card_header) or "").strip()
        full_name = (row.get(full_name_header) or "").strip()

        if not student_card or not full_name:
            errors.append(
                BulkEnrollmentRowError(
                    line=line_number,
                    student_card=student_card or None,
                    detail="Fila invalida: carnet y nombre son obligatorios",
                )
            )
            continue

        student_result = await db.execute(select(Student).where(Student.student_card == student_card))
        student = student_result.scalar_one_or_none()

        if student is None:
            student = Student(
                full_name=full_name,
                student_card=student_card,
                email=f"{student_card}@usb.ve",
            )
            db.add(student)
            await db.flush()
            students_created += 1
        else:
            students_existing += 1

        enrollment_result = await db.execute(
            select(Enrollment).where(Enrollment.course_id == course.id, Enrollment.student_id == student.id)
        )
        enrollment = enrollment_result.scalar_one_or_none()

        if enrollment is None:
            db.add(Enrollment(course_id=course.id, student_id=student.id))
            enrollments_created += 1
        else:
            enrollments_existing += 1

    await db.commit()

    return BulkEnrollmentResult(
        course_id=course.id,
        rows_total=rows_total,
        students_created=students_created,
        students_existing=students_existing,
        enrollments_created=enrollments_created,
        enrollments_existing=enrollments_existing,
        errors=errors,
    )


async def update_subject(
    db: AsyncSession,
    subject_id: uuid.UUID,
    payload: SubjectUpdate,
    current_user: User,
) -> SubjectOut:
    subject_result = await db.execute(select(Subject).where(Subject.id == subject_id))
    subject = subject_result.scalar_one_or_none()
    if subject is None:
        raise NotFoundException("Materia no encontrada")

    if not _is_admin(current_user):
        raise ForbiddenException("Solo un admin puede actualizar materias")

    existing_code = await db.execute(select(Subject).where(Subject.code == payload.code, Subject.id != subject_id))
    if existing_code.scalar_one_or_none() is not None:
        raise ConflictException("Ya existe una materia con ese codigo")

    subject.code = payload.code
    subject.name = payload.name
    subject.credits = payload.credits

    db.add(subject)
    await db.commit()
    await db.refresh(subject)

    return SubjectOut(id=subject.id, code=subject.code, name=subject.name, credits=subject.credits)


async def update_course(
    db: AsyncSession,
    current_user: User,
    course_id: uuid.UUID,
    payload: CourseUpdate,
) -> CourseOut:
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    course = course_result.scalar_one_or_none()
    if course is None:
        raise NotFoundException("Curso no encontrado")

    if not _is_admin(current_user) and course.professor_id != current_user.id:
        raise ForbiddenException("No tienes permiso para actualizar este curso")

    subject_result = await db.execute(select(Subject).where(Subject.id == payload.subject_id))
    if subject_result.scalar_one_or_none() is None:
        raise NotFoundException("Materia no encontrada")

    professor_result = await db.execute(select(User).where(User.id == payload.professor_id))
    professor = professor_result.scalar_one_or_none()
    if professor is None:
        raise NotFoundException("Profesor no encontrado")
    if professor.role != "professor":
        raise BadRequestException("El usuario indicado no tiene rol professor")

    if not _is_admin(current_user) and payload.professor_id != current_user.id:
        raise ForbiddenException("No puedes reasignar cursos a otro profesor")

    course.subject_id = payload.subject_id
    course.professor_id = payload.professor_id
    course.term = payload.term
    course.year = payload.year

    db.add(course)
    await db.commit()
    await db.refresh(course)

    return CourseOut(
        id=course.id,
        subject_id=course.subject_id,
        professor_id=course.professor_id,
        term=course.term,
        year=course.year,
    )


async def update_student(
    db: AsyncSession,
    student_id: uuid.UUID,
    payload: StudentUpdate,
    current_user: User,
) -> StudentOut:
    student_result = await db.execute(select(Student).where(Student.id == student_id))
    student = student_result.scalar_one_or_none()
    if student is None:
        raise NotFoundException("Estudiante no encontrado")

    if not _is_admin(current_user):
        raise ForbiddenException("Solo un admin puede actualizar estudiantes")

    target_email = payload.email or f"{payload.student_card}@usb.ve"

    existing_card = await db.execute(
        select(Student).where(Student.student_card == payload.student_card, Student.id != student_id)
    )
    if existing_card.scalar_one_or_none() is not None:
        raise ConflictException("Ya existe un estudiante con ese carnet")

    existing_email = await db.execute(select(Student).where(Student.email == target_email, Student.id != student_id))
    if existing_email.scalar_one_or_none() is not None:
        raise ConflictException("Ya existe un estudiante con ese correo")

    student.full_name = payload.full_name
    student.student_card = payload.student_card
    student.email = target_email

    db.add(student)
    await db.commit()
    await db.refresh(student)

    return StudentOut(
        id=student.id,
        full_name=student.full_name,
        student_card=student.student_card,
        email=student.email,
    )


async def update_evaluation(
    db: AsyncSession,
    current_user: User,
    evaluation_id: uuid.UUID,
    payload: EvaluationUpdate,
) -> EvaluationOut:
    evaluation_result = await db.execute(select(Evaluation).where(Evaluation.id == evaluation_id))
    evaluation = evaluation_result.scalar_one_or_none()
    if evaluation is None:
        raise NotFoundException("Evaluacion no encontrada")

    current_course_result = await db.execute(select(Course).where(Course.id == evaluation.course_id))
    current_course = current_course_result.scalar_one_or_none()
    if current_course is None:
        raise NotFoundException("Curso no encontrado")

    if not _is_admin(current_user) and current_course.professor_id != current_user.id:
        raise ForbiddenException("No tienes permiso para actualizar esta evaluacion")

    new_course_result = await db.execute(select(Course).where(Course.id == payload.course_id))
    new_course = new_course_result.scalar_one_or_none()
    if new_course is None:
        raise NotFoundException("Curso no encontrado")

    if not _is_admin(current_user) and new_course.professor_id != current_user.id:
        raise ForbiddenException("No puedes mover la evaluacion a un curso ajeno")

    evaluation.course_id = payload.course_id
    evaluation.description = payload.description
    evaluation.percentage = payload.percentage
    evaluation.evaluation_type = payload.evaluation_type
    evaluation.due_date = payload.due_date

    db.add(evaluation)
    await db.commit()
    await db.refresh(evaluation)

    return EvaluationOut(
        id=evaluation.id,
        course_id=evaluation.course_id,
        description=evaluation.description,
        percentage=evaluation.percentage,
        evaluation_type=evaluation.evaluation_type,
        due_date=evaluation.due_date,
    )


async def update_enrollment(
    db: AsyncSession,
    current_user: User,
    enrollment_id: uuid.UUID,
    payload: EnrollmentUpdate,
) -> EnrollmentOut:
    enrollment_result = await db.execute(select(Enrollment).where(Enrollment.id == enrollment_id))
    enrollment = enrollment_result.scalar_one_or_none()
    if enrollment is None:
        raise NotFoundException("Inscripcion no encontrada")

    current_course_result = await db.execute(select(Course).where(Course.id == enrollment.course_id))
    current_course = current_course_result.scalar_one_or_none()
    if current_course is None:
        raise NotFoundException("Curso no encontrado")

    if not _is_admin(current_user) and current_course.professor_id != current_user.id:
        raise ForbiddenException("No tienes permiso para actualizar esta inscripcion")

    new_course_result = await db.execute(select(Course).where(Course.id == payload.course_id))
    new_course = new_course_result.scalar_one_or_none()
    if new_course is None:
        raise NotFoundException("Curso no encontrado")

    student_result = await db.execute(select(Student).where(Student.id == payload.student_id))
    if student_result.scalar_one_or_none() is None:
        raise NotFoundException("Estudiante no encontrado")

    if not _is_admin(current_user) and new_course.professor_id != current_user.id:
        raise ForbiddenException("No puedes mover la inscripcion a un curso ajeno")

    duplicate = await db.execute(
        select(Enrollment).where(
            Enrollment.course_id == payload.course_id,
            Enrollment.student_id == payload.student_id,
            Enrollment.id != enrollment_id,
        )
    )
    if duplicate.scalar_one_or_none() is not None:
        raise ConflictException("Ya existe esa inscripcion curso-estudiante")

    enrollment.course_id = payload.course_id
    enrollment.student_id = payload.student_id
    enrollment.final_grade = payload.final_grade

    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)

    return EnrollmentOut(
        id=enrollment.id,
        course_id=enrollment.course_id,
        student_id=enrollment.student_id,
        final_grade=enrollment.final_grade,
    )


async def update_evaluation_grade(
    db: AsyncSession,
    current_user: User,
    evaluation_grade_id: uuid.UUID,
    payload: EvaluationGradeUpdate,
) -> EvaluationGradeOut:
    evaluation_grade_result = await db.execute(select(EvaluationGrade).where(EvaluationGrade.id == evaluation_grade_id))
    evaluation_grade = evaluation_grade_result.scalar_one_or_none()
    if evaluation_grade is None:
        raise NotFoundException("Nota de evaluacion no encontrada")

    current_evaluation_result = await db.execute(select(Evaluation).where(Evaluation.id == evaluation_grade.evaluation_id))
    current_evaluation = current_evaluation_result.scalar_one_or_none()
    if current_evaluation is None:
        raise NotFoundException("Evaluacion no encontrada")

    current_course_result = await db.execute(select(Course).where(Course.id == current_evaluation.course_id))
    current_course = current_course_result.scalar_one_or_none()
    if current_course is None:
        raise NotFoundException("Curso no encontrado")

    if not _is_admin(current_user) and current_course.professor_id != current_user.id:
        raise ForbiddenException("No tienes permiso para actualizar esta nota")

    evaluation_result = await db.execute(select(Evaluation).where(Evaluation.id == payload.evaluation_id))
    evaluation = evaluation_result.scalar_one_or_none()
    if evaluation is None:
        raise NotFoundException("Evaluacion no encontrada")

    enrollment_result = await db.execute(select(Enrollment).where(Enrollment.id == payload.enrollment_id))
    enrollment = enrollment_result.scalar_one_or_none()
    if enrollment is None:
        raise NotFoundException("Inscripcion no encontrada")

    if enrollment.course_id != evaluation.course_id:
        raise BadRequestException("La evaluacion y la inscripcion deben pertenecer al mismo curso")

    destination_course_result = await db.execute(select(Course).where(Course.id == evaluation.course_id))
    destination_course = destination_course_result.scalar_one_or_none()
    if destination_course is None:
        raise NotFoundException("Curso no encontrado")

    if not _is_admin(current_user) and destination_course.professor_id != current_user.id:
        raise ForbiddenException("No puedes mover la nota a un curso ajeno")

    if payload.grade > evaluation.percentage:
        raise BadRequestException("La nota no puede ser mayor que el porcentaje de la evaluacion")

    duplicate = await db.execute(
        select(EvaluationGrade).where(
            EvaluationGrade.evaluation_id == payload.evaluation_id,
            EvaluationGrade.enrollment_id == payload.enrollment_id,
            EvaluationGrade.id != evaluation_grade_id,
        )
    )
    if duplicate.scalar_one_or_none() is not None:
        raise ConflictException("Ya existe una nota para esta evaluacion e inscripcion")

    evaluation_grade.evaluation_id = payload.evaluation_id
    evaluation_grade.enrollment_id = payload.enrollment_id
    evaluation_grade.grade = payload.grade

    db.add(evaluation_grade)
    await db.commit()
    await db.refresh(evaluation_grade)

    return EvaluationGradeOut(
        id=evaluation_grade.id,
        evaluation_id=evaluation_grade.evaluation_id,
        enrollment_id=evaluation_grade.enrollment_id,
        grade=evaluation_grade.grade,
    )
