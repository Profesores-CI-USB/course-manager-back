# Health — Estado del servicio

Sin prefijo de versión — disponible en la raíz.

---

## GET /health

Verifica que el servidor esté funcionando.

**Auth:** No requerida

**Respuesta 200:**
```json
{
  "status": "ok"
}
```

Útil para health checks en Docker, Kubernetes o load balancers.

---

## GET /

Retorna información básica de la API.

**Auth:** No requerida

**Respuesta 200:**
```json
{
  "name": "Course Manager Backend",
  "docs": "/docs",
  "api_prefix": "/api/v1"
}
```
