"""
Servicio de Caché Técnico de Infraestructura (Puerto de salida).
Gestiona el estado y metadatos de descargas de forma independiente al dominio.
"""
import uuid
from typing import Optional
from datetime import datetime
from application.ports.outbound.cache_service_port import CacheServicePort
from infrastructure.adapters.outbound.sqlite.connection import get_connection

class SQLiteCacheService(CacheServicePort):
    """
    Controla la expiración y registro de las consultas realizadas a la API externa.
    """

    def registrar_descarga(
        self,
        indicador_id: str,
        anio_inicio: int,
        anio_fin: int
    ) -> None:
        """
        Registra o actualiza la fecha de la última descarga exitosa para un rango de años.
        """
        if anio_inicio > anio_fin:
            raise ValueError("El año de inicio no puede ser mayor que el año de fin.")

        id_cache = str(uuid.uuid4())
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conexion = get_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO metadatos_cache_infra
                    (id, indicador_id, anio_inicio, anio_fin, ultima_descarga)
                VALUES (?, ?, ?, ?, ?)
            """, (id_cache, indicador_id, anio_inicio, anio_fin, ahora))
            conexion.commit()
        except Exception as e:
            conexion.rollback()
            raise e
        finally:
            conexion.close()

    def tiene_datos_en_cache(
        self,
        indicador_id: str,
        anio_inicio: int,
        anio_fin: int
    ) -> bool:
        """
        Verifica si hay datos descargados previamente en la BD local
        para el indicador y rango solicitado.
        """
        conexion = get_connection()
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM datos_historicos
            WHERE indicador_id = ?
              AND anio >= ?
              AND anio <= ?
        """, (indicador_id, anio_inicio, anio_fin))
        conteo = cursor.fetchone()[0]
        conexion.close()
        return conteo > 0

    def obtener_fecha_ultima_descarga(self, indicador_id: str) -> Optional[str]:
        """
        Retorna la fecha de la última descarga exitosa para el indicador.
        """
        conexion = get_connection()
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT MAX(ultima_descarga) FROM metadatos_cache_infra
            WHERE indicador_id = ?
        """, (indicador_id,))
        fila = cursor.fetchone()
        conexion.close()

        if fila and fila[0]:
            return fila[0]
        return None
