"""
Puerto de Salida (Outbound Port) para la persistencia de Datos Históricos.
"""
from abc import ABC, abstractmethod
from typing import List
from domain.entities import DatoHistorico
from domain.value_objects import Year

class DatoHistoricoRepository(ABC):
    """
    Puerto para almacenar y consultar la serie temporal de datos históricos.
    """
    @abstractmethod
    def guardar_serie(self, datos: List[DatoHistorico]) -> None:
        """Persiste una lista de puntos de datos históricos."""
        pass

    @abstractmethod
    def buscar_serie(
        self,
        indicador_id: str,
        desde: Year,
        hasta: Year
    ) -> List[DatoHistorico]:
        """Recupera la serie de datos históricos en un rango de años."""
        pass
