"""
Pruebas de integración para repositorios SQLite y servicio de caché.
"""
import os
import unittest
from unittest.mock import patch

# Definir la ruta de la base de datos de pruebas
TEST_DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "test_repositories_data.db"
)

# Parchear RUTA_BD antes de importar
with patch("infrastructure.database.connection.RUTA_BD", TEST_DB_PATH):
    from infrastructure.database.connection import get_connection
    from infrastructure.database.migrations import run_migrations
    from infrastructure.repositories.sqlite_repositories import SQLiteIndicadorRepository, SQLiteDatoHistoricoRepository
    from infrastructure.cache.cache_service import CacheService
    from domain.entities import IndicadorEconomico, DatoHistorico
    from domain.value_objects import Year, Percentage, Source
    from domain.events import EventDispatcher, IndicadorCreado, DatoHistoricoAgregado, SerieActualizada


class TestRepositoriesAndCache(unittest.TestCase):

    def setUp(self):
        # Asegurar BD limpia
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except Exception:
                pass

        # Iniciar parches
        self.patchers = [
            patch("infrastructure.database.connection.RUTA_BD", TEST_DB_PATH),
            patch("infrastructure.database.migrations.get_connection", get_connection),
            patch("infrastructure.repositories.sqlite_repositories.get_connection", get_connection),
            patch("infrastructure.cache.cache_service.get_connection", get_connection),
        ]
        for p in self.patchers:
            p.start()

        # Ejecutar esquema inicial
        run_migrations()

        self.indicador_repo = SQLiteIndicadorRepository()
        self.dato_repo = SQLiteDatoHistoricoRepository(self.indicador_repo)
        self.cache_service = CacheService()

        # Limpiar listeners de eventos para pruebas
        EventDispatcher._listeners = {}

    def tearDown(self):
        # Detener parches
        for p in self.patchers:
            p.stop()

        # Limpiar archivo de base de datos
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except Exception:
                pass

    def test_indicador_repository_lifecycle(self):
        # Captura de eventos
        eventos_creados = []
        EventDispatcher.registrar(IndicadorCreado, lambda e: eventos_creados.append(e))

        ind = IndicadorEconomico(
            nombre="Indicador de Prueba",
            unidad="%",
            descripcion="Descripción del indicador de prueba.",
            codigo_banco_mundial="PRUEBA.IND"
        )

        # 1. Guardar indicador
        self.indicador_repo.guardar(ind)
        self.assertEqual(len(eventos_creados), 1)
        self.assertEqual(eventos_creados[0].indicador_id, ind.id)
        self.assertEqual(eventos_creados[0].codigo_banco_mundial, "PRUEBA.IND")

        # 2. Buscar por ID
        encontrado_id = self.indicador_repo.buscar_por_id(ind.id)
        self.assertIsNotNone(encontrado_id)
        self.assertEqual(encontrado_id.nombre, "Indicador de Prueba")
        self.assertEqual(encontrado_id.codigo_banco_mundial, "PRUEBA.IND")

        # 3. Buscar por código externo
        encontrado_codigo = self.indicador_repo.buscar_por_codigo_externo("PRUEBA.IND")
        self.assertIsNotNone(encontrado_codigo)
        self.assertEqual(encontrado_codigo.id, ind.id)

        # 4. Listar todos
        lista = self.indicador_repo.listar_todos()
        self.assertEqual(len(lista), 1)
        self.assertEqual(lista[0].id, ind.id)

    def test_dato_historico_repository_lifecycle(self):
        ind = IndicadorEconomico(
            nombre="Indicador de Prueba",
            unidad="%",
            descripcion="Descripción",
            codigo_banco_mundial="PRUEBA.IND"
        )
        self.indicador_repo.guardar(ind)

        # Captura de eventos
        datos_agregados = []
        series_actualizadas = []
        EventDispatcher.registrar(DatoHistoricoAgregado, lambda e: datos_agregados.append(e))
        EventDispatcher.registrar(SerieActualizada, lambda e: series_actualizadas.append(e))

        dato1 = DatoHistorico(
            indicador_id=ind.id,
            anio=Year(2020),
            valor=Percentage(12.5),
            fuente=Source("Banco Mundial")
        )
        dato2 = DatoHistorico(
            indicador_id=ind.id,
            anio=Year(2021),
            valor=Percentage(15.0),
            fuente=Source("Banco Mundial")
        )

        # 1. Guardar serie
        self.dato_repo.guardar_serie([dato1, dato2])
        self.assertEqual(len(datos_agregados), 2)
        self.assertEqual(len(series_actualizadas), 1)
        self.assertEqual(series_actualizadas[0].cantidad_puntos, 2)

        # 2. Buscar serie
        serie = self.dato_repo.buscar_serie(ind.id, Year(2020), Year(2021))
        self.assertEqual(len(serie), 2)
        self.assertEqual(serie[0].anio.value, 2020)
        self.assertEqual(serie[0].valor.value, 12.5)
        self.assertEqual(serie[1].anio.value, 2021)
        self.assertEqual(serie[1].valor.value, 15.0)

        # Buscar fuera del rango
        serie_vacia = self.dato_repo.buscar_serie(ind.id, Year(2018), Year(2019))
        self.assertEqual(len(serie_vacia), 0)

    def test_cache_service_lifecycle(self):
        ind = IndicadorEconomico(
            nombre="Indicador de Prueba",
            unidad="%",
            descripcion="Descripción",
            codigo_banco_mundial="PRUEBA.IND"
        )
        self.indicador_repo.guardar(ind)

        # 1. Verificar inicialmente sin caché
        self.assertFalse(self.cache_service.tiene_datos_en_cache(ind.id, 2010, 2020))
        self.assertIsNone(self.cache_service.obtener_fecha_ultima_descarga(ind.id))

        # 2. Registrar descarga en metadatos
        self.cache_service.registrar_descarga(ind.id, 2010, 2020)
        self.assertIsNotNone(self.cache_service.obtener_fecha_ultima_descarga(ind.id))

        # 3. Guardar un dato para verificar tiene_datos_en_cache
        dato = DatoHistorico(
            indicador_id=ind.id,
            anio=Year(2015),
            valor=Percentage(5.5),
            fuente=Source("Banco Mundial")
        )
        self.dato_repo.guardar_serie([dato])

        # Verificar que tiene_datos_en_cache retorne True porque existe el registro en el rango
        self.assertTrue(self.cache_service.tiene_datos_en_cache(ind.id, 2010, 2020))
        # Pero retorne False para un rango fuera
        self.assertFalse(self.cache_service.tiene_datos_en_cache(ind.id, 2021, 2025))


class TestDashboardApplicationService(unittest.TestCase):

    def setUp(self):
        # Asegurar BD limpia
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except Exception:
                pass

        # Iniciar parches
        self.patchers = [
            patch("infrastructure.database.connection.RUTA_BD", TEST_DB_PATH),
            patch("infrastructure.database.migrations.get_connection", get_connection),
            patch("infrastructure.repositories.sqlite_repositories.get_connection", get_connection),
            patch("infrastructure.cache.cache_service.get_connection", get_connection),
        ]
        for p in self.patchers:
            p.start()

        # Ejecutar esquema inicial
        run_migrations()

        # Usar la fábrica para crear el servicio con inyección de dependencias
        from application.services import crear_servicio_aplicacion
        self.service = crear_servicio_aplicacion()
        self.service.inicializar_catalogo()

    def tearDown(self):
        for p in self.patchers:
            p.stop()

        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except Exception:
                pass

    def test_obtener_datos_fallback_offline(self):
        from domain.exceptions import DatosNoEncontradosError
        
        # 1. Al consultar un indicador sin caché ni red, debe lanzar DatosNoEncontradosError (porque la API fallará/no hay internet)
        with self.assertRaises(DatosNoEncontradosError):
            self.service.obtener_datos_indicador("FP.CPI.TOTL.ZG", 2000, 2020, forzar_descarga=True)

        # 2. Ahora simulamos datos guardados en SQLite
        indicador = self.service.indicador_repo.buscar_por_codigo_externo("FP.CPI.TOTL.ZG")
        self.assertIsNotNone(indicador)

        dato = DatoHistorico(
            indicador_id=indicador.id,
            anio=Year(2010),
            valor=Percentage(4.5),
            fuente=Source("Banco Mundial")
        )
        self.service.dato_historico_repo.guardar_serie([dato])

        # 3. Al consultar con cache existente, debe retornar los datos de SQLite con la fuente efectiva correcta
        res = self.service.obtener_datos_indicador("FP.CPI.TOTL.ZG", 2010, 2010)
        self.assertEqual(res.fuente_efectiva, "Base de Datos Local (Offline)")
        self.assertEqual(len(res.datos), 1)
        self.assertEqual(res.datos[0].valor.value, 4.5)


if __name__ == "__main__":
    unittest.main()

