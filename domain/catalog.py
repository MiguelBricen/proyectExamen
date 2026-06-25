"""
Catálogo de Indicadores Socioeconómicos del Dominio.
Define los indicadores soportados oficialmente por el negocio.
"""
from typing import Dict

INDICADOR_CATALOG: Dict[str, dict] = {
    "PIB (USD)": {
        "codigo": "NY.GDP.MKTP.CD",
        "unidad": "USD",
        "descripcion": "Producto Interno Bruto en dólares corrientes. Mide el valor total de bienes y servicios producidos en Nicaragua."
    },
    "Inflación (%)": {
        "codigo": "FP.CPI.TOTL.ZG",
        "unidad": "%",
        "descripcion": "Variación porcentual del Índice de Precios al Consumidor (IPC). Refleja el aumento general de precios en la economía."
    },
    "Desempleo (%)": {
        "codigo": "SL.UEM.TOTL.ZS",
        "unidad": "%",
        "descripcion": "Porcentaje de la fuerza laboral sin empleo. Incluye personas que buscan trabajo activamente."
    },
    "Población Total": {
        "codigo": "SP.POP.TOTL",
        "unidad": "personas",
        "descripcion": "Número total de habitantes en Nicaragua según estimaciones del Banco Mundial."
    },
    "Esperanza de Vida": {
        "codigo": "SP.DYN.LE00.IN",
        "unidad": "años",
        "descripcion": "Promedio de años que se espera que viva un recién nacido si las condiciones de mortalidad actuales se mantienen."
    }
}
