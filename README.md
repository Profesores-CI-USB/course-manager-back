# Plantilla Backend FastAPI

Plantilla lista para usar con:

- FastAPI
- Postgres en Neon (vía `DATABASE_URL` con `sslmode=require`)
- Redis para manejo de sesiones/refresh token
- Autenticación JWT (`access_token` + `refresh_token`)
- SMTP Gmail global y SMTP por usuario
- Recuperación/cambio de contraseña
- Roles de usuario (`admin`, `professor`)
- Gestión académica base (materias, cursos, estudiantes, evaluaciones, inscripciones y notas)
- Módulo base para integrar un modelo propio de IA (ejemplo: red neuronal simple)

## Estructura del proyecto

```text
.
├── app/
│   ├── core/
│   │   ├── config.py          # Variables de entorno y configuración global
│   │   └── security.py        # JWT, hash de password, cifrado SMTP
│   ├── db/
│   │   ├── base.py            # Base ORM de SQLAlchemy
│   │   └── session.py         # Engine Async, sesión DB y cliente Redis
│   ├── models/
│   │   ├── user.py            # Modelo User
│   │   └── academic.py        # Modelos académicos
│   ├── routers/
│   │   ├── auth.py            # Auth + recuperación/cambio de clave
│   │   ├── users.py           # Perfil y credenciales SMTP por usuario
│   │   ├── mail.py            # Envío de correo
│   │   ├── ai.py              # Inferencia de IA
│   │   └── health.py          # Health check
│   ├── schemas/               # DTOs de request/response
│   ├── services/
│   │   ├── mail_service.py    # Lógica SMTP
│   │   └── ai_model.py        # Registro e inferencia de modelos IA
│   ├── main_app.py            # Creación de FastAPI e include routers
│   └── __init__.py
├── .env.example
├── justfile                   # Comandos de desarrollo
├── main.py                    # Entry point: expone app para uvicorn/vercel
├── scripts/
│   └── create_admin.py        # Script para crear/promover admin
├── requirements.txt
└── README.md
```

## Cómo ejecutar el proyecto

1. Crear entorno virtual e instalar dependencias:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

1. Copiar variables de entorno:

```bash
cp .env.example .env
```

1. Completar al menos estas variables en `.env`:

- `DATABASE_URL` (Neon)
- `REDIS_URL`
- `JWT_SECRET_KEY`
- `SMTP_CREDENTIALS_KEY` (Fernet)

Opcional (SMTP global fallback):

- `MAIL_DEFAULT_SENDER`
- `MAIL_DEFAULT_PASSWORD`

1. Iniciar Redis local (si no usas uno remoto):

```bash
docker run -d --name course-manager-redis -p 6379:6379 redis:7
```

1. Ejecutar la API:

```bash
uvicorn main:app --reload
```

También puedes usar `just`:

```bash
just run
```

Para preparar todo en un solo comando (instalar dependencias + migrar + ejecutar API):

```bash
just dev-setup
```

1. Verificar:

- Health: `http://127.0.0.1:8000/health`
- Swagger: `http://127.0.0.1:8000/docs`

> Nota: actualmente la app crea tablas al arrancar (`Base.metadata.create_all` en `init_models`).
> En entornos productivos se recomienda usar migraciones con Alembic (sección siguiente).

## Comandos útiles (`justfile`)

- `just dev-setup` → instala dependencias, aplica migraciones y levanta la API.
- `just run` → levanta la API en desarrollo.
- `just create-admin EMAIL PASSWORD [FULL_NAME]` → crea o promueve un usuario admin.
- `just migrate-up` → aplica todas las migraciones pendientes.
- `just migrate-down` → revierte la última migración.
- `just migrate-create "mensaje"` → crea migración autogenerada.
- `just migrate-create-empty "mensaje"` → crea migración vacía/manual.
- `just migrate-current` → muestra la revisión actual aplicada.
- `just migrate-history` → muestra historial de migraciones.
- `just migrate-heads` → muestra heads de migración.
- `just migrate-stamp REVISION` → marca revisión sin ejecutar migraciones.

Ejemplo:

```bash
just create-admin admin@demo.com "ClaveSegura123!" "Admin Principal"
```

## Migraciones de base de datos (Alembic)

Aunque el proyecto crea tablas automáticamente en desarrollo, puedes controlar cambios de esquema con Alembic.

El proyecto ya incluye carpeta `alembic/`, `alembic.ini` y scripts de migración.

`alembic/env.py` ya está configurado para:

- Leer `DATABASE_URL` desde `.env`.
- Convertir `postgresql://` a `postgresql+asyncpg://` cuando aplica.
- Adaptar `sslmode` a `ssl` para compatibilidad con `asyncpg`.

Flujo recomendado:

```bash
alembic revision --autogenerate -m "mensaje"
alembic upgrade head
```

Para revertir una versión:

```bash
alembic downgrade -1
```

Flujo recomendado de trabajo:

- Modifica modelos en `app/models`.
- Genera revisión con `--autogenerate`.
- Revisa el script generado antes de aplicarlo.
- Ejecuta `alembic upgrade head`.

## Endpoints principales

### Auth

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/register-admin` (solo admin autenticado)
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `POST /api/v1/auth/forgot-password`
- `POST /api/v1/auth/reset-password`
- `POST /api/v1/auth/change-password`

Reglas de rol:

- El registro público (`/auth/register`) solo crea `professor`.
- Solo un `admin` puede crear otro `admin` vía `/auth/register-admin`.

### Usuario y SMTP propio

- `GET /api/v1/users/me`
- `GET /api/v1/users/me/smtp`
- `PUT /api/v1/users/me/smtp`

> La contraseña SMTP del usuario se guarda cifrada (Fernet) en la base de datos.
> En SMTP por usuario solo varían correo y contraseña; host, puerto y TLS se toman de la configuración global (`.env`).

### Correo

- `POST /api/v1/mail/send`

Usa SMTP del usuario autenticado si existe; si no, usa SMTP global por `.env`.

### IA

- `POST /api/v1/ai/predict`

Modelo actual: `simple_nn` (red neuronal mínima de ejemplo, 3 features).

## Modelo académico (tablas)

Tablas creadas en inglés:

- `subjects`
- `courses`
- `students`
- `evaluations`
- `enrollments`
- `evaluation_grades`

Reglas principales:

- `subjects.code` es único.
- `students.student_card` usa formato `XX-XXXXX`.
- `courses.term` permitido: `april-july`, `january-march`, `september-december`, `summer`.
- `evaluations.evaluation_type` permitido: `exam`, `homework`, `workshop`, `project`, `report`, `presentation`, `video`.
- Notas (`grade`, `final_grade`) en rango `0-100`.

## Variables nuevas de entorno

Además de las variables existentes, ahora se usan:

- `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES` (default `30`)
- `FRONTEND_URL` (para link de recuperación; default `http://localhost:5173`)

## Cómo agregar y entrenar modelos propios de IA

### 1) Crear y entrenar tu modelo

Recomendación práctica:

- Crea un script de entrenamiento, por ejemplo: `app/services/train_my_model.py`.
- Entrena con tus datos (scikit-learn, PyTorch, TensorFlow, etc.).
- Guarda el artefacto del modelo en disco (ejemplo: `artifacts/my_model.pkl` o `artifacts/model.pt`).

Ejemplo de flujo mínimo con scikit-learn:

```python
# app/services/train_my_model.py
from sklearn.linear_model import LogisticRegression
from sklearn.datasets import make_classification
import joblib

X, y = make_classification(n_samples=500, n_features=8, random_state=42)
model = LogisticRegression(max_iter=1000)
model.fit(X, y)
joblib.dump(model, "artifacts/my_model.pkl")
```

### 2) Integrarlo en la API

En `app/services/ai_model.py`:

1. Crea una clase que herede de `BaseInferenceModel`.
2. Carga el artefacto entrenado en `__init__`.
3. Implementa `predict(features)`.
4. Registra la clase en `MODELS`.

Ejemplo:

```python
class MySklearnModel(BaseInferenceModel):
    name = "my_sklearn_model"

    def __init__(self):
        import joblib
        self.model = joblib.load("artifacts/my_model.pkl")

    def predict(self, features: list[float]) -> dict:
        score = float(self.model.predict_proba([features])[0][1])
        return {
            "model": self.name,
            "score": round(score, 6),
            "label": "positive" if score >= 0.5 else "negative",
        }

MODELS["my_sklearn_model"] = MySklearnModel()
```

### 3) Activarlo por configuración

En `.env`:

```env
AI_MODEL_NAME=my_sklearn_model
```

### 4) Buenas prácticas para entrenamiento

- Separa entrenamiento de inferencia (no entrenar dentro de endpoints).
- Versiona artefactos (`my_model_v1.pkl`, `my_model_v2.pkl`).
- Guarda métricas (accuracy, F1, AUC) y fecha de entrenamiento.
- Valida tamaño y orden de `features` para mantener compatibilidad.
- Si el modelo es pesado, cárgalo una sola vez en memoria al iniciar la app.

## Notas para Gmail SMTP

- Host: `smtp.gmail.com`
- Puerto TLS: `587`
- Recomendado usar **App Password** (no la contraseña normal)
- Requiere 2FA en la cuenta Gmail para App Password
