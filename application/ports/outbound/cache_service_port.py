"""
Puerto de Salida (Outbound Port) para el servicio de caché técnico de infraestructura.
"""
from abc import ABC, abstractmethod
from typing import Optional

class CacheServicePort(ABC):
    """
    Puerto para controlar las descargas y expiración de datos en la persistencia local.
    """
    @abstractmethod
    def registrar_descarga(
        self,
        indicador_id: str,
        anio_inicio: int,
        anio_fin: int
    ) -> None:
        """Registra la descarga exitosa de datos en un rango de años."""
        pass

    @abstractmethod
    def tiene_datos_en_cache(
        self,
        indicador_id: str,
        anio_inicio: int,
        anio_fin: int
    ) -> bool:
        """Verifica si ya existen datos registrados localmente para el rango solicitado."""
        pass

    @abstractmethod
    def obtener_fecha_ultima_descarga(self, indicador_id: str) -> Optional[str]:
        """Obtiene la fecha y hora de la última descarga exitosa registrada."""
        pass
