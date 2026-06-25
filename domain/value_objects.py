"""
Módulo de Value Objects (VO) para el dominio socioeconómico.
Clases inmutables que encapsulan lógica de validación e integridad.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class Year:
    value: int

    def __post_init__(self):
        # Asegurarse de que el año sea un entero
        if not isinstance(self.value, (int, float)):
            raise TypeError("El año debe ser un número entero.")
        anio_int = int(self.value)
        if not (1900 <= anio_int <= 2100):
            raise ValueError(f"El año {anio_int} está fuera del rango permitido [1900, 2100].")
        # Forzar entero
        object.__setattr__(self, 'value', anio_int)


@dataclass(frozen=True)
class GDP:
    value: float

    def __post_init__(self):
        if not isinstance(self.value, (int, float)):
            raise TypeError("El PIB (GDP) debe ser un número real.")
        val_float = float(self.value)
        if val_float <= 0:
            raise ValueError("El PIB (GDP) debe ser estrictamente mayor que cero.")
        object.__setattr__(self, 'value', val_float)


@dataclass(frozen=True)
class Percentage:
    value: float

    def __post_init__(self):
        if not isinstance(self.value, (int, float)):
            raise TypeError("El porcentaje debe ser un número real.")
        val_float = float(self.value)
        if not (0 <= val_float <= 100):
            raise ValueError(f"El porcentaje {val_float}% debe estar en el rango [0, 100].")
        object.__setattr__(self, 'value', val_float)


@dataclass(frozen=True)
class Population:
    value: int

    def __post_init__(self):
        if not isinstance(self.value, (int, float)):
            raise TypeError("La población debe ser un número entero.")
        val_int = int(self.value)
        if val_int < 0:
            raise ValueError("La población no puede ser negativa.")
        object.__setattr__(self, 'value', val_int)


@dataclass(frozen=True)
class LifeExpectancyYear:
    value: float

    def __post_init__(self):
        if not isinstance(self.value, (int, float)):
            raise TypeError("La esperanza de vida debe ser un número real.")
        val_float = float(self.value)
        if val_float <= 0:
            raise ValueError("La esperanza de vida debe ser estrictamente mayor que cero.")
        object.__setattr__(self, 'value', val_float)


@dataclass(frozen=True)
class Source:
    value: str

    def __post_init__(self):
        if not isinstance(self.value, str):
            raise TypeError("La fuente debe ser una cadena de texto.")
        val_stripped = self.value.strip()
        if not val_stripped:
            raise ValueError("La fuente de datos no puede ser vacía.")
        object.__setattr__(self, 'value', val_stripped)


# Registro OCP que mapea las unidades a sus clases de Value Objects correspondientes
VALOR_VO_REGISTRY = {
    "USD": GDP,
    "%": Percentage,
    "personas": Population,
    "años": LifeExpectancyYear,
}

def crear_valor_vo(valor: float, unidad: str):
    """
    Función de factoría para retornar el Value Object adecuado
    según la unidad del indicador. Abierta para extensión, cerrada para modificación (OCP).
    """
    vo_class = VALOR_VO_REGISTRY.get(unidad)
    if vo_class:
        if vo_class is Population:
            return vo_class(int(valor))
        return vo_class(valor)
    return valor

