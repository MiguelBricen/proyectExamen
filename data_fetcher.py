"""
=============================================================
  Módulo de Obtención de Datos — API del Banco Mundial
=============================================================
  Este módulo contiene toda la lógica para:
    1. Definir los indicadores que se consultan
    2. Hacer las peticiones HTTP a la API del Banco Mundial
    3. Limpiar y transformar los datos en DataFrames de pandas
    4. Cachear los resultados para evitar llamadas repetidas
    5. Guardar/recuperar datos en base de datos SQLite local
       para funcionamiento sin conexión a internet
=============================================================
"""

import requests
import pandas as pd
import streamlit as st

# Módulo de base de datos local (SQLite)
from database import (
    guardar_indicadores,
    guardar_datos,
    obtener_datos_local,
    tiene_datos_en_cache,
    fecha_ultima_descarga,
)

# ──────────────────────────────────────────────────────────────
# CONSTANTES DE CONFIGURACIÓN
# ──────────────────────────────────────────────────────────────

CODIGO_PAIS = "NIC"          # Código ISO3 de Nicaragua
NOMBRE_PAIS = "Nicaragua"    # Nombre mostrado en la interfaz
BASE_URL    = "https://api.worldbank.org/v2"  # URL base de la API

# Tiempo en segundos que dura el caché de datos (1 hora)
TIEMPO_CACHE_SEGUNDOS = 3600

# ──────────────────────────────────────────────────────────────
# CATÁLOGO DE INDICADORES
# ──────────────────────────────────────────────────────────────
# Cada indicador tiene:
#   codigo      → identificador oficial del Banco Mundial
#   unidad      → unidad de medida para mostrar en gráficos
#   descripcion → explicación breve para el usuario
#   icono       → emoji representativo
#   formato     → formato de texto para el último valor
# ──────────────────────────────────────────────────────────────
INDICADORES = {
    "PIB (USD)": {
        "codigo":      "NY.GDP.MKTP.CD",
        "unidad":      "USD",
        "descripcion": "Producto Interno Bruto en dólares corrientes. "
                       "Mide el valor total de bienes y servicios producidos en Nicaragua.",
        "icono":       "PIB",
        "formato":     "${:,.0f}",
    },
    "Inflación (%)": {
        "codigo":      "FP.CPI.TOTL.ZG",
        "unidad":      "%",
        "descripcion": "Variación porcentual del Índice de Precios al Consumidor (IPC). "
                       "Refleja el aumento general de precios en la economía.",
        "icono":       "IPC",
        "formato":     "{:.1f}%",
    },
    "Desempleo (%)": {
        "codigo":      "SL.UEM.TOTL.ZS",
        "unidad":      "%",
        "descripcion": "Porcentaje de la fuerza laboral sin empleo. "
                       "Incluye personas que buscan trabajo activamente.",
        "icono":       "EMP",
        "formato":     "{:.1f}%",
    },
    "Población Total": {
        "codigo":      "SP.POP.TOTL",
        "unidad":      "personas",
        "descripcion": "Número total de habitantes en Nicaragua "
                       "según estimaciones del Banco Mundial.",
        "icono":       "POB",
        "formato":     "{:,.0f}",
    },
    "Esperanza de Vida": {
        "codigo":      "SP.DYN.LE00.IN",
        "unidad":      "años",
        "descripcion": "Promedio de años que se espera que viva un recién nacido "
                       "si las condiciones de mortalidad actuales se mantienen.",
        "icono":       "EVD",
        "formato":     "{:.1f} años",
    },
}


# ──────────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL: OBTENER DATOS DE LA API
# ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=TIEMPO_CACHE_SEGUNDOS, show_spinner=False)
def obtener_datos_indicador(
    codigo_indicador: str,
    anio_inicio: int,
    anio_fin: int,
) -> pd.DataFrame | None:
    """
    Consulta la API del Banco Mundial y retorna los datos del indicador
    para Nicaragua en el rango de años especificado.

    Estrategia con base de datos local (modo offline):
      1. Intenta obtener datos de la API del Banco Mundial.
      2. Si la API responde → guarda los datos en SQLite local.
      3. Si no hay conexión → intenta recuperar datos de SQLite.
      4. Si no hay datos locales → retorna None.

    La función usa caché automático de Streamlit para evitar
    múltiples llamadas a la API con los mismos parámetros.

    Parámetros
    ----------
    codigo_indicador : str
        Código del indicador en el Banco Mundial (ej. 'NY.GDP.MKTP.CD').
    anio_inicio : int
        Primer año del rango de consulta.
    anio_fin : int
        Último año del rango de consulta.

    Retorna
    -------
    pd.DataFrame | None
        DataFrame con columnas ['año', 'valor'] si tuvo éxito,
        o None si ocurrió un error de red/API y no hay datos locales.
    """
    # Construir la URL de la API con los parámetros correctos
    # Documentación: https://datahelpdesk.worldbank.org/knowledgebase/articles/898581
    url = (
        f"{BASE_URL}/country/{CODIGO_PAIS}"
        f"/indicator/{codigo_indicador}"
        f"?date={anio_inicio}:{anio_fin}"
        f"&format=json"
        f"&per_page=100"   # Máximo de registros por página
    )

    try:
        # ── 1. Intentar obtener datos de la API ────────────────
        respuesta = requests.get(url, timeout=15)

        # Verificar que la respuesta sea exitosa (código 200)
        respuesta.raise_for_status()

        # Parsear el JSON de respuesta
        datos_json = respuesta.json()

        # La API retorna una lista con 2 elementos:
        # [0] → metadatos de la paginación
        # [1] → lista de registros de datos
        if not datos_json or len(datos_json) < 2:
            return pd.DataFrame(columns=["año", "valor"])

        registros = datos_json[1]

        # Si no hay registros, retornar DataFrame vacío
        if not registros:
            return pd.DataFrame(columns=["año", "valor"])

        # Transformar la lista de registros en un DataFrame limpio
        df = _limpiar_datos(registros)

        # ── 2. Guardar en SQLite para uso offline ──────────────
        # Solo guarda si obtuvo datos válidos de la API
        if df is not None and not df.empty:
            guardar_indicadores(INDICADORES)
            guardar_datos(codigo_indicador, df, anio_inicio, anio_fin)

        return df

    except requests.exceptions.ConnectionError:
        # ── 3. Sin conexión: intentar datos locales ────────────
        return _obtener_datos_offline(codigo_indicador, anio_inicio, anio_fin)

    except requests.exceptions.Timeout:
        # La API tardó demasiado: intentar datos locales
        return _obtener_datos_offline(codigo_indicador, anio_inicio, anio_fin)

    except requests.exceptions.HTTPError:
        # Error HTTP (404, 500, etc.): intentar datos locales
        return _obtener_datos_offline(codigo_indicador, anio_inicio, anio_fin)

    except (KeyError, ValueError, IndexError):
        # Error al parsear la respuesta JSON
        return pd.DataFrame(columns=["año", "valor"])


# ──────────────────────────────────────────────────────────────
# FUNCIÓN AUXILIAR: RECUPERAR DATOS EN MODO OFFLINE
# ──────────────────────────────────────────────────────────────
def _obtener_datos_offline(
    codigo_indicador: str,
    anio_inicio: int,
    anio_fin: int,
) -> pd.DataFrame | None:
    """
    Recupera los datos del indicador desde la base de datos SQLite local.

    Se llama automáticamente cuando la API no está disponible.

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
        Datos locales si existen, o None si la BD está vacía.
    """
    df_local = obtener_datos_local(codigo_indicador, anio_inicio, anio_fin)
    return df_local


# ──────────────────────────────────────────────────────────────
# FUNCIÓN AUXILIAR: LIMPIAR DATOS
# ──────────────────────────────────────────────────────────────
def _limpiar_datos(registros: list) -> pd.DataFrame:
    """
    Transforma la lista de registros crudos de la API en un
    DataFrame de pandas limpio y ordenado.

    La API retorna registros con este formato:
    {
        "date": "2020",       → año como texto
        "value": 13614.5,     → valor numérico (puede ser None)
        "country": {...},     → información del país
        ...
    }

    Parámetros
    ----------
    registros : list
        Lista de diccionarios retornada por la API.

    Retorna
    -------
    pd.DataFrame
        DataFrame con columnas ['año', 'valor'], ordenado por año.
    """
    filas = []

    for registro in registros:
        anio  = registro.get("date")    # Año del registro
        valor = registro.get("value")   # Valor del indicador

        # Incluir solo registros con año válido
        if anio is not None:
            filas.append({
                "año":   int(anio),
                "valor": float(valor) if valor is not None else None,
            })

    # Crear DataFrame, ordenar por año y resetear índice
    df = pd.DataFrame(filas, columns=["año", "valor"])
    df = df.sort_values("año").reset_index(drop=True)

    return df
