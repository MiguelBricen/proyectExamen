"""
=============================================================
  Módulo de Base de Datos Local — SQLite
=============================================================
  Este módulo gestiona la persistencia local de los datos
  del Banco Mundial usando SQLite, siguiendo las prácticas
  del Manual SQLite del proyecto.

  Funciones principales:
    1. Crear/conectar la base de datos nicaragua_data.db
    2. Guardar datos descargados de la API
    3. Recuperar datos almacenados para modo offline
    4. Verificar el estado de la base de datos
=============================================================
"""

import sqlite3
import os
import pandas as pd
from datetime import datetime

# ──────────────────────────────────────────────────────────────
# CONFIGURACIÓN DE LA BASE DE DATOS
# ──────────────────────────────────────────────────────────────

# Nombre del archivo de base de datos SQLite
NOMBRE_BD = "nicaragua_data.db"

# Ruta al archivo de la base de datos (junto al script)
RUTA_BD = os.path.join(os.path.dirname(os.path.abspath(__file__)), NOMBRE_BD)


# ──────────────────────────────────────────────────────────────
# FUNCIÓN: CONECTAR A LA BASE DE DATOS
# ──────────────────────────────────────────────────────────────
def conectar() -> sqlite3.Connection:
    """
    Crea o abre la base de datos SQLite local.

    Si el archivo nicaragua_data.db no existe, lo crea
    automáticamente en el directorio del proyecto.

    Retorna
    -------
    sqlite3.Connection
        Objeto de conexión activa a la base de datos.
    """
    conexion = sqlite3.connect(RUTA_BD)
    # Activar integridad referencial (obligatorio según el manual)
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


# ──────────────────────────────────────────────────────────────
# FUNCIÓN: INICIALIZAR EL ESQUEMA
# ──────────────────────────────────────────────────────────────
def inicializar_base_datos():
    """
    Crea las tablas de la base de datos si no existen.

    Esquema:
      - indicadores : catálogo de los indicadores disponibles
      - datos_historicos : valores anuales por indicador
      - metadatos_cache  : registro de cuándo se descargó cada dato

    Usa IF NOT EXISTS para que sea seguro ejecutar múltiples veces.
    """
    conexion = conectar()
    cursor = conexion.cursor()

    # ── Tabla: indicadores ─────────────────────────────────────
    # Guarda el catálogo de indicadores del Banco Mundial
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS indicadores (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo      TEXT    UNIQUE NOT NULL,
            nombre      TEXT    NOT NULL,
            unidad      TEXT    NOT NULL,
            descripcion TEXT,
            icono       TEXT,
            formato     TEXT
        )
    """)

    # ── Tabla: datos_historicos ────────────────────────────────
    # Almacena los valores anuales descargados de la API
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS datos_historicos (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            indicador_codigo TEXT   NOT NULL,
            anio            INTEGER NOT NULL,
            valor           REAL,
            UNIQUE(indicador_codigo, anio),
            FOREIGN KEY (indicador_codigo) REFERENCES indicadores(codigo)
                ON DELETE CASCADE
        )
    """)

    # ── Tabla: metadatos_cache ─────────────────────────────────
    # Registra la última vez que se descargaron datos para un
    # indicador en un rango de años determinado
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metadatos_cache (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            indicador_codigo TEXT    NOT NULL,
            anio_inicio      INTEGER NOT NULL,
            anio_fin         INTEGER NOT NULL,
            ultima_descarga  TEXT    NOT NULL,
            UNIQUE(indicador_codigo, anio_inicio, anio_fin),
            FOREIGN KEY (indicador_codigo) REFERENCES indicadores(codigo)
                ON DELETE CASCADE
        )
    """)

    conexion.commit()
    conexion.close()


# ──────────────────────────────────────────────────────────────
# FUNCIÓN: GUARDAR CATÁLOGO DE INDICADORES
# ──────────────────────────────────────────────────────────────
def guardar_indicadores(indicadores: dict):
    """
    Inserta o actualiza el catálogo de indicadores en la BD.

    Usa INSERT OR REPLACE para mantener actualizado el catálogo
    sin generar errores si ya existen entradas.

    Parámetros
    ----------
    indicadores : dict
        Diccionario con la misma estructura que INDICADORES
        en data_fetcher.py.
    """
    conexion = conectar()
    cursor = conexion.cursor()

    for nombre, meta in indicadores.items():
        cursor.execute("""
            INSERT OR REPLACE INTO indicadores
                (codigo, nombre, unidad, descripcion, icono, formato)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            meta["codigo"],
            nombre,
            meta["unidad"],
            meta.get("descripcion", ""),
            meta.get("icono", ""),
            meta.get("formato", "{}"),
        ))

    conexion.commit()
    conexion.close()


# ──────────────────────────────────────────────────────────────
# FUNCIÓN: GUARDAR DATOS DESCARGADOS DE LA API
# ──────────────────────────────────────────────────────────────
def guardar_datos(codigo_indicador: str, df: pd.DataFrame,
                  anio_inicio: int, anio_fin: int):
    """
    Persiste en la base de datos local los datos obtenidos de la API.

    Parámetros
    ----------
    codigo_indicador : str
        Código del indicador (ej. 'NY.GDP.MKTP.CD').
    df : pd.DataFrame
        DataFrame con columnas ['año', 'valor'] retornado por la API.
    anio_inicio : int
        Año de inicio del rango descargado.
    anio_fin : int
        Año de fin del rango descargado.
    """
    if df is None or df.empty:
        return

    conexion = conectar()
    cursor = conexion.cursor()

    # Insertar cada fila del DataFrame usando INSERT OR REPLACE
    # para actualizar valores si ya existen (idempotente)
    for _, fila in df.iterrows():
        cursor.execute("""
            INSERT OR REPLACE INTO datos_historicos
                (indicador_codigo, anio, valor)
            VALUES (?, ?, ?)
        """, (
            codigo_indicador,
            int(fila["año"]),
            float(fila["valor"]) if pd.notna(fila["valor"]) else None,
        ))

    # Registrar la descarga en los metadatos del caché
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT OR REPLACE INTO metadatos_cache
            (indicador_codigo, anio_inicio, anio_fin, ultima_descarga)
        VALUES (?, ?, ?, ?)
    """, (codigo_indicador, anio_inicio, anio_fin, ahora))

    conexion.commit()
    conexion.close()


# ──────────────────────────────────────────────────────────────
# FUNCIÓN: RECUPERAR DATOS DESDE LA BASE DE DATOS LOCAL
# ──────────────────────────────────────────────────────────────
def obtener_datos_local(codigo_indicador: str,
                        anio_inicio: int,
                        anio_fin: int) -> pd.DataFrame | None:
    """
    Consulta los datos almacenados localmente para un indicador
    en el rango de años especificado.

    Parámetros
    ----------
    codigo_indicador : str
        Código del indicador del Banco Mundial.
    anio_inicio : int
        Primer año del rango.
    anio_fin : int
        Último año del rango.

    Retorna
    -------
    pd.DataFrame | None
        DataFrame con columnas ['año', 'valor'] si hay datos,
        o None si la base de datos no tiene registros.
    """
    # Verificar que la base de datos existe
    if not os.path.exists(RUTA_BD):
        return None

    conexion = conectar()
    cursor = conexion.cursor()

    # Consultar datos históricos para el indicador y rango de años
    cursor.execute("""
        SELECT anio, valor
        FROM datos_historicos
        WHERE indicador_codigo = ?
          AND anio >= ?
          AND anio <= ?
        ORDER BY anio ASC
    """, (codigo_indicador, anio_inicio, anio_fin))

    filas = cursor.fetchall()
    conexion.close()

    if not filas:
        return None

    # Construir DataFrame con los datos locales
    df = pd.DataFrame(filas, columns=["año", "valor"])
    return df


# ──────────────────────────────────────────────────────────────
# FUNCIÓN: VERIFICAR SI HAY DATOS EN CACHÉ
# ──────────────────────────────────────────────────────────────
def tiene_datos_en_cache(codigo_indicador: str,
                         anio_inicio: int,
                         anio_fin: int) -> bool:
    """
    Verifica si existen datos locales para el indicador y rango.

    Parámetros
    ----------
    codigo_indicador : str
        Código del indicador del Banco Mundial.
    anio_inicio : int
        Primer año del rango.
    anio_fin : int
        Último año del rango.

    Retorna
    -------
    bool
        True si hay al menos un registro en la BD, False si no.
    """
    if not os.path.exists(RUTA_BD):
        return False

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM datos_historicos
        WHERE indicador_codigo = ?
          AND anio >= ?
          AND anio <= ?
          AND valor IS NOT NULL
    """, (codigo_indicador, anio_inicio, anio_fin))

    conteo = cursor.fetchone()[0]
    conexion.close()

    return conteo > 0


# ──────────────────────────────────────────────────────────────
# FUNCIÓN: OBTENER FECHA DE ÚLTIMA DESCARGA
# ──────────────────────────────────────────────────────────────
def fecha_ultima_descarga(codigo_indicador: str) -> str | None:
    """
    Retorna la fecha de la última descarga exitosa de un indicador.

    Parámetros
    ----------
    codigo_indicador : str
        Código del indicador del Banco Mundial.

    Retorna
    -------
    str | None
        Fecha como cadena 'YYYY-MM-DD HH:MM:SS' o None si
        nunca se ha descargado.
    """
    if not os.path.exists(RUTA_BD):
        return None

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT MAX(ultima_descarga) FROM metadatos_cache
        WHERE indicador_codigo = ?
    """, (codigo_indicador,))

    resultado = cursor.fetchone()
    conexion.close()

    if resultado and resultado[0]:
        return resultado[0]
    return None


# ──────────────────────────────────────────────────────────────
# FUNCIÓN: RESUMEN DEL ESTADO DE LA BASE DE DATOS
# ──────────────────────────────────────────────────────────────
def obtener_resumen_bd() -> dict:
    """
    Retorna un resumen del estado actual de la base de datos local.

    Retorna
    -------
    dict
        Diccionario con:
        - existe        : bool, si el archivo .db existe
        - total_registros: int, número total de filas en datos_historicos
        - indicadores   : list de códigos con datos almacenados
        - ruta          : str, ruta absoluta al archivo .db
    """
    resumen = {
        "existe": os.path.exists(RUTA_BD),
        "total_registros": 0,
        "indicadores": [],
        "ruta": RUTA_BD,
    }

    if not resumen["existe"]:
        return resumen

    conexion = conectar()
    cursor = conexion.cursor()

    # Total de registros
    cursor.execute("SELECT COUNT(*) FROM datos_historicos")
    resumen["total_registros"] = cursor.fetchone()[0]

    # Indicadores con datos
    cursor.execute("""
        SELECT DISTINCT indicador_codigo FROM datos_historicos
    """)
    resumen["indicadores"] = [fila[0] for fila in cursor.fetchall()]

    conexion.close()
    return resumen


# ──────────────────────────────────────────────────────────────
# INICIALIZACIÓN AUTOMÁTICA
# ──────────────────────────────────────────────────────────────
# Al importar este módulo, la base de datos y sus tablas se
# crean automáticamente si no existen.
inicializar_base_datos()
