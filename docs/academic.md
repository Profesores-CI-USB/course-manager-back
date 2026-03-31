# Academic — Materias, Cursos, Estudiantes, Evaluaciones, Inscripciones y Notas

Prefijo: `/api/v1/academic`

Todos los endpoints requieren autenticación. La visibilidad está restringida por rol:
- **Admin**: ve y edita todos los recursos.
- **Professor**: ve y edita solo los recursos asociados a sus propios cursos.

---

## MATERIAS (Subjects)

### GET /api/v1/academic/subjects

Lista las materias. Los profesores solo ven materias de cursos que les fueron asignados.

**Auth:** Bearer token — cualquier rol

**Query params:**

| Param | Tipo | Por defecto | Descripción |
|---|---|---|---|
| `code` | string | — | Filtro parcial por código (case-insensitive) |
| `name` | string | — | Filtro parcial por nombre (case-insensitive) |
| `limit` | int (1–200) | 50 | Máximo de resultados |
| `offset` | int (≥0) | 0 | Desplazamiento para paginación |
| `order_by` | `code` \| `name` \| `credits` | `code` | Campo de ordenamiento |
| `order_dir` | `asc` \| `desc` | `asc` | Dirección |

**Respuesta 200:**
```json
[
  {
    "id": "a1b2c3d4-0000-0000-0000-000000000001",
    "code": "CI3641",
    "name": "Lenguajes de Programación",
    "credits": 4
  },
  {
    "id": "a1b2c3d4-0000-0000-0000-000000000002",
    "code": "MA1111",
    "name": "Cálculo I",
    "credits": 4
  }
]
```

---

### POST /api/v1/academic/subjects

Crea una nueva materia.

**Auth:** Bearer token — solo `admin`

**Body:**
```json
{
  "code": "CI3641",
  "name": "Lenguajes de Programación",
  "credits": 4
}
```

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `code` | string | Sí | Código único de la materia |
| `name` | string | Sí | Nombre descriptivo |
| `credits` | int | Sí | Unidades de crédito |

**Respuesta 201:**
```json
{
  "id": "a1b2c3d4-0000-0000-0000-000000000001",
  "code": "CI3641",
  "name": "Lenguajes de Programación",
  "credits": 4
}
```

**Errores:**
| Código | Causa | Ejemplo |
|---|---|---|
| `403` | No es admin | `{"detail": "Solo un admin puede crear materias"}` |
| `409` | Código duplicado | `{"detail": "Ya existe una materia con ese codigo"}` |

---

### PUT /api/v1/academic/subjects/{subject_id}

Actualiza una materia existente.

**Auth:** Bearer token — solo `admin`

**Path:** `subject_id` (UUID)

**Body:**
```json
{
  "code": "CI3641",
  "name": "Lenguajes de Programación II",
  "credits": 3
}
```

**Respuesta 200:**
```json
{
  "id": "a1b2c3d4-0000-0000-0000-000000000001",
  "code": "CI3641",
  "name": "Lenguajes de Programación II",
  "credits": 3
}
```

**Errores:**
| Código | Causa | Ejemplo |
|---|---|---|
| `403` | No es admin | `{"detail": "Solo un admin puede actualizar materias"}` |
| `404` | Materia no encontrada | `{"detail": "Materia no encontrada"}` |
| `409` | Código ya usado por otra materia | `{"detail": "Ya existe una materia con ese codigo"}` |

---

## CURSOS (Courses)

### GET /api/v1/academic/courses

Lista los cursos. Los profesores solo ven sus propios cursos.

**Auth:** Bearer token — cualquier rol

**Query params:**

| Param | Tipo | Por defecto | Descripción |
|---|---|---|---|
| `subject_id` | UUID | — | Filtrar por materia |
| `term` | string | — | Filtrar por período (`april-july`, `january-march`, `september-december`, `summer`) |
| `year` | int | — | Filtrar por año |
| `professor_id` | UUID | — | Filtrar por profesor (solo admin puede usar este filtro) |
| `limit` | int (1–200) | 50 | Máximo de resultados |
| `offset` | int (≥0) | 0 | Desplazamiento |
| `order_by` | `year` \| `term` \| `subject_id` \| `professor_id` | `year` | Campo de ordenamiento |
| `order_dir` | `asc` \| `desc` | `desc` | Dirección |

**Respuesta 200:**
```json
[
  {
    "id": "b2c3d4e5-0000-0000-0000-000000000001",
    "subject_id": "a1b2c3d4-0000-0000-0000-000000000001",
    "professor_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "term": "april-july",
    "year": 2026
  }
]
```

---

### POST /api/v1/academic/courses

Crea un nuevo curso. El usuario autenticado queda asignado como profesor. Un admin puede asignar explícitamente otro profesor.

**Auth:** Bearer token — cualquier rol

**Body (usuario regular):**
```json
{
  "subject_id": "a1b2c3d4-0000-0000-0000-000000000001",
  "term": "april-july",
  "year": 2026
}
```

**Body (admin asignando a otro profesor):**
```json
{
  "subject_id": "a1b2c3d4-0000-0000-0000-000000000001",
  "professor_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "term": "april-july",
  "year": 2026
}
```

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `subject_id` | UUID | Sí | Materia del curso |
| `professor_id` | UUID | No | Solo lo considera el admin; si se omite o no es admin, se usa `current_user.id` |
| `term` | string | Sí | `april-july`, `january-march`, `september-december` o `summer` |
| `year` | int | Sí | Año del curso |

**Respuesta 201:**
```json
{
  "id": "b2c3d4e5-0000-0000-0000-000000000001",
  "subject_id": "a1b2c3d4-0000-0000-0000-000000000001",
  "professor_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "term": "april-july",
  "year": 2026
}
```

**Errores:**
| Código | Causa | Ejemplo |
|---|---|---|
| `404` | Materia no encontrada | `{"detail": "Materia no encontrada"}` |
| `404` | Profesor no encontrado (admin) | `{"detail": "Profesor no encontrado"}` |
| `400` | Usuario indicado no tiene rol professor (admin) | `{"detail": "El usuario indicado no tiene rol professor"}` |

---

### PUT /api/v1/academic/courses/{course_id}

Actualiza un curso. Los profesores solo pueden actualizar sus propios cursos y no pueden reasignarlos a otro profesor.

**Auth:** Bearer token — cualquier rol (con restricciones)

**Path:** `course_id` (UUID)

**Body:**
```json
{
  "subject_id": "a1b2c3d4-0000-0000-0000-000000000001",
  "professor_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "term": "september-december",
  "year": 2026
}
```

**Respuesta 200:** mismo formato que la respuesta de creación.

**Errores:**
| Código | Causa | Ejemplo |
|---|---|---|
| `403` | No es el profesor del curso | `{"detail": "No tienes permiso para actualizar este curso"}` |
| `403` | Profesor intenta reasignar el curso a otro | `{"detail": "No puedes reasignar cursos a otro profesor"}` |
| `404` | Curso, materia o profesor no encontrado | `{"detail": "Curso no encontrado"}` |
| `400` | El usuario indicado no tiene rol professor | `{"detail": "El usuario indicado no tiene rol professor"}` |

---

## ESTUDIANTES (Students)

### GET /api/v1/academic/students

Lista estudiantes. Los profesores solo ven estudiantes inscritos en sus cursos.

**Auth:** Bearer token — cualquier rol

**Query params:**

| Param | Tipo | Por defecto | Descripción |
|---|---|---|---|
| `course_id` | UUID | — | Filtrar por curso |
| `student_card` | string | — | Filtro parcial por carnet |
| `email` | string | — | Filtro parcial por correo |
| `full_name` | string | — | Filtro parcial por nombre |
| `limit` | int (1–200) | 50 | Máximo de resultados |
| `offset` | int (≥0) | 0 | Desplazamiento |
| `order_by` | `full_name` \| `student_card` \| `email` | `full_name` | Campo de ordenamiento |
| `order_dir` | `asc` \| `desc` | `asc` | Dirección |

**Respuesta 200:**
```json
[
  {
    "id": "c3d4e5f6-0000-0000-0000-000000000001",
    "full_name": "Carlos Pérez",
    "student_card": "16-10123",
    "email": "16-10123@usb.ve"
  }
]
```

---

### POST /api/v1/academic/students

Crea un nuevo estudiante. Si no se provee email, se genera automáticamente como `{carnet}@usb.ve`.

**Auth:** Bearer token — solo `admin`

**Body:**
```json
{
  "full_name": "Carlos Pérez",
  "student_card": "16-10123",
  "email": "carlos.perez@gmail.com"
}
```

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `full_name` | string | Sí | Nombre completo |
| `student_card` | string | Sí | Carnet único (e.g. `16-10123`) |
| `email` | string (email) | No | Si se omite se usa `{carnet}@usb.ve` |

**Respuesta 201:**
```json
{
  "id": "c3d4e5f6-0000-0000-0000-000000000001",
  "full_name": "Carlos Pérez",
  "student_card": "16-10123",
  "email": "carlos.perez@gmail.com"
}
```

**Errores:**
| Código | Causa | Ejemplo |
|---|---|---|
| `403` | No es admin | `{"detail": "Solo un admin puede crear estudiantes"}` |
| `409` | Carnet duplicado | `{"detail": "Ya existe un estudiante con ese carnet"}` |
| `409` | Email duplicado | `{"detail": "Ya existe un estudiante con ese correo"}` |

---

### PUT /api/v1/academic/students/{student_id}

Actualiza un estudiante existente.

**Auth:** Bearer token — solo `admin`

**Path:** `student_id` (UUID)

**Body:**
```json
{
  "full_name": "Carlos Andrés Pérez",
  "student_card": "16-10123",
  "email": "carlos.perez@usb.ve"
}
```

**Respuesta 200:** mismo formato que la respuesta de creación.

**Errores:**
| Código | Causa | Ejemplo |
|---|---|---|
| `403` | No es admin | `{"detail": "Solo un admin puede actualizar estudiantes"}` |
| `404` | Estudiante no encontrado | `{"detail": "Estudiante no encontrado"}` |
| `409` | Carnet o email ya en uso por otro estudiante | `{"detail": "Ya existe un estudiante con ese carnet"}` |

---

## EVALUACIONES (Evaluations)

### GET /api/v1/academic/evaluations

Lista evaluaciones. Los profesores solo ven evaluaciones de sus cursos.

**Auth:** Bearer token — cualquier rol

**Query params:**

| Param | Tipo | Por defecto | Descripción |
|---|---|---|---|
| `course_id` | UUID | — | Filtrar por curso |
| `evaluation_type` | string | — | Filtrar por tipo |
| `due_date_from` | date (ISO) | — | Filtrar desde fecha de entrega |
| `due_date_to` | date (ISO) | — | Filtrar hasta fecha de entrega |
| `limit` | int (1–200) | 50 | Máximo de resultados |
| `offset` | int (≥0) | 0 | Desplazamiento |
| `order_by` | `due_date` \| `percentage` \| `evaluation_type` | `due_date` | Campo de ordenamiento |
| `order_dir` | `asc` \| `desc` | `desc` | Dirección |

**Respuesta 200:**
```json
[
  {
    "id": "d4e5f6a7-0000-0000-0000-000000000001",
    "course_id": "b2c3d4e5-0000-0000-0000-000000000001",
    "description": "Examen parcial 1",
    "percentage": "30.00",
    "evaluation_type": "exam",
    "due_date": "2026-05-15"
  }
]
```

---

### POST /api/v1/academic/evaluations

Crea una evaluación en un curso.

**Auth:** Bearer token — admin o profesor dueño del curso

**Body:**
```json
{
  "course_id": "b2c3d4e5-0000-0000-0000-000000000001",
  "description": "Examen parcial 1",
  "percentage": 30.00,
  "evaluation_type": "exam",
  "due_date": "2026-05-15"
}
```

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `course_id` | UUID | Sí | Curso al que pertenece |
| `description` | string | Sí | Descripción de la evaluación |
| `percentage` | decimal (0–100) | Sí | Peso en la nota final |
| `evaluation_type` | string | Sí | `exam`, `homework`, `workshop`, `project`, `report`, `presentation`, `video` |
| `due_date` | date (ISO) | Sí | Fecha de entrega/realización |

**Respuesta 201:** mismo formato que la respuesta de listado.

**Errores:**
| Código | Causa | Ejemplo |
|---|---|---|
| `403` | No es admin ni profesor del curso | `{"detail": "No tienes permiso para crear evaluaciones en este curso"}` |
| `404` | Curso no encontrado | `{"detail": "Curso no encontrado"}` |

---

### PUT /api/v1/academic/evaluations/{evaluation_id}

Actualiza una evaluación. Los profesores solo pueden modificar evaluaciones de sus cursos y no pueden moverlas a cursos ajenos.

**Auth:** Bearer token — admin o profesor dueño del curso

**Path:** `evaluation_id` (UUID)

**Body:** mismo esquema que creación.

**Respuesta 200:** mismo formato que listado.

**Errores:**
| Código | Causa | Ejemplo |
|---|---|---|
| `403` | Sin permiso sobre la evaluación o el curso destino | `{"detail": "No tienes permiso para actualizar esta evaluacion"}` |
| `404` | Evaluación o curso no encontrado | `{"detail": "Evaluacion no encontrada"}` |

---

## INSCRIPCIONES (Enrollments)

### GET /api/v1/academic/enrollments

Lista inscripciones. Los profesores solo ven inscripciones de sus cursos.

**Auth:** Bearer token — cualquier rol

**Query params:**

| Param | Tipo | Por defecto | Descripción |
|---|---|---|---|
| `course_id` | UUID | — | Filtrar por curso |
| `student_id` | UUID | — | Filtrar por estudiante |
| `limit` | int (1–200) | 50 | Máximo de resultados |
| `offset` | int (≥0) | 0 | Desplazamiento |
| `order_by` | `id` \| `final_grade` | `id` | Campo de ordenamiento |
| `order_dir` | `asc` \| `desc` | `asc` | Dirección |

**Respuesta 200:**
```json
[
  {
    "id": "e5f6a7b8-0000-0000-0000-000000000001",
    "course_id": "b2c3d4e5-0000-0000-0000-000000000001",
    "student_id": "c3d4e5f6-0000-0000-0000-000000000001",
    "final_grade": null
  }
]
```

---

### POST /api/v1/academic/enrollments

Inscribe un estudiante en un curso.

**Auth:** Bearer token — admin o profesor dueño del curso

**Body:**
```json
{
  "course_id": "b2c3d4e5-0000-0000-0000-000000000001",
  "student_id": "c3d4e5f6-0000-0000-0000-000000000001"
}
```

**Respuesta 201:**
```json
{
  "id": "e5f6a7b8-0000-0000-0000-000000000001",
  "course_id": "b2c3d4e5-0000-0000-0000-000000000001",
  "student_id": "c3d4e5f6-0000-0000-0000-000000000001",
  "final_grade": null
}
```

**Errores:**
| Código | Causa | Ejemplo |
|---|---|---|
| `403` | Sin permiso sobre el curso | `{"detail": "No tienes permiso para inscribir estudiantes en este curso"}` |
| `404` | Curso o estudiante no encontrado | `{"detail": "Curso no encontrado"}` |
| `409` | El estudiante ya está inscrito | `{"detail": "El estudiante ya esta inscrito en este curso"}` |

---

### POST /api/v1/academic/enrollments/bulk-csv

Inscripción masiva de estudiantes desde un archivo CSV. Crea estudiantes que no existan. Omite inscripciones duplicadas silenciosamente.

**Auth:** Bearer token — admin o profesor dueño del curso

**Content-Type:** `multipart/form-data`

**Form fields:**

| Campo | Tipo | Descripción |
|---|---|---|
| `course_id` | UUID | Curso donde inscribir |
| `file` | archivo `.csv` | CSV con columnas `carnet` (o `student_card`) y `nombre` (o `full_name` o `name`) |

**Formato CSV esperado:**
```
carnet,nombre
16-10123,Carlos Pérez
17-20456,María González
18-30789,Luis Rodríguez
```

**Respuesta 201:**
```json
{
  "course_id": "b2c3d4e5-0000-0000-0000-000000000001",
  "rows_total": 3,
  "students_created": 2,
  "students_existing": 1,
  "enrollments_created": 3,
  "enrollments_existing": 0,
  "errors": []
}
```

Con errores por fila:
```json
{
  "course_id": "b2c3d4e5-0000-0000-0000-000000000001",
  "rows_total": 3,
  "students_created": 2,
  "students_existing": 0,
  "enrollments_created": 2,
  "enrollments_existing": 0,
  "errors": [
    {
      "line": 3,
      "student_card": null,
      "detail": "Fila invalida: carnet y nombre son obligatorios"
    }
  ]
}
```

**Errores (globales, no por fila):**
| Código | Causa | Ejemplo |
|---|---|---|
| `403` | Sin permiso sobre el curso | `{"detail": "Solo el profesor encargado o un admin puede hacer carga masiva en este curso"}` |
| `404` | Curso no encontrado | `{"detail": "Curso no encontrado"}` |
| `400` | Archivo no es CSV | `{"detail": "El archivo debe ser CSV"}` |
| `400` | CSV no legible en UTF-8 | `{"detail": "No se pudo leer el CSV en UTF-8"}` |
| `400` | CSV sin encabezados o columnas requeridas ausentes | `{"detail": "CSV invalido: requiere columnas carnet y nombre"}` |

---

### PUT /api/v1/academic/enrollments/{enrollment_id}

Actualiza una inscripción (principalmente para registrar la nota final).

**Auth:** Bearer token — admin o profesor dueño del curso

**Path:** `enrollment_id` (UUID)

**Body:**
```json
{
  "course_id": "b2c3d4e5-0000-0000-0000-000000000001",
  "student_id": "c3d4e5f6-0000-0000-0000-000000000001",
  "final_grade": 85.50
}
```

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `course_id` | UUID | Sí | Curso de la inscripción |
| `student_id` | UUID | Sí | Estudiante |
| `final_grade` | decimal (0–100) | No | Nota final |

**Respuesta 200:**
```json
{
  "id": "e5f6a7b8-0000-0000-0000-000000000001",
  "course_id": "b2c3d4e5-0000-0000-0000-000000000001",
  "student_id": "c3d4e5f6-0000-0000-0000-000000000001",
  "final_grade": "85.50"
}
```

**Errores:**
| Código | Causa | Ejemplo |
|---|---|---|
| `403` | Sin permiso | `{"detail": "No tienes permiso para actualizar esta inscripcion"}` |
| `404` | Inscripción, curso o estudiante no encontrado | `{"detail": "Inscripcion no encontrada"}` |
| `409` | Ya existe esa combinación curso-estudiante | `{"detail": "Ya existe esa inscripcion curso-estudiante"}` |

---

## NOTAS DE EVALUACIÓN (Evaluation Grades)

### GET /api/v1/academic/evaluation-grades

Lista notas de evaluación. Los profesores solo ven notas de sus cursos.

**Auth:** Bearer token — cualquier rol

**Query params:**

| Param | Tipo | Por defecto | Descripción |
|---|---|---|---|
| `course_id` | UUID | — | Filtrar por curso |
| `evaluation_id` | UUID | — | Filtrar por evaluación |
| `enrollment_id` | UUID | — | Filtrar por inscripción |
| `student_id` | UUID | — | Filtrar por estudiante |
| `limit` | int (1–200) | 50 | Máximo de resultados |
| `offset` | int (≥0) | 0 | Desplazamiento |
| `order_by` | `id` \| `grade` | `id` | Campo de ordenamiento |
| `order_dir` | `asc` \| `desc` | `asc` | Dirección |

**Respuesta 200:**
```json
[
  {
    "id": "f6a7b8c9-0000-0000-0000-000000000001",
    "evaluation_id": "d4e5f6a7-0000-0000-0000-000000000001",
    "enrollment_id": "e5f6a7b8-0000-0000-0000-000000000001",
    "grade": "28.50"
  }
]
```

---

### POST /api/v1/academic/evaluation-grades

Registra la nota de un estudiante en una evaluación.

**Auth:** Bearer token — admin o profesor dueño del curso

**Restricciones de negocio:**
- La evaluación y la inscripción deben pertenecer al mismo curso.
- La nota no puede superar el porcentaje asignado a la evaluación.
- No puede haber dos notas para la misma evaluación e inscripción.

**Body:**
```json
{
  "evaluation_id": "d4e5f6a7-0000-0000-0000-000000000001",
  "enrollment_id": "e5f6a7b8-0000-0000-0000-000000000001",
  "grade": 28.50
}
```

**Respuesta 201:**
```json
{
  "id": "f6a7b8c9-0000-0000-0000-000000000001",
  "evaluation_id": "d4e5f6a7-0000-0000-0000-000000000001",
  "enrollment_id": "e5f6a7b8-0000-0000-0000-000000000001",
  "grade": "28.50"
}
```

**Errores:**
| Código | Causa | Ejemplo |
|---|---|---|
| `403` | Sin permiso sobre el curso | `{"detail": "No tienes permiso para registrar notas en este curso"}` |
| `404` | Evaluación o inscripción no encontrada | `{"detail": "Evaluacion no encontrada"}` |
| `400` | Evaluación e inscripción en cursos distintos | `{"detail": "La evaluacion y la inscripcion deben pertenecer al mismo curso"}` |
| `400` | Nota supera el porcentaje de la evaluación | `{"detail": "La nota no puede ser mayor que el porcentaje de la evaluacion"}` |
| `409` | Ya existe nota para esa evaluación e inscripción | `{"detail": "Ya existe una nota para esta evaluacion e inscripcion"}` |

---

### PUT /api/v1/academic/evaluation-grades/{evaluation_grade_id}

Actualiza una nota existente.

**Auth:** Bearer token — admin o profesor dueño del curso

**Path:** `evaluation_grade_id` (UUID)

**Body:** mismo esquema que creación.

**Respuesta 200:** mismo formato que listado.

**Errores:**
| Código | Causa | Ejemplo |
|---|---|---|
| `403` | Sin permiso sobre el curso actual o el destino | `{"detail": "No tienes permiso para actualizar esta nota"}` |
| `404` | Nota, evaluación, inscripción o curso no encontrado | `{"detail": "Nota de evaluacion no encontrada"}` |
| `400` | Nota supera el porcentaje | `{"detail": "La nota no puede ser mayor que el porcentaje de la evaluacion"}` |
| `409` | Duplicado en la combinación evaluación-inscripción | `{"detail": "Ya existe una nota para esta evaluacion e inscripcion"}` |
