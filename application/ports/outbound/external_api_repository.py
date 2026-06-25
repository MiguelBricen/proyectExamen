"""
Puerto de Salida (Outbound Port) para la obtención de datos de la API externa.
"""
from abc import ABC, abstractmethod
from typing import List
from domain.entities import IndicadorEconomico, DatoHistorico

class ExternalApiRepository(ABC):
    """
    Puerto para la consulta externa de datos de indicadores.
    """
    @abstractmethod
    def obtener_datos(
        self,
        indicador: IndicadorEconomico,
        anio_inicio: int,
        anio_fin: int
    ) -> List[DatoHistorico]:
        """Consulta y descarga datos desde la API externa del Banco Mundial."""
        pass
