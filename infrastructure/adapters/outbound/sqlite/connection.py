"""
Módulo de conexión a la base de datos SQLite de infraestructura.
"""
import os
import sqlite3

# Nombre y ruta de la base de datos
NOMBRE_BD = "nicaragua_data.db"

# Subir 5 niveles desde la ubicación actual para llegar a la raíz del proyecto
base_dir = os.path.abspath(__file__)
for _ in range(5):
    base_dir = os.path.dirname(base_dir)

RUTA_BD = os.path.join(base_dir, NOMBRE_BD)

def get_connection() -> sqlite3.Connection:
    """
    Establece conexión con la base de datos SQLite y activa foreign keys.
    """
    conexion = sqlite3.connect(RUTA_BD)
    conexion.execute("PRAGMA foreign_keys = ON;")
    conexion.row_factory = sqlite3.Row
    return conexion
