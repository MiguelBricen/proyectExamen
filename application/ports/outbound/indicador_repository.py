"""
Puerto de Salida (Outbound Port) para la persistencia de Indicadores.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities import IndicadorEconomico

class IndicadorRepository(ABC):
    """
    Puerto para almacenar y consultar Indicadores Económicos.
    """
    @abstractmethod
    def guardar(self, indicador: IndicadorEconomico) -> None:
        """Persiste o actualiza un indicador."""
        pass

    @abstractmethod
    def buscar_por_id(self, id_entidad: str) -> Optional[IndicadorEconomico]:
        """Busca un indicador por su ID interno."""
        pass

    @abstractmethod
    def buscar_por_codigo_externo(self, codigo: str) -> Optional[IndicadorEconomico]:
        """Busca un indicador por su código externo."""
        pass

    @abstractmethod
    def listar_todos(self) -> List[IndicadorEconomico]:
        """Retorna todos los indicadores registrados."""
        pass
