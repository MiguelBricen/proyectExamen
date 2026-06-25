"""
Implementaciones SQLite para IndicadorRepository y DatoHistoricoRepository (Puertos de salida).
Realizan la conversión entre la persistencia relacional y el dominio.
"""
from typing import List, Optional
from application.ports.outbound.indicador_repository import IndicadorRepository
from application.ports.outbound.dato_historico_repository import DatoHistoricoRepository
from domain.entities import IndicadorEconomico, DatoHistorico
from domain.value_objects import (
    Year, Source, GDP, Percentage, Population, LifeExpectancyYear, crear_valor_vo
)
from domain.events import EventDispatcher, IndicadorCreado, DatoHistoricoAgregado, SerieActualizada
from infrastructure.adapters.outbound.sqlite.connection import get_connection


class SQLiteIndicadorRepository(IndicadorRepository):
    """
    Adaptador de persistencia SQLite para el catálogo de indicadores.
    """

    def guardar(self, indicador: IndicadorEconomico) -> None:
        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("SELECT 1 FROM indicadores WHERE id = ?", (indicador.id,))
        existe = cursor.fetchone() is not None

        cursor.execute("""
            INSERT OR REPLACE INTO indicadores 
                (id, codigo_banco_mundial, nombre, unidad, descripcion)
            VALUES (?, ?, ?, ?, ?)
        """, (
            indicador.id,
            indicador.codigo_banco_mundial,
            indicador.nombre,
            indicador.unidad,
            indicador.descripcion
        ))
        conexion.commit()
        conexion.close()

        if not existe:
            EventDispatcher.publicar(
                IndicadorCreado(
                    indicador_id=indicador.id,
                    codigo_banco_mundial=indicador.codigo_banco_mundial or "",
                    nombre=indicador.nombre
                )
            )

    def buscar_por_id(self, id_entidad: str) -> Optional[IndicadorEconomico]:
        conexion = get_connection()
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT id, codigo_banco_mundial, nombre, unidad, descripcion
            FROM indicadores WHERE id = ?
        """, (id_entidad,))
        fila = cursor.fetchone()
        conexion.close()

        if not fila:
            return None

        return IndicadorEconomico(
            id_entidad=fila["id"],
            codigo_banco_mundial=fila["codigo_banco_mundial"],
            nombre=fila["nombre"],
            unidad=fila["unidad"],
            descripcion=fila["descripcion"]
        )

    def buscar_por_codigo_externo(self, codigo: str) -> Optional[IndicadorEconomico]:
        conexion = get_connection()
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT id, codigo_banco_mundial, nombre, unidad, descripcion
            FROM indicadores WHERE codigo_banco_mundial = ?
        """, (codigo,))
        fila = cursor.fetchone()
        conexion.close()

        if not fila:
            return None

        return IndicadorEconomico(
            id_entidad=fila["id"],
            codigo_banco_mundial=fila["codigo_banco_mundial"],
            nombre=fila["nombre"],
            unidad=fila["unidad"],
            descripcion=fila["descripcion"]
        )

    def listar_todos(self) -> List[IndicadorEconomico]:
        conexion = get_connection()
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT id, codigo_banco_mundial, nombre, unidad, descripcion
            FROM indicadores
        """)
        filas = cursor.fetchall()
        conexion.close()

        indicadores = []
        for fila in filas:
            indicadores.append(
                IndicadorEconomico(
                    id_entidad=fila["id"],
                    codigo_banco_mundial=fila["codigo_banco_mundial"],
                    nombre=fila["nombre"],
                    unidad=fila["unidad"],
                    descripcion=fila["descripcion"]
                )
            )
        return indicadores


class SQLiteDatoHistoricoRepository(DatoHistoricoRepository):
    """
    Adaptador de persistencia SQLite para datos históricos.
    """

    def __init__(self, indicador_repo: IndicadorRepository):
        self.indicador_repo = indicador_repo

    def guardar_serie(self, datos: List[DatoHistorico]) -> None:
        if not datos:
            return

        ind_id = datos[0].indicador_id
        indicador = self.indicador_repo.buscar_por_id(ind_id)
        if not indicador:
            raise ValueError(f"Indicador con ID {ind_id} no registrado en la BD.")

        conexion = get_connection()
        cursor = conexion.cursor()

        try:
            for dato in datos:
                if dato.valor is None or dato.valor.value is None:
                    continue

                cursor.execute("""
                    INSERT OR REPLACE INTO datos_historicos 
                        (id, indicador_id, anio, valor, fuente)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    dato.id,
                    dato.indicador_id,
                    dato.anio.value,
                    dato.valor.value,
                    dato.fuente.value
                ))

                EventDispatcher.publicar(
                    DatoHistoricoAgregado(
                        indicador_id=dato.indicador_id,
                        anio=dato.anio.value,
                        valor=dato.valor.value,
                        fuente=dato.fuente.value
                    )
                )

            conexion.commit()

            EventDispatcher.publicar(
                SerieActualizada(
                    indicador_id=ind_id,
                    cantidad_puntos=len(datos)
                )
            )
        except Exception as e:
            conexion.rollback()
            raise e
        finally:
            conexion.close()

    def buscar_serie(
        self,
        indicador_id: str,
        desde: Year,
        hasta: Year
    ) -> List[DatoHistorico]:
        indicador = self.indicador_repo.buscar_por_id(indicador_id)
        if not indicador:
            return []

        conexion = get_connection()
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT id, indicador_id, anio, valor, fuente
            FROM datos_historicos
            WHERE indicador_id = ?
              AND anio >= ?
              AND anio <= ?
            ORDER BY anio ASC
        """, (indicador_id, desde.value, hasta.value))

        filas = cursor.fetchall()
        conexion.close()

        serie = []
        for fila in filas:
            vo_valor = crear_valor_vo(fila["valor"], indicador.unidad)
            serie.append(
                DatoHistorico(
                    id_entidad=fila["id"],
                    indicador_id=fila["indicador_id"],
                    anio=Year(fila["anio"]),
                    valor=vo_valor,
                    fuente=Source(fila["fuente"])
                )
            )
        return serie
