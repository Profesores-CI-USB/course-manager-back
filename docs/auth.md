# Auth — Autenticación y contraseñas

Prefijo: `/api/v1/auth`

---

## POST /api/v1/auth/users

Crea un nuevo usuario. Solo accesible por administradores.

**Auth:** Bearer token requerido — rol `admin`

**Body:**
```json
{
  "email": "profesor@usb.ve",
  "password": "secreto123",
  "full_name": "Ana Torres",
  "role": "professor"
}
```

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `email` | string (email) | Sí | Correo único del usuario |
| `password` | string | Sí | Contraseña en texto plano (se hashea internamente) |
| `full_name` | string | No | Nombre completo |
| `role` | `"admin"` \| `"professor"` | No | Por defecto `"professor"` |

**Respuesta 201:**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "email": "profesor@usb.ve",
  "full_name": "Ana Torres",
  "role": "professor",
  "smtp_configured": false,
  "created_at": "2026-03-31T10:00:00Z"
}
```

**Errores:**
| Código | Causa | Ejemplo |
|---|---|---|
| `401` | No autenticado | `{"detail": "Token inválido"}` |
| `403` | No es admin | `{"detail": "Solo un admin puede crear usuarios"}` |
| `409` | Email duplicado | `{"detail": "El correo ya está registrado"}` |

---

## POST /api/v1/auth/login

Autentica un usuario y retorna tokens de acceso.

**Auth:** No requerida

**Body:**
```json
{
  "email": "admin@usb.ve",
  "password": "secreto123"
}
```

**Respuesta 200:**
```json
{
  "user": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "email": "admin@usb.ve",
    "full_name": "Admin Principal",
    "role": "admin",
    "smtp_configured": false,
    "created_at": "2026-01-01T00:00:00Z"
  },
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
}
```

**Errores:**
| Código | Causa | Ejemplo |
|---|---|---|
| `401` | Credenciales incorrectas | `{"detail": "Credenciales inválidas"}` |

---

## POST /api/v1/auth/refresh

Renueva el access token usando el refresh token. El refresh token anterior es invalidado y se emite uno nuevo.

**Auth:** No requerida

**Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Respuesta 200:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errores:**
| Código | Causa | Ejemplo |
|---|---|---|
| `401` | Token inválido o no es de tipo refresh | `{"detail": "Refresh token inválido"}` |
| `401` | Token revocado (ya fue usado o sesión cerrada) | `{"detail": "Refresh token revocado"}` |

---

## POST /api/v1/auth/logout

Cierra la sesión invalidando el refresh token en Redis.

**Auth:** No requerida (el token se pasa en el body)

**Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Respuesta 200:**
```json
{
  "message": "Sesión cerrada"
}
```

**Errores:**
| Código | Causa | Ejemplo |
|---|---|---|
| `401` | Token no es de tipo refresh | `{"detail": "Refresh token inválido"}` |

---

## POST /api/v1/auth/forgot-password

Inicia el flujo de recuperación de contraseña. Envía un correo con enlace si el email existe. Por seguridad, siempre retorna el mismo mensaje independientemente de si el email existe o no.

**Auth:** No requerida

**Body:**
```json
{
  "email": "profesor@usb.ve"
}
```

**Respuesta 200:**
```json
{
  "message": "Si el correo existe, se enviaron instrucciones para recuperar la contraseña"
}
```

**Errores:**
| Código | Causa | Ejemplo |
|---|---|---|
| `400` | SMTP global no configurado | `{"detail": "SMTP global no configurado para recuperación de contraseña"}` |

---

## POST /api/v1/auth/reset-password

Establece una nueva contraseña usando el token recibido por correo.

**Auth:** No requerida

**Body:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "new_password": "nuevaContraseña456"
}
```

**Respuesta 200:**
```json
{
  "message": "Contraseña actualizada correctamente"
}
```

**Errores:**
| Código | Causa | Ejemplo |
|---|---|---|
| `401` | Token inválido, expirado o de tipo incorrecto | `{"detail": "Token de recuperación inválido"}` |
| `404` | Usuario no encontrado | `{"detail": "Usuario no encontrado"}` |

---

## POST /api/v1/auth/change-password

Cambia la contraseña del usuario autenticado.

**Auth:** Bearer token requerido — cualquier rol

**Body:**
```json
{
  "current_password": "secreto123",
  "new_password": "nuevaContraseña456"
}
```

**Respuesta 200:**
```json
{
  "message": "Contraseña actualizada correctamente"
}
```

**Errores:**
| Código | Causa | Ejemplo |
|---|---|---|
| `401` | Contraseña actual incorrecta | `{"detail": "Contraseña actual inválida"}` |
| `400` | Nueva contraseña igual a la actual | `{"detail": "La nueva contraseña debe ser diferente a la actual"}` |
