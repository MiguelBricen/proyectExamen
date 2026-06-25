"""
Módulo de gestión de migraciones para SQLite.
Permite actualizar (up) y deshacer (down) esquemas de base de datos.
"""
import os
import sqlite3
from infrastructure.adapters.outbound.sqlite.connection import get_connection

# Directorio de scripts SQL de migración
MIGRATIONS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "migrations"
)

def run_migrations():
    """
    Ejecuta todas las migraciones pendientes en orden secuencial.
    """
    from infrastructure.adapters.outbound.sqlite.connection import RUTA_BD
    # Si la base de datos existe pero no tiene la tabla schema_version,
    # significa que es la base de datos vieja sin versionar.
    # La eliminamos para recrearla de forma limpia y aplicar la migración 001.
    if os.path.exists(RUTA_BD):
        conexion_temp = sqlite3.connect(RUTA_BD)
        cursor_temp = conexion_temp.cursor()
        try:
            cursor_temp.execute("SELECT 1 FROM schema_version")
            has_schema_version = True
        except sqlite3.OperationalError:
            has_schema_version = False
        finally:
            conexion_temp.close()
        
        if not has_schema_version:
            print("Base de datos antigua detectada sin control de versiones. Eliminando para recreación limpia...")
            try:
                os.remove(RUTA_BD)
            except Exception as e:
                print(f"Advertencia: No se pudo eliminar el archivo BD directamente: {e}")

    conexion = get_connection()
    cursor = conexion.cursor()

    # Crear la tabla de control de versiones si no existe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version    INTEGER PRIMARY KEY,
            aplicada_en TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
    """)
    conexion.commit()

    migraciones_disponibles = {
        1: {
            "name": "Initial Schema",
            "up_file": "001_initial_schema.sql",
            "down_file": "001_down.sql"
        }
    }

    for version_id, meta in sorted(migraciones_disponibles.items()):
        cursor.execute("SELECT 1 FROM schema_version WHERE version = ?", (version_id,))
        ya_aplicada = cursor.fetchone()

        if not ya_aplicada:
            up_path = os.path.join(MIGRATIONS_DIR, meta["up_file"])
            if not os.path.exists(up_path):
                raise FileNotFoundError(f"No se encuentra el archivo de migración: {up_path}")

            print(f"Aplicando migración {version_id:03d}: {meta['name']}...")
            with open(up_path, "r", encoding="utf-8") as f:
                sql_script = f.read()

            try:
                cursor.executescript(sql_script)
                cursor.execute(
                    "INSERT INTO schema_version (version) VALUES (?)",
                    (version_id,)
                )
                conexion.commit()
                print(f"Migración {version_id:03d} aplicada con éxito.")
            except Exception as e:
                conexion.rollback()
                print(f"Error aplicando migración {version_id:03d}: {e}")
                raise e

    conexion.close()


def rollback_migrations():
    """
    Deshace la última migración aplicada (o todas en orden inverso).
    """
    conexion = get_connection()
    cursor = conexion.cursor()

    # Comprobar si existe la tabla
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='schema_version'
    """)
    if not cursor.fetchone():
        print("No existe tabla de control de versiones. Nada que revertir.")
        conexion.close()
        return

    migraciones_disponibles = {
        1: {
            "name": "Initial Schema",
            "up_file": "001_initial_schema.sql",
            "down_file": "001_down.sql"
        }
    }

    cursor.execute("SELECT version FROM schema_version ORDER BY version DESC")
    aplicadas = [fila[0] for fila in cursor.fetchall()]

    for version_id in aplicadas:
        if version_id in migraciones_disponibles:
            meta = migraciones_disponibles[version_id]
            down_path = os.path.join(MIGRATIONS_DIR, meta["down_file"])

            if not os.path.exists(down_path):
                print(f"Advertencia: Archivo down {meta['down_file']} no existe. Saltando rollback.")
                continue

            print(f"Revirtiendo migración {version_id:03d}: {meta['name']}...")
            with open(down_path, "r", encoding="utf-8") as f:
                sql_script = f.read()

            try:
                cursor.executescript(sql_script)
                cursor.execute("DELETE FROM schema_version WHERE version = ?", (version_id,))
                conexion.commit()
                print(f"Migración {version_id:03d} revertida con éxito.")
            except Exception as e:
                conexion.rollback()
                print(f"Error al revertir migración {version_id:03d}: {e}")
                raise e

    cursor.execute("SELECT COUNT(*) FROM schema_version")
    if cursor.fetchone()[0] == 0:
        cursor.execute("DROP TABLE IF EXISTS schema_version")
        conexion.commit()

    conexion.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "down":
        rollback_migrations()
    else:
        run_migrations()
