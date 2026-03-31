class AppException(Exception):
    """Base para todas las excepciones de dominio."""

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class NotFoundException(AppException):
    def __init__(self, detail: str = "Recurso no encontrado"):
        super().__init__(detail)


class ForbiddenException(AppException):
    def __init__(self, detail: str = "No tienes permiso para realizar esta acción"):
        super().__init__(detail)


class ConflictException(AppException):
    def __init__(self, detail: str = "Conflicto con el estado actual del recurso"):
        super().__init__(detail)


class BadRequestException(AppException):
    def __init__(self, detail: str = "Solicitud inválida"):
        super().__init__(detail)


class UnauthorizedException(AppException):
    def __init__(self, detail: str = "No autorizado"):
        super().__init__(detail)


class InternalException(AppException):
    def __init__(self, detail: str = "Error interno del servidor"):
        super().__init__(detail)


class BadGatewayException(AppException):
    def __init__(self, detail: str = "Error al contactar un servicio externo"):
        super().__init__(detail)
