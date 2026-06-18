"""
Módulo de Repositorios (Puertos/Interfaces).
Define los puertos de comunicación con los sistemas de persistencia.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities import IndicadorEconomico, DatoHistorico
from domain.value_objects import Year

class IndicadorRepository(ABC):
    """
    Puerto para la persistencia y consulta de Indicadores Económicos.
    """
    @abstractmethod
    def guardar(self, indicador: IndicadorEconomico) -> None:
        """Persiste o actualiza un indicador en el repositorio."""
        pass

    @abstractmethod
    def buscar_por_id(self, id_entidad: str) -> Optional[IndicadorEconomico]:
        """Busca un indicador por su ID de dominio (UUID)."""
        pass

    @abstractmethod
    def buscar_por_codigo_externo(self, codigo: str) -> Optional[IndicadorEconomico]:
        """Busca un indicador por su código externo (Banco Mundial)."""
        pass

    @abstractmethod
    def listar_todos(self) -> List[IndicadorEconomico]:
        """Retorna todos los indicadores registrados."""
        pass


class DatoHistoricoRepository(ABC):
    """
    Puerto para la persistencia y consulta de Datos Históricos (Series).
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
        """Recupera la serie histórica de un indicador en un rango de años."""
        pass


class ExternalApiRepository(ABC):
    """
    Puerto para la obtención de datos desde la API externa.
    """
    @abstractmethod
    def obtener_datos(
        self,
        indicador: IndicadorEconomico,
        anio_inicio: int,
        anio_fin: int
    ) -> List[DatoHistorico]:
        """
        Consulta y descarga los datos desde la API externa del Banco Mundial.
        """
        pass

