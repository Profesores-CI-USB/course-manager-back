# Mail — Envío de correos

Prefijo: `/api/v1/mail`

El servicio usa la jerarquía de credenciales SMTP:
1. Credenciales propias del usuario (configuradas en `PUT /api/v1/users/me/smtp`)
2. Credenciales globales del servidor (`SMTP_*` en `.env`)

Si ninguna está disponible, el endpoint falla con `400`.

---

## POST /api/v1/mail/send

Envía un correo desde la cuenta SMTP del usuario autenticado.

**Auth:** Bearer token requerido — cualquier rol

**Body:**
```json
{
  "to_email": "destinatario@ejemplo.com",
  "subject": "Asunto del correo",
  "body": "Contenido del mensaje en texto plano."
}
```

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `to_email` | string (email) | Sí | Destinatario |
| `subject` | string | Sí | Asunto |
| `body` | string | Sí | Cuerpo en texto plano |

**Respuesta 200:**
```json
{
  "message": "Correo enviado correctamente"
}
```

**Errores:**
| Código | Causa | Ejemplo |
|---|---|---|
| `400` | Credenciales SMTP del usuario incompletas | `{"detail": "Credenciales SMTP del usuario incompletas"}` |
| `400` | Sin SMTP propio ni global configurado | `{"detail": "No hay SMTP por usuario ni SMTP global configurado"}` |
| `401` | No autenticado | `{"detail": "Token inválido"}` |
| `502` | Error de conexión con el servidor SMTP | `{"detail": "Error enviando correo SMTP: [Errno 111] Connection refused"}` |

---

## POST /api/v1/mail/test

Envía un correo de prueba con soporte de Markdown o HTML. **Solo disponible cuando `ENVIRONMENT=development`** (valor por defecto).

**Auth:** Bearer token requerido — cualquier rol

**Body:**
```json
{
  "to_email": "destinatario@ejemplo.com",
  "subject": "Prueba de correo",
  "body": "# Hola\n\nEste es un correo de **prueba** con _Markdown_.",
  "content_type": "markdown"
}
```

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `to_email` | string (email) | Sí | Destinatario |
| `subject` | string | Sí | Asunto |
| `body` | string | Sí | Contenido en Markdown o HTML según `content_type` |
| `content_type` | `"markdown"` \| `"html"` | No | Formato del cuerpo. Default: `"markdown"` |

Cuando `content_type` es `"markdown"`, el cuerpo se convierte a HTML antes de enviarse. El cliente de correo recibe el mensaje con la versión HTML renderizada (con fallback en texto plano).

**Respuesta 200:**
```json
{
  "message": "Correo de prueba enviado correctamente"
}
```

**Errores:**
| Código | Causa | Ejemplo |
|---|---|---|
| `400` | Sin SMTP configurado | `{"detail": "No hay SMTP por usuario ni SMTP global configurado"}` |
| `401` | No autenticado | `{"detail": "Token inválido"}` |
| `403` | Entorno no es desarrollo | `{"detail": "Este endpoint solo está disponible en entorno de desarrollo"}` |
| `502` | Error de conexión SMTP | `{"detail": "Error enviando correo SMTP: ..."}` |

> **Nota:** Para deshabilitar el endpoint en producción, establece `ENVIRONMENT=production` en el `.env`.
