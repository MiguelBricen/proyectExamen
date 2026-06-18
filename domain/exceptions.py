"""
Excepciones de dominio personalizadas.
Permiten desacoplar la interfaz y los servicios de excepciones técnicas específicas de infraestructura.
"""

class DomainException(Exception):
    """Excepción base para todos los errores de dominio."""
    pass


class ApiCaidaError(DomainException):
    """Lanzada cuando ocurre un error al consultar el servicio o la API externa."""
    def __init__(self, mensaje: str = "La API externa del Banco Mundial no está disponible o devolvió un error."):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


class DatosNoEncontradosError(DomainException):
    """Lanzada cuando no se encuentran datos ni locales ni en la API para un indicador y rango."""
    def __init__(self, mensaje: str = "No se encontraron datos para el indicador y rango de años solicitados."):
        self.mensaje = mensaje
        super().__init__(self.mensaje)
