"""
=============================================================
  Dashboard Estadístico de Nicaragua - Banco Mundial (Hexagonal)
=============================================================
  Autor   : Proyecto Examen - Administración de S.O.
  Fecha   : 2026
  Librerías: streamlit, pandas, plotly
  Fuente  : API pública del Banco Mundial (World Bank API)
=============================================================
"""

import streamlit as st
import pandas as pd

# Módulos locales de la nueva arquitectura hexagonal
from application.services import crear_servicio_aplicacion
from domain.exceptions import ApiCaidaError, DatosNoEncontradosError
from presentation.ui_adapter import INDICADORES
from charts import (
    grafico_linea,
    grafico_barras,
    grafico_area,
    tarjetas_estadisticas,
)

# Inicialización única del servicio de aplicación mediante la fábrica de dependencias
app_service = crear_servicio_aplicacion()
app_service.inicializar_catalogo()


# ──────────────────────────────────────────────────────────────
# OBTENCIÓN Y CACHEO DE DATOS EN LA PRESENTACIÓN
# ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def obtener_datos_dataframe(codigo_externo: str, anio_inicio: int, anio_fin: int) -> pd.DataFrame:
    """
    Obtiene los datos históricos del servicio de aplicación y los transforma
    en un DataFrame de pandas con formato ['año', 'valor'].
    """
    try:
        # Intentar obtener los datos (puede descargar de API o cargar de cache SQLite)
        resultado = app_service.obtener_datos_indicador(
            codigo_externo=codigo_externo,
            anio_inicio=anio_inicio,
            anio_fin=anio_fin,
            forzar_descarga=False
        )
        st.session_state["offline_mode"] = (resultado.fuente_efectiva == "Base de Datos Local (Offline)")
        serie = resultado.datos
    except (ApiCaidaError, DatosNoEncontradosError) as ex:
        # Excepciones del dominio capturadas en la UI
        st.sidebar.warning(f"⚠️ {ex.mensaje}")
        st.session_state["offline_mode"] = True
        return pd.DataFrame(columns=["año", "valor"])
    except Exception as ex:
        st.sidebar.error(f"❌ Error inesperado: {ex}")
        st.session_state["offline_mode"] = True
        return pd.DataFrame(columns=["año", "valor"])

    if not serie:
        return pd.DataFrame(columns=["año", "valor"])

    # Transformar a DataFrame para compatibilidad con charts.py
    rows = [{"año": d.anio.value, "valor": d.valor.value} for d in serie]
    return pd.DataFrame(rows, columns=["año", "valor"])


# ──────────────────────────────────────────────────────────────
# DESCARGA MASIVA: POBLAR BASE DE DATOS LOCAL
# ──────────────────────────────────────────────────────────────
def _descargar_todos_los_datos():
    """
    Descarga todos los indicadores del Banco Mundial y los guarda en SQLite.
    Llamado cuando el usuario pulsa el botón del sidebar.
    """
    ANIO_INICIO = 1960
    ANIO_FIN    = 2023

    progreso = st.sidebar.progress(0, text="Iniciando descarga...")
    total    = len(INDICADORES)
    exitosos = 0

    for i, (nombre, meta) in enumerate(INDICADORES.items()):
        codigo = meta["codigo"]
        progreso.progress(
            int((i / total) * 100),
            text=f"⎳ Descargando: {nombre}",
        )

        try:
            # Forzamos la descarga desde el servicio
            app_service.obtener_datos_indicador(
                codigo_externo=codigo,
                anio_inicio=ANIO_INICIO,
                anio_fin=ANIO_FIN,
                forzar_descarga=True
            )
            exitosos += 1
        except Exception as e:
            print(f"Error descargando {nombre} para población: {e}")

    progreso.progress(100, text="✅ ¡Descarga completada!")
    resumen = app_service.obtener_resumen_bd()
    st.sidebar.success(
        f"✅ **{resumen['total_registros']} registros** guardados.\n\n"
        f"{exitosos}/{total} indicadores descargados."
    )
    # Limpiar el caché de Streamlit para forzar recarga
    st.cache_data.clear()
    st.rerun()


# ──────────────────────────────────────────────────────────────
# CONFIGURACIÓN DE LA PÁGINA
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Nicaragua — Banco Mundial",
    page_icon="🇳🇮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Cargar estilos CSS externos
with open("styles.css", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# ENCABEZADO PRINCIPAL
# ──────────────────────────────────────────────────────────────
def mostrar_encabezado():
    """Renderiza el encabezado visual del dashboard con bandera y título."""
    st.markdown(
        """
        <div class="hero-header">
            <div class="hero-flag">🇳🇮</div>
            <div class="hero-text">
                <h1>Dashboard Estadístico</h1>
                <p class="hero-subtitle">
                    Análisis socioeconómico de <strong>Nicaragua</strong>
                    · Datos oficiales del Banco Mundial
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────
# BARRA LATERAL (CONTROLES)
# ──────────────────────────────────────────────────────────────
def construir_sidebar() -> dict:
    """
    Construye el panel lateral con todos los controles de usuario.
    """
    with st.sidebar:
        # Logo / título lateral
        st.markdown(
            """
            <div class="sidebar-logo">
                <span class="sidebar-icon"></span>
                <span class="sidebar-title">Indicadores</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("---")

        # ── Selector de indicador ──────────────────────────────
        st.markdown("###  Indicador económico")
        nombres_indicadores = list(INDICADORES.keys())
        indicador_seleccionado = st.selectbox(
            label="Selecciona un indicador:",
            options=nombres_indicadores,
            index=0,
            help="Elige el indicador que deseas analizar.",
        )
        indicador_clave = INDICADORES[indicador_seleccionado]["codigo"]

        st.markdown("---")

        # ── Rango de años ─────────────────────────────────────
        st.markdown("###  Rango de años")
        col1, col2 = st.columns(2)
        with col1:
            anio_inicio = st.number_input(
                "Desde:", min_value=1960, max_value=2023, value=2000, step=1
            )
        with col2:
            anio_fin = st.number_input(
                "Hasta:", min_value=1960, max_value=2023, value=2023, step=1
            )

        # Validar que el rango sea correcto
        if anio_inicio > anio_fin:
            st.error(" El año inicial no puede ser mayor que el año final.")
            anio_inicio, anio_fin = anio_fin, anio_inicio

        st.markdown("---")

        # ── Tipo de gráfico ───────────────────────────────────
        st.markdown("###  Tipo de visualización")
        tipo_grafico = st.radio(
            label="Elige el formato:",
            options=["Línea", "Barras", "Área"],
            horizontal=False,
            help="Selecciona cómo deseas ver los datos.",
        )

        st.markdown("---")

        # ── Estado de la base de datos local ──────────────────
        st.markdown("### 🗳️ Base de datos local")
        resumen_bd = app_service.obtener_resumen_bd()

        if resumen_bd["total_registros"] > 0:
            st.success(
                f"✅ **{resumen_bd['total_registros']} registros** almacenados\n\n"
                f"Modo offline disponible",
                icon=None,
            )
            # Mostrar fecha de última descarga del indicador actual
            ultima = app_service.obtener_fecha_ultima_descarga(indicador_clave)
            if ultima:
                fecha_fmt = ultima.split(" ")[0]
                st.caption(f"🕒 Última descarga: **{fecha_fmt}**")
        else:
            st.warning(
                "⚠️ Sin datos locales.\n\nUsa el botón para\ndescargar y guardar datos.",
                icon=None,
            )

        # ── Botón: Descargar todos los datos ──────────────────
        if st.button(
            "⬇ Descargar todos los datos",
            help="Descarga todos los indicadores del Banco Mundial y los guarda localmente para uso offline.",
            use_container_width=True,
        ):
            _descargar_todos_los_datos()

        st.markdown("---")

        # ── Información del proyecto ──────────────────────────
        st.markdown(
            """
            <div class="sidebar-info">
                <p> <strong>Fuente de datos</strong></p>
                <p>API del Banco Mundial</p>
                <p>worldbank.org</p>
                <hr>
                <p>🇳🇮 País analizado: <strong>Nicaragua</strong></p>
                <p>Código ISO: <code>NIC</code></p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return {
        "indicador_clave": indicador_clave,
        "indicador_nombre": indicador_seleccionado,
        "anio_inicio": int(anio_inicio),
        "anio_fin": int(anio_fin),
        "tipo_grafico": tipo_grafico,
    }


# ──────────────────────────────────────────────────────────────
# SECCIÓN: ESTADÍSTICAS RESUMIDAS
# ──────────────────────────────────────────────────────────────
def mostrar_estadisticas(df: pd.DataFrame, opciones: dict):
    """
    Muestra las tarjetas de estadísticas (promedio, máx, mín, total).
    """
    st.markdown("##  Estadísticas del período")
    unidad = INDICADORES[opciones["indicador_nombre"]]["unidad"]
    tarjetas_estadisticas(df, unidad)


# ──────────────────────────────────────────────────────────────
# SECCIÓN: GRÁFICO PRINCIPAL
# ──────────────────────────────────────────────────────────────
def mostrar_grafico(df: pd.DataFrame, opciones: dict):
    """
    Renderiza el gráfico interactivo según el tipo elegido.
    """
    st.markdown("##  Evolución histórica")

    indicador_nombre = opciones["indicador_nombre"]
    tipo             = opciones["tipo_grafico"]
    unidad           = INDICADORES[indicador_nombre]["unidad"]
    descripcion      = INDICADORES[indicador_nombre]["descripcion"]

    # Mostrar descripción del indicador
    st.info(f" **{indicador_nombre}**: {descripcion}", icon=None)

    # Renderizar el gráfico según el tipo seleccionado
    if tipo == "Línea":
        fig = grafico_linea(df, indicador_nombre, unidad)
    elif tipo == "Barras":
        fig = grafico_barras(df, indicador_nombre, unidad)
    else:  # Área
        fig = grafico_area(df, indicador_nombre, unidad)

    st.plotly_chart(fig, use_container_width=True)


# ──────────────────────────────────────────────────────────────
# SECCIÓN: TABLA DE DATOS
# ──────────────────────────────────────────────────────────────
def mostrar_tabla(df: pd.DataFrame, opciones: dict):
    """
    Muestra la tabla de datos crudos con opción de descarga CSV.
    """
    with st.expander(" Ver tabla de datos completa", expanded=False):
        col_tabla, col_descarga = st.columns([3, 1])

        with col_tabla:
            unidad = INDICADORES[opciones["indicador_nombre"]]["unidad"]
            # Formatear el DataFrame para mostrar
            df_mostrar = df.copy()
            df_mostrar.columns = ["Año", f"Valor ({unidad})"]
            df_mostrar = df_mostrar.sort_values("Año", ascending=False).reset_index(
                drop=True
            )
            st.dataframe(df_mostrar, use_container_width=True, height=300)

        with col_descarga:
            csv = df_mostrar.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                label="⬇ Descargar CSV",
                data=csv,
                file_name=f"nicaragua_{opciones['indicador_nombre'].replace(' ', '_')}.csv",
                mime="text/csv",
                help="Descarga los datos en formato CSV.",
            )


# ──────────────────────────────────────────────────────────────
# SECCIÓN: COMPARATIVA MULTI-INDICADOR
# ──────────────────────────────────────────────────────────────
def mostrar_resumen_general(anio_inicio: int, anio_fin: int):
    """
    Muestra una vista rápida de todos los indicadores para el
    último año disponible en el rango seleccionado.
    """
    st.markdown("---")
    st.markdown("##  Panorama general — Último valor disponible")

    cols = st.columns(len(INDICADORES))

    for idx, (nombre, meta) in enumerate(INDICADORES.items()):
        with cols[idx]:
            # Obtener datos del indicador (con caché automático)
            df_ind = obtener_datos_dataframe(meta["codigo"], anio_inicio, anio_fin)

            if df_ind is not None and not df_ind.empty:
                ultimo = df_ind.dropna(subset=["valor"]).sort_values("año").iloc[-1]
                valor_fmt = meta["formato"].format(ultimo["valor"])
                anio_fmt  = int(ultimo["año"])

                st.markdown(
                    f"""
                    <div class="mini-card">
                        <div class="mini-card-icon">{meta['icono']}</div>
                        <div class="mini-card-nombre">{nombre}</div>
                        <div class="mini-card-valor">{valor_fmt}</div>
                        <div class="mini-card-anio">Año {anio_fmt}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div class="mini-card mini-card-error">
                        <div class="mini-card-icon">{meta['icono']}</div>
                        <div class="mini-card-nombre">{nombre}</div>
                        <div class="mini-card-valor">Sin datos</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ──────────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL
# ──────────────────────────────────────────────────────────────
def main():
    """
    Punto de entrada principal del dashboard.
    """
    # 1. Encabezado
    mostrar_encabezado()

    # 2. Controles laterales → obtener opciones del usuario
    opciones = construir_sidebar()

    # 3. Cargar datos
    with st.spinner(f" Cargando datos de **{opciones['indicador_nombre']}**..."):
        df = obtener_datos_dataframe(
            codigo_externo=opciones["indicador_clave"],
            anio_inicio=opciones["anio_inicio"],
            anio_fin=opciones["anio_fin"],
        )

    # 4. Manejo de estado offline / errores
    if st.session_state.get("offline_mode", False):
        st.warning(
            "📴 **Sin conexión a Internet** — Mostrando datos almacenados localmente.\n\n"
            "Los datos provienen de la base de datos SQLite local del dispositivo.",
            icon=None,
        )

    if df.empty or df["valor"].isna().all():
        st.warning(
            f" No hay datos disponibles para **{opciones['indicador_nombre']}** "
            f"en el rango {opciones['anio_inicio']} – {opciones['anio_fin']}.",
            icon="",
        )
        st.stop()

    # 5. Mostrar componentes del dashboard
    mostrar_estadisticas(df, opciones)
    mostrar_grafico(df, opciones)
    mostrar_tabla(df, opciones)

    # 6. Panorama general de todos los indicadores
    mostrar_resumen_general(opciones["anio_inicio"], opciones["anio_fin"])

    # 7. Pie de página
    st.markdown(
        """
        <div class="footer">
            🇳🇮 Dashboard Estadístico de Nicaragua &nbsp;·&nbsp;
            Datos: <a href="https://data.worldbank.org" target="_blank">World Bank Open Data</a>
            &nbsp;·&nbsp; Construido con Streamlit & Plotly
        </div>
        """,
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────
# PUNTO DE ENTRADA
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
