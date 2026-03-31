# AI — Predicciones

Prefijo: `/api/v1/ai`

Módulo de inferencia con modelos de IA. El modelo activo se configura con `AI_MODEL_NAME` en `.env` (por defecto `simple_nn`).

---

## POST /api/v1/ai/predict

Ejecuta una predicción con el modelo activo.

**Auth:** No requerida

### Modelo `simple_nn`

Red neuronal simple con 2 capas ocultas. Recibe exactamente 3 features numéricas y retorna una puntuación entre 0 y 1 con su etiqueta (`positive` / `negative`).

**Body:**
```json
{
  "features": [0.5, -1.2, 3.0]
}
```

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `features` | array de float | Sí | Exactamente 3 valores numéricos |

**Respuesta 200:**
```json
{
  "model": "simple_nn",
  "score": 0.734521,
  "label": "positive"
}
```

| Campo | Descripción |
|---|---|
| `model` | Nombre del modelo usado |
| `score` | Probabilidad entre 0.0 y 1.0 |
| `label` | `"positive"` si score ≥ 0.5, `"negative"` si score < 0.5 |

**Errores:**
| Código | Causa | Ejemplo |
|---|---|---|
| `400` | Número incorrecto de features | `{"detail": "El modelo simple_nn requiere exactamente 3 features"}` |
| `422` | Array vacío o con tipos incorrectos | `{"detail": [{"loc": ["body", "features"], "msg": "..."}]}` |
| `500` | Modelo configurado en `.env` no existe | `{"detail": "Modelo de IA 'nombre_modelo' no registrado"}` |

**Ejemplos adicionales:**

Predicción negativa:
```json
// Request
{ "features": [-2.0, -3.0, -1.5] }

// Response
{
  "model": "simple_nn",
  "score": 0.182340,
  "label": "negative"
}
```

Features inválidas (más de 3):
```json
// Request
{ "features": [1.0, 2.0, 3.0, 4.0] }

// Response 400
{ "detail": "El modelo simple_nn requiere exactamente 3 features" }
```
