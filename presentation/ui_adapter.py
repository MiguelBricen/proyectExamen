"""
Adaptador de Presentación de UI.
Desacopla los detalles de la interfaz visual (iconos, formatos de texto, caching de UI) del modelo de dominio.
"""
import streamlit as st
import pandas as pd
from typing import Dict
from domain.catalog import INDICADOR_CATALOG
from domain.exceptions import ApiCaidaError, DatosNoEncontradosError

# Atributos específicos de la presentación visual
UI_METADATA = {
    "PIB (USD)": {
        "icono":       "PIB",
        "formato":     "${:,.0f}",
    },
    "Inflación (%)": {
        "icono":       "IPC",
        "formato":     "{:.1f}%",
    },
    "Desempleo (%)": {
        "icono":       "EMP",
        "formato":     "{:.1f}%",
    },
    "Población Total": {
        "icono":       "POB",
        "formato":     "{:,.0f}",
    },
    "Esperanza de Vida": {
        "icono":       "EVD",
        "formato":     "{:.1f} años",
    },
}

# Construir el catálogo completo uniendo el catálogo del dominio con los metadatos de UI
INDICADORES: Dict[str, dict] = {}
for nombre, meta_dominio in INDICADOR_CATALOG.items():
    meta_ui = UI_METADATA.get(nombre, {"icono": "📊", "formato": "{}"})
    INDICADORES[nombre] = {
        "codigo": meta_dominio["codigo"],
        "unidad": meta_dominio["unidad"],
        "descripcion": meta_dominio["descripcion"],
        "icono": meta_ui["icono"],
        "formato": meta_ui["formato"]
    }


def obtener_icono(indicador_nombre: str) -> str:
    """
    Retorna el identificador de ícono / emoji para un indicador.
    """
    if indicador_nombre in INDICADORES:
        return INDICADORES[indicador_nombre]["icono"]
    return "📊"


def formatear_valor(valor: float, unidad: str) -> str:
    """
    Formatea un valor numérico según la unidad del indicador para su visualización en la UI.
    """
    for _, meta in INDICADORES.items():
        if meta["unidad"] == unidad:
            return meta["formato"].format(valor)
    return f"{valor} {unidad}"


def obtener_formato_hover(unidad: str) -> str:
    """
    Genera la plantilla de hover de Plotly para el indicador.
    """
    if unidad == "USD":
        return "%{y:$,.2f}"
    elif unidad == "%":
        return "%{y:.2f}%"
    elif unidad == "personas":
        return "%{y:,.0f}"
    else:
        return "%{y:.2f}"


@st.cache_data(ttl=3600, show_spinner=False)
def obtener_datos_dataframe_ui(_app_service, codigo_externo: str, anio_inicio: int, anio_fin: int) -> pd.DataFrame:
    """
    Obtiene los datos históricos del servicio de aplicación y los transforma
    en un DataFrame de pandas con formato ['año', 'valor'].
    Utiliza el prefijo '_' en _app_service para evitar que Streamlit intente hashear la instancia del servicio.
    """
    try:
        resultado = _app_service.obtener_datos_indicador(
            codigo_externo=codigo_externo,
            anio_inicio=anio_inicio,
            anio_fin=anio_fin,
            forzar_descarga=False
        )
        st.session_state["offline_mode"] = (resultado.fuente_efectiva == "Base de Datos Local (Offline)")
        serie = resultado.datos
    except (ApiCaidaError, DatosNoEncontradosError) as ex:
        st.sidebar.warning(f"⚠️ {ex.mensaje}")
        st.session_state["offline_mode"] = True
        return pd.DataFrame(columns=["año", "valor"])
    except Exception as ex:
        st.sidebar.error(f"❌ Error inesperado: {ex}")
        st.session_state["offline_mode"] = True
        return pd.DataFrame(columns=["año", "valor"])

    if not serie:
        return pd.DataFrame(columns=["año", "valor"])

    rows = [{"año": d.anio.value, "valor": d.valor.value} for d in serie]
    return pd.DataFrame(rows, columns=["año", "valor"])
