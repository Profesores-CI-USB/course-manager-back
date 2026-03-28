# Course Manager Backend (FastAPI)

Backend para gestion academica con autenticacion JWT, Redis para sesiones de refresh, correo SMTP y endpoints de dominio academico.

## Stack

- FastAPI
- SQLAlchemy Async + PostgreSQL (Neon compatible)
- Alembic
- Redis
- JWT (`access` + `refresh`)
- SMTP global + credenciales SMTP por usuario

## Funcionalidades

- Autenticacion completa:
- registro publico de profesores
- registro de admins (solo por admin autenticado)
- login, refresh, logout
- recuperacion y cambio de clave
- Perfil de usuario y credenciales SMTP por usuario.
- Modulo academico:
- materias, cursos, estudiantes
- evaluaciones, inscripciones, notas por evaluacion
- listados con filtros, paginacion y ordenamiento
- actualizaciones por ID
- carga masiva CSV de estudiantes por `course_id`
- Endpoint base de IA (`/ai/predict`) con modelo de ejemplo.

## Arquitectura

Estructura principal:

```text
.
├── app/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── routers/
│   ├── schemas/
│   ├── services/
│   └── main_app.py
├── alembic/
├── scripts/
├── justfile
├── main.py
└── README.md
```

Notas:

- `app/routers/auth.py` y `app/routers/academic.py` estan en modo "thin router": exponen endpoints y delegan la logica de negocio a `app/services`.
- `app/main_app.py` incluye routers bajo `API_V1_PREFIX` (default: `/api/v1`), excepto `health`.
- Al iniciar, la app ejecuta `init_models()` (creacion de tablas en desarrollo) y valida conexion a Redis.

## Requisitos

- Python 3.11+
- Redis (local o remoto)
- PostgreSQL (local o Neon)

## Variables de entorno

Base recomendada: copia `.env.example` a `.env`.

### `.env` para desarrollo (Docker Compose)

Valores listos para usar con `docker-compose.yml` incluido en el repo:

```env
# App
PROJECT_NAME=Course Manager Backend
API_V1_PREFIX=/api/v1
FRONTEND_URL=http://localhost:5173

# Base de datos (coincide con docker-compose.yml)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/course_manager_db

# Redis (coincide con docker-compose.yml)
REDIS_URL=redis://localhost:6379/0

# JWT — genera un valor aleatorio seguro, p.ej.: openssl rand -hex 32
JWT_SECRET_KEY=dev_secret_cambia_esto
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=30

# SMTP global — en desarrollo puedes usar una cuenta de prueba o dejar vacío
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
MAIL_DEFAULT_SENDER=tu_correo@gmail.com
MAIL_DEFAULT_PASSWORD=tu_app_password

# Fernet key para cifrar credenciales SMTP por usuario
# Genera con: just generate-fernet-key
SMTP_CREDENTIALS_KEY=

# IA
AI_MODEL_NAME=simple_nn
```

### Sustituciones para produccion

| Variable | Desarrollo | Produccion |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/course_manager_db` | URL de Neon u otro Postgres gestionado (`postgres://...` tambien funciona, se reescribe automaticamente) |
| `REDIS_URL` | `redis://localhost:6379/0` | URL de Redis remoto (Upstash, Railway, etc.) |
| `JWT_SECRET_KEY` | cualquier string | valor aleatorio largo generado con `openssl rand -hex 32` |
| `FRONTEND_URL` | `http://localhost:5173` | URL publica del frontend (para CORS y links en emails) |
| `MAIL_DEFAULT_SENDER` / `MAIL_DEFAULT_PASSWORD` | cuenta de prueba | cuenta de produccion o relay SMTP dedicado |
| `SMTP_CREDENTIALS_KEY` | puede dejarse vacio | clave Fernet generada con `just generate-fernet-key` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | reducir segun politica de seguridad |

Importante sobre SMTP:

- En SMTP por usuario solo se configuran `smtp_email` y `smtp_password`.
- `host`, `port` y `use_tls` siempre se toman de la configuracion global (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USE_TLS`).

## Ejecucion local

1. Crear y activar entorno virtual.
2. Instalar dependencias.
3. Levantar Postgres y Redis (Docker recomendado).
4. Configurar `.env`.
5. Ejecutar API.

### Opcion recomendada: Docker Compose

El repo ahora incluye `docker-compose.yml` con:

- `postgres` en `localhost:5432`
- `redis` en `localhost:6379`

Levantar servicios:

```bash
docker compose up -d
```

Con `just`:

```bash
just infra-up
```

Ver estado:

```bash
docker compose ps
```

Detener servicios:

```bash
docker compose down
```

Con `just`:

```bash
just infra-down
```

Limpiar infraestructura de desarrollo (contenedores, red y volumenes del compose):

```bash
just infra-clean
```

Para usar esos contenedores en desarrollo, en `.env` usa los valores del bloque de desarrollo de la seccion "Variables de entorno" arriba (o el resumen):

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/course_manager_db
REDIS_URL=redis://localhost:6379/0
```

### Opcion alternativa: contenedores separados

Postgres:

```bash
docker run -d --name course-manager-postgres \
	-e POSTGRES_DB=postgres \
	-e POSTGRES_USER=postgres \
	-e POSTGRES_PASSWORD=postgres \
	-p 5432:5432 postgres:16-alpine
```

Redis:

```bash
docker run -d --name course-manager-redis -p 6379:6379 redis:7
```

Comandos:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Accesos:

- Health: `http://127.0.0.1:8000/health`
- Docs: `http://127.0.0.1:8000/docs`

## Comandos utiles (`justfile`)

- `just run`
- `just dev-setup`
- `just infra-up`
- `just infra-down`
- `just infra-clean`
- `just create-admin EMAIL PASSWORD [FULL_NAME]`
- `just migrate-up`
- `just migrate-down`
- `just migrate-create "mensaje"`
- `just migrate-create-empty "mensaje"`
- `just migrate-current`
- `just migrate-history`
- `just migrate-heads`
- `just migrate-status`
- `just migrate-stamp REVISION`
- `just migrate-stamp-head`
- `just migrate-create-safe "mensaje"`
- `just migrate-up-to REVISION`
- `just migrate-down-to REVISION`

## Migraciones (Alembic)

Flujo recomendado:

```bash
just migrate-create-safe "descripcion corta"
just migrate-up
```

Chequeo de estado:

```bash
just migrate-status
```

Resolver desalineacion tipica (`DuplicateTableError` por tablas ya existentes fuera de Alembic):

1. Confirmar estado con `just migrate-status`.
2. Si el esquema ya esta aplicado en DB, marcar revision sin ejecutar SQL con `just migrate-stamp REVISION` o `just migrate-stamp-head`.
3. Generar la siguiente migracion y aplicarla.

Regla para cambios `NOT NULL` en tablas con datos:

1. Agregar columna nullable.
2. Hacer backfill.
3. Cambiar a non-null.

## API

### Auth (`/api/v1/auth`)

- `POST /register`
- `POST /register-admin`
- `POST /login`
- `POST /refresh`
- `POST /logout`
- `POST /forgot-password`
- `POST /reset-password`
- `POST /change-password`

Reglas:

- `register` publico crea usuarios con rol `professor`.
- `register-admin` requiere usuario autenticado con rol `admin`.

### Users (`/api/v1/users`)

- `GET /me`
- `GET /me/smtp`
- `PUT /me/smtp`

### Mail (`/api/v1/mail`)

- `POST /send`

Comportamiento SMTP:

- Si el usuario tiene SMTP propio configurado, se usa ese usuario/password.
- Si no, se usa SMTP global (`MAIL_DEFAULT_SENDER`/`MAIL_DEFAULT_PASSWORD`).
- `SMTP_HOST`, `SMTP_PORT` y `SMTP_USE_TLS` siempre son globales.

### AI (`/api/v1/ai`)

- `POST /predict`

### Academic (`/api/v1/academic`)

Creacion:

- `POST /subjects`
- `POST /courses`
- `POST /students`
- `POST /evaluations`
- `POST /enrollments`
- `POST /evaluation-grades`
- `POST /enrollments/bulk-csv` (multipart form)

Lectura con filtros/paginacion/orden:

- `GET /subjects`
- `GET /courses`
- `GET /students`
- `GET /evaluations`
- `GET /enrollments`
- `GET /evaluation-grades`

Parametros comunes de listados:

- `limit` (1-200)
- `offset` (>= 0)
- `order_dir` (`asc` o `desc`)

`order_by` soportado por endpoint:

- `subjects`: `code`, `name`, `credits`
- `courses`: `year`, `term`, `subject_id`, `professor_id`
- `students`: `full_name`, `student_card`, `email`
- `evaluations`: `due_date`, `percentage`, `evaluation_type`
- `enrollments`: `id`, `final_grade`
- `evaluation-grades`: `id`, `grade`

Actualizacion por ID:

- `PUT /subjects/{subject_id}`
- `PUT /courses/{course_id}`
- `PUT /students/{student_id}`
- `PUT /evaluations/{evaluation_id}`
- `PUT /enrollments/{enrollment_id}`
- `PUT /evaluation-grades/{evaluation_grade_id}`

Reglas de negocio academicas:

- `subjects.code` unico.
- `students.student_card` unico.
- `students.email` unico. Si no se envia, se autogenera como `"{student_card}@usb.ve"`.
- En notas por evaluacion, `grade` no puede ser mayor a `evaluation.percentage`.
- En `evaluation_grades`, evaluacion e inscripcion deben pertenecer al mismo curso.

## RBAC academico

Visibilidad en listados:

- `admin`: ve todo.
- `professor`: ve solo data relacionada a sus cursos (cursos, evaluaciones, inscripciones, notas, estudiantes vinculados y materias vinculadas).

Edicion:

- `subjects` y `students`: cualquier usuario autenticado.
- `courses`, `evaluations`, `enrollments`, `evaluation-grades`: `admin` puede editar cualquiera.
- `courses`, `evaluations`, `enrollments`, `evaluation-grades`: `professor` solo puede editar entidades de sus cursos.

## Carga masiva CSV de inscripciones

Endpoint:

- `POST /api/v1/academic/enrollments/bulk-csv`

`multipart/form-data` esperado:

- campo `course_id` (UUID)
- campo `file` (`.csv`)

Encabezados validos CSV:

- carnet: `carnet` o `student_card`
- nombre: `nombre`, `full_name` o `name`

Comportamiento:

- Crea estudiante si no existe (email default `carnet@usb.ve`).
- Si estudiante ya existe, lo reutiliza.
- Crea inscripcion si no existe.
- Devuelve contadores y errores por fila.

## Notas de despliegue

- Existe `vercel.json` para despliegue en Vercel.
- Para produccion se recomienda depender de Alembic como fuente de verdad de esquema y evitar `create_all` en runtime.
