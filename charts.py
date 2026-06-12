"""
=============================================================
  Módulo de Visualización — Gráficos con Plotly
=============================================================
  Este módulo contiene todas las funciones de visualización:
    1. grafico_linea    → Gráfico de línea temporal
    2. grafico_barras   → Gráfico de barras verticales
    3. grafico_area     → Gráfico de área con gradiente
    4. tarjetas_estadisticas → Métricas resumidas (KPIs)
=============================================================
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st

# ──────────────────────────────────────────────────────────────
# PALETA DE COLORES DEL DASHBOARD
# ──────────────────────────────────────────────────────────────
COLOR_PRIMARIO    = "#00B4D8"   # Azul cian (color principal)
COLOR_SECUNDARIO  = "#0077B6"   # Azul oscuro
COLOR_ACENTO      = "#90E0EF"   # Azul claro (resaltes)
COLOR_FONDO       = "#0D1117"   # Fondo oscuro
COLOR_FONDO_PLOT  = "#161B22"   # Fondo del área de trazado
COLOR_TEXTO       = "#E6EDF3"   # Texto claro
COLOR_CUADRICULA  = "#30363D"   # Líneas de cuadrícula

# Configuración de layout compartida entre todos los gráficos
LAYOUT_BASE = dict(
    paper_bgcolor = COLOR_FONDO_PLOT,
    plot_bgcolor  = COLOR_FONDO_PLOT,
    font          = dict(color=COLOR_TEXTO, family="Inter, Roboto, sans-serif"),
    margin        = dict(l=60, r=30, t=60, b=60),
    xaxis         = dict(
        gridcolor    = COLOR_CUADRICULA,
        linecolor    = COLOR_CUADRICULA,
        title_font   = dict(size=13),
        tickfont     = dict(size=11),
        showgrid     = True,
    ),
    yaxis         = dict(
        gridcolor    = COLOR_CUADRICULA,
        linecolor    = COLOR_CUADRICULA,
        title_font   = dict(size=13),
        tickfont     = dict(size=11),
        showgrid     = True,
        zeroline     = True,
        zerolinecolor= COLOR_CUADRICULA,
    ),
    hovermode     = "x unified",
    legend        = dict(
        bgcolor     = "rgba(0,0,0,0.3)",
        bordercolor = COLOR_CUADRICULA,
        borderwidth = 1,
    ),
)


# ──────────────────────────────────────────────────────────────
# FUNCIÓN AUXILIAR: FORMATEAR HOVER
# ──────────────────────────────────────────────────────────────
def _formato_hover(unidad: str) -> str:
    """
    Genera la plantilla de hover según la unidad del indicador.

    Parámetros
    ----------
    unidad : str
        Unidad de medida (ej. 'USD', '%', 'personas').

    Retorna
    -------
    str
        Plantilla de formato para plotly.
    """
    if unidad == "USD":
        return "%{y:$,.2f}"
    elif unidad == "%":
        return "%{y:.2f}%"
    elif unidad == "personas":
        return "%{y:,.0f}"
    else:
        return "%{y:.2f}"


# ──────────────────────────────────────────────────────────────
# GRÁFICO DE LÍNEA
# ──────────────────────────────────────────────────────────────
def grafico_linea(df: pd.DataFrame, titulo: str, unidad: str) -> go.Figure:
    """
    Crea un gráfico de línea temporal con marcadores interactivos.

    Parámetros
    ----------
    df     : DataFrame con columnas ['año', 'valor']
    titulo : Nombre del indicador (usado como título y leyenda)
    unidad : Unidad de medida del eje Y

    Retorna
    -------
    go.Figure
        Figura de Plotly lista para renderizar.
    """
    df_limpio = df.dropna(subset=["valor"])  # Eliminar filas sin datos

    fig = go.Figure()

    # Trazar la línea principal con marcadores
    fig.add_trace(
        go.Scatter(
            x            = df_limpio["año"],
            y            = df_limpio["valor"],
            mode         = "lines+markers",
            name         = titulo,
            line         = dict(color=COLOR_PRIMARIO, width=3),
            marker       = dict(
                color  = COLOR_PRIMARIO,
                size   = 7,
                line   = dict(color=COLOR_FONDO, width=2),
            ),
            hovertemplate = f"<b>Año %{{x}}</b><br>{titulo}: {_formato_hover(unidad)}<extra></extra>",
        )
    )

    # Actualizar layout con la configuración base
    fig.update_layout(
        **LAYOUT_BASE,
        title = dict(
            text     = f"<b>{titulo}</b> — Evolución histórica en Nicaragua",
            font     = dict(size=16, color=COLOR_TEXTO),
            x        = 0.01,
        ),
        xaxis_title = "Año",
        yaxis_title = f"{titulo} ({unidad})",
    )

    return fig


# ──────────────────────────────────────────────────────────────
# GRÁFICO DE BARRAS
# ──────────────────────────────────────────────────────────────
def grafico_barras(df: pd.DataFrame, titulo: str, unidad: str) -> go.Figure:
    """
    Crea un gráfico de barras verticales con gradiente de color.

    Parámetros
    ----------
    df     : DataFrame con columnas ['año', 'valor']
    titulo : Nombre del indicador
    unidad : Unidad de medida del eje Y

    Retorna
    -------
    go.Figure
        Figura de Plotly lista para renderizar.
    """
    df_limpio = df.dropna(subset=["valor"])

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x             = df_limpio["año"],
            y             = df_limpio["valor"],
            name          = titulo,
            marker        = dict(
                color     = df_limpio["valor"],
                colorscale= [[0, COLOR_SECUNDARIO], [1, COLOR_ACENTO]],
                line      = dict(color=COLOR_FONDO, width=0.5),
            ),
            hovertemplate = f"<b>Año %{{x}}</b><br>{titulo}: {_formato_hover(unidad)}<extra></extra>",
        )
    )

    fig.update_layout(
        **LAYOUT_BASE,
        title = dict(
            text  = f"<b>{titulo}</b> — Comparativa anual en Nicaragua",
            font  = dict(size=16, color=COLOR_TEXTO),
            x     = 0.01,
        ),
        xaxis_title  = "Año",
        yaxis_title  = f"{titulo} ({unidad})",
        bargap       = 0.15,
    )

    return fig


# ──────────────────────────────────────────────────────────────
# GRÁFICO DE ÁREA
# ──────────────────────────────────────────────────────────────
def grafico_area(df: pd.DataFrame, titulo: str, unidad: str) -> go.Figure:
    """
    Crea un gráfico de área con relleno semitransparente bajo la curva.

    Parámetros
    ----------
    df     : DataFrame con columnas ['año', 'valor']
    titulo : Nombre del indicador
    unidad : Unidad de medida del eje Y

    Retorna
    -------
    go.Figure
        Figura de Plotly lista para renderizar.
    """
    df_limpio = df.dropna(subset=["valor"])

    fig = go.Figure()

    # Área rellena (opaca, debajo de la línea)
    fig.add_trace(
        go.Scatter(
            x             = df_limpio["año"],
            y             = df_limpio["valor"],
            mode          = "lines",
            name          = titulo,
            fill          = "tozeroy",
            fillcolor     = "rgba(0, 180, 216, 0.15)",   # Azul semitransparente
            line          = dict(color=COLOR_PRIMARIO, width=2.5),
            hovertemplate = f"<b>Año %{{x}}</b><br>{titulo}: {_formato_hover(unidad)}<extra></extra>",
        )
    )

    # Marcadores sobre la línea
    fig.add_trace(
        go.Scatter(
            x             = df_limpio["año"],
            y             = df_limpio["valor"],
            mode          = "markers",
            name          = "Puntos",
            marker        = dict(
                color     = COLOR_ACENTO,
                size      = 6,
                line      = dict(color=COLOR_FONDO, width=1),
            ),
            hoverinfo     = "skip",  # No mostrar hover duplicado
            showlegend    = False,
        )
    )

    fig.update_layout(
        **LAYOUT_BASE,
        title = dict(
            text  = f"<b>{titulo}</b> — Área temporal en Nicaragua",
            font  = dict(size=16, color=COLOR_TEXTO),
            x     = 0.01,
        ),
        xaxis_title = "Año",
        yaxis_title = f"{titulo} ({unidad})",
    )

    return fig


# ──────────────────────────────────────────────────────────────
# TARJETAS DE ESTADÍSTICAS
# ──────────────────────────────────────────────────────────────
def tarjetas_estadisticas(df: pd.DataFrame, unidad: str):
    """
    Muestra 4 métricas clave del indicador como tarjetas KPI:
    Promedio, Máximo, Mínimo y Último valor.

    Parámetros
    ----------
    df     : DataFrame con columnas ['año', 'valor']
    unidad : Unidad de medida para mostrar en las tarjetas
    """
    df_limpio = df.dropna(subset=["valor"])

    if df_limpio.empty:
        st.warning("No hay suficientes datos para calcular estadísticas.")
        return

    # Calcular estadísticas básicas
    promedio = df_limpio["valor"].mean()
    maximo   = df_limpio["valor"].max()
    minimo   = df_limpio["valor"].min()
    ultimo   = df_limpio.sort_values("año").iloc[-1]["valor"]
    anio_max = int(df_limpio.loc[df_limpio["valor"].idxmax(), "año"])
    anio_min = int(df_limpio.loc[df_limpio["valor"].idxmin(), "año"])
    anio_ult = int(df_limpio.sort_values("año").iloc[-1]["año"])

    # Determinar formato de los números
    def formatear(val: float) -> str:
        """Formatea un número según la unidad de medida."""
        if unidad == "USD":
            if val >= 1e9:
                return f"${val/1e9:.2f}B"
            elif val >= 1e6:
                return f"${val/1e6:.2f}M"
            else:
                return f"${val:,.2f}"
        elif unidad == "%":
            return f"{val:.2f}%"
        elif unidad == "personas":
            if val >= 1e6:
                return f"{val/1e6:.2f}M"
            else:
                return f"{val:,.0f}"
        else:
            return f"{val:.2f}"

    # Mostrar las 4 tarjetas en columnas
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="stat-card stat-card-blue">
                <div class="stat-icon">AVG</div>
                <div class="stat-label">Promedio</div>
                <div class="stat-value">{formatear(promedio)}</div>
                <div class="stat-sub">{unidad}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="stat-card stat-card-green">
                <div class="stat-icon">MAX</div>
                <div class="stat-label">Máximo</div>
                <div class="stat-value">{formatear(maximo)}</div>
                <div class="stat-sub">Año {anio_max}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="stat-card stat-card-red">
                <div class="stat-icon">MIN</div>
                <div class="stat-label">Mínimo</div>
                <div class="stat-value">{formatear(minimo)}</div>
                <div class="stat-sub">Año {anio_min}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
            <div class="stat-card stat-card-purple">
                <div class="stat-icon">ULT</div>
                <div class="stat-label">Último valor</div>
                <div class="stat-value">{formatear(ultimo)}</div>
                <div class="stat-sub">Año {anio_ult}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
