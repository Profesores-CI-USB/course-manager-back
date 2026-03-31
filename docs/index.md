# API Documentation — Course Manager Backend

Base URL: `http://127.0.0.1:8000`
Swagger interactivo: `http://127.0.0.1:8000/docs`
Prefijo de versión: `/api/v1`

## Autenticación

La mayoría de endpoints requieren un **JWT access token** en el header:

```
Authorization: Bearer <access_token>
```

El token se obtiene en `POST /api/v1/auth/login`.

## Roles

| Rol | Descripción |
|---|---|
| `admin` | Acceso total. Puede crear usuarios, materias, cursos y estudiantes. |
| `professor` | Acceso restringido a sus propios cursos y los recursos asociados. |

## Endpoints por módulo

| Archivo | Módulo | Prefijo |
|---|---|---|
| [auth.md](auth.md) | Autenticación y gestión de contraseñas | `/api/v1/auth` |
| [users.md](users.md) | Perfil y credenciales SMTP del usuario | `/api/v1/users` |
| [academic.md](academic.md) | Materias, cursos, estudiantes, evaluaciones, inscripciones y notas | `/api/v1/academic` |
| [mail.md](mail.md) | Envío de correos por SMTP | `/api/v1/mail` |
| [ai.md](ai.md) | Predicciones con modelos de IA | `/api/v1/ai` |
| [stats.md](stats.md) | Estadísticas de cursos, configuración y entrenamiento de modelos IA, predicciones | `/api/v1/stats` |
| [health.md](health.md) | Estado del servicio | `/health` |

## Códigos de error comunes

| HTTP | Causa |
|---|---|
| `400` | Datos inválidos en el body o lógica de negocio |
| `401` | Token ausente, expirado o inválido |
| `403` | Sin permisos para realizar la acción |
| `404` | Recurso no encontrado |
| `409` | Conflicto (duplicado) |
| `502` | Error al contactar un servicio externo (SMTP) |

Todos los errores retornan:
```json
{ "detail": "Descripción del error" }
```

## Convención de documentación

Cada archivo de módulo documenta sus endpoints con:
- Método y ruta
- Autenticación requerida y roles permitidos
- Parámetros (path, query, body)
- Respuesta exitosa
- Casos de error posibles con ejemplos
