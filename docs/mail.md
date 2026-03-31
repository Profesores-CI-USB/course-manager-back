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
