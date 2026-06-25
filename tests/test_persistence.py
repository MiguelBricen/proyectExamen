"""
Pruebas de integración para la persistencia, restricciones de integridad y auditoría.
"""
import os
import sqlite3
import unittest
from unittest.mock import patch

# Mock del archivo de base de datos para no alterar la base de datos real
TEST_DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "test_nicaragua_data.db"
)

# Patch de la ruta de la base de datos antes de importar los componentes
with patch("infrastructure.adapters.outbound.sqlite.connection.RUTA_BD", TEST_DB_PATH):
    from infrastructure.adapters.outbound.sqlite.connection import get_connection
    from infrastructure.adapters.outbound.sqlite.migrations import run_migrations, rollback_migrations
    from infrastructure.adapters.outbound.sqlite.sqlite_repositories import SQLiteIndicadorRepository, SQLiteDatoHistoricoRepository
    from domain.entities import IndicadorEconomico, DatoHistorico
    from domain.value_objects import Year, GDP, Percentage, Source


class TestPersistenceAndAudit(unittest.TestCase):

    def setUp(self):
        # Asegurarse de empezar con una BD limpia
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except Exception:
                pass
        
        # Parchear RUTA_BD en todos los módulos involucrados para redireccionar a la BD de pruebas
        self.patchers = [
            patch("infrastructure.adapters.outbound.sqlite.connection.RUTA_BD", TEST_DB_PATH),
            patch("infrastructure.adapters.outbound.sqlite.migrations.get_connection", get_connection),
            patch("infrastructure.adapters.outbound.sqlite.sqlite_repositories.get_connection", get_connection),
        ]
        for p in self.patchers:
            p.start()

        # Ejecutar migraciones
        run_migrations()
        self.indicador_repo = SQLiteIndicadorRepository()
        self.dato_repo = SQLiteDatoHistoricoRepository(self.indicador_repo)

    def tearDown(self):
        # Detener patches
        for p in self.patchers:
            p.stop()
        
        # Eliminar archivo de BD de pruebas
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except Exception:
                pass

    def test_schema_created_correctly(self):
        conexion = get_connection()
        cursor = conexion.cursor()
        
        # Verificar tablas creadas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tablas = [fila["name"] for fila in cursor.fetchall()]
        conexion.close()

        self.assertIn("indicadores", tablas)
        self.assertIn("datos_historicos", tablas)
        self.assertIn("metadatos_cache_infra", tablas)
        self.assertIn("log_cambios", tablas)

    def test_check_constraints_datos_historicos_anio(self):
        ind = IndicadorEconomico(
            nombre="Indicador Test",
            unidad="%",
            descripcion="Descripción Test",
            codigo_banco_mundial="TEST.CODE"
        )
        self.indicador_repo.guardar(ind)

        conexion = get_connection()
        cursor = conexion.cursor()

        # Insertar año inválido (< 1900) directamente en la BD para probar CHECK constraint
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO datos_historicos (id, indicador_id, anio, valor, fuente)
                VALUES ('d1', ?, 1800, 15.0, 'Banco Mundial')
            """, (ind.id,))
            conexion.commit()

        # Insertar año inválido (> 2100)
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO datos_historicos (id, indicador_id, anio, valor, fuente)
                VALUES ('d2', ?, 2200, 15.0, 'Banco Mundial')
            """, (ind.id,))
            conexion.commit()

        conexion.close()

    def test_check_constraints_datos_historicos_valor_not_null(self):
        ind = IndicadorEconomico(
            nombre="Indicador Test",
            unidad="%",
            descripcion="Descripción Test",
            codigo_banco_mundial="TEST.CODE"
        )
        self.indicador_repo.guardar(ind)

        conexion = get_connection()
        cursor = conexion.cursor()

        # Insertar valor nulo directly to test database-level NOT NULL check
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO datos_historicos (id, indicador_id, anio, valor, fuente)
                VALUES ('d3', ?, 2020, NULL, 'Banco Mundial')
            """, (ind.id,))
            conexion.commit()

        conexion.close()

    def test_triggers_audit_log(self):
        # Guardar un indicador
        ind = IndicadorEconomico(
            nombre="Indicador Test",
            unidad="%",
            descripcion="Descripción Test",
            codigo_banco_mundial="TEST.CODE"
        )
        self.indicador_repo.guardar(ind)

        # Guardar datos
        dato = DatoHistorico(
            indicador_id=ind.id,
            anio=Year(2021),
            valor=Percentage(45.5),
            fuente=Source("FMI")
        )
        self.dato_repo.guardar_serie([dato])

        # Consultar log de cambios
        conexion = get_connection()
        cursor = conexion.cursor()
        cursor.execute("SELECT tabla, registro_id, tipo_operacion, datos_nuevos FROM log_cambios ORDER BY id ASC")
        logs = cursor.fetchall()
        conexion.close()

        # Deberíamos tener al menos 2 registros (1 de indicadores y 1 de datos_historicos)
        self.assertEqual(len(logs), 2)
        
        # Verificar logs de indicadores
        self.assertEqual(logs[0]["tabla"], "indicadores")
        self.assertEqual(logs[0]["tipo_operacion"], "INSERT")
        self.assertEqual(logs[0]["registro_id"], ind.id)

        # Verificar logs de datos
        self.assertEqual(logs[1]["tabla"], "datos_historicos")
        self.assertEqual(logs[1]["tipo_operacion"], "INSERT")
        self.assertEqual(logs[1]["registro_id"], dato.id)

if __name__ == "__main__":
    unittest.main()
