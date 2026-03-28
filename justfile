set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

# Muestra la lista de comandos disponibles
default:
    @just --list

# Ejecuta la API en modo desarrollo con recarga automática
run:
    source .venv/bin/activate && uvicorn main:app --reload

# Instala dependencias, aplica migraciones y levanta la API
dev-setup:
  source .venv/bin/activate && pip install -r requirements.txt && alembic upgrade head && uvicorn main:app --reload

# Levanta Postgres y Redis definidos en docker-compose.yml
infra-up:
  docker compose up -d

# Detiene los servicios de infraestructura
infra-down:
  docker compose down

# Limpia infraestructura: baja servicios y elimina volumenes/recursos huerfanos
infra-clean:
  docker compose down --volumes --remove-orphans

# Genera una nueva clave Fernet para SMTP_CREDENTIALS_KEY
generate-fernet-key:
    source .venv/bin/activate && python scripts/generate_fernet_key.py

# Crea o promueve un usuario admin (FULL_NAME es opcional)
create-admin EMAIL PASSWORD FULL_NAME="":
    source .venv/bin/activate && if [[ -n "{{FULL_NAME}}" ]]; then \
      python scripts/create_admin.py --email "{{EMAIL}}" --password "{{PASSWORD}}" --full-name "{{FULL_NAME}}"; \
    else \
      python scripts/create_admin.py --email "{{EMAIL}}" --password "{{PASSWORD}}"; \
    fi

# Aplica todas las migraciones pendientes
migrate-up:
  source .venv/bin/activate && alembic upgrade head

# Revierte la última migración aplicada
migrate-down:
  source .venv/bin/activate && alembic downgrade -1

# Crea una nueva migración autogenerada (ej: just migrate-create "add roles")
migrate-create MESSAGE:
  source .venv/bin/activate && alembic revision --autogenerate -m "{{MESSAGE}}"

# Crea una migración vacía/manual (sin autogenerate)
migrate-create-empty MESSAGE:
  source .venv/bin/activate && alembic revision -m "{{MESSAGE}}"

# Muestra la revisión actual aplicada en la base de datos
migrate-current:
  source .venv/bin/activate && alembic current

# Muestra historial de migraciones
migrate-history:
  source .venv/bin/activate && alembic history

# Muestra heads de migraciones
migrate-heads:
  source .venv/bin/activate && alembic heads

# Muestra estado resumido de migraciones (current + heads)
migrate-status:
  source .venv/bin/activate && alembic current && alembic heads

# Marca una revisión sin ejecutar migraciones (usar con cuidado)
migrate-stamp REVISION:
  source .venv/bin/activate && alembic stamp {{REVISION}}

# Marca la base en el head actual sin ejecutar migraciones (usar con cuidado)
migrate-stamp-head:
  source .venv/bin/activate && alembic stamp head

# Crea migración autogenerada garantizando que la DB esté en head primero
migrate-create-safe MESSAGE:
  source .venv/bin/activate && alembic upgrade head && alembic revision --autogenerate -m "{{MESSAGE}}"

# Sube o baja a una revisión específica
migrate-up-to REVISION:
  source .venv/bin/activate && alembic upgrade {{REVISION}}

migrate-down-to REVISION:
  source .venv/bin/activate && alembic downgrade {{REVISION}}
