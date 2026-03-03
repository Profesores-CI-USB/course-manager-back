# Plantilla Backend FastAPI

Plantilla lista para usar con:

- FastAPI
- Postgres en Neon (vía `DATABASE_URL` con `sslmode=require`)
- Redis para manejo de sesiones/refresh token
- Autenticación JWT (`access_token` + `refresh_token`)
- SMTP Gmail global y SMTP por usuario
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
│   │   └── user.py            # Modelo User
│   ├── routers/
│   │   ├── auth.py            # Register/login/refresh/logout
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
├── main.py                    # Entry point: expone app para uvicorn/vercel
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

1. Verificar:

- Health: `http://127.0.0.1:8000/health`
- Swagger: `http://127.0.0.1:8000/docs`

> Nota: actualmente la app crea tablas al arrancar (`Base.metadata.create_all` en `init_models`).
> En entornos productivos se recomienda usar migraciones con Alembic (sección siguiente).

## Migraciones de base de datos (Alembic)

Aunque el proyecto crea tablas automáticamente en desarrollo, puedes controlar cambios de esquema con Alembic.

1. Instalar Alembic:

```bash
pip install alembic
```

1. Inicializar Alembic en el proyecto:

```bash
alembic init alembic
```

1. Configurar `alembic.ini`:

- Cambia `sqlalchemy.url` por tu `DATABASE_URL` (Neon).
- Si usas Neon, asegura `sslmode=require` en la URL.

1. Configurar `alembic/env.py` para usar los modelos del proyecto:

- Importa `Base` desde `app.db.base`.
- Importa `app.models` para registrar metadatos.
- Define `target_metadata = Base.metadata`.

1. Crear una migración nueva (autogenerada):

```bash
alembic revision --autogenerate -m "create users table"
```

1. Aplicar migraciones:

```bash
alembic upgrade head
```

1. Revertir una versión (si hace falta):

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
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`

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
