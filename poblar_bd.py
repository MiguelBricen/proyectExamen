"""
Script para poblar la base de datos local con todos los indicadores utilizando la Arquitectura Hexagonal.
"""
import sys
from infrastructure.adapters.outbound.sqlite.migrations import run_migrations
from application.services.dashboard_application_service import crear_servicio_aplicacion
from domain.catalog import INDICADOR_CATALOG

sys.stdout.reconfigure(encoding="utf-8")

ANIO_INICIO = 1960
ANIO_FIN = 2023

print("=" * 60)
print("Población de Datos (Hexagonal): Banco Mundial -> SQLite")
print("=" * 60)

# 1. Correr migraciones para asegurar el esquema e integridad de datos
print("\nEjecutando migraciones de base de datos...")
run_migrations()
print("Base de datos e integridad listas (CHECK constraints, triggers).")

# 2. Inicializar el servicio de aplicación
servicio = crear_servicio_aplicacion()

# 3. Inicializar catálogo de indicadores en la BD
print("\nInicializando catálogo de indicadores...")
servicio.inicializar_catalogo()

exitosos = 0
total = len(INDICADOR_CATALOG)

# 4. Descargar datos para cada indicador
for nombre, meta in INDICADOR_CATALOG.items():
    codigo = meta["codigo"]
    print(f"\nDescargando serie: {nombre}")
    print(f"  Código externo: {codigo}")

    try:
        # Descarga forzada para poblar o actualizar con datos de la API
        resultado = servicio.obtener_datos_indicador(
            codigo_externo=codigo,
            anio_inicio=ANIO_INICIO,
            anio_fin=ANIO_FIN,
            forzar_descarga=True
        )

        validos = len(resultado.datos)
        print(f"  OK: {validos} registros descargados y validados en dominio.")
        exitosos += 1

    except Exception as e:
        print(f"  ERROR: No se pudieron obtener datos para {nombre}: {e}")

resumen = servicio.obtener_resumen_bd()
print("\n" + "=" * 60)
print("COMPLETADO")
print(f"  Indicadores: {exitosos}/{total} descargados con éxito.")
print(f"  Registros en BD:   {resumen['total_registros']}")
print(f"  Archivo de BD:     {resumen['ruta']}")
print("=" * 60)
print("\nEl dashboard local ya se encuentra poblado y listo para uso offline.")
