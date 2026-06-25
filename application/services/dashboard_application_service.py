"""
Servicio de Aplicación (DashboardApplicationService).
Implementa el caso de uso del Dashboard (DashboardUseCase) interactuando con los puertos de persistencia y API.
"""
from typing import List, Optional
from dataclasses import dataclass
from domain.entities import IndicadorEconomico, DatoHistorico
from domain.value_objects import Year
from domain.exceptions import ApiCaidaError, DatosNoEncontradosError
from domain.catalog import INDICADOR_CATALOG

from application.ports.inbound.dashboard_use_case import DashboardUseCase
from application.ports.outbound.indicador_repository import IndicadorRepository
from application.ports.outbound.dato_historico_repository import DatoHistoricoRepository
from application.ports.outbound.external_api_repository import ExternalApiRepository
from application.ports.outbound.cache_service_port import CacheServicePort

@dataclass
class DatosIndicadorResult:
    """Representa el resultado de la consulta de un indicador, indicando la procedencia de los datos."""
    datos: List[DatoHistorico]
    fuente_efectiva: str  # "API del Banco Mundial" o "Base de Datos Local (Offline)"

class DashboardApplicationService(DashboardUseCase):
    """
    Controlador central de la aplicación que coordina la persistencia y descargas de red.
    """
    def __init__(
        self,
        indicador_repo: IndicadorRepository,
        dato_historico_repo: DatoHistoricoRepository,
        api_repo: ExternalApiRepository,
        cache_service: CacheServicePort
    ):
        """Inyección de dependencias a través del constructor."""
        self.indicador_repo = indicador_repo
        self.dato_historico_repo = dato_historico_repo
        self.api_repo = api_repo
        self.cache_service = cache_service

    def inicializar_catalogo(self) -> None:
        """
        Registra los indicadores del catálogo predeterminado en la base de datos local.
        Reutiliza los IDs (UUIDs) si ya existen.
        """
        for nombre, meta in INDICADOR_CATALOG.items():
            existente = self.indicador_repo.buscar_por_codigo_externo(meta["codigo"])
            if existente:
                existente.nombre = nombre
                existente.descripcion = meta["descripcion"]
                existente.unidad = meta["unidad"]
                self.indicador_repo.guardar(existente)
            else:
                nuevo = IndicadorEconomico(
                    nombre=nombre,
                    unidad=meta["unidad"],
                    descripcion=meta["descripcion"],
                    codigo_banco_mundial=meta["codigo"]
                )
                self.indicador_repo.guardar(nuevo)

    def obtener_datos_indicador(
        self,
        codigo_externo: str,
        anio_inicio: int,
        anio_fin: int,
        forzar_descarga: bool = False
    ) -> DatosIndicadorResult:
        """
        Coordina la obtención de datos para un indicador en un rango de años.
        Aplica la estrategia de almacenamiento caché e implementa soporte offline.
        """
        indicador = self.indicador_repo.buscar_por_codigo_externo(codigo_externo)
        if not indicador:
            raise DatosNoEncontradosError(f"Indicador con código {codigo_externo} no registrado en el catálogo.")

        tiene_cache = self.cache_service.tiene_datos_en_cache(indicador.id, anio_inicio, anio_fin)

        if tiene_cache and not forzar_descarga:
            datos_locales = self.dato_historico_repo.buscar_serie(
                indicador.id,
                Year(anio_inicio),
                Year(anio_fin)
            )
            if datos_locales:
                return DatosIndicadorResult(
                    datos=datos_locales,
                    fuente_efectiva="Base de Datos Local (Offline)"
                )

        try:
            datos_descargados = self.api_repo.obtener_datos(
                indicador,
                anio_inicio,
                anio_fin
            )

            if datos_descargados:
                self.dato_historico_repo.guardar_serie(datos_descargados)
                self.cache_service.registrar_descarga(
                    indicador.id,
                    anio_inicio,
                    anio_fin
                )
                return DatosIndicadorResult(
                    datos=datos_descargados,
                    fuente_efectiva="API del Banco Mundial"
                )
            
            raise DatosNoEncontradosError(f"La API no retornó registros para {indicador.nombre} en el rango solicitado.")

        except ApiCaidaError as ex:
            print(f"[Offline Mode Fallback] API no disponible: {ex}. Intentando leer de SQLite...")
            datos_locales = self.dato_historico_repo.buscar_serie(
                indicador.id,
                Year(anio_inicio),
                Year(anio_fin)
            )
            if datos_locales:
                return DatosIndicadorResult(
                    datos=datos_locales,
                    fuente_efectiva="Base de Datos Local (Offline)"
                )
            raise DatosNoEncontradosError(
                f"No se pudieron obtener datos de la API ({ex}) ni existen registros locales offline."
            ) from ex

    def obtener_resumen_bd(self) -> dict:
        """
        Genera un resumen técnico del estado de la base de datos local.
        """
        from infrastructure.adapters.outbound.sqlite.connection import RUTA_BD
        import os
        conexion = None
        total_registros = 0
        codigos_con_datos = []
        existe_bd = os.path.exists(RUTA_BD)

        if existe_bd:
            from infrastructure.adapters.outbound.sqlite.connection import get_connection
            try:
                conexion = get_connection()
                cursor = conexion.cursor()
                cursor.execute("SELECT COUNT(*) FROM datos_historicos")
                total_registros = cursor.fetchone()[0]

                cursor.execute("""
                    SELECT DISTINCT i.codigo_banco_mundial 
                    FROM datos_historicos d
                    JOIN indicadores i ON d.indicador_id = i.id
                """)
                codigos_con_datos = [fila[0] for fila in cursor.fetchall() if fila[0]]
            except Exception as ex:
                print(f"Error al obtener resumen de BD: {ex}")
            finally:
                if conexion:
                    conexion.close()

        return {
            "existe": existe_bd,
            "total_registros": total_registros,
            "indicadores": codigos_con_datos,
            "ruta": RUTA_BD
        }

    def obtener_fecha_ultima_descarga(self, codigo_externo: str) -> Optional[str]:
        """
        Retorna la fecha y hora de la última descarga exitosa para un indicador.
        """
        indicador = self.indicador_repo.buscar_por_codigo_externo(codigo_externo)
        if indicador:
            return self.cache_service.obtener_fecha_ultima_descarga(indicador.id)
        return None


def crear_servicio_aplicacion() -> DashboardApplicationService:
    """
    Función fábrica que compone y resuelve las dependencias de infraestructura
    para inyectarlas en el servicio de aplicación.
    """
    from infrastructure.adapters.outbound.sqlite.sqlite_repositories import SQLiteIndicadorRepository, SQLiteDatoHistoricoRepository
    from infrastructure.adapters.outbound.api.worldbank_api_repository import WorldBankApiRepository
    from infrastructure.adapters.outbound.cache.sqlite_cache_service import SQLiteCacheService

    indicador_repo = SQLiteIndicadorRepository()
    dato_historico_repo = SQLiteDatoHistoricoRepository(indicador_repo)
    api_repo = WorldBankApiRepository()
    cache_service = SQLiteCacheService()

    return DashboardApplicationService(
        indicador_repo=indicador_repo,
        dato_historico_repo=dato_historico_repo,
        api_repo=api_repo,
        cache_service=cache_service
    )
