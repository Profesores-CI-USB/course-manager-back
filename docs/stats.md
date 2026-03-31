# Stats — Estadísticas y Predicciones IA

Prefijo: `/api/v1/stats`

Todos los endpoints requieren autenticación (`Bearer <access_token>`).

---

## Escala de notas

Las notas se almacenan en escala **0–100** y se reportan en escala **1–5** según:

| Nota (0–100) | Escala |
|---|---|
| 85 – 100 | 5 |
| 70 – 84 | 4 |
| 50 – 69 | 3 |
| 30 – 49 | 2 |
| 0 – 29 | 1 |

Umbral de aprobación: **50** (escala 3).

---

## GET /stats/courses

Retorna estadísticas agregadas por curso.

- **Admin**: ve todos los cursos.
- **Professor**: ve solo sus propios cursos.

### Query params

| Param | Tipo | Requerido | Descripción |
|---|---|---|---|
| `course_id` | UUID | No | Filtrar por un curso específico |

### Respuesta exitosa `200`

```json
{
  "summary": {
    "total_courses": 3,
    "total_enrolled": 75,
    "graded_students": 60,
    "pending_students": 15,
    "global_avg_grade": 67.4,
    "global_avg_scale_grade": 3.12,
    "global_pass_rate": 0.7833,
    "overall_grade_distribution": {
      "five": 10,
      "four": 18,
      "three": 19,
      "two": 8,
      "one": 5,
      "pending": 15
    }
  },
  "courses": [
    {
      "course_id": "uuid",
      "subject_code": "CI3825",
      "subject_name": "Sistemas Operativos",
      "term": "january-march",
      "year": 2026,
      "professor_id": "uuid",
      "total_enrolled": 25,
      "graded_count": 20,
      "avg_final_grade": 71.5,
      "avg_scale_grade": 3.65,
      "pass_rate": 0.8,
      "grade_distribution": {
        "five": 4,
        "four": 8,
        "three": 5,
        "two": 2,
        "one": 1,
        "pending": 5
      },
      "evaluations": {
        "total": 4,
        "fully_graded": 3,
        "completion_rate": 0.75
      }
    }
  ]
}
```

### Errores

| HTTP | Causa |
|---|---|
| `401` | Token ausente o inválido |

---

## POST /stats/predict

Realiza predicciones de notas finales o probabilidad de aprobación para las inscripciones de un curso, usando un modelo IA previamente entrenado.

### Body

```json
{
  "model_config_id": "uuid-del-modelo",
  "course_id": "uuid-del-curso",
  "enrollment_id": null
}
```

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `model_config_id` | UUID | Sí | ID del `AIModelConfig` a usar |
| `course_id` | UUID | Sí | Curso sobre el cual predecir |
| `enrollment_id` | UUID | No | Predecir solo para una inscripción concreta |

### Respuesta exitosa `200`

```json
{
  "model_config_id": "uuid",
  "model_name": "Modelo Regresión v1",
  "model_type": "linear",
  "target": "final_grade",
  "predictions": [
    {
      "enrollment_id": "uuid",
      "student_id": "uuid",
      "student_card": "20-12345",
      "current_partial_grade": 45.5,
      "graded_pct_coverage": 60.0,
      "predicted_final_grade": 72.3,
      "predicted_scale_grade": 4,
      "pass_probability": null
    }
  ]
}
```

Para modelos con `target = "pass_probability"`, `predicted_final_grade` y `predicted_scale_grade` son `null` y `pass_probability` contiene un valor entre 0 y 1.

### Errores

| HTTP | Causa |
|---|---|
| `400` | Modelo no entrenado |
| `403` | El profesor no tiene acceso al curso |
| `404` | Modelo, curso o inscripciones no encontrados |

---

## GET /stats/ai-model-configs

Lista las configuraciones de modelos IA.

- **Admin**: ve todas.
- **Professor**: ve solo las suyas.

### Respuesta exitosa `200`

```json
[
  {
    "id": "uuid",
    "name": "Modelo Regresión v1",
    "description": "Regresión lineal para nota final",
    "model_type": "linear",
    "target": "final_grade",
    "hyperparams": { "max_features": 10, "epochs": 50 },
    "is_trained": true,
    "trained_at": "2026-03-31T10:00:00Z",
    "created_by": "uuid",
    "created_at": "2026-03-30T09:00:00Z",
    "updated_at": "2026-03-31T10:00:00Z"
  }
]
```

---

## POST /stats/ai-model-configs

Crea una nueva configuración de modelo IA.

### Body

```json
{
  "name": "Modelo Regresión v1",
  "description": "Regresión lineal para predecir nota final",
  "model_type": "linear",
  "target": "final_grade",
  "hyperparams": {
    "max_features": 10,
    "epochs": 50,
    "learning_rate": 0.001
  }
}
```

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `name` | string | Sí | Nombre único |
| `description` | string | No | Descripción opcional |
| `model_type` | `"linear"` \| `"dense_nn"` | Sí | Arquitectura del modelo |
| `target` | `"final_grade"` \| `"pass_probability"` | Sí | Variable objetivo |
| `hyperparams` | object | Sí (puede ser `{}`) | Hiperparámetros (ver tabla abajo) |

**Hiperparámetros disponibles:**

| Clave | Default | Descripción |
|---|---|---|
| `max_features` | 10 | Número máximo de evaluaciones como features |
| `epochs` | 50 | Épocas de entrenamiento |
| `learning_rate` | 0.001 | Tasa de aprendizaje |
| `hidden_units` | `[64, 32]` | Tamaños de capas ocultas (solo `dense_nn`) |

### Respuesta exitosa `201`

Mismo esquema que GET list.

### Errores

| HTTP | Causa |
|---|---|
| `409` | Ya existe una configuración con ese nombre |

---

## GET /stats/ai-model-configs/{id}

Obtiene una configuración por ID.

### Errores

| HTTP | Causa |
|---|---|
| `403` | No es el creador ni admin |
| `404` | No encontrada |

---

## PUT /stats/ai-model-configs/{id}

Actualiza nombre, descripción o hiperparámetros. Cambiar `hyperparams` invalida el modelo entrenado (requiere re-entrenamiento).

### Body (todos los campos son opcionales)

```json
{
  "name": "Nuevo nombre",
  "description": "Nueva descripción",
  "hyperparams": { "max_features": 12, "epochs": 100 }
}
```

### Errores

| HTTP | Causa |
|---|---|
| `403` | No es el creador ni admin |
| `404` | No encontrada |
| `409` | Nombre duplicado |

---

## DELETE /stats/ai-model-configs/{id}

Elimina la configuración y sus pesos del sistema de archivos.

### Respuesta exitosa `204`

Sin cuerpo.

### Errores

| HTTP | Causa |
|---|---|
| `403` | No es el creador ni admin |
| `404` | No encontrada |

---

## POST /stats/ai-model-configs/{id}/train

Entrena el modelo usando todos los datos históricos disponibles (inscripciones con nota final registrada).

### Respuesta exitosa `200`

```json
{
  "config_id": "uuid",
  "is_trained": true,
  "trained_at": "2026-03-31T10:00:00Z",
  "samples_used": 142,
  "message": "Modelo entrenado con 142 muestras."
}
```

### Errores

| HTTP | Causa |
|---|---|
| `400` | No hay suficientes datos de entrenamiento |
| `403` | No es el creador ni admin |
| `404` | No encontrada |
