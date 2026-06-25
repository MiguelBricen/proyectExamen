"""
Puerto de Entrada (Inbound Port).
Define el caso de uso principal del Dashboard.
"""
from abc import ABC, abstractmethod
from typing import Optional
from domain.entities import DatoHistorico

class DashboardUseCase(ABC):
    """
    Define las operaciones disponibles desde los adaptadores de entrada (UI, CLI, etc.).
    """
    @abstractmethod
    def inicializar_catalogo(self) -> None:
        """Inicializa el catálogo predeterminado de indicadores en la persistencia local."""
        pass

    @abstractmethod
    def obtener_datos_indicador(
        self,
        codigo_externo: str,
        anio_inicio: int,
        anio_fin: int,
        forzar_descarga: bool = False
    ):
        """Obtiene y procesa la serie histórica de un indicador."""
        pass

    @abstractmethod
    def obtener_resumen_bd(self) -> dict:
        """Retorna el resumen técnico de la persistencia local."""
        pass

    @abstractmethod
    def obtener_fecha_ultima_descarga(self, codigo_externo: str) -> Optional[str]:
        """Obtiene la fecha de la última descarga exitosa para un indicador."""
        pass
