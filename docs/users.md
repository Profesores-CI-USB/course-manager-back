# Users — Perfil y credenciales SMTP

Prefijo: `/api/v1/users`

Todos los endpoints requieren autenticación. Operan sobre el usuario que hace la petición (`current_user`).

---

## GET /api/v1/users/me

Retorna el perfil del usuario autenticado.

**Auth:** Bearer token requerido — cualquier rol

**Respuesta 200:**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "email": "profesor@usb.ve",
  "full_name": "Ana Torres",
  "role": "professor",
  "smtp_configured": true,
  "created_at": "2026-01-15T08:30:00Z"
}
```

**Errores:**
| Código | Causa | Ejemplo |
|---|---|---|
| `401` | No autenticado | `{"detail": "Token inválido"}` |

---

## GET /api/v1/users/me/smtp

Retorna el estado de las credenciales SMTP del usuario. No expone la contraseña.

**Auth:** Bearer token requerido — cualquier rol

**Respuesta 200:**
```json
{
  "smtp_email": "profesor@gmail.com",
  "has_password": true
}
```

Si no tiene credenciales configuradas:
```json
{
  "smtp_email": null,
  "has_password": false
}
```

**Errores:**
| Código | Causa | Ejemplo |
|---|---|---|
| `401` | No autenticado | `{"detail": "Token inválido"}` |

---

## PUT /api/v1/users/me/smtp

Guarda o reemplaza las credenciales SMTP del usuario. La contraseña se cifra con Fernet antes de almacenarse.

**Auth:** Bearer token requerido — cualquier rol

**Body:**
```json
{
  "smtp_email": "profesor@gmail.com",
  "smtp_password": "app-password-aqui"
}
```

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `smtp_email` | string (email) | Sí | Cuenta de correo SMTP |
| `smtp_password` | string | Sí | Contraseña o app password (se cifra con Fernet) |

**Respuesta 200:**
```json
{
  "smtp_email": "profesor@gmail.com",
  "has_password": true
}
```

**Errores:**
| Código | Causa | Ejemplo |
|---|---|---|
| `401` | No autenticado | `{"detail": "Token inválido"}` |
| `422` | Email inválido | `{"detail": [{"loc": ["body", "smtp_email"], "msg": "value is not a valid email address"}]}` |
