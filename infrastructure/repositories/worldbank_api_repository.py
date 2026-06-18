"""
Adaptador de infraestructura para consumir la API externa del Banco Mundial.
Retorna directamente entidades de dominio limpias y validadas.
"""
import requests
from typing import List
from domain.entities import IndicadorEconomico, DatoHistorico
from domain.value_objects import Year, Source
from domain.repositories import ExternalApiRepository
from domain.exceptions import ApiCaidaError
from infrastructure.repositories.sqlite_repositories import crear_valor_vo

class WorldBankApiRepository(ExternalApiRepository):
    """
    Cliente de infraestructura para la API del Banco Mundial.
    """
    def __init__(self, base_url: str = "https://api.worldbank.org/v2", country_code: str = "NIC"):
        self.base_url = base_url
        self.country_code = country_code

    def obtener_datos(
        self,
        indicador: IndicadorEconomico,
        anio_inicio: int,
        anio_fin: int
    ) -> List[DatoHistorico]:
        """
        Consulta la API para el indicador y rango de años provisto.
        Filtra y omite los registros que no posean valor (evitando nulos).
        """
        if not indicador.codigo_banco_mundial:
            return []

        url = (
            f"{self.base_url}/country/{self.country_code}"
            f"/indicator/{indicador.codigo_banco_mundial}"
            f"?date={anio_inicio}:{anio_fin}"
            f"&format=json"
            f"&per_page=100"
        )

        try:
            respuesta = requests.get(url, timeout=15)
            respuesta.raise_for_status()
            datos_json = respuesta.json()

            if not datos_json or len(datos_json) < 2 or not datos_json[1]:
                return []

            registros = datos_json[1]
            entidades_datos = []

            for reg in registros:
                anio_str = reg.get("date")
                valor_raw = reg.get("value")

                # Regla de integridad: Si el Banco Mundial no reportó valor para un año,
                # no se debe crear el registro (valor no nullable).
                if anio_str is not None and valor_raw is not None:
                    try:
                        anio_vo = Year(int(anio_str))
                        valor_vo = crear_valor_vo(float(valor_raw), indicador.unidad)
                        fuente_vo = Source("Banco Mundial")

                        entidades_datos.append(
                             DatoHistorico(
                                 indicador_id=indicador.id,
                                 anio=anio_vo,
                                 valor=valor_vo,
                                 fuente=fuente_vo
                             )
                        )
                    except (ValueError, TypeError) as val_err:
                        # Omitimos datos que fallen validación de dominio (e.g. años negativos, valores incorrectos)
                        print(f"[API Warning] Dato omitido por validación de dominio: {val_err}")
                        continue

            return entidades_datos

        except requests.exceptions.RequestException as e:
            # En caso de error de red o de HTTP, elevamos una excepción de dominio
            mensaje_error = f"Error al conectar con la API del Banco Mundial para el indicador '{indicador.nombre}': {e}"
            print(f"[API Error] {mensaje_error}")
            raise ApiCaidaError(mensaje_error) from e
        except Exception as e:
            # Otros errores inesperados (parsing, etc.)
            mensaje_error = f"Error inesperado procesando datos de la API para '{indicador.nombre}': {e}"
            print(f"[API Parse Error] {mensaje_error}")
            raise ApiCaidaError(mensaje_error) from e

