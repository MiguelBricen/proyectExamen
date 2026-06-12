"""Script para poblar la base de datos local con todos los indicadores."""
import sys
import requests
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

from data_fetcher import INDICADORES, CODIGO_PAIS, BASE_URL
from database import (
    inicializar_base_datos,
    guardar_indicadores,
    guardar_datos,
    obtener_resumen_bd,
)

ANIO_INICIO = 1960
ANIO_FIN = 2023

print("=" * 50)
print("Descarga de datos: Banco Mundial -> SQLite")
print("=" * 50)

inicializar_base_datos()
guardar_indicadores(INDICADORES)

exitosos = 0

for nombre, meta in INDICADORES.items():
    codigo = meta["codigo"]
    print(f"\nDescargando: {nombre}")
    print(f"  Codigo: {codigo}")

    url = (
        f"{BASE_URL}/country/{CODIGO_PAIS}"
        f"/indicator/{codigo}"
        f"?date={ANIO_INICIO}:{ANIO_FIN}"
        f"&format=json&per_page=100"
    )

    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        datos = resp.json()

        if datos and len(datos) >= 2 and datos[1]:
            filas = []
            for r in datos[1]:
                if r.get("date") is not None:
                    v = r.get("value")
                    filas.append({
                        "año": int(r["date"]),
                        "valor": float(v) if v is not None else None,
                    })

            df = pd.DataFrame(filas, columns=["año", "valor"])
            df = df.sort_values("año").reset_index(drop=True)
            guardar_datos(codigo, df, ANIO_INICIO, ANIO_FIN)
            validos = df["valor"].notna().sum()
            print(f"  OK: {len(df)} registros ({validos} con valor)")
            exitosos += 1
        else:
            print("  Sin datos en la respuesta.")

    except requests.exceptions.ConnectionError:
        print("\nERROR: Sin conexion a internet.")
        print("Conectate al WiFi e intenta de nuevo.")
        sys.exit(1)
    except Exception as e:
        print(f"  ERROR: {e}")

resumen = obtener_resumen_bd()
print("\n" + "=" * 50)
print("COMPLETADO")
print(f"  Indicadores: {exitosos}/{len(INDICADORES)}")
print(f"  Registros:   {resumen['total_registros']}")
print(f"  Archivo:     nicaragua_data.db")
print("=" * 50)
print("\nEl dashboard ahora funciona sin internet.")
