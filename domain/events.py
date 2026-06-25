"""
Módulo de Eventos de Dominio.
Permite el desacoplamiento y comunicación de cambios de estado en el modelo.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Callable, Dict, Type

@dataclass
class DomainEvent:
    """Clase base para todos los eventos de dominio."""
    ocurrido_en: datetime = field(default_factory=datetime.now, init=False)


@dataclass
class IndicadorCreado(DomainEvent):
    indicador_id: str
    codigo_banco_mundial: str
    nombre: str


@dataclass
class DatoHistoricoAgregado(DomainEvent):
    indicador_id: str
    anio: int
    valor: float
    fuente: str


@dataclass
class SerieActualizada(DomainEvent):
    indicador_id: str
    cantidad_puntos: int


class EventDispatcher:
    """
    Despachador/Publicador simple de eventos de dominio para CQRS ligero o logs.
    """
    _listeners: Dict[Type[DomainEvent], List[Callable]] = {}

    @classmethod
    def registrar(cls, event_type: Type[DomainEvent], handler: Callable):
        if event_type not in cls._listeners:
            cls._listeners[event_type] = []
        cls._listeners[event_type].append(handler)

    @classmethod
    def publicar(cls, event: DomainEvent):
        event_type = type(event)
        if event_type in cls._listeners:
            for handler in cls._listeners[event_type]:
                try:
                    handler(event)
                except Exception as e:
                    # En producción se registraría en logs, aquí simplemente capturamos
                    print(f"[Error al manejar evento {event_type.__name__}]: {e}")
