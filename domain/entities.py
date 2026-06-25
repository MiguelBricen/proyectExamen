"""
Módulo de Entidades de Dominio.
Contiene la lógica de negocio y las clases base con identidad propia.
"""
import uuid
from typing import List, Optional, Any
from domain.value_objects import Year, Source

class DatoHistorico:
    """
    Entidad que representa un punto de dato en una serie temporal histórica.
    """
    def __init__(
        self,
        indicador_id: str,
        anio: Year,
        valor: Any,  # Puede ser un GDP, Percentage, Population, LifeExpectancyYear
        fuente: Source,
        id_entidad: Optional[str] = None
    ):
        self.id = id_entidad if id_entidad else str(uuid.uuid4())
        self.indicador_id = indicador_id
        self.anio = anio
        self.valor = valor
        self.fuente = fuente

    def __repr__(self):
        return (
            f"DatoHistorico(id={self.id}, indicador_id={self.indicador_id}, "
            f"anio={self.anio.value}, valor={self.valor.value}, fuente={self.fuente.value})"
        )


class IndicadorEconomico:
    """
    Agregado Raíz que representa un indicador socioeconómico.
    """
    def __init__(
        self,
        nombre: str,
        unidad: str,
        descripcion: str,
        codigo_banco_mundial: Optional[str] = None,
        id_entidad: Optional[str] = None,
        datos: Optional[List[DatoHistorico]] = None
    ):
        self.id = id_entidad if id_entidad else str(uuid.uuid4())
        self.codigo_banco_mundial = codigo_banco_mundial
        self.nombre = nombre
        self.unidad = unidad
        self.descripcion = descripcion
        self.datos = datos if datos is not None else []

    def agregar_dato(self, dato: DatoHistorico):
        """Agrega un dato histórico a la lista del indicador."""
        if dato.indicador_id != self.id:
            raise ValueError("El dato histórico no pertenece a este indicador.")
        # Evitar duplicados por año y fuente
        for d in self.datos:
            if d.anio.value == dato.anio.value and d.fuente.value == dato.fuente.value:
                # Actualizar el valor si ya existe
                d.valor = dato.valor
                return
        self.datos.append(dato)

    def __repr__(self):
        return (
            f"IndicadorEconomico(id={self.id}, codigo_externo={self.codigo_banco_mundial}, "
            f"nombre={self.nombre}, unidad={self.unidad})"
        )
